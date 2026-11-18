"""Pytest suite for bot scenarios and template contract."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from local_practice import engine  # noqa: E402


def make(template: str) -> str:
    return engine.create_bot(template, dict(engine.TEMPLATES[template]["defaults"]))["id"]


def text(replies: list[dict]) -> str:
    return "\n".join(m.get("text", "") for m in replies)


def buttons(replies: list[dict]) -> list[dict]:
    return [b for m in replies for b in m.get("buttons", [])]


@pytest.fixture()
def booking():
    return make("booking")


@pytest.fixture()
def shop():
    return make("shop")


@pytest.fixture()
def gift():
    return make("gift")


def test_visible_templates():
    assert [k for k in engine.TEMPLATES if k not in ("ai", "lead")] == ["booking", "gift", "shop"]


@pytest.mark.parametrize("template", ["booking", "gift", "shop"])
def test_template_has_four_fields_and_defaults(template):
    meta = engine.TEMPLATES[template]
    assert len(meta["fields"]) >= 4
    assert all(meta["defaults"].get(f["key"]) for f in meta["fields"] if f.get("required"))


@pytest.mark.parametrize("template", ["booking", "gift", "shop"])
def test_template_has_cover(template):
    cover = ROOT / "platform" / "static" / "covers" / f"{template}.png"
    assert cover.exists() and cover.stat().st_size > 30_000


@pytest.mark.parametrize("template", ["booking", "gift", "shop"])
def test_no_placeholder_in_brief(template):
    bot = engine.create_bot(template, dict(engine.TEMPLATES[template]["defaults"]))
    brief = json.dumps(bot["config"]["brief"], ensure_ascii=False)
    assert not re.search(r"\[[^\]]+\]", brief)
    assert "REPLACE" not in brief.upper()


def test_beauty_start_and_services(booking):
    result = engine.message(booking, action="start")
    labels = [b["label"] for b in buttons(result)]
    assert labels == ["✂️ Стрижка и укладка", "💅 Маникюр", "👣 SMART-педикюр", "🎨 Окрашивание"]


def test_beauty_contact_flow_and_admin(booking):
    engine.message(booking, action="start")
    service = engine.message(booking, action="beauty:svc:hair")
    assert "Стрижка и укладка" in text(service)
    engine.message(booking, action="beauty:book:hair")
    engine.message(booking, action="beauty:date:tomorrow")
    contact_prompt = engine.message(booking, action="beauty:time:10:00")
    assert any(m.get("contact_request") for m in contact_prompt)
    result = engine.message(booking, action="beauty:contact:+7 902 123-45-67")
    assert "Запись подтверждена" in text(result)
    assert any(m.get("admin") for m in result)


def test_booking_back_resets_stage(booking):
    engine.message(booking, action="service:0")
    result = engine.message(booking, action="back")
    assert "Выберите услугу" in text(result)


def test_booking_cancel_resets(booking):
    engine.message(booking, action="service:0")
    result = engine.message(booking, action="cancel")
    assert "Выберите услугу" in text(result)


def test_gift_has_channel_url_and_grants(gift):
    result = engine.message(gift, action="start")
    assert any(b["action"].startswith("url:") for b in buttons(result))
    granted = engine.message(gift, action="check")
    assert "Спасибо за подписку" in text(granted)
    assert any(b["action"].startswith("url:") for b in buttons(granted))
    assert any(m.get("admin") for m in granted)


def test_shop_showcase_and_prices(shop):
    result = engine.message(shop, action="start")
    labels = [b["label"] for b in buttons(result)]
    assert labels[:4] == ["🍯 Медовик", "❤️ Красный бархат", "🍬 Набор макарон", "✨ Корпусные десерты"]


def test_shop_product_card(shop):
    result = engine.message(shop, action="shop:product:1")
    assert "Классический Медовик" in text(result)
    assert "2 600 ₽" in text(result)
    assert any(b["action"] == "shop:add:1" for b in buttons(result))


def test_shop_add_and_cart(shop):
    result = engine.message(shop, action="shop:add:1")
    assert "«Медовик» добавлен" in text(result)
    cart = engine.message(shop, action="shop:cart")
    assert "Медовик" in text(cart)
    assert "2 600 ₽" in text(cart)
    assert any(b["action"] == "shop:checkout" for b in buttons(cart))


def test_shop_checkout_contact(shop):
    engine.message(shop, action="shop:add:1")
    prompt = engine.message(shop, action="shop:checkout")
    assert "номер телефона" in text(prompt)
    result = engine.message(shop, text="+7 999 123-45-67, на субботу к 15:00")
    assert "Заказ принят" in text(result)
    assert any(m.get("admin") for m in result)


def test_shop_empty_cart(shop):
    result = engine.message(shop, action="shop:cart")
    assert "пуста" in text(result).lower()


def test_beauty_date_buttons(booking):
    engine.message(booking, action="start")
    result = engine.message(booking, action="beauty:book:hair")
    actions = [b["action"] for b in buttons(result)]
    assert actions[:3] == ["beauty:date:today", "beauty:date:tomorrow", "beauty:date:after"]


def test_beauty_time_slots(booking):
    engine.message(booking, action="start")
    today = engine.message(booking, action="beauty:date:today")
    assert [b["label"] for b in buttons(today)][:2] == ["17:30", "19:00"]
    tomorrow = engine.message(booking, action="beauty:date:tomorrow")
    assert [b["label"] for b in buttons(tomorrow)][:4] == ["10:00", "12:30", "15:00", "18:00"]


def _fill_beauty(bid: str):
    engine.message(bid, action="start")
    engine.message(bid, action="beauty:svc:hair")
    engine.message(bid, action="beauty:book:hair")
    engine.message(bid, action="beauty:date:tomorrow")
    engine.message(bid, action="beauty:time:10:00")
    return engine.message(bid, action="beauty:contact:+7 902 123-45-67")


def test_owner_order_journal(booking):
    result = _fill_beauty(booking)
    assert "Запись подтверждена" in text(result)
    rows = engine.orders(booking)
    assert rows and rows[-1]["type"] == "booking"
    assert rows[-1]["time"] == "10:00"
    assert engine.stats(booking).get("bookings") == 1

def test_services_human_price_format():
    rows = engine._services("Стрижка 1500 р 60 минут\nСпа Энергия 6000 90 минут")
    assert rows[0] == {"title": "Стрижка", "price": "1500 ₽", "duration": "60 мин"}
    assert rows[1] == {"title": "Спа Энергия", "price": "6000 ₽", "duration": "90 мин"}

