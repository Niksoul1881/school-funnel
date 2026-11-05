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


def test_booking_text_flow_and_admin(booking):
    engine.message(booking, action="start")
    assert "На какую дату" in text(engine.message(booking, text="хочу стрижку"))
    assert "Выберите время" in text(engine.message(booking, text="завтра"))
    assert "Как вас зовут" in text(engine.message(booking, text="15:00"))
    assert "телефон" in text(engine.message(booking, text="Никита")).lower()
    assert "Проверьте заявку" in text(engine.message(booking, text="+7 902 123-45-67"))
    result = engine.message(booking, text="да")
    assert "Готово" in text(result)
    assert any(m.get("admin") for m in result)
    assert all(not m.get("admin") for m in result[:-1])


def test_booking_rejects_short_phone(booking):
    engine.message(booking, action="start")
    engine.message(booking, action="service:0")
    engine.message(booking, action="date:tomorrow")
    engine.message(booking, action="time:12:00")
    engine.message(booking, text="Никита")
    result = engine.message(booking, text="123")
    assert "ошибка" in text(result).lower() or "ещё раз" in text(result).lower()


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


def test_shop_has_prices_with_currency(shop):
    result = engine.message(shop, action="cat:Все")
    cards = [m for m in result if "₽" in m.get("text", "")]
    assert cards


def test_shop_search_and_cart(shop):
    engine.message(shop, action="start")
    product = engine.BOTS[shop]["config"]["products"][0]
    assert product["title"] in text(engine.message(shop, text=product["title"]))
    engine.message(shop, action=f"add:{product['id']}")
    cart = engine.message(shop, action="cart")
    assert product["title"] in text(cart)
    assert "Итого" in text(cart)
    assert any(b["action"].startswith("qty:+") for b in buttons(cart))


def test_shop_quantity_and_remove(shop):
    product = engine.BOTS[shop]["config"]["products"][0]
    engine.message(shop, action=f"add:{product['id']}")
    assert "× 2" in text(engine.message(shop, action=f"qty:+{product['id']}"))
    assert "× 1" in text(engine.message(shop, action=f"qty:-{product['id']}"))
    assert "пустая" in text(engine.message(shop, action=f"remove:{product['id']}")).lower()


def test_shop_checkout_requires_address(shop):
    product = engine.BOTS[shop]["config"]["products"][0]
    engine.message(shop, action=f"add:{product['id']}")
    engine.message(shop, action="checkout")
    engine.message(shop, text="Никита")
    engine.message(shop, text="+7 902 123-45-67")
    result = engine.message(shop, text="Москва, Примерная 10")
    assert "ORD-" in text(result)
    assert any(m.get("admin") for m in result)


def test_shop_pickup(shop):
    product = engine.BOTS[shop]["config"]["products"][0]
    engine.message(shop, action=f"add:{product['id']}")
    engine.message(shop, action="checkout")
    engine.message(shop, text="Никита")
    engine.message(shop, text="+7 902 123-45-67")
    result = engine.message(shop, action="pickup")
    assert "Самовывоз" in text(result)
    assert "ORD-" in text(result)
