import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from local_practice import engine


def _text(result):
    return "\n".join(m.get("text", "") for m in result)


def test_custom_beauty_brief_reaches_client_flow():
    bot = engine.create_bot(
        "booking",
        {
            "business_name": "Тест Студия",
            "services": "Стрижка, Маникюр",
            "details": "Стрижка — 1000 ₽\nМаникюр — 2000 ₽",
            "slots": "10:00, 15:00",
            "contact": "@test_admin",
            "greeting": "Своё приветствие студии",
            "confirmation": "Готово! {Дата} в {Время}. Адрес: Тестовая 1",
            "address": "Тестовая 1",
        },
    )
    bot_id = bot["id"]
    started = engine.message(bot_id, action="start", user_name="Анна")
    assert "Своё приветствие студии" in _text(started)
    labels = [b["label"] for b in started[0]["buttons"]]
    assert "Стрижка" in labels and "Маникюр" in labels
    engine.message(bot_id, action="beauty:svc:0")
    engine.message(bot_id, action="beauty:book:0")
    engine.message(bot_id, action="beauty:date:tomorrow")
    engine.message(bot_id, action="beauty:time:10:00")
    final = engine.message(bot_id, action="beauty:contact:+79990000000")
    assert "Готово! Завтра в 10:00" in _text(final)
    assert "Тестовая 1" in _text(final)
