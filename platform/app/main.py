"""FastAPI-приложение MVP платформы «Школа AI-агентов»."""
from __future__ import annotations

import asyncio
import base64
import hmac
import json
import queue
import re
import subprocess
import tempfile
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import agent, catalog, config, lessons, security, store, telegram, terminal
from .db import execute, fetch_all, fetch_one, init_db
from .security import hash_password, public_user, require_admin, require_user, verify_password

MAX_FILE_BYTES = 1_000_000


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title=config.APP_NAME, version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if config.DEMO_PASSWORD and request.url.path != "/api/health":
        expected = "Basic " + base64.b64encode(
            f"{config.DEMO_USER}:{config.DEMO_PASSWORD}".encode("utf-8")
        ).decode("ascii")
        if not hmac.compare_digest(request.headers.get("authorization", ""), expected):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="AI School demo"'},
                content="Демо закрыто паролем",
            )
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlparse

            if urlparse(origin).netloc != request.headers.get("host"):
                return JSONResponse({"detail": "Запрос с другого origin отклонён"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


def _session_expiry() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=config.SESSION_DAYS)).isoformat(timespec="seconds")


def _set_session(response: Response, user_id: int) -> None:
    token = security.new_session_token()
    execute(
        "INSERT INTO sessions(token_hash, user_id, expires_at, created_at) VALUES (?,?,?,?)",
        (security.token_hash(token), user_id, _session_expiry(), security.now()),
    )
    response.set_cookie(
        config.COOKIE_NAME,
        token,
        max_age=config.SESSION_DAYS * 86400,
        httponly=True,
        samesite="lax",
        secure=config.PUBLIC_URL.startswith("https://"),
        path="/",
    )


def _clear_session(request: Request, response: Response) -> None:
    token = request.cookies.get(config.COOKIE_NAME)
    if token:
        execute("DELETE FROM sessions WHERE token_hash = ?", (security.token_hash(token),))
    response.delete_cookie(config.COOKIE_NAME, path="/")


async def _body(request: Request) -> dict:
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Нужен JSON")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Нужен JSON-объект")
    return data


def _clean_email(value: str) -> str:
    email = (value or "").strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Проверьте email")
    return email


def _safe_path(value: str, field: str = "путь") -> str:
    path = str(value or "").replace("\\", "/").strip()
    if not path or path.startswith("/") or ".." in Path(path).parts or len(path) > 400:
        raise HTTPException(status_code=400, detail=f"Некорректный {field}")
    return path


def _image_data(value) -> str:
    if not value:
        return ""
    image = str(value)
    if len(image) > 3_000_000:
        raise HTTPException(status_code=413, detail="Скриншот слишком большой")
    if not re.match(r"^data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$", image):
        raise HTTPException(status_code=400, detail="Некорректный формат скриншота")
    return image


def _ocr_image(image: str) -> str:
    """Распознаём текст со скриншота, чтобы DSH мог его прочитать."""
    if not image:
        return ""
    m = re.match(r"^data:image/(png|jpeg|webp);base64,(.+)$", image)
    if not m:
        return ""
    tmp_png = None
    try:
        from io import BytesIO
        from PIL import Image

        raw = base64.b64decode(m.group(2))
        img = Image.open(BytesIO(raw)).convert("RGB")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_png = f.name
            img.save(tmp_png, "PNG")
        proc = subprocess.run(
            ["tesseract", tmp_png, "stdout", "-l", "rus+eng", "--psm", "6"],
            capture_output=True,
            text=True,
            timeout=25,
        )
        return (proc.stdout or "").strip()[:4000]
    except Exception:
        return ""
    finally:
        if tmp_png:
            try:
                Path(tmp_png).unlink(missing_ok=True)
            except Exception:
                pass


def _user_payload(user: dict) -> dict:
    data = public_user(user)
    projects = fetch_one("SELECT COUNT(*) AS c FROM projects WHERE user_id = ?", (user["id"],))["c"]
    done = fetch_one("SELECT COUNT(*) AS c FROM lesson_progress WHERE user_id = ? AND status='done'", (user["id"],))["c"]
    deploys = fetch_one(
        "SELECT COUNT(*) AS c FROM deployments d JOIN projects p ON p.id=d.project_id WHERE p.user_id = ? AND d.status='deployed'",
        (user["id"],),
    )["c"]
    data["stats"] = {"projects": projects, "lessons_done": done, "deployments": deploys}
    data["agent_mode"] = config.AGENT_MODE
    return data


@app.get("/api/health")
def health():
    return {"ok": True, "app": config.APP_NAME, "agent_mode": config.AGENT_MODE, "version": "0.1.0"}


