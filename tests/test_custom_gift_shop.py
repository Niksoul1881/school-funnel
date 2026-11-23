import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from local_practice import engine


def _text(result):
    return "\n".join(m.get("text", "") for m in result)


def test_custom_gift_greeting_and_channel():
    bot = engine.create_bot(
        "gift",
        {
            "business_name": "Тест Школа",
            "channel": "https://t.me/test_channel",
            "gift": "https://t.me/test_gift",
            "contact": "https://t.me/test_curator",
            "greeting": "Своё приветствие воронки",
        },
    )
    result = engine.message(bot["id"], action="start")
    assert "Своё приветствие воронки" in _text(result)
    assert any("test_channel" in b["action"] for b in result[0]["buttons"])


def test_custom_shop_greeting_name_and_product():
    bot = engine.create_bot(
        "shop",
        {
            "business_name": "Тест Магазин",
            "products": "Тестовый товар | 1234 | описание | Товары | 🧪 | https://example.com/x.jpg",
            "contact": "@test_manager",
            "greeting": "Своё приветствие магазина",
        },
    )
    started = engine.message(bot["id"], action="start")
    assert "Своё приветствие магазина" in _text(started)
    labels = [b["label"] for b in started[0]["buttons"]]
    assert any("Тестовый товар" in label for label in labels)
    engine.message(bot["id"], action="shop:add:1")
    cart = engine.message(bot["id"], action="shop:cart")
    assert "Тестовый товар" in _text(cart)
