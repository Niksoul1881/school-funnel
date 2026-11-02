"""SQLite-слой MVP: схема, подключение и демо-данные."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    balance_rub REAL NOT NULL DEFAULT 1500,
    token_balance INTEGER NOT NULL DEFAULT 1000000,
    tokens_spent INTEGER NOT NULL DEFAULT 0,
    last_seen_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id TEXT NOT NULL,
    name TEXT NOT NULL,
    brief_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, path)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    meta_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    platform TEXT NOT NULL DEFAULT 'telegram',
    token_enc TEXT NOT NULL DEFAULT '',
    bot_username TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    log_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    tokens INTEGER NOT NULL DEFAULT 0,
    cost_rub REAL NOT NULL DEFAULT 0,
    price_rub REAL NOT NULL DEFAULT 0,
    demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    meta_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'done',
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, lesson_id)
);

CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_messages_project ON messages(project_id);
CREATE INDEX IF NOT EXISTS idx_usage_user ON usage(user_id);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_kind_time ON events(kind, created_at);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Мягкая миграция старой БД под токенный баланс."""
    user_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "token_balance" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN token_balance INTEGER NOT NULL DEFAULT 1000000")
    if "tokens_spent" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN tokens_spent INTEGER NOT NULL DEFAULT 0")
    if "last_seen_at" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_seen_at TEXT")
    usage_cols = {row[1] for row in conn.execute("PRAGMA table_info(usage)")}
    if "tokens" not in usage_cols:
        conn.execute("ALTER TABLE usage ADD COLUMN tokens INTEGER NOT NULL DEFAULT 0")
    if "price_rub" not in usage_cols:
        conn.execute("ALTER TABLE usage ADD COLUMN price_rub REAL NOT NULL DEFAULT 0")
    if "demo" not in usage_cols:
        conn.execute("ALTER TABLE usage ADD COLUMN demo INTEGER NOT NULL DEFAULT 0")
        conn.execute("UPDATE usage SET demo = 1 WHERE kind = 'topup'")
    conn.commit()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def fetch_one(sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(sql, tuple(params)).fetchone()


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with connect() as conn:
        return list(conn.execute(sql, tuple(params)).fetchall())


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    with connect() as conn:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return int(cur.lastrowid or 0)


def init_db() -> None:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()
    if not fetch_one("SELECT id FROM users LIMIT 1"):
        _seed()


def _seed() -> None:
    """Демо-аккаунты и один готовый проект, чтобы дашборд не был пустым."""
    import json as _json

    from . import catalog
    from .security import hash_password, now

    demo_id = execute(
        "INSERT INTO users(email, password_hash, name, role, balance_rub, token_balance, tokens_spent, created_at) VALUES (?,?,?,?,?,?,?,?)",
        ("demo@school.local", hash_password("demo1234"), "Егор", "student", 0, config.START_TOKENS, 0, now()),
    )
    execute(
        "INSERT INTO users(email, password_hash, name, role, balance_rub, token_balance, tokens_spent, created_at) VALUES (?,?,?,?,?,?,?,?)",
        ("admin@school.local", hash_password("admin1234"), "Админ", "admin", 0, config.START_TOKENS, 0, now()),
    )

    brief = {
        "business_name": "Салон «Лотос»",
        "niche": "салон красоты",
        "product": "стрижки, окрашивание, маникюр",
        "audience": "женщины 25–45, ходят раз в 3–4 недели",
        "goal": "запись на услуги и напоминания",
        "tone": "дружелюбный, спокойный, без давления",
        "price": "стрижка — 3 500 ₽, окрашивание — от 7 000 ₽, маникюр — 2 500 ₽",
        "faq": "Можно ли записаться на сегодня?|Да, если есть свободное окно — бот покажет ближайшее.\nЕсть ли парковка?|Да, во дворе дома, бесплатно для клиентов.",
        "contact": "@lotos_salon, +7 999 123-45-67",
        "payment": "none",
        "accent": "#ff4f8b",
    }
    files = catalog.generate_files("bot-vizitka", brief)
    ts = now()
    project_id = execute(
        "INSERT INTO projects(user_id, template_id, name, brief_json, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (demo_id, "bot-vizitka", "Салон «Лотос»", _json.dumps(brief, ensure_ascii=False), "draft", ts, ts),
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
            "Проект готов. Я собрал бота-визитку под салон «Лотос»: меню, услуги, ответы на частые вопросы и контакт. Напиши, что поправить — например, «добавь меню: Услуги, Записаться, Цены, Связаться».",
            _json.dumps({"kind": "welcome"}, ensure_ascii=False),
            ts,
        ),
    )
    for lesson in ("l0", "l1"):
        execute(
            "INSERT INTO lesson_progress(user_id, lesson_id, status, updated_at) VALUES (?,?,?,?)",
            (demo_id, lesson, "done", ts),
        )

    # Второй демо-проект: мини-апп, чтобы на дашборде было два направления.
    tpl = catalog.TEMPLATES_BY_ID["miniapp-showcase"]
    brief2 = dict(tpl["defaults"])
    brief2["business_name"] = "Витрина «Пион»"
    files2 = catalog.generate_files("miniapp-showcase", brief2)
    project2 = execute(
        "INSERT INTO projects(user_id, template_id, name, brief_json, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (demo_id, "miniapp-showcase", brief2["business_name"], _json.dumps(brief2, ensure_ascii=False), "draft", ts, ts),
    )
    for path, content in files2.items():
        execute(
            "INSERT INTO files(project_id, path, content, updated_at) VALUES (?,?,?,?)",
            (project2, path, content, ts),
        )
    execute(
        "INSERT INTO messages(project_id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
        (
            project2,
            "assistant",
            "Мини-апп собран: витрина с обложкой, разделами, ценами и кнопкой «Написать». Скажи, что поменять — например, «цвет #8b5cf6».",
            _json.dumps({"kind": "welcome"}, ensure_ascii=False),
            ts,
        ),
    )