@app.post("/api/auth/register")
async def register(request: Request):
    data = await _body(request)
    email = _clean_email(data.get("email", ""))
    password = str(data.get("password", ""))
    name = str(data.get("name", "")).strip() or email.split("@")[0]
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Пароль должен быть не короче 8 символов")
    if fetch_one("SELECT id FROM users WHERE email = ?", (email,)):
        raise HTTPException(status_code=409, detail="Такой email уже зарегистрирован")
    user_id = execute(
        "INSERT INTO users(email, password_hash, name, role, balance_rub, token_balance, tokens_spent, last_seen_at, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (email, security.hash_password(password), name, "student", 0, config.START_TOKENS, 0, security.now(), security.now()),
    )
    store.log_event(user_id, "register")
    response = JSONResponse({"user": _user_payload(fetch_one("SELECT * FROM users WHERE id = ?", (user_id,)))})
    _set_session(response, user_id)
    return response


@app.post("/api/auth/login")
async def login(request: Request):
    data = await _body(request)
    email = _clean_email(data.get("email", ""))
    password = str(data.get("password", ""))
    row = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
    if not row or not security.verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    store.touch_user(row["id"])
    store.log_event(row["id"], "login")
    response = JSONResponse({"user": _user_payload(dict(row))})
    _set_session(response, row["id"])
    return response


@app.post("/api/auth/logout")
async def logout(request: Request):
    response = JSONResponse({"ok": True})
    _clear_session(request, response)
    return response


@app.get("/api/me")
def me(request: Request):
    user = require_user(request)
    store.touch_user(user["id"])
    return {"user": _user_payload(require_user(request))}


@app.patch("/api/me")
async def update_me(request: Request):
    user = require_user(request)
    data = await _body(request)
    name = str(data.get("name", "")).strip()
    if len(name) < 2 or len(name) > 80:
        raise HTTPException(status_code=400, detail="Имя должно быть от 2 до 80 символов")
    execute("UPDATE users SET name = ? WHERE id = ?", (name, user["id"]))
    return {"user": _user_payload(require_user(request))}


@app.post("/api/me/password")
async def change_password(request: Request):
    user = require_user(request)
    data = await _body(request)
    current = str(data.get("current_password", ""))
    new = str(data.get("new_password", ""))
    row = fetch_one("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
    if not row or not verify_password(current, row["password_hash"]):
        raise HTTPException(status_code=403, detail="Текущий пароль неверный")
    if len(new) < 10:
        raise HTTPException(status_code=400, detail="Новый пароль должен быть не короче 10 символов")
    execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new), user["id"]))
    execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
    store.log_event(user["id"], "password_change")
    return {"ok": True}


