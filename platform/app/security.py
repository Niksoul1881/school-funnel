"""Пароли, сессии и шифрование токенов."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Request

from . import config

try:  # argon2 установлен в окружении; scrypt — запасной вариант
    from argon2 import PasswordHasher

    _ph = PasswordHasher()
except Exception:  # pragma: no cover
    _ph = None

_fernet = Fernet(config.FERNET_KEY)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_password(password: str) -> str:
    if _ph is not None:
        return _ph.hash(password)
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), n=2**14, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("scrypt$"):
        try:
            _, salt, digest = stored.split("$", 2)
            calc = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), n=2**14, r=8, p=1).hex()
            return hmac.compare_digest(calc, digest)
        except Exception:
            return False
    if _ph is None:
        return False
    try:
        return bool(_ph.verify(stored, password))
    except Exception:
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def encrypt_secret(value: str) -> str:
    return _fernet.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    try:
        return _fernet.decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""


def public_user(row: Any) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "balance_rub": round(float(row["balance_rub"]), 2),
        "token_balance": int(row["token_balance"] or 0),
        "tokens_spent": int(row["tokens_spent"] or 0),
        "last_seen_at": row["last_seen_at"] if "last_seen_at" in row.keys() else None,
        "created_at": row["created_at"],
    }


def current_user(request: Request) -> dict | None:
    from .db import fetch_one

    token = request.cookies.get(config.COOKIE_NAME)
    if not token:
        return None
    row = fetch_one(
        """
        SELECT u.*, s.expires_at AS session_expires
        FROM sessions s JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ?
        """,
        (token_hash(token),),
    )
    if not row:
        return None
    if row["session_expires"] < now():
        return None
    return dict(row)


def require_user(request: Request) -> dict:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Нужно войти в аккаунт")
    return user


def require_admin(request: Request) -> dict:
    user = require_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Только для администратора")
    return user
