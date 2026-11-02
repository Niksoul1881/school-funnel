"""Операции с проектами, файлами, сообщениями, деплоем и балансом."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from . import catalog, config
from .db import execute, fetch_all, fetch_one
from .security import decrypt_secret, encrypt_secret, now


def log_event(user_id: int, kind: str, project_id: int | None = None, meta: dict | None = None) -> None:
    execute(
        "INSERT INTO events(user_id, project_id, kind, meta_json, created_at) VALUES (?,?,?,?,?)",
        (user_id, project_id, kind, json.dumps(meta or {}, ensure_ascii=False), now()),
    )


def touch_user(user_id: int) -> None:
    execute("UPDATE users SET last_seen_at = ? WHERE id = ?", (now(), user_id))


def events_for(user_id: int, limit: int = 30) -> list[dict]:
    rows = fetch_all("SELECT * FROM events WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    return [dict(r) for r in rows]


def demo_tokens_for(user_id: int) -> int:
    row = fetch_one("SELECT COALESCE(SUM(tokens),0) AS t FROM usage WHERE user_id = ? AND kind = 'topup' AND demo = 1", (user_id,))
    return int(row["t"]) if row else 0


def _template(template_id: str) -> dict:
    t = catalog.TEMPLATES_BY_ID.get(template_id)
    if not t:
        return {"id": template_id, "name": template_id, "direction": "bot", "icon": "bot"}
    return {k: t[k] for k in ("id", "name", "direction", "tagline", "price", "icon", "stack")}


def list_projects(user_id: int) -> list[dict]:
    rows = fetch_all("SELECT * FROM projects WHERE user_id = ? OR is_shared = 1 ORDER BY updated_at DESC", (user_id,))
    out = []
    for row in rows:
        files_count = fetch_one("SELECT COUNT(*) AS c FROM files WHERE project_id = ?", (row["id"],))["c"]
        deploy = fetch_one("SELECT status, bot_username FROM deployments WHERE project_id = ?", (row["id"],))
        out.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "template_id": row["template_id"],
            "template": _template(row["template_id"]),
            "status": row["status"],
            "is_shared": bool(row["is_shared"]) if "is_shared" in row.keys() else False,
            "files_count": files_count,
            "deployment": dict(deploy) if deploy else None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })
    return out


def create_project(user_id: int, template_id: str, name: str, brief: dict) -> int:
    files = catalog.generate_files(template_id, brief)
    ts = now()
    project_id = execute(
        "INSERT INTO projects(user_id, template_id, name, brief_json, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (user_id, template_id, name, json.dumps(brief, ensure_ascii=False), "draft", ts, ts),
    )
    for path, content in files.items():
        execute(
            "INSERT INTO files(project_id, path, content, updated_at) VALUES (?,?,?,?)",
            (project_id, path, content, ts),
        )
    execute(
        "INSERT INTO messages(project_id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
        (
            project_id,
            "assistant",
            "Проект собран. Файлы уже в рабочей папке, превью справа. Напиши, что поправить — я изменю тексты и код. Например: «добавь меню: Услуги, Записаться, Цены, Связаться».",
            json.dumps({"kind": "welcome"}, ensure_ascii=False),
            ts,
        ),
    )
    return project_id


def import_project(user_id: int, name: str, files: list[dict]) -> int:
    """Создаёт проект из папки пользователя (только текстовые файлы)."""
    ts = now()
    project_id = execute(
        "INSERT INTO projects(user_id, template_id, name, brief_json, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (user_id, "imported", name[:120], "{}", "draft", ts, ts),
    )
    for item in files:
        execute(
            "INSERT INTO files(project_id, path, content, updated_at) VALUES (?,?,?,?)",
            (project_id, item["path"], item["content"], ts),
        )
    execute(
        "INSERT INTO messages(project_id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
        (
            project_id,
            "assistant",
            f"Папка загружена. Файлов: {len(files)}. Я вижу структуру проекта. Скажи, что сделать — например, «объясни main.py» или «добавь README».",
            json.dumps({"kind": "import"}, ensure_ascii=False),
            ts,
        ),
    )
    return project_id


def get_project(user_id: int, project_id: int, is_admin: bool = False) -> dict | None:
    row = fetch_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not row:
        return None
    if row["user_id"] != user_id and not is_admin and not row["is_shared"]:
        return None
    files = fetch_all("SELECT path, content, updated_at FROM files WHERE project_id = ? ORDER BY path", (project_id,))
    folders = fetch_all("SELECT path FROM folders WHERE project_id = ? ORDER BY path", (project_id,))
    messages = fetch_all("SELECT * FROM messages WHERE project_id = ? ORDER BY id", (project_id,))
    deploy = fetch_one("SELECT * FROM deployments WHERE project_id = ?", (project_id,))
    deployment = None
    if deploy:
        deployment = {
            "id": deploy["id"],
            "platform": deploy["platform"],
            "bot_username": deploy["bot_username"],
            "status": deploy["status"],
            "log": json.loads(deploy["log_json"] or "[]"),
            "created_at": deploy["created_at"],
            "updated_at": deploy["updated_at"],
        }
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "template_id": row["template_id"],
        "template": _template(row["template_id"]),
        "status": row["status"],
        "is_shared": bool(row["is_shared"]) if "is_shared" in row.keys() else False,
        "brief": json.loads(row["brief_json"] or "{}"),
        "files": [dict(f) for f in files],
        "folders": [f["path"] for f in folders],
        "messages": [
            {"id": m["id"], "role": m["role"], "content": m["content"], "meta": json.loads(m["meta_json"] or "{}"), "created_at": m["created_at"]}
            for m in messages
        ],
        "deployment": deployment,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def delete_project(user_id: int, project_id: int) -> bool:
    row = fetch_one("SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
    if not row:
        return False
    execute("DELETE FROM projects WHERE id = ?", (project_id,))
    return True


def touch_project(project_id: int) -> None:
    execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now(), project_id))


def get_files(project_id: int) -> dict[str, str]:
    return {r["path"]: r["content"] for r in fetch_all("SELECT path, content FROM files WHERE project_id = ?", (project_id,))}


def write_file(project_id: int, path: str, content: str) -> None:
    ts = now()
    existing = fetch_one("SELECT id FROM files WHERE project_id = ? AND path = ?", (project_id, path))
    if existing:
        execute("UPDATE files SET content = ?, updated_at = ? WHERE id = ?", (content, ts, existing["id"]))
    else:
        execute("INSERT INTO files(project_id, path, content, updated_at) VALUES (?,?,?,?)", (project_id, path, content, ts))
    touch_project(project_id)


def create_folder(project_id: int, path: str) -> None:
    parts = [p for p in path.split("/") if p]
    for i in range(1, len(parts) + 1):
        sub = "/".join(parts[:i])
        exists = fetch_one("SELECT id FROM folders WHERE project_id = ? AND path = ?", (project_id, sub))
        if not exists:
            execute("INSERT INTO folders(project_id, path, created_at) VALUES (?,?,?)", (project_id, sub, now()))
    touch_project(project_id)


def delete_file(project_id: int, path: str) -> None:
    execute("DELETE FROM files WHERE project_id = ? AND path = ?", (project_id, path))
    touch_project(project_id)


def delete_folder(project_id: int, path: str) -> None:
    execute("DELETE FROM files WHERE project_id = ? AND (path = ? OR path LIKE ?)", (project_id, path, path + "/%"))
    execute("DELETE FROM folders WHERE project_id = ? AND (path = ? OR path LIKE ?)", (project_id, path, path + "/%"))
    touch_project(project_id)


def rename_path(project_id: int, old: str, new: str) -> None:
    if not old or not new or old == new:
        return
    conflict_file = fetch_one("SELECT id FROM files WHERE project_id = ? AND (path = ? OR path LIKE ?)", (project_id, new, new + "/%"))
    conflict_folder = fetch_one("SELECT id FROM folders WHERE project_id = ? AND (path = ? OR path LIKE ?)", (project_id, new, new + "/%"))
    if conflict_file or conflict_folder:
        raise ValueError("Такое имя уже существует")
    for table in ("files", "folders"):
        rows = fetch_all(f"SELECT id, path FROM {table} WHERE project_id = ? AND (path = ? OR path LIKE ?)", (project_id, old, old + "/%"))
        for row in rows:
            target = new + row["path"][len(old):]
            execute(f"UPDATE {table} SET path = ? WHERE id = ?", (target, row["id"]))
    touch_project(project_id)


def rename_project(user_id: int, project_id: int, name: str, is_admin: bool = False) -> bool:
    row = fetch_one("SELECT user_id FROM projects WHERE id = ?", (project_id,))
    if not row or (row["user_id"] != user_id and not is_admin):
        return False
    execute("UPDATE projects SET name = ?, updated_at = ? WHERE id = ?", (name, now(), project_id))
    return True


def set_shared(user_id: int, project_id: int, shared: bool, is_admin: bool = False) -> bool:
    row = fetch_one("SELECT user_id FROM projects WHERE id = ?", (project_id,))
    if not row or (row["user_id"] != user_id and not is_admin):
        return False
    execute("UPDATE projects SET is_shared = ?, updated_at = ? WHERE id = ?", (1 if shared else 0, now(), project_id))
    return True


def add_message(project_id: int, role: str, content: str, meta: dict | None = None) -> int:
    return execute(
        "INSERT INTO messages(project_id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
        (project_id, role, content, json.dumps(meta or {}, ensure_ascii=False), now()),
    )


def save_deployment(project_id: int, token: str, username: str, status: str, log: list[dict]) -> None:
    enc = encrypt_secret(token)
    ts = now()
    existing = fetch_one("SELECT id FROM deployments WHERE project_id = ?", (project_id,))
    if existing:
        execute(
            "UPDATE deployments SET token_enc = ?, bot_username = ?, status = ?, log_json = ?, updated_at = ? WHERE id = ?",
            (enc, username, status, json.dumps(log, ensure_ascii=False), ts, existing["id"]),
        )
    else:
        execute(
            "INSERT INTO deployments(project_id, platform, token_enc, bot_username, status, log_json, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (project_id, "telegram", enc, username, status, json.dumps(log, ensure_ascii=False), ts, ts),
        )
    execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))


def get_deployment_token(project_id: int) -> str:
    row = fetch_one("SELECT token_enc FROM deployments WHERE project_id = ?", (project_id,))
    return decrypt_secret(row["token_enc"]) if row else ""


def charge(user_id: int, project_id: int | None, kind: str, tokens_in: int, tokens_out: int) -> dict:
    """Списывает токены за запрос. 1 токен баланса = 1 токен модели."""
    tokens = max(1, int(tokens_in) + int(tokens_out))
    price_rub = round(tokens * config.SELL_PRICE_PER_TOKEN, 4)
    cost_rub = round(tokens * config.TOKEN_COST_PER_TOKEN, 4)
    row = fetch_one("SELECT token_balance FROM users WHERE id = ?", (user_id,))
    if not row:
        raise ValueError("Пользователь не найден")
    balance = int(row["token_balance"] or 0)
    if balance < tokens:
        raise ValueError("Не хватает токенов. Пополни баланс в разделе «Баланс».")
    execute(
        "UPDATE users SET token_balance = token_balance - ?, tokens_spent = tokens_spent + ? WHERE id = ?",
        (tokens, tokens, user_id),
    )
    execute(
        "INSERT INTO usage(user_id, project_id, kind, tokens_in, tokens_out, tokens, cost_rub, price_rub, demo, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (user_id, project_id, kind, tokens_in, tokens_out, tokens, cost_rub, price_rub, 0, now()),
    )
    return {"tokens": tokens, "price_rub": price_rub, "cost_rub": cost_rub, "balance": balance - tokens}


def buy_tokens(user_id: int, package: dict) -> dict:
    """Покупка пакета токенов (в MVP — демо, без реального платежа)."""
    tokens = int(package["tokens"])
    price_rub = float(package["price_rub"])
    cost_rub = round(tokens * config.TOKEN_COST_PER_TOKEN, 2)
    execute(
        "UPDATE users SET token_balance = token_balance + ? WHERE id = ?",
        (tokens, user_id),
    )
    row = fetch_one("SELECT token_balance FROM users WHERE id = ?", (user_id,))
    execute(
        "INSERT INTO usage(user_id, project_id, kind, tokens_in, tokens_out, tokens, cost_rub, price_rub, demo, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (user_id, None, "topup", 0, 0, tokens, cost_rub, price_rub, 1, now()),
    )
    return {
        "added": tokens,
        "price_rub": price_rub,
        "balance": int(row["token_balance"] or 0),
        "package": package.get("id", ""),
        "demo": True,
    }


def usage_for(user_id: int, limit: int = 30) -> list[dict]:
    rows = fetch_all(
        "SELECT u.*, p.name AS project_name FROM usage u LEFT JOIN projects p ON p.id = u.project_id WHERE u.user_id = ? ORDER BY u.id DESC LIMIT ?",
        (user_id, limit),
    )
    return [dict(r) for r in rows]


def admin_stats() -> dict:
    now_dt = datetime.now(timezone.utc)
    d1 = (now_dt - timedelta(days=1)).isoformat()
    d7 = (now_dt - timedelta(days=7)).isoformat()
    d30 = (now_dt - timedelta(days=30)).isoformat()
    users = fetch_one(
        "SELECT COUNT(*) AS c, COALESCE(SUM(token_balance),0) AS token_balance, COALESCE(SUM(tokens_spent),0) AS tokens_spent FROM users"
    )
    projects = fetch_one("SELECT COUNT(*) AS c FROM projects")
    deploys = fetch_one("SELECT COUNT(*) AS c FROM deployments")
    usage = fetch_one(
        "SELECT COALESCE(SUM(tokens),0) AS tokens, COALESCE(SUM(cost_rub),0) AS cost, COALESCE(SUM(tokens_in),0) AS tin, COALESCE(SUM(tokens_out),0) AS tout FROM usage WHERE kind != 'topup'"
    )
    chat_stats = fetch_one("SELECT COUNT(*) AS c, COALESCE(SUM(tokens),0) AS tokens FROM usage WHERE kind = 'chat'")
    topups = fetch_one(
        "SELECT COALESCE(SUM(tokens),0) AS tokens, COALESCE(SUM(price_rub),0) AS revenue, COALESCE(SUM(cost_rub),0) AS cost FROM usage WHERE kind = 'topup' AND demo = 0"
    )
    demo_topups = fetch_one(
        "SELECT COALESCE(SUM(tokens),0) AS tokens FROM usage WHERE kind = 'topup' AND demo = 1"
    )
    active_1d = fetch_one("SELECT COUNT(DISTINCT user_id) AS c FROM events WHERE created_at >= ?", (d1,))["c"]
    active_7d = fetch_one("SELECT COUNT(DISTINCT user_id) AS c FROM events WHERE created_at >= ?", (d7,))["c"]
    active_30d = fetch_one("SELECT COUNT(DISTINCT user_id) AS c FROM events WHERE created_at >= ?", (d30,))["c"]
    events_7d = fetch_one("SELECT COUNT(*) AS c FROM events WHERE created_at >= ?", (d7,))["c"]
    new_users_7d = fetch_one("SELECT COUNT(*) AS c FROM users WHERE created_at >= ?", (d7,))["c"]
    recent_users = fetch_all(
        """SELECT u.id, u.email, u.name, u.role, u.token_balance, u.tokens_spent, u.last_seen_at, u.created_at,
                  COUNT(DISTINCT p.id) AS projects,
                  (SELECT COUNT(*) FROM messages m JOIN projects pp ON pp.id = m.project_id WHERE pp.user_id = u.id) AS messages,
                  (SELECT COALESCE(SUM(tokens),0) FROM usage WHERE user_id = u.id AND kind = 'chat') AS tokens_used,
                  (SELECT COUNT(*) FROM events WHERE user_id = u.id) AS events_count,
                  (SELECT MAX(created_at) FROM events WHERE user_id = u.id) AS last_event
           FROM users u LEFT JOIN projects p ON p.user_id = u.id
           GROUP BY u.id ORDER BY u.id DESC LIMIT 20"""
    )
    recent_projects = fetch_all(
        "SELECT p.id, p.name, p.template_id, p.status, p.created_at, u.email FROM projects p JOIN users u ON u.id = p.user_id ORDER BY p.id DESC LIMIT 20"
    )
    recent_usage = fetch_all(
        "SELECT u.id, u.kind, u.tokens_in, u.tokens_out, u.tokens, u.cost_rub, u.price_rub, u.demo, u.created_at, us.email FROM usage u JOIN users us ON us.id = u.user_id ORDER BY u.id DESC LIMIT 20"
    )
    recent_events = fetch_all(
        "SELECT e.id, e.kind, e.project_id, e.meta_json, e.created_at, u.email FROM events e JOIN users u ON u.id = e.user_id ORDER BY e.id DESC LIMIT 25"
    )
    activity_rows = fetch_all(
        "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS events, COUNT(DISTINCT user_id) AS users FROM events WHERE created_at >= ? GROUP BY day ORDER BY day",
        (d7,),
    )
    by_day = {r["day"]: {"events": r["events"], "users": r["users"]} for r in activity_rows}
    activity = []
    for i in range(6, -1, -1):
        day = (now_dt - timedelta(days=i)).date().isoformat()
        activity.append({"day": day, "events": by_day.get(day, {}).get("events", 0), "users": by_day.get(day, {}).get("users", 0)})
    event_counts = fetch_all(
        "SELECT kind, COUNT(*) AS c FROM events WHERE created_at >= ? GROUP BY kind ORDER BY c DESC LIMIT 12",
        (d30,),
    )
    revenue = round(float(topups["revenue"]), 2)
    provider_cost = round(float(topups["cost"]), 2)
    return {
        "users": users["c"],
        "token_balance": int(users["token_balance"]),
        "tokens_spent": int(users["tokens_spent"]),
        "projects": projects["c"],
        "deployments": deploys["c"],
        "tokens_used": int(usage["tokens"]),
        "tokens_in": int(usage["tin"]),
        "tokens_out": int(usage["tout"]),
        "usage_cost": round(float(usage["cost"]), 2),
        "avg_tokens": round(float(chat_stats["tokens"]) / chat_stats["c"]) if chat_stats["c"] else 0,
        "chats": chat_stats["c"],
        "tokens_sold": int(topups["tokens"]),
        "demo_tokens": int(demo_topups["tokens"]),
        "revenue": revenue,
        "provider_cost": provider_cost,
        "margin": round(revenue - provider_cost, 2),
        "active_1d": active_1d,
        "active_7d": active_7d,
        "active_30d": active_30d,
        "events_7d": events_7d,
        "new_users_7d": new_users_7d,
        "activity": activity,
        "event_counts": [dict(r) for r in event_counts],
        "recent_users": [dict(r) for r in recent_users],
        "recent_projects": [dict(r) for r in recent_projects],
        "recent_usage": [dict(r) for r in recent_usage],
        "recent_events": [dict(r) for r in recent_events],
    }


def admin_user_detail(user_id: int) -> dict | None:
    user = fetch_one(
        "SELECT id, email, name, role, token_balance, tokens_spent, last_seen_at, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    if not user:
        return None
    projects = fetch_all(
        "SELECT id, name, template_id, status, created_at, updated_at FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,),
    )
    usage = fetch_all(
        "SELECT id, kind, tokens_in, tokens_out, tokens, cost_rub, price_rub, demo, created_at FROM usage WHERE user_id = ? ORDER BY id DESC LIMIT 30",
        (user_id,),
    )
    events = fetch_all(
        "SELECT id, kind, project_id, meta_json, created_at FROM events WHERE user_id = ? ORDER BY id DESC LIMIT 50",
        (user_id,),
    )
    done = fetch_one("SELECT COUNT(*) AS c FROM lesson_progress WHERE user_id = ? AND status='done'", (user_id,))["c"]
    messages = fetch_one(
        "SELECT COUNT(*) AS c FROM messages m JOIN projects p ON p.id = m.project_id WHERE p.user_id = ?", (user_id,)
    )["c"]
    return {
        "user": dict(user),
        "projects": [dict(r) for r in projects],
        "usage": [dict(r) for r in usage],
        "events": [dict(r) for r in events],
        "stats": {"projects": len(projects), "lessons_done": done, "messages": messages},
    }
