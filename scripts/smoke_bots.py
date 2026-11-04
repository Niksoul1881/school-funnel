"""Hard smoke test for the three bot scenarios and live Telegram tokens."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / "private" / "telegram-test.env")

from local_practice import engine  # noqa: E402

passed: list[str] = []
failed: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        passed.append(name)
        print(f"  OK  {name}")
    else:
        failed.append(name)
        print(f"  FAIL {name} {detail}")


def last(replies):
    return replies[-1] if replies else {}


def test_booking():
    print("\n[1] Запись к мастеру")
    brief = {
        "business_name": "Красотка",
        "services": "Стрижка — 2500 ₽ — 60 мин\nМаникюр — 1500 ₽ — 60 мин\nПедикюр — 2000 ₽ — 60 мин",
        "slots": "10:00, 12:00, 14:00, 16:00, 18:00",
        "address": "Пришвина 20",
        "contact": "@soulnik",
    }
    bot = engine.create_bot("booking", brief)
    bid = bot["id"]
    engine.message(bid, action="start")
    r = engine.message(bid, text="хочу стрижку")
    check("booking: понимает услугу текстом", "На какую дату" in last(r).get("text", ""), last(r).get("text", "")[:80])
    r = engine.message(bid, text="завтра")
    check("booking: понимает «завтра»", "Выберите время" in last(r).get("text", ""), last(r).get("text", "")[:80])
    r = engine.message(bid, text="15:00")
    check("booking: понимает время текстом", "Как вас зовут" in last(r).get("text", ""), last(r).get("text", "")[:80])
    r = engine.message(bid, text="Никита")
    check("booking: принимает имя", "телефон" in last(r).get("text", "").lower(), last(r).get("text", "")[:80])
    r = engine.message(bid, text="+79021234567")
    check("booking: принимает телефон", "Проверьте заявку" in last(r).get("text", ""), last(r).get("text", "")[:80])
    r = engine.message(bid, text="да")
    admin = [m for m in r if m.get("admin")]
    check("booking: заявка подтверждается", any("Готово" in m.get("text", "") for m in r), last(r).get("text", "")[:80])
    check("booking: уведомление владельцу", bool(admin), "admin message missing")
    check("booking: уведомление не клиенту", all(not m.get("admin") for m in r[:-1]), "")


def test_ai():
    print("\n[2] AI-консультант")
    brief = {
        "business_name": "Труба у Палыча",
        "niche": "магазин сантехники",
        "knowledge": (
            "Магазин «Труба у Палыча» — сантехника. "
            "Ассортимент: трубы, фитинги, краны, смесители, унитазы, радиаторы, бойлеры, насосы. "
            "Адрес: Пришвина 20. Работаем каждый день с 9 до 21. "
            "Доставка по городу по договорённости. Оплата картой и наличными. "
            "Помогаем подобрать по фото и размерам."
        ),
        "contact": "https://t.me/Soulnikita",
        "faq": "Есть ли доставка?|Да, по городу — по договорённости. Самовывоз есть всегда.",
    }
    bot = engine.create_bot("ai", brief)
    bid = bot["id"]
    engine.message(bid, action="start")
    answers = []
    for question in ("Где вы находитесь?", "Работаете ли вы в воскресенье?", "Есть ли доставка?"):
        r = engine.message(bid, text=question)
        answers.append(last(r).get("text", ""))
        print(f"    Q: {question}\n    A: {answers[-1][:160]}")
    check("ai: отвечает на вопрос об адресе", "Пришвина" in answers[0], answers[0][:80])
    check("ai: отвечает про воскресенье", "9" in answers[1] or "каждый" in answers[1].lower(), answers[1][:80])
    check("ai: отвечает про доставку", "достав" in answers[2].lower(), answers[2][:80])
    r = engine.message(bid, text="У вас есть золотые унитазы из космоса?")
    check("ai: зовёт человека на неизвестное", any(m.get("admin") for m in r) or "уточ" in last(r).get("text", "").lower(), last(r).get("text", "")[:80])


def test_shop():
    print("\n[3] Витрина товаров")
    brief = {
        "business_name": "Кекс",
        "products": "Кекс «Ваниль» | 250 | Ванильный кекс | Кексы | 🧁 | \nМедовик | 3200 | Медовые коржи | Торты | 🍰 | ",
        "delivery": "Самовывоз: Пришвина 20",
        "contact": "@Soulnikita",
    }
    bot = engine.create_bot("shop", brief)
    bid = bot["id"]
    engine.message(bid, action="start")
    r = engine.message(bid, text="медовик")
    check("shop: поиск товара текстом", "Медовик" in last(r).get("text", ""), last(r).get("text", "")[:80])
    r = engine.message(bid, action="add:2")
    check("shop: добавление в корзину", "корзине" in last(r).get("text", "").lower(), last(r).get("text", "")[:80])
    r = engine.message(bid, action="cart")
    check("shop: корзина", "Медовик" in last(r).get("text", ""), last(r).get("text", "")[:80])
    engine.message(bid, action="checkout")
    engine.message(bid, text="Никита")
    r = engine.message(bid, text="+79021234567")
    check("shop: заказ оформляется", any("Заказ принят" in m.get("text", "") for m in r), last(r).get("text", "")[:80])
    check("shop: уведомление владельцу", any(m.get("admin") for m in r), "admin message missing")


def test_live_tokens():
    print("\n[4] Живые Telegram-токены")
    tokens = {
        "platform": os.getenv("PLATFORM_BOT_TOKEN", "").strip(),
        "booking": os.getenv("BOOKING_BOT_TOKEN", "").strip(),
        "ai": os.getenv("AI_BOT_TOKEN", "").strip(),
        "shop": os.getenv("SHOP_BOT_TOKEN", "").strip(),
    }
    for name, token in tokens.items():
        if not token:
            check(f"telegram: @{name} токен задан", False, "пусто в private/telegram-test.env")
            continue
        try:
            r = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=20).json()
            check(f"telegram: @{name} жив", r.get("ok") is True, str(r.get("description")))
        except Exception as exc:
            check(f"telegram: @{name} жив", False, str(exc))


def test_persistence():
    print("\n[5] Сохранение ботов")
    path = ROOT / "private" / "tenants.json"
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    check("persistence: файл есть", path.exists(), str(path))
    check("persistence: три бота", len(records) >= 3, f"records={len(records)}")
    names = {item.get("username") for item in records}
    for expected in ("booking_test_soulnik_bot", "ai_test_soulnik_bot", "shop_test_soulnik_bot"):
        check(f"persistence: {expected}", expected in names)


if __name__ == "__main__":
    test_booking()
    test_ai()
    test_shop()
    test_live_tokens()
    test_persistence()
    print("\n" + "=" * 50)
    print(f"PASSED {len(passed)} · FAILED {len(failed)}")
    if failed:
        print("FAILED:", ", ".join(failed))
        raise SystemExit(1)
