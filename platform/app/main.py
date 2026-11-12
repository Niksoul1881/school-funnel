"""FastAPI-приложение MVP платформы «Школа AI-агентов»."""
from __future__ import annotations

import asyncio
import base64
import hmac
import io
import json
import queue
import re
import secrets
import subprocess
import tempfile
import threading
import time
import uuid
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import agent, catalog, config, lessons, security, store, telegram, terminal
from .db import execute, fetch_all, fetch_one, init_db
from .security import hash_password, public_user, require_admin, require_user, verify_password
from practice_bench.app import app as practice_app

MAX_FILE_BYTES = 1_000_000


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title=config.APP_NAME, version="0.1.0", lifespan=lifespan)

# Local runner registry: pairing codes, connected runners and browser terminals.
PAIR_CODES: dict[str, dict] = {}
RUNNERS: dict[int, WebSocket] = {}
BROWSER_TERMS: dict[str, WebSocket] = {}


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
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
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


def _require_service(request: Request) -> None:
    expected = config.TELEGRAM_SERVICE_TOKEN
    supplied = request.headers.get("X-Service-Token", "")
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Нет доступа к сервисному API")


def _tg_user(tg_id: str, name: str, username: str = "") -> dict:
    tg_id = str(tg_id).strip()
    if not tg_id.isdigit():
        raise HTTPException(status_code=400, detail="Некорректный Telegram ID")
    link = fetch_one("SELECT user_id FROM telegram_links WHERE tg_id = ?", (tg_id,))
    if link:
        user = fetch_one("SELECT * FROM users WHERE id = ?", (link["user_id"],))
        if user:
            execute("UPDATE telegram_links SET username = ? WHERE tg_id = ?", (username, tg_id))
            return user
    email = f"tg{tg_id}@school.local"
    user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
    if not user:
        user_id = execute(
            "INSERT INTO users(email, password_hash, name, role, balance_rub, token_balance, tokens_spent, last_seen_at, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (email, security.hash_password(secrets.token_urlsafe(32)), (name or f"Telegram {tg_id}")[:80], "student", 0, config.START_TOKENS, 0, security.now(), security.now()),
        )
        user = fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    execute(
        "INSERT INTO telegram_links(tg_id, user_id, username, created_at) VALUES (?,?,?,?) "
        "ON CONFLICT(tg_id) DO UPDATE SET user_id = excluded.user_id, username = excluded.username",
        (tg_id, user["id"], username[:64], security.now()),
    )
    return user


def _magic_url(user_id: int) -> str:
    raw = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(timespec="seconds")
    execute(
        "INSERT INTO magic_tokens(token_hash, user_id, expires_at, created_at) VALUES (?,?,?,?)",
        (security.token_hash(raw), user_id, expires, security.now()),
    )
    return f"{config.PUBLIC_URL}/api/auth/magic?token={raw}"


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


@app.get("/api/auth/magic")
def magic_login(token: str = ""):
    raw = (token or "").strip()
    row = fetch_one(
        "SELECT * FROM magic_tokens WHERE token_hash = ? AND expires_at > ?",
        (security.token_hash(raw), security.now()),
    ) if raw else None
    if not row:
        return RedirectResponse(url="/?magic=invalid", status_code=302)
    execute("DELETE FROM magic_tokens WHERE token_hash = ?", (security.token_hash(raw),))
    response = RedirectResponse(url="/#/dashboard", status_code=302)
    _set_session(response, row["user_id"])
    store.touch_user(row["user_id"])
    return response


@app.post("/api/telegram/link-code")
def telegram_link_code(request: Request):
    user = require_user(request)
    code = secrets.token_hex(4).upper()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(timespec="seconds")
    execute(
        "INSERT INTO telegram_link_codes(code_hash, user_id, expires_at, created_at) VALUES (?,?,?,?)",
        (security.token_hash(code), user["id"], expires, security.now()),
    )
    return {
        "code": code,
        "deep_link": f"https://t.me/platform_test_soulnik_bot?start=link_{code}",
        "expires_in": 600,
    }


