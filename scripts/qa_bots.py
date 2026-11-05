"""Professional smoke/QA pass for the three visible Telegram bot scenarios."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / "private" / "telegram-test.env")

from local_practice import engine  # noqa: E402

PUBLIC = "https://school.91-184-242-178.sslip.io:8443"
VISIBLE = ("booking", "gift", "shop")
passed: list[str] = []
failed: list[str] = []


def ok(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        passed.append(name)
        print(f"  OK   {name}")
    else:
        failed.append(name)
        print(f"  FAIL {name} {detail}")


def fresh(template: str) -> str:
    brief = dict(engine.TEMPLATES[template]["defaults"])
    return engine.create_bot(template, brief)["id"]


def texts(replies: list[dict]) -> str:
    return "\n".join(r.get("text", "") for r in replies)


def admin(replies: list[dict]) -> list[dict]:
    return [r for r in replies if r.get("admin")]


def test_booking() -> None:
    print("\n[booking] запись")
    bid = fresh("booking")
    r = engine.message(bid, action="start")
    ok("booking: приветствие", "Выберите услугу" in texts(r), texts(r)[:80])

    r = engine.message(bid, text="хочу стрижку")
    ok("booking: услуга текстом", "На какую дату" in texts(r), texts(r)[:80])
    r = engine.message(bid, text="завтра")
    ok("booking: дата текстом", "Выберите время" in texts(r), texts(r)[:80])
    r = engine.message(bid, text="15:00")
    ok("booking: время текстом", "Как вас зовут" in texts(r), texts(r)[:80])
    r = engine.message(bid, text="Никита")
    ok("booking: имя", "телефон" in texts(r).lower(), texts(r)[:80])
    r = engine.message(bid, text="123")
    ok("booking: плохой телефон отклонён", "ошибка" in texts(r).lower() or "ещё раз" in texts(r).lower(), texts(r)[:80])
    r = engine.message(bid, text="+7 902 123-45-67")
    ok("booking: телефон принят", "Проверьте заявку" in texts(r), texts(r)[:80])
    r = engine.message(bid, text="да")
    ok("booking: подтверждение текстом", "Готово" in texts(r), texts(r)[:80])
    ok("booking: уведомление владельцу", bool(admin(r)), "admin missing")
    ok("booking: клиент не видит admin", all(not m.get("admin") for m in r[:-1]), "")

    # Reset during confirm must return to the first step.
    bid2 = fresh("booking")
    engine.message(bid2, text="стрижка")
    engine.message(bid2, text="завтра")
    engine.message(bid2, text="12:00")
    engine.message(bid2, text="Тест")
    engine.message(bid2, text="+79001112233")
    r = engine.message(bid2, text="заново")
    ok("booking: «заново» сбрасывает этап", "Выберите услугу" in texts(r), texts(r)[:80])


def test_gift() -> None:
    print("\n[gift] подарок за подписку")
    bid = fresh("gift")
    r = engine.message(bid, action="start")
    ok("gift: приветствие", "подарок" in texts(r).lower(), texts(r)[:80])
    buttons = [b for m in r for b in m.get("buttons", [])]
    ok("gift: ссылка на канал", any(b["action"].startswith("url:") for b in buttons), str(buttons))
    ok("gift: кнопка проверки", any(b["action"] == "check" for b in buttons), str(buttons))
    r = engine.message(bid, text="подписался")
    ok("gift: подарок выдаётся", "Спасибо за подписку" in texts(r), texts(r)[:80])
    ok("gift: кнопка забрать", any(b["action"].startswith("url:") for m in r for b in m.get("buttons", [])), "")
    ok("gift: уведомление владельцу", bool(admin(r)), "admin missing")


def test_shop() -> None:
    print("\n[shop] витрина")
    bid = fresh("shop")
    r = engine.message(bid, action="start")
    ok("shop: приветствие", "каталог" in texts(r).lower(), texts(r)[:80])
    r = engine.message(bid, action="cat:Все")
    ok("shop: категория «Все»", len(r) >= 2 and any("₽" in m.get("text", "") for m in r), f"messages={len(r)}")
    ok("shop: фото товара в карточке", any(m.get("image") for m in r), "no image")
    r = engine.message(bid, text="медовик")
    ok("shop: поиск товара", "Медовик" in texts(r), texts(r)[:80])
    products = engine.BOTS[bid]["config"]["products"]
    product = next(p for p in products if p["title"] == "Медовик")
    r = engine.message(bid, action=f"add:{product['id']}")
    ok("shop: добавление", "корзине" in texts(r).lower(), texts(r)[:80])
    r = engine.message(bid, action="cart")
    ok("shop: корзина", product["title"] in texts(r) and "Итого" in texts(r), texts(r)[:80])
    r = engine.message(bid, action="clear")
    ok("shop: очистка", "очищена" in texts(r).lower(), texts(r)[:80])
    engine.message(bid, action=f"add:{product['id']}")
    r = engine.message(bid, action="checkout")
    ok("shop: checkout", "Как вас зовут" in texts(r), texts(r)[:80])
    engine.message(bid, text="Никита")
    r = engine.message(bid, text="123")
    ok("shop: плохой телефон отклонён", "Проверьте" in texts(r) or "ещё раз" in texts(r), texts(r)[:80])
    r = engine.message(bid, text="+7 902 123-45-67")
    ok("shop: заказ принят", "Заказ принят" in texts(r), texts(r)[:80])
    ok("shop: уведомление магазину", bool(admin(r)), "admin missing")


def test_metadata() -> None:
    print("\n[templates] брифы и обложки")
    visible = [k for k in engine.TEMPLATES if k not in ("ai", "lead")]
    ok("templates: ровно 3 активных", visible == list(VISIBLE), str(visible))
    for key in visible:
        meta = engine.TEMPLATES[key]
        fields = meta["fields"]
        ok(f"{key}: 4+ поля", len(fields) >= 4, str(len(fields)))
        ok(f"{key}: обязательные заполнены", all(meta["defaults"].get(f["key"]) for f in fields if f.get("required")), str(meta["defaults"]))
        ok(f"{key}: нет пустых label", all(f.get("label") for f in fields), "")
        cover = ROOT / "platform" / "static" / "covers" / f"{key}.png"
        ok(f"{key}: обложка есть", cover.exists() and cover.stat().st_size > 30_000, f"{cover} {cover.stat().st_size if cover.exists() else 0}")
    # content generated from defaults must not contain placeholders like [адрес]
    for key in visible:
        bot = engine.create_bot(key, dict(engine.TEMPLATES[key]["defaults"]))
        joined = json.dumps(bot["config"]["brief"], ensure_ascii=False)
        ok(f"{key}: без [placeholder]", not re.search(r"\[[^\]]+\]", joined) and "REPLACE" not in joined.upper(), "")


def test_web() -> None:
    print("\n[web] каталог и обложки")
    try:
        health = httpx.get(f"{PUBLIC}/api/health", timeout=20).json()
        ok("web: health", health.get("ok") is True, str(health))
    except Exception as exc:
        ok("web: health", False, str(exc))
    try:
        catalog = httpx.get(f"{PUBLIC}/api/catalog", timeout=20).json()["templates"]
        ids = [t["id"] for t in catalog]
        ok("web: 3 шаблона без AI/lead", set(ids) == set(VISIBLE) and len(ids) == 3, str(ids))
        for item in catalog:
            ok(f"web: обложка {item['id']}", httpx.get(PUBLIC + item["cover"], timeout=20).status_code == 200, item["cover"])
    except Exception as exc:
        ok("web: catalog", False, str(exc))


def test_tokens() -> None:
    print("\n[live] Telegram-токены")
    for name, env in (("platform", "PLATFORM_BOT_TOKEN"), ("booking", "BOOKING_BOT_TOKEN"), ("shop", "SHOP_BOT_TOKEN"), ("ai", "AI_BOT_TOKEN")):
        token = os.getenv(env, "").strip()
        if not token:
            ok(f"token: {name}", False, f"{env} пуст")
            continue
        try:
            data = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=20).json()
            ok(f"token: {name} жив", data.get("ok") is True, str(data.get("description")))
        except Exception as exc:
            ok(f"token: {name} жив", False, str(exc))


def test_persistence() -> None:
    print("\n[persistence] сохранение")
    path = ROOT / "private" / "tenants.json"
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    ok("storage: файл есть", path.exists(), str(path))
    ok("storage: booking и shop", {r.get("template") for r in records} >= {"booking", "shop"}, str([r.get("template") for r in records]))
    ok("storage: AI/lead не поднимаются", all(r.get("template") not in ("ai", "lead") for r in records), "")


if __name__ == "__main__":
    test_booking()
    test_gift()
    test_shop()
    test_metadata()
    test_web()
    test_tokens()
    test_persistence()
    print("\n" + "=" * 60)
    print(f"PASSED {len(passed)} · FAILED {len(failed)}")
    if failed:
        print("FAILED:", ", ".join(failed))
        raise SystemExit(1)