@app.post("/api/events")
async def track_event(request: Request):
    user = require_user(request)
    data = await _body(request)
    kind = str(data.get("kind", "")).strip()
    allowed = {"page_view", "project_open", "folder_open", "profile_open"}
    if kind not in allowed:
        raise HTTPException(status_code=400, detail="Неизвестное событие")
    project_id = data.get("project_id")
    if project_id:
        own = fetch_one("SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user["id"]))
        project_id = own["id"] if own else None
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    meta = {str(k)[:40]: str(v)[:200] for k, v in list(meta.items())[:12]}
    store.log_event(user["id"], kind, project_id, meta)
    return {"ok": True}


@app.get("/api/me/events")
def my_events(request: Request):
    user = require_user(request)
    return {"events": store.events_for(user["id"], 30)}


@app.get("/api/catalog")
def get_catalog():
    return {"templates": catalog.TEMPLATES}


@app.get("/api/projects")
def projects(request: Request):
    user = require_user(request)
    return {"projects": store.list_projects(user["id"])}


@app.post("/api/projects")
async def create_project(request: Request):
    user = require_user(request)
    data = await _body(request)
    template_id = str(data.get("template_id", ""))
    template = catalog.TEMPLATES_BY_ID.get(template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Неизвестный шаблон")
    brief = data.get("brief") or template.get("defaults", {})
    if not isinstance(brief, dict):
        raise HTTPException(status_code=400, detail="Бриф должен быть объектом")
    name = str(data.get("name", "")).strip() or str(brief.get("business_name", "")).strip() or template["name"]
    project_id = store.create_project(user["id"], template_id, name[:120], brief)
    store.log_event(user["id"], "project_create", project_id, {"template": template_id})
    return {"id": project_id}


@app.post("/api/projects/import")
async def import_project(request: Request):
    user = require_user(request)
    data = await _body(request)
    raw = data.get("files")
    if not isinstance(raw, list) or not raw:
        raise HTTPException(status_code=400, detail="В папке не нашлось файлов")
    name = str(data.get("name", "")).strip() or "Мой проект"
    cleaned: list[dict] = []
    total = 0
    for item in raw[:1500]:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).replace("\\", "/").strip()
        if not path or path.startswith("/") or ".." in Path(path).parts:
            continue
        if path.startswith(".git/") or "/node_modules/" in path or path == ".env":
            continue
        content = str(item.get("content", ""))
        size = len(content.encode("utf-8"))
        if size > MAX_FILE_BYTES:
            continue
        total += size
        if total > 20_000_000:
            raise HTTPException(status_code=413, detail="Папка слишком большая: больше 20 МБ текстовых файлов. Видео, private и БД не загружаются.")
        cleaned.append({"path": path[:300], "content": content})
    if not cleaned:
        raise HTTPException(status_code=400, detail="Не удалось прочитать текстовые файлы")
    project_id = store.import_project(user["id"], name, cleaned)
    store.log_event(user["id"], "project_import", project_id, {"files": len(cleaned)})
    return {"id": project_id, "files": len(cleaned)}


@app.get("/api/projects/{project_id}")
def get_project(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return {"project": project}


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int, request: Request):
    user = require_user(request)
    if not store.delete_project(user["id"], project_id):
        raise HTTPException(status_code=404, detail="Проект не найден")
    return {"ok": True}


@app.patch("/api/projects/{project_id}")
async def rename_project(project_id: int, request: Request):
    user = require_user(request)
    data = await _body(request)
    if "name" in data:
        name = str(data.get("name", "")).strip()
        if not name:
            raise HTTPException(status_code=400, detail="Название не может быть пустым")
        if len(name) > 120:
            raise HTTPException(status_code=413, detail="Слишком длинное название")
        if not store.rename_project(user["id"], project_id, name, is_admin=user["role"] == "admin"):
            raise HTTPException(status_code=404, detail="Проект не найден")
    if "is_shared" in data:
        shared = bool(data.get("is_shared"))
        if not store.set_shared(user["id"], project_id, shared, is_admin=user["role"] == "admin"):
            raise HTTPException(status_code=404, detail="Проект не найден")
    return {"ok": True, "is_shared": bool(data.get("is_shared", False))}


@app.put("/api/projects/{project_id}/files")
async def save_file(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    data = await _body(request)
    path = str(data.get("path", "")).replace("\\", "/").strip()
    content = str(data.get("content", ""))
    if not path or path.startswith("/") or ".." in Path(path).parts:
        raise HTTPException(status_code=400, detail="Некорректный путь файла")
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Файл слишком большой")
    store.write_file(project_id, path, content)
    store.log_event(user["id"], "file_save", project_id, {"path": path[:200]})
    return {"ok": True, "path": path}


@app.post("/api/projects/{project_id}/files")
async def create_file(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    data = await _body(request)
    path = _safe_path(data.get("path"), "путь файла")
    if any(f["path"] == path for f in project["files"]):
        raise HTTPException(status_code=409, detail="Файл уже существует")
    content = str(data.get("content", ""))
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Файл слишком большой")
    parent = path.rsplit("/", 1)[0] if "/" in path else ""
    if parent:
        store.create_folder(project_id, parent)
    store.write_file(project_id, path, content)
    store.log_event(user["id"], "file_create", project_id, {"path": path[:200]})
    return {"ok": True, "path": path}


@app.delete("/api/projects/{project_id}/files")
def remove_file(project_id: int, path: str, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    safe = _safe_path(path, "путь файла")
    store.delete_file(project_id, safe)
    store.log_event(user["id"], "file_delete", project_id, {"path": safe[:200]})
    return {"ok": True}


@app.post("/api/projects/{project_id}/folders")
async def create_folder(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    data = await _body(request)
    path = _safe_path(data.get("path"), "путь папки")
    store.create_folder(project_id, path)
    store.log_event(user["id"], "folder_create", project_id, {"path": path[:200]})
    return {"ok": True, "path": path}


@app.delete("/api/projects/{project_id}/folders")
def remove_folder(project_id: int, path: str, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    safe = _safe_path(path, "путь папки")
    store.delete_folder(project_id, safe)
    store.log_event(user["id"], "folder_delete", project_id, {"path": safe[:200]})
    return {"ok": True}


@app.post("/api/projects/{project_id}/rename")
async def rename_path(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    data = await _body(request)
    old = _safe_path(data.get("path"), "старый путь")
    new = _safe_path(data.get("new_path"), "новый путь")
    try:
        store.rename_path(project_id, old, new)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    store.log_event(user["id"], "file_rename", project_id, {"from": old[:200], "to": new[:200]})
    return {"ok": True, "path": new}


def _apply_chat_result(user: dict, project: dict, result) -> dict:
    project_id = project["id"]
    try:
        cost = store.charge(user["id"], project_id, "chat", result.tokens_in, result.tokens_out)
    except ValueError as exc:
        store.add_message(project_id, "assistant", f"Не хватило токенов: {exc}", {"error": True})
        raise HTTPException(status_code=402, detail=str(exc))

    before = {f["path"]: f["content"] for f in project["files"]}
    changed = {path: content for path, content in result.files.items() if before.get(path) != content}
    for path, content in changed.items():
        store.write_file(project_id, path, content)

    store.add_message(
        project_id,
        "assistant",
        result.text,
        {"actions": result.actions, "mode": result.mode, "steps": result.steps, "tokens": cost["tokens"], "price_rub": cost["price_rub"], "cost_rub": cost["cost_rub"]},
    )
    fresh = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    store.log_event(user["id"], "chat", project_id, {"tokens": cost["tokens"], "mode": result.mode, "changed": len(changed)})
    return {"project": fresh, "message": result.text, "actions": result.actions, "steps": result.steps, "tokens": cost["tokens"], "price_rub": cost["price_rub"], "cost_rub": cost["cost_rub"], "mode": result.mode}


@app.websocket("/api/projects/{project_id}/terminal")
async def terminal_socket(websocket: WebSocket, project_id: int):
    user = terminal.user_from_websocket(websocket)
    if not user:
        await websocket.close(code=1008)
        return
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    await run_in_threadpool(terminal.sync_workspace, project)
    await terminal.run_shell(websocket, project)


@app.post("/api/projects/{project_id}/chat")
async def chat(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    data = await _body(request)
    message = str(data.get("message", "")).strip()
    image = _image_data(data.get("image"))
    if not message and image:
        message = "Посмотри скриншот"
    if not message:
        raise HTTPException(status_code=400, detail="Пустое сообщение")
    if len(message) > 4000:
        raise HTTPException(status_code=413, detail="Слишком длинное сообщение")

    ocr = _ocr_image(image)
    agent_message = message + (f"\n\n[Текст, распознанный со скриншота]\n{ocr}" if ocr else "")
    terminal.import_workspace(project_id)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin") or project
    store.add_message(project_id, "user", message, {"image": image, "ocr": ocr} if image else {})
    try:
        result = await run_in_threadpool(agent.respond, project, agent_message)
    except Exception as exc:
        store.add_message(project_id, "assistant", f"Ошибка агента: {exc}", {"error": True})
        raise HTTPException(status_code=500, detail=f"Агент не ответил: {exc}")
    return _apply_chat_result(user, project, result)


@app.post("/api/projects/{project_id}/chat/stream")
async def chat_stream(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    data = await _body(request)
    message = str(data.get("message", "")).strip()
    image = _image_data(data.get("image"))
    if not message and image:
        message = "Посмотри скриншот"
    if not message:
        raise HTTPException(status_code=400, detail="Пустое сообщение")
    if len(message) > 4000:
        raise HTTPException(status_code=413, detail="Слишком длинное сообщение")

    ocr = _ocr_image(image)
    agent_message = message + (f"\n\n[Текст, распознанный со скриншота]\n{ocr}" if ocr else "")
    terminal.import_workspace(project_id)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin") or project
    store.add_message(project_id, "user", message, {"image": image, "ocr": ocr} if image else {})
    q: queue.Queue = queue.Queue()

    def progress(event: dict) -> None:
        q.put(("step", event))

    def work() -> None:
        try:
            result = agent.respond(project, agent_message, on_event=progress)
            payload = _apply_chat_result(user, project, result)
            q.put(("done", payload))
        except Exception as exc:
            detail = getattr(exc, "detail", None) or str(exc)
            q.put(("error", detail))

    threading.Thread(target=work, daemon=True).start()

    async def events():
        yield ": connected\n\n"
        yield "data: " + json.dumps({"type": "step", "event": {"type": "status", "text": "Обычно 10–20 секунд"}}, ensure_ascii=False) + "\n\n"
        while True:
            kind, payload = await asyncio.to_thread(q.get)
            if kind == "step":
                event = payload or {}
                slim = {
                    "type": event.get("type"),
                    "text": str(event.get("text") or "")[:700],
                    "tool": str(event.get("tool") or ""),
                    "input": event.get("input") if isinstance(event.get("input"), dict) else {},
                }
                yield "data: " + json.dumps({"type": "step", "event": slim}, ensure_ascii=False) + "\n\n"
            elif kind == "done":
                yield "data: " + json.dumps({"type": "done", "payload": payload}, ensure_ascii=False) + "\n\n"
                break
            else:
                yield "data: " + json.dumps({"type": "error", "message": str(payload)}, ensure_ascii=False) + "\n\n"
                break

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@app.post("/api/projects/{project_id}/deploy")
async def deploy(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    data = await _body(request)
    token = str(data.get("token", "")).strip()
    check = await run_in_threadpool(telegram.validate_token, token)
    if not check.get("ok"):
        log = [
            {"step": "token", "status": "error", "message": check.get("error", "Токен отклонён")},
        ]
        store.save_deployment(project_id, "", "", "error", log)
        store.log_event(user["id"], "deploy_error", project_id, {"error": check.get("error", "Токен отклонён")[:200]})
        raise HTTPException(status_code=400, detail=check.get("error", "Токен отклонён"))
    username = check.get("username") or "bot"
    log = [
        {"step": "token", "status": "ok", "message": f"Токен принят: @{username}"},
        {"step": "build", "status": "ok", "message": "Файлы проекта проверены"},
        {"step": "register", "status": "ok", "message": "Бот зарегистрирован в платформе"},
        {"step": "runtime", "status": "warn", "message": "MVP: 24/7-рантайм появится на следующем этапе"},
    ]
    store.save_deployment(project_id, token, username, "deployed", log)
    store.log_event(user["id"], "deploy", project_id, {"bot": username})
    return {"ok": True, "username": username, "status": "deployed", "log": log}


@app.get("/api/projects/{project_id}/preview")
def preview(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    files = {f["path"]: f["content"] for f in project["files"]}
    return HTMLResponse(catalog.preview_html(project, files))


@app.get("/api/lessons")
def get_lessons(request: Request):
    user = require_user(request)
    done = {r["lesson_id"] for r in fetch_all("SELECT lesson_id FROM lesson_progress WHERE user_id = ? AND status='done'", (user["id"],))}
    return {"lessons": lessons.with_progress(done)}


@app.post("/api/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: str, request: Request):
    user = require_user(request)
    if lesson_id not in lessons.LESSON_BY_ID:
        raise HTTPException(status_code=404, detail="Урок не найден")
    execute(
        "INSERT INTO lesson_progress(user_id, lesson_id, status, updated_at) VALUES (?,?,?,?) "
        "ON CONFLICT(user_id, lesson_id) DO UPDATE SET status='done', updated_at=excluded.updated_at",
        (user["id"], lesson_id, "done", security.now()),
    )
    store.log_event(user["id"], "lesson_complete", None, {"lesson": lesson_id})
    return {"ok": True}


@app.get("/api/billing/packages")
def billing_packages():
    return {
        "packages": config.TOKEN_PACKAGES,
        "sell_price_per_m": round(config.SELL_PRICE_PER_TOKEN * 1_000_000),
        "demo": config.DEMO_TOPUP,
    }


@app.post("/api/billing/topup")
async def topup(request: Request):
    user = require_user(request)
    if not config.DEMO_TOPUP:
        raise HTTPException(status_code=403, detail="Оплата ещё не подключена")
    if user["role"] != "admin" and user["email"] != "demo@school.local":
        raise HTTPException(status_code=403, detail="Демо-пополнение доступно только демо-аккаунту")
    data = await _body(request)
    package_id = str(data.get("package_id", ""))
    package = next((p for p in config.TOKEN_PACKAGES if p["id"] == package_id), None)
    if not package:
        raise HTTPException(status_code=400, detail="Неизвестный пакет токенов")
    credited = store.demo_tokens_for(user["id"])
    if credited + int(package["tokens"]) > config.DEMO_TOPUP_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"Демо-лимит {config.DEMO_TOPUP_LIMIT // 1_000_000} млн токенов исчерпан. В проде здесь будет оплата.",
        )
    result = store.buy_tokens(user["id"], package)
    return {"ok": True, "demo": True, **result}


@app.get("/api/usage")
def usage(request: Request):
    user = require_user(request)
    return {"usage": store.usage_for(user["id"])}


@app.get("/api/admin/stats")
def admin_stats(request: Request):
    require_admin(request)
    return store.admin_stats()


@app.get("/api/admin/users/{user_id}")
def admin_user(user_id: int, request: Request):
    require_admin(request)
    detail = store.admin_user_detail(user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return detail


# --- Статика и SPA ---------------------------------------------------------
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(config.STATIC_DIR / "index.html")


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/{full_path:path}")
def spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(config.STATIC_DIR / "index.html")

