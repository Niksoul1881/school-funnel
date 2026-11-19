import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telegram_bots.platform_bot import builder_fields, field_prompt


def test_builder_step_counts():
    assert len(builder_fields("booking")) == 9
    assert len(builder_fields("gift")) == 10
    assert len(builder_fields("shop")) == 7


def test_every_step_has_number_and_label():
    for template in ("booking", "gift", "shop"):
        fields = builder_fields(template)
        for index, field in enumerate(fields):
            text = field_prompt(template, index)
            assert f"Шаг {index + 1} из {len(fields)}" in text
            assert field["label"] in text


def test_beauty_photo_has_full_tip():
    fields = builder_fields("booking")
    index = next(i for i, f in enumerate(fields) if f["key"] == "photo")
    text = field_prompt("booking", index)
    assert "Шаг 2: Визуальное оформление" in text
    assert "Идеального универсального фото не существует" in text
    assert "визуал строго у заказчика" in text


def test_required_doc_phrases_present():
    checks = {
        ("booking", "description"): "Добро пожаловать в пространство красоты",
        ("booking", "greeting"): "Почему выбирают именно нас",
        ("booking", "confirmation"): "{Дата} в {Время}",
        ("gift", "description"): "Бесплатный [гайд / чек-лист / мини-курс]",
        ("gift", "timer2h"): "таймер на 2 часа",
        ("shop", "products"): "Добавить товар",
    }
    for (template, key), phrase in checks.items():
        fields = builder_fields(template)
        index = next(i for i, f in enumerate(fields) if f["key"] == key)
        assert phrase in field_prompt(template, index)


def test_beauty_tips_are_not_truncated():
    fields = builder_fields("booking")
    by_key = {f["key"]: i for i, f in enumerate(fields)}
    description = field_prompt("booking", by_key["description"])
    greeting = field_prompt("booking", by_key["greeting"])
    assert "чтобы текст красиво висел над кнопкой «Старт»" in description
    assert "разбить на удобные абзацы и добавить пару смайликов" in greeting
    assert "чтобы клиентам было приятно и легко читать" in greeting