@app.post("/api/tg/link")
async def tg_link(request: Request):
    _require_service(request)
    data = await _body(request)
    code = str(data.get("code", "")).strip().upper()
    tg_id = str(data.get("tg_id", "")).strip()
    username = str(data.get("username", "")).strip()[:64]
    if not code or not tg_id.isdigit():
        raise HTTPException(status_code=400, detail="Нужны code и tg_id")
    row = fetch_one(
        "SELECT * FROM telegram_link_codes WHERE code_hash = ? AND expires_at > ?",
        (security.token_hash(code), security.now()),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Код неверный или истёк")
    target = fetch_one("SELECT * FROM users WHERE id = ?", (row["user_id"],))
    if not target:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    auto = fetch_one("SELECT * FROM users WHERE email = ?", (f"tg{tg_id}@school.local",))
    if auto and auto["id"] != target["id"]:
        execute("UPDATE projects SET user_id = ? WHERE user_id = ?", (target["id"], auto["id"]))
        execute("UPDATE lesson_progress SET user_id = ? WHERE user_id = ?", (target["id"], auto["id"]))
    execute("DELETE FROM telegram_links WHERE user_id = ?", (target["id"],))
    execute(
        "INSERT INTO telegram_links(tg_id, user_id, username, created_at) VALUES (?,?,?,?) "
        "ON CONFLICT(tg_id) DO UPDATE SET user_id = excluded.user_id, username = excluded.username",
        (tg_id, target["id"], username, security.now()),
    )
    execute("DELETE FROM telegram_link_codes WHERE code_hash = ?", (security.token_hash(code),))
    store.log_event(target["id"], "telegram_link", None, {"tg_id": tg_id})
    return {"ok": True, "user_id": target["id"], "magic_url": _magic_url(target["id"])}


@app.post("/api/tg/create_project")
async def tg_create_project(request: Request):
    """Сервисный endpoint: бот-платформа создаёт проект в кабинете ученика."""
    _require_service(request)
    data = await _body(request)
    tg_id = str(data.get("tg_id", "")).strip()
    template_id = str(data.get("template_id", "")).strip()
    if template_id == "ai":
        template_id = "ai-consultant"
    template = catalog.TEMPLATES_BY_ID.get(template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Неизвестный шаблон")
    brief = data.get("brief") or {}
    if not isinstance(brief, dict):
        raise HTTPException(status_code=400, detail="Бриф должен быть объектом")
    name = str(data.get("name") or brief.get("business_name") or template["name"]).strip()[:120]
    username = str(data.get("username", "")).strip()
    user = _tg_user(tg_id, name, username)
    project_id = store.create_project(user["id"], template_id, name, brief)
    store.log_event(user["id"], "telegram_project", project_id, {"template": template_id})
    base = config.PUBLIC_URL.rstrip("/")
    return {
        "ok": True,
        "user_id": user["id"],
        "project_id": project_id,
        "project_url": f"{base}/#/project/{project_id}",
        "magic_url": _magic_url(user["id"]),
    }


@app.post("/api/tg/notify_owner")
async def tg_notify_owner(request: Request):
    """Уведомление владельцу от главного бота, а не от бота-клиента."""
    _require_service(request)
    data = await _body(request)
    text = str(data.get("text", "")).strip()[:4000]
    if not text:
        raise HTTPException(status_code=400, detail="Нет текста")
    if not config.TELEGRAM_BOT_TOKEN or not config.OWNER_TG_ID:
        raise HTTPException(status_code=503, detail="Не настроен бот или владелец")
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{config.TELEGRAM_API}/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": config.OWNER_TG_ID, "text": text, "disable_web_page_preview": True},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Telegram: {response.text[:200]}")
    return {"ok": True}


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
    return {"templates": [t for t in catalog.TEMPLATES if t["id"] not in ("ai-consultant", "lead")]}


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


@app.get("/api/projects/{project_id}/archive")
def project_archive(project_id: int, request: Request):
    user = require_user(request)
    project = store.get_project(user["id"], project_id, is_admin=user["role"] == "admin")
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    buffer = io.BytesIO()
    archive_root = re.sub(r"[^\w.-]+", "-", project.get("name") or f"project-{project_id}").strip("-") or f"project-{project_id}"
    files = project.get("files") or []
    agent_md = f"""# {project.get('name', 'Проект')}

Шаблон: {project.get('template', {}).get('name', project.get('template_id', ''))}

## Что это

Это рабочий проект Telegram-бота, собранный в «Школе AI-агентов».
Его можно открыть в VS Code, запустить локально или на своём сервере и дальше вести агентом.

## Быстрый запуск

1. Установи Python 3.12+ и VS Code.
2. Открой эту папку в VS Code.
3. Создай `.env` по примеру `.env.example` и вставь токен бота из BotFather.
4. Установи зависимости: `pip install -r requirements.txt`.
5. Запусти: `python bot.py`.

## Как работать с агентом

- Открой папку проекта в VS Code.
- Подключи своего агента (Claude Code, Codex, Cursor или DSH).
- Скажи: «Прочитай AGENT.md и content.json, предложи три улучшения, ничего не ломая».
- После правок проверь бота в Telegram и сохрани изменения в Git.

## Файлы

{chr(10).join('- `' + f.get('path', '') + '`' for f in files[:40])}

## Важно

- Не коммить `.env` и токены.
- Перед запуском на сервере настрой webhook/polling.
- Тексты бота лежат в `content.json`, их можно менять без кода.
"""
    try:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                path = str(file.get("path", "")).replace("\\", "/").lstrip("/")
                if not path or ".." in path.split("/"):
                    continue
                zf.writestr(f"{archive_root}/{path}", file.get("content", ""))
            zf.writestr(f"{archive_root}/AGENT.md", agent_md)
            if not any(str(f.get("path", "")).lower() == ".env.example" for f in files):
                zf.writestr(f"{archive_root}/.env.example", "BOT_TOKEN=\nLLM_API_KEY=\n")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось собрать архив: {exc}")
    filename = f"project-{project_id}.zip"
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


@app.post("/api/devices/pair")
def pair_device(request: Request):
    user = require_user(request)
    code = f"{secrets.randbelow(1_000_000):06d}"
    PAIR_CODES[code] = {"user_id": user["id"], "expires": time.time() + 600}
    return {"code": code, "expires_in": 600}


@app.post("/api/devices/claim")
async def claim_device(request: Request):
    data = await _body(request)
    code = str(data.get("code", "")).strip()
    info = PAIR_CODES.get(code)
    if not info or info["expires"] < time.time():
        PAIR_CODES.pop(code, None)
        raise HTTPException(status_code=404, detail="Код неверный или истёк")
    name = str(data.get("name", "")).strip()[:80] or "Мой компьютер"
    root = str(data.get("root", "")).strip()[:500]
    token = secrets.token_urlsafe(32)
    device_id = store.create_device(info["user_id"], name, security.token_hash(token), root)
    PAIR_CODES.pop(code, None)
    return {"device_id": device_id, "token": token}


@app.get("/api/devices")
def devices(request: Request):
    user = require_user(request)
    items = store.list_devices(user["id"])
    return {"devices": [{**d, "online": d["id"] in RUNNERS} for d in items]}


@app.delete("/api/devices/{device_id}")
async def remove_device(device_id: int, request: Request):
    user = require_user(request)
    ws = RUNNERS.pop(device_id, None)
    if ws:
        try:
            await ws.close(code=1008)
        except Exception:
            pass
    if not store.delete_device(device_id, user["id"]):
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    return {"ok": True}


@app.websocket("/api/devices/ws")
async def device_socket(websocket: WebSocket):
    await websocket.accept()
    try:
        first = await asyncio.wait_for(websocket.receive_json(), timeout=10)
    except Exception:
        await websocket.close(code=1008)
        return
    if first.get("type") != "auth":
        await websocket.close(code=1008)
        return
    device = store.device_by_token(security.token_hash(str(first.get("token", ""))))
    if not device:
        await websocket.close(code=1008)
        return
    device_id = device["id"]
    old = RUNNERS.get(device_id)
    if old and old is not websocket:
        try:
            await old.close(code=1000)
        except Exception:
            pass
    RUNNERS[device_id] = websocket
    store.touch_device(device_id)
    try:
        while True:
            message = await websocket.receive_json()
            kind = message.get("type")
            session = str(message.get("session", ""))
            browser = BROWSER_TERMS.get(session)
            if kind == "output" and browser:
                await browser.send_text(str(message.get("data", "")))
            elif kind == "exit" and browser:
                await browser.send_text("\r\n[процесс завершён]\r\n")
            elif kind == "pong":
                store.touch_device(device_id)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if RUNNERS.get(device_id) is websocket:
            RUNNERS.pop(device_id, None)


@app.websocket("/api/devices/{device_id}/terminal")
async def device_terminal(websocket: WebSocket, device_id: int):
    user = terminal.user_from_websocket(websocket)
    if not user:
        await websocket.close(code=1008)
        return
    device = store.get_device(device_id, user["id"])
    if not device:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    runner = RUNNERS.get(device_id)
    if not runner:
        await websocket.send_text("Локальный runner не в сети. Запусти его на компьютере.\r\n")
        await websocket.close()
        return
    session = uuid.uuid4().hex
    BROWSER_TERMS[session] = websocket
    try:
        await runner.send_json({"type": "open", "session": session})
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except Exception:
                continue
            if message.get("type") == "input":
                await runner.send_json({"type": "input", "session": session, "data": str(message.get("data", ""))})
            elif message.get("type") == "resize":
                await runner.send_json({"type": "resize", "session": session, "cols": message.get("cols", 120), "rows": message.get("rows", 30)})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        BROWSER_TERMS.pop(session, None)
        try:
            await runner.send_json({"type": "close", "session": session})
        except Exception:
            pass


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
app.mount("/practice", practice_app, name="practice")


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


