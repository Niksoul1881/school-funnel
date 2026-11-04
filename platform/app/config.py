"""Конфигурация MVP платформы.

Все секреты читаются из переменных окружения или platform/.env.
Ничего секретного не хранится в коде и не попадает в git.
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
STATIC_DIR = BASE_DIR / "static"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_env(path: Path) -> None:
    """Минимальный загрузчик .env без внешних зависимостей."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env(BASE_DIR / ".env")

DB_PATH = Path(os.environ.get("DB_PATH", DATA_DIR / "platform.db"))
COOKIE_NAME = "school_sid"
SESSION_DAYS = int(os.environ.get("SESSION_DAYS", "30"))
APP_NAME = os.environ.get("APP_NAME", "Школа AI-агентов")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://127.0.0.1:8000")
# Если задан DEMO_PASSWORD — весь сайт закрыт HTTP Basic Auth (для публичного демо).
DEMO_USER = os.environ.get("DEMO_USER", "demo")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "").strip()
AGENT_MODE = os.environ.get("AGENT_MODE", "mock").strip().lower()
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
TELEGRAM_SERVICE_TOKEN = os.environ.get("TELEGRAM_SERVICE_TOKEN", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("PLATFORM_BOT_TOKEN", "").strip()
OWNER_TG_ID = os.environ.get("OWNER_TG_ID", "").strip()
DSH_BIN = os.environ.get("DSH_BIN", "dsh")
TELEGRAM_API = "https://api.telegram.org"

# Токенная модель: ученик покупает пакеты токенов, агент списывает токены за запросы.
START_TOKENS = int(os.environ.get("START_TOKENS", "1000000"))
# Демо-начисление пакетов без оплаты. В проде выключить.
DEMO_TOPUP = os.environ.get("DEMO_TOPUP", "1").strip().lower() in ("1", "true", "yes", "on")
DEMO_TOPUP_LIMIT = int(os.environ.get("DEMO_TOPUP_LIMIT", "5000000"))
# Розничная цена токена: 390 ₽ за 1 млн.
SELL_PRICE_PER_TOKEN = float(os.environ.get("SELL_PRICE_PER_TOKEN", "0.00039"))
# Ориентир себестоимости токена (DeepSeek flash, микс input/output).
TOKEN_COST_PER_TOKEN = float(os.environ.get("TOKEN_COST_PER_TOKEN", "0.00015"))
TOKEN_PACKAGES = [
    {"id": "start", "name": "Старт", "tokens": 1_000_000, "price_rub": 390},
    {"id": "pro", "name": "Про", "tokens": 5_000_000, "price_rub": 1690},
    {"id": "studio", "name": "Студия", "tokens": 10_000_000, "price_rub": 2990},
]
# Себестоимость по типам токенов — для аналитики, не для списания.
COST_IN_PER_TOKEN = float(os.environ.get("COST_IN_PER_TOKEN", "0.000015"))
COST_OUT_PER_TOKEN = float(os.environ.get("COST_OUT_PER_TOKEN", "0.000060"))


def _secret_key() -> str:
    value = os.environ.get("SECRET_KEY", "").strip()
    if value:
        return value
    # Стабильный локальный секрет: генерируем один раз и храним в data/.
    key_file = DATA_DIR / ".secret_key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    value = secrets.token_urlsafe(48)
    key_file.write_text(value, encoding="utf-8")
    return value


SECRET_KEY = _secret_key()


def _fernet_key() -> bytes:
    """Детерминированный Fernet-ключ из SECRET_KEY (32 байта urlsafe base64)."""
    raw = os.environ.get("FERNET_KEY", "").strip()
    if raw:
        return raw.encode("utf-8")
    digest = hashlib.sha256(SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


FERNET_KEY = _fernet_key()
