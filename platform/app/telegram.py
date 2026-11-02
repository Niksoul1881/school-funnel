"""Проверка Telegram-бота по токену через getMe."""
from __future__ import annotations

import httpx

from .config import TELEGRAM_API


def mask_token(token: str) -> str:
    token = token.strip()
    if len(token) < 12:
        return "***"
    return token[:6] + "…" + token[-4:]


def validate_token(token: str) -> dict:
    token = token.strip()
    if not token or ":" not in token:
        return {"ok": False, "error": "Токен выглядит как 123456:ABC-DEF… Проверьте формат."}
    try:
        response = httpx.get(f"{TELEGRAM_API}/bot{token}/getMe", timeout=12)
        data = response.json()
    except Exception as exc:
        return {"ok": False, "error": f"Не удалось связаться с Telegram: {exc}"}
    if not data.get("ok"):
        description = data.get("description", "Telegram отклонил токен")
        if str(description).lower() in ("unauthorized", "not found"):
            description = "Telegram отклонил токен. Скопируйте его целиком из @BotFather."
        return {"ok": False, "error": description}
    result = data.get("result", {})
    return {
        "ok": True,
        "id": result.get("id"),
        "username": result.get("username"),
        "first_name": result.get("first_name"),
        "can_join_groups": result.get("can_join_groups"),
    }
