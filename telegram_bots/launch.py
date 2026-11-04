"""Launch the three test bots with polling from private/telegram-test.env."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "private" / "telegram-test.env"
RUNTIME = ROOT / "telegram_bots" / "runtime"
LOG = ROOT / "telegram_bots" / "launch.log"

sys.path.insert(0, str(ROOT / "platform"))
from app import catalog  # noqa: E402


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_FILE.exists():
        raise SystemExit(f"Нет файла {ENV_FILE}")
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.lstrip("\ufeff").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lstrip("\ufeff")] = value.strip().lstrip("\ufeff")
    return values


def valid(token: str) -> tuple[bool, str]:
    try:
        with httpx.Client(timeout=15) as client:
            data = client.get(f"https://api.telegram.org/bot{token}/getMe").json()
        if data.get("ok"):
            return True, data["result"].get("username", "")
        return False, data.get("description", "ошибка Telegram")
    except Exception as exc:
        return False, str(exc)


def main() -> None:
    env = read_env()
    owner = env.get("OWNER_TG_ID", "").strip()
    specs = [
        ("booking", "BOOKING_BOT_TOKEN"),
        ("ai-consultant", "AI_BOT_TOKEN"),
        ("shop", "SHOP_BOT_TOKEN"),
    ]
    if not any(env.get(token_key, "").strip() for _, token_key in specs):
        raise SystemExit(
            "Заполни private/telegram-test.env: BOOKING_BOT_TOKEN, AI_BOT_TOKEN, SHOP_BOT_TOKEN."
        )

    RUNTIME.mkdir(parents=True, exist_ok=True)
    log = LOG.open("a", encoding="utf-8")
    children: list[tuple[str, subprocess.Popen]] = []

    for template_id, token_key in specs:
        token = env.get(token_key, "").strip()
        if not token:
            print(f"[-] {template_id}: {token_key} пуст — пропускаю")
            continue
        ok, username = valid(token)
        if not ok:
            print(f"[!] {template_id}: токен не принят — {username}")
            continue
        template = catalog.TEMPLATES_BY_ID[template_id]
        brief = template["defaults"]
        files = catalog.generate_files(template_id, brief)
        out = RUNTIME / template_id
        out.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            target = out / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        child_env = os.environ.copy()
        child_env.update({
            "BOT_TOKEN": token,
            "ADMIN_CHAT_ID": owner,
            "LLM_API_KEY": env.get("LLM_API_KEY", ""),
            "LLM_BASE_URL": env.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            "LLM_MODEL": env.get("LLM_MODEL", "deepseek-chat"),
            "PYTHONIOENCODING": "utf-8",
        })
        proc = subprocess.Popen(
            [sys.executable, "bot.py"],
            cwd=out,
            env=child_env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        children.append((template_id, proc))
        print(f"[+] {template_id}: @{username} запущен (pid {proc.pid})")

    if not children:
        raise SystemExit("Ни один бот не запущен. Проверь токены.")

    print("\nБоты работают. Напиши каждому /start в Telegram.")
    print("Ctrl+C — остановить.\n")
    try:
        while True:
            for template_id, proc in children:
                code = proc.poll()
                if code is not None:
                    print(f"[!] {template_id} завершился с кодом {code}. Смотри launch.log")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nОстанавливаю…")
    finally:
        for _, proc in children:
            if proc.poll() is None:
                proc.terminate()
        log.close()


if __name__ == "__main__":
    main()
