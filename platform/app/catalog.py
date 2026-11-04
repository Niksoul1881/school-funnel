"""Каталог шаблонов и генерация файлов проекта.

Шаблон — это не «болванка», а набор файлов с манифестом:
направление, бриф, стек, превью и инструкция запуска.
"""
from __future__ import annotations

import html
import json
import re
from typing import Any

from .template_ai import AI_CONSULTANT_BOT_PY
from .template_booking import BOOKING_BOT_PY
from .template_manifest import TEMPLATES
from .template_shop import SHOP_BOT_PY, SHOP_CATALOG_BOT_PY, SHOP_CSS, SHOP_HTML, SHOP_JS

DIRECTIONS = {
    "bot": "Чат-бот",
    "agent": "AI-агент",
    "miniapp": "Мини-приложение",
}


def _common_fields(direction: str) -> list[dict]:
    fields = [
        {"key": "business_name", "label": "Название бизнеса", "type": "text", "placeholder": "Салон «Лотос»", "required": True},
        {"key": "niche", "label": "Ниша", "type": "text", "placeholder": "салон красоты", "required": True},
        {"key": "product", "label": "Продукт или услуги", "type": "textarea", "placeholder": "стрижки, окрашивание, маникюр", "required": True},
        {"key": "audience", "label": "Аудитория", "type": "text", "placeholder": "женщины 25–45", "required": True},
        {"key": "goal", "label": "Главная цель", "type": "text", "placeholder": "запись на услуги", "required": True},
        {"key": "tone", "label": "Тон общения", "type": "text", "placeholder": "дружелюбный, без давления", "required": True},
        {"key": "price", "label": "Цены", "type": "textarea", "placeholder": "стрижка — 3 500 ₽\nокрашивание — от 7 000 ₽", "required": False},
        {"key": "faq", "label": "Частые вопросы", "type": "textarea", "placeholder": "Можно ли записаться на сегодня?|Да, если есть окно.\nЕсть ли парковка?|Да, во дворе.", "required": False, "hint": "Каждый вопрос с новой строки: Вопрос|Ответ"},
        {"key": "contact", "label": "Контакт", "type": "text", "placeholder": "@salon, +7 999 123-45-67", "required": True},
        {"key": "payment", "label": "Оплата", "type": "select", "options": [
            {"value": "none", "label": "Без оплаты"},
            {"value": "stars", "label": "Telegram Stars"},
            {"value": "card", "label": "Карта / Robokassa"},
        ], "default": "none"},
        {"key": "accent", "label": "Акцентный цвет", "type": "color", "default": "#ff4f8b"},
    ]
    if direction == "agent":
        fields += [
            {"key": "sources", "label": "Источники", "type": "textarea", "placeholder": "https://example.com/rss\nhttps://t.me/channel", "required": False, "hint": "По одной ссылке на строку"},
            {"key": "schedule", "label": "Расписание", "type": "select", "options": [
                {"value": "09:00", "label": "Каждый день в 09:00"},
                {"value": "18:00", "label": "Каждый день в 18:00"},
                {"value": "weekly", "label": "Раз в неделю"},
            ], "default": "09:00"},
            {"key": "format", "label": "Что в отчёте", "type": "textarea", "placeholder": "3 главные новости, 1 вывод, ссылки", "required": False},
        ]
    if direction == "miniapp":
        fields += [
            {"key": "sections", "label": "Экраны", "type": "text", "placeholder": "Главная, Услуги, Записаться, Контакты", "required": False},
        ]
    return fields


LEGACY_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "bot-vizitka",
        "name": "Бот-визитка с AI",
        "direction": "bot",
        "tagline": "Меню, услуги, ответы на вопросы и контакт — за вечер.",
        "description": "Универсальный бот для эксперта, салона или магазина: приветствие, меню, прайс, частые вопросы, кнопка «связаться». Основа для первого заказа.",
        "price": "5–15 тыс. ₽",
        "stack": ["Python", "aiogram", "content.json"],
        "preview": "bot",
        "icon": "bot",
        "badge": "MVP",
        "brief_fields": _common_fields("bot"),
        "defaults": {
            "business_name": "Салон «Лотос»",
            "niche": "салон красоты",
            "product": "стрижки, окрашивание, маникюр",
            "audience": "женщины 25–45",
            "goal": "запись на услуги",
            "tone": "дружелюбный, без давления",
            "price": "стрижка — 3 500 ₽, окрашивание — от 7 000 ₽, маникюр — 2 500 ₽",
            "faq": "Можно ли записаться на сегодня?|Да, если есть свободное окно — бот покажет ближайшее.\nЕсть ли парковка?|Да, во дворе дома.",
            "contact": "@lotos_salon, +7 999 123-45-67",
            "payment": "none",
            "accent": "#ff4f8b",
        },
    },
    {
        "id": "bot-funnel",
        "name": "Бот-воронка с оплатой",
        "direction": "bot",
        "tagline": "Лид-магнит, прогрев по дням и оплата внутри Telegram.",
        "description": "Бот, который забирает заявку, выдаёт подарок, прогревает и продаёт. Каркас для продюсеров и экспертов: анкета, цепочка, оплата, аналитика.",
        "price": "40–60 тыс. ₽",
        "stack": ["Python", "aiogram", "воронка"],
        "preview": "bot",
        "icon": "bot",
        "badge": "",
        "brief_fields": _common_fields("bot"),
        "defaults": {
            "business_name": "Курс «Спокойный доход»",
            "niche": "онлайн-школа",
            "product": "курс по AI-автоматизации",
            "audience": "женщины 30–50, хотят второй доход",
            "goal": "заявка и оплата курса",
            "tone": "тёплый, честный, без давления",
            "price": "курс — 49 900 ₽, рассрочка — 4 158 ₽/мес",
            "faq": "Сколько длится курс?|9 модулей, 6–8 недель.\nЕсть ли рассрочка?|Да, без переплаты.",
            "contact": "@school_manager",
            "payment": "stars",
            "accent": "#8b5cf6",
        },
    },
    {
        "id": "ai-assistant",
        "name": "AI-ассистент по материалам",
        "direction": "bot",
        "tagline": "Отвечает ученикам по урокам, PDF и методичкам.",
        "description": "Бот с базой знаний: загружаете материалы, он отвечает по ним и передаёт сложные вопросы куратору. Каркас RAG для школ и экспертов.",
        "price": "80–150 тыс. ₽",
        "stack": ["Python", "aiogram", "RAG"],
        "preview": "bot",
        "icon": "bot",
        "badge": "",
        "brief_fields": _common_fields("bot"),
        "defaults": {
            "business_name": "Школа AI-агентов",
            "niche": "онлайн-школа",
            "product": "курс по ботам и агентам",
            "audience": "новички 25–45",
            "goal": "ответы на вопросы учеников 24/7",
            "tone": "спокойный, по делу, с поддержкой",
            "price": "курс — 49 900 ₽",
            "faq": "Где взять доступ к урокам?|В личном кабинете, ссылка приходит после оплаты.\nЧто если не получается?|Напишите куратору, бот передаст вопрос.",
            "contact": "@school_support",
            "payment": "none",
            "accent": "#3ec7ff",
        },
    },
    {
        "id": "content-agent",
        "name": "Контент-завод",
        "direction": "agent",
        "tagline": "Сам пишет посты по рубрикам и присылает на одобрение.",
        "description": "Агент по расписанию собирает темы, пишет посты в голосе бренда и присылает в Telegram с кнопками «Опубликовать / В слот / Правки».",
        "price": "15–60 тыс. ₽",
        "stack": ["Python", "cron", "LLM"],
        "preview": "agent",
        "icon": "agent",
        "badge": "",
        "brief_fields": _common_fields("agent"),
        "defaults": {
            "business_name": "Канал «Спокойный AI»",
            "niche": "AI и автоматизация",
            "product": "контент для Telegram и Reels",
            "audience": "предприниматели и эксперты",
            "goal": "регулярный контент без выгорания",
            "tone": "дерзкий, но по делу",
            "price": "",
            "faq": "",
            "contact": "@content_manager",
            "payment": "none",
            "accent": "#ff8a3d",
            "sources": "https://t.me/ai_newz\nhttps://techcrunch.com/feed/",
            "schedule": "09:00",
            "format": "3 поста: новость, разбор, история. Без воды, с эмодзи и CTA.",
        },
    },
    {
        "id": "price-agent",
        "name": "Мониторинг цен",
        "direction": "agent",
        "tagline": "Следит за конкурентами и присылает только изменения.",
        "description": "Агент обходит сайты конкурентов, записывает цены и наличие, сравнивает с прошлым запуском и пишет в Telegram: где упало, где закончилось.",
        "price": "15–30 тыс. ₽",
        "stack": ["Python", "httpx", "таблица"],
        "preview": "agent",
        "icon": "agent",
        "badge": "",
        "brief_fields": _common_fields("agent"),
        "defaults": {
            "business_name": "Магазин «Полка»",
            "niche": "товары для дома",
            "product": "посудa и декор",
            "audience": "покупатели маркетплейсов",
            "goal": "держать цены под контролем",
            "tone": "сухо, цифрами",
            "price": "",
            "faq": "",
            "contact": "@shop_owner",
            "payment": "none",
            "accent": "#3ddc97",
            "sources": "https://example-shop.ru/catalog\nhttps://second-shop.ru/catalog",
            "schedule": "09:00",
            "format": "Таблица: товар, наша цена, конкурент, разница, наличие.",
        },
    },
    {
        "id": "miniapp-showcase",
        "name": "Мини-апп витрины",
        "direction": "miniapp",
        "tagline": "Красивая витрина внутри Telegram — без скачивания.",
        "description": "Приложение-витрина: обложка, подборки, карточки товаров и кнопка «Купить». Открывается из бота, работает на телефоне как обычное приложение.",
        "price": "20–40 тыс. ₽",
        "stack": ["HTML", "CSS", "JS"],
        "preview": "miniapp",
        "icon": "app",
        "badge": "MVP",
        "brief_fields": _common_fields("miniapp"),
        "defaults": {
            "business_name": "Студия «Лотос»",
            "niche": "одежда и аксессуары",
            "product": "базовый гардероб",
            "audience": "женщины 25–40",
            "goal": "продажи через витрину",
            "tone": "лёгкий, современный",
            "price": "футболка — 2 900 ₽, брюки — 5 900 ₽",
            "faq": "",
            "contact": "@lotos_store",
            "payment": "card",
            "accent": "#ff4f8b",
            "sections": "Главная, Каталог, Подборки, Контакты",
        },
    },
    {
        "id": "miniapp-cabinet",
        "name": "Кабинет ученика",
        "direction": "miniapp",
        "tagline": "Уроки, прогресс и задание дня — в телефоне ученика.",
        "description": "Личный кабинет для онлайн-школы: уроки, прогресс, задание дня, AI-помощник и оплата. Каркас, который можно продать школе за 50 тыс. ₽+.",
        "price": "от 50 тыс. ₽",
        "stack": ["HTML", "CSS", "JS"],
        "preview": "miniapp",
        "icon": "app",
        "badge": "",
        "brief_fields": _common_fields("miniapp"),
        "defaults": {
            "business_name": "Школа AI-агентов",
            "niche": "онлайн-школа",
            "product": "курс по AI-агентам",
            "audience": "ученики 25–45",
            "goal": "довести ученика до конца курса",
            "tone": "поддерживающий",
            "price": "курс — 49 900 ₽",
            "faq": "",
            "contact": "@school_support",
            "payment": "stars",
            "accent": "#8b5cf6",
            "sections": "Сегодня, Уроки, Прогресс, Профиль",
        },
    },
]

TEMPLATES_BY_ID = {t["id"]: t for t in [*LEGACY_TEMPLATES, *TEMPLATES]}

# Служебный шаблон для проектов, загруженных папкой. В каталог не попадает.
IMPORTED_TEMPLATE = {
    "id": "imported",
    "name": "Мой проект",
    "direction": "code",
    "tagline": "Твоя папка с файлами",
    "description": "Проект, загруженный с компьютера. Работай с файлами и AI-помощником.",
    "price": "",
    "stack": ["твой код"],
    "preview": "code",
    "icon": "folder",
    "badge": "",
    "brief_fields": [],
    "defaults": {},
}
TEMPLATES_BY_ID["imported"] = IMPORTED_TEMPLATE


def _text(value: Any, fallback: str = "") -> str:
    return str(value).strip() if value is not None else fallback


def _parse_prices(raw: str) -> list[dict]:
    items: list[dict] = []
    for part in re.split(r"[,;\n]", raw or ""):
        part = part.strip()
        if not part:
            continue
        if "—" in part:
            title, price = part.split("—", 1)
        elif " - " in part:
            title, price = part.split(" - ", 1)
        else:
            title, price = part, ""
        items.append({"title": title.strip(), "price": price.strip()})
    return items or [{"title": "Прайс", "price": _text(raw, "по запросу")}]


def _parse_faq(raw: str) -> list[dict]:
    items: list[dict] = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            q, a = line.split("|", 1)
        elif "—" in line:
            q, a = line.split("—", 1)
        else:
            q, a = line, "Уточните детали у администратора."
        items.append({"q": q.strip(), "a": a.strip()})
    return items or [
        {"q": "Как записаться?", "a": "Нажмите «Записаться» — я подскажу свободное время."},
        {"q": "Сколько стоит?", "a": "Цены указаны в разделе «Цены»."},
    ]


def _parse_services(raw: str) -> list[dict]:
    items: list[dict] = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("—")]
        if len(parts) < 2:
            parts = [p.strip() for p in line.split("|")]
        title = parts[0] if parts else line
        price = parts[1] if len(parts) > 1 else "по запросу"
        duration = parts[2] if len(parts) > 2 else "60 мин"
        items.append({"title": title, "price": price, "duration": duration})
    return items or [{"title": "Консультация", "price": "по запросу", "duration": "60 мин"}]


def _parse_products(raw: str) -> list[dict]:
    items: list[dict] = []
    for index, line in enumerate((raw or "").splitlines()):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        items.append({
            "id": index + 1,
            "title": parts[0] if parts else line,
            "price": parts[1] if len(parts) > 1 else "по запросу",
            "description": parts[2] if len(parts) > 2 else "",
            "category": parts[3] if len(parts) > 3 else "Другое",
            "emoji": parts[4] if len(parts) > 4 else "🛍️",
            "image": parts[5] if len(parts) > 5 else "",
        })
    return items or [
        {"id": 1, "title": "Товар 1", "price": "1 000 ₽", "description": "Описание", "category": "Другое", "emoji": "🛍️"},
        {"id": 2, "title": "Товар 2", "price": "2 000 ₽", "description": "Описание", "category": "Другое", "emoji": "🛍️"},
    ]


def _menu_for(template_id: str) -> list[dict]:
    if template_id == "bot-funnel":
        return [
            {"id": "gift", "title": "Забрать подарок"},
            {"id": "program", "title": "Программа"},
            {"id": "prices", "title": "Цены"},
            {"id": "contact", "title": "Связаться"},
        ]
    if template_id == "ai-assistant":
        return [
            {"id": "lessons", "title": "Уроки"},
            {"id": "faq", "title": "Частые вопросы"},
            {"id": "contact", "title": "Куратор"},
        ]
    return [
        {"id": "services", "title": "Услуги"},
        {"id": "book", "title": "Записаться"},
        {"id": "prices", "title": "Цены"},
        {"id": "contact", "title": "Связаться"},
    ]


def build_content(template_id: str, brief: dict) -> dict:
    name = _text(brief.get("business_name"), "Проект")
    niche = _text(brief.get("niche"), "бизнес")
    tone = _text(brief.get("tone"), "дружелюбный")
    accent = _text(brief.get("accent"), "#ff4f8b")
    if not re.match(r"^#[0-9a-fA-F]{6}$", accent):
        accent = "#ff4f8b"
    base = {
        "template": template_id,
        "business": {"name": name, "niche": niche, "tone": tone, "accent": accent},
        "tone": tone,
        "contact": _text(brief.get("contact"), "@manager"),
        "faq": _parse_faq(_text(brief.get("faq"), "")),
    }
    if template_id == "booking":
        slots = [s.strip() for s in re.split(r"[,;\n]", _text(brief.get("slots"), "")) if s.strip()]
        return {
            **base,
            "greeting": f"Здравствуйте! Это {name}. Запишу вас к мастеру за пару шагов.",
            "master_name": _text(brief.get("master_name"), "Мастер"),
            "services": _parse_services(_text(brief.get("services"), "")),
            "slots": slots or ["10:00", "12:00", "14:00", "16:00", "18:00"],
            "address": _text(brief.get("address"), ""),
            "admin_chat_id": _text(brief.get("admin_chat_id"), ""),
        }
    if template_id == "ai-consultant":
        knowledge = _text(brief.get("knowledge"), "")
        if not knowledge:
            knowledge = f"{name} — {niche}. Контакт: {base['contact']}."
        return {
            **base,
            "greeting": f"Здравствуйте! Я консультант {name}. Спросите что угодно — отвечу по делу.",
            "knowledge": knowledge,
            "model": _text(brief.get("model"), "deepseek-chat"),
            "fallback": f"Не хочу выдумывать. Лучше уточню у человека: {base['contact']}.",
        }
    if template_id == "shop":
        products = _parse_products(_text(brief.get("products"), ""))
        categories = []
        for product in products:
            if product["category"] not in categories:
                categories.append(product["category"])
        return {
            **base,
            "faq": [],
            "greeting": f"Здравствуйте! Это {name}. Выбирайте — заказ придёт нам в Telegram.",
            "products": products,
            "categories": categories,
            "delivery": [line.strip() for line in _text(brief.get("delivery"), "").splitlines() if line.strip()],
        }
    sections = [s.strip() for s in _text(brief.get("sections"), "Главная, Услуги, Записаться, Контакты").split(",") if s.strip()]
    greeting = {
        "bot-funnel": f"Привет! Это {name}. Помогу разобраться с курсом и забрать подарок.",
        "ai-assistant": f"Здравствуйте! Я AI-ассистент {name}. Отвечу по урокам и материалам.",
    }.get(template_id, f"Здравствуйте! Это {name}. Помогу с выбором и записью.")
    return {
        "template": template_id,
        "business": {"name": name, "niche": niche, "tone": tone, "accent": accent},
        "greeting": greeting,
        "goal": _text(brief.get("goal"), ""),
        "audience": _text(brief.get("audience"), ""),
        "product": _text(brief.get("product"), ""),
        "menu": _menu_for(template_id),
        "prices": _parse_prices(_text(brief.get("price"), "по запросу")),
        "faq": _parse_faq(_text(brief.get("faq"), "")),
        "contact": _text(brief.get("contact"), "@manager"),
        "payment": _text(brief.get("payment"), "none"),
        "sections": sections,
        "schedule": _text(brief.get("schedule"), "09:00"),
        "sources": [s.strip() for s in _text(brief.get("sources"), "").splitlines() if s.strip()],
        "format": _text(brief.get("format"), "3 главные новости, 1 вывод, ссылки"),
    }


BOT_PY = '''"""Telegram-бот проекта. Сгенерирован платформой; тексты — в content.json."""
import asyncio
import json
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

CONTENT = json.loads(Path(__file__).with_name("content.json").read_text(encoding="utf-8"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
dp = Dispatcher()


def menu_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=item["title"], callback_data=f"menu:{item['id']}")] for item in CONTENT["menu"]]
    rows.append([InlineKeyboardButton(text="Частые вопросы", callback_data="menu:faq")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def faq_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=item["q"][:60], callback_data=f"faq:{i}")] for i, item in enumerate(CONTENT["faq"])]
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def prices_text() -> str:
    return "\\n".join(f"• {p['title']} — {p['price']}" for p in CONTENT["prices"])


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(CONTENT["greeting"], reply_markup=menu_keyboard())


@dp.callback_query(F.data.startswith("menu:"))
async def menu(call: CallbackQuery) -> None:
    action = call.data.split(":", 1)[1]
    if action in ("services", "prices", "program"):
        await call.message.edit_text("Цены и услуги:\\n\\n" + prices_text(), reply_markup=menu_keyboard())
    elif action == "book":
        await call.message.edit_text(
            f"Запись: {CONTENT['contact']}\\nНапишите удобный день и время — администратор подтвердит.",
            reply_markup=menu_keyboard(),
        )
    elif action == "contact":
        await call.message.edit_text(f"Связаться: {CONTENT['contact']}", reply_markup=menu_keyboard())
    elif action == "gift":
        await call.message.edit_text(
            "Подарок: мини-гайд «5 ошибок при выборе» уже ждёт. Напишите «гайд» — пришлю.",
            reply_markup=menu_keyboard(),
        )
    elif action == "lessons":
        await call.message.edit_text("Уроки открываются в личном кабинете. Ссылка — в закрепе.", reply_markup=menu_keyboard())
    elif action == "faq":
        await call.message.edit_text("Выберите вопрос:", reply_markup=faq_keyboard())
    else:
        await call.message.edit_text(CONTENT["greeting"], reply_markup=menu_keyboard())
    await call.answer()


@dp.callback_query(F.data.startswith("faq:"))
async def faq(call: CallbackQuery) -> None:
    index = int(call.data.split(":", 1)[1])
    item = CONTENT["faq"][index]
    await call.message.edit_text(f"{item['q']}\\n\\n{item['a']}", reply_markup=faq_keyboard())
    await call.answer()


@dp.message(F.text)
async def any_message(message: Message) -> None:
    text = (message.text or "").lower()
    if "цена" in text or "стоим" in text:
        await message.answer(prices_text(), reply_markup=menu_keyboard())
    elif "запис" in text:
        await message.answer(f"Запись: {CONTENT['contact']}", reply_markup=menu_keyboard())
    else:
        await message.answer(CONTENT["greeting"], reply_markup=menu_keyboard())


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен.")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''


AGENT_PY = '''"""AI-агент проекта: собирает данные и присылает отчёт в Telegram."""
import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).parent
CONTENT = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
SCHEDULE = json.loads((ROOT / "schedule.json").read_text(encoding="utf-8"))
SOURCES = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))


async def fetch(source: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(source)
            return response.text[:4000]
    except Exception as exc:
        return f"Ошибка источника {source}: {exc}"


async def build_digest() -> str:
    parts = [f"# {CONTENT['business']['name']} · {datetime.now():%d.%m.%Y %H:%M}"]
    for source in SOURCES.get("sources", []):
        raw = await fetch(source)
        parts.append(f"\\n## {source}\\n{raw[:1200]}")
    parts.append("\\n---\\nФормат: " + CONTENT.get("format", "3 главные новости, 1 вывод, ссылки"))
    return "\\n".join(parts)


async def send_telegram(text: str) -> None:
    token = __import__("os").getenv("BOT_TOKEN", "")
    chat_id = __import__("os").getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("BOT_TOKEN / TELEGRAM_CHAT_ID не заданы — печатаю отчёт в консоль.\\n")
        print(text)
        return
    async with httpx.AsyncClient(timeout=20) as client:
        await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text[:4000]})


async def main() -> None:
    digest = await build_digest()
    await send_telegram(digest)


if __name__ == "__main__":
    asyncio.run(main())
'''


MINIAPP_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div id="app"></div>
<script>window.__CONTENT__ = __CONTENT_JSON__;</script>
<script src="app.js"></script>
</body>
</html>
'''


MINIAPP_CSS = ''':root{--accent:__ACCENT__;--ink:#151a28;--muted:#6b7280;--line:#eceef5;--soft:#f7f8fc}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--soft);color:var(--ink)}
.app{max-width:460px;margin:0 auto;min-height:100vh;background:#fff;padding-bottom:78px}
.hero{background:linear-gradient(135deg,var(--accent),#8b5cf6);color:#fff;padding:28px 20px 34px;border-radius:0 0 26px 26px}
.hero .kicker{font-size:11px;letter-spacing:.16em;text-transform:uppercase;opacity:.8;font-weight:800}
.hero h1{font-size:28px;line-height:1.1;margin:10px 0 8px}
.hero p{margin:0;opacity:.9;font-size:14px;line-height:1.5}
.sections{display:flex;gap:8px;overflow:auto;padding:14px 16px 4px}
.sections button{border:1px solid var(--line);background:#fff;color:var(--ink);padding:8px 13px;border-radius:999px;font-weight:700;font-size:12px;white-space:nowrap}
.sections button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.content{padding:12px 16px 20px}
.card{border:1px solid var(--line);border-radius:18px;padding:16px;margin-bottom:12px;background:#fff}
.card h3{margin:0 0 6px;font-size:16px}
.card p{margin:0;color:var(--muted);font-size:13px;line-height:1.5}
.price{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--line);font-size:14px}
.price:last-child{border-bottom:0}
.price b{color:var(--accent)}
.btn{display:block;width:100%;border:0;background:var(--accent);color:#fff;padding:14px;border-radius:14px;font-weight:800;font-size:15px;margin-top:8px}
.tabbar{position:fixed;bottom:0;left:0;right:0;max-width:460px;margin:0 auto;background:#fff;border-top:1px solid var(--line);display:flex;justify-content:space-around;padding:10px 4px 12px}
.tabbar button{border:0;background:none;color:var(--muted);font-size:11px;font-weight:700}
.tabbar button.on{color:var(--accent)}
'''


MINIAPP_JS = '''(function(){
  const c = window.__CONTENT__;
  const app = document.getElementById('app');
  const e = (v) => String(v ?? '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  let active = 0;
  const sections = c.sections && c.sections.length ? c.sections : ['Главная','Каталог','Контакты'];
  function render(){
    app.innerHTML = `
      <header class="hero">
        <div class="kicker">${e(c.business.niche)}</div>
        <h1>${e(c.business.name)}</h1>
        <p>${e(c.greeting)}</p>
      </header>
      <div class="sections">
        ${sections.map((s,i)=>`<button class="${i===active?'on':''}" data-i="${i}">${e(s)}</button>`).join('')}
      </div>
      <main class="content">
        <div class="card">
          <h3>${e(sections[active])}</h3>
          <p>${e(c.product || c.goal || 'Подборка и запись — внутри приложения.')}</p>
        </div>
        <div class="card">
          <h3>Цены</h3>
          ${c.prices.map(p=>`<div class="price"><span>${e(p.title)}</span><b>${e(p.price)}</b></div>`).join('')}
        </div>
        <div class="card">
          <h3>Связаться</h3>
          <p>${e(c.contact)}</p>
          <button class="btn" data-contact>Написать</button>
        </div>
      </main>
      <nav class="tabbar">
        ${sections.slice(0,4).map((s,i)=>`<button class="${i===active?'on':''}" data-i="${i}">${e(s)}</button>`).join('')}
      </nav>`;
    app.querySelectorAll('[data-i]').forEach(b=>b.onclick=()=>{active=+b.dataset.i;render();});
    app.querySelectorAll('[data-contact]').forEach(b=>b.onclick=()=>alert('Контакт: '+c.contact));
  }
  render();
})();
'''


def _readme(template: dict, content: dict) -> str:
    name = content["business"]["name"]
    if template["id"] == "booking":
        return f"""# Запись к мастеру — {name}

Telegram-бот записи: услуга → дата → время → имя → телефон → заявка администратору.

## Что внутри

- `bot.py` — пошаговая запись, SQLite, уведомление администратору.
- `content.json` — услуги, окна, адрес, контакты; код менять не нужно.
- `.env.example` — токен бота и Telegram ID администратора.
- `requirements.txt`, `Dockerfile` — запуск.

## Запуск

```bash
cp .env.example .env
# BOT_TOKEN — из @BotFather
# ADMIN_CHAT_ID — ваш Telegram ID (узнать у @userinfobot)
pip install -r requirements.txt
python bot.py
```

## Проверка

1. `/start` — бот покажет услуги.
2. Выберите услугу, дату `12.11`, время, имя и телефон.
3. Подтвердите — администратору придёт заявка, в `bookings.db` появится запись.

## Важно

Свободные окна в `content.json` — статические. Для календаря с занятостью нужен следующий уровень: интеграция с Google Calendar / CRM.
"""
    if template["id"] == "ai-consultant":
        return f"""# Умный консультант — {name}

AI-бот, который отвечает свободным текстом по базе знаний, а не кнопками.

## Что внутри

- `bot.py` — aiogram + LLM, история диалога, fallback на человека.
- `knowledge.md` — всё, что бот имеет право знать. Главный файл для настройки.
- `content.json` — бренд, тон, контакт, модель.
- `.env.example` — токен бота и LLM-ключ.

## Запуск

```bash
cp .env.example .env
# BOT_TOKEN — из @BotFather
# ADMIN_CHAT_ID — куда присылать вопросы без ответа
# LLM_API_KEY — ключ DeepSeek/OpenAI-совместимого API
pip install -r requirements.txt
python bot.py
```

Можно использовать DeepSeek, OpenRouter, локальный Ollama — любой OpenAI-совместимый endpoint.

## Как настраивать

1. Замените `knowledge.md` реальными правилами, ценами и адресами.
2. Прогоните `test_questions.md` — 10 вопросов.
3. Проверьте 5 нестандартных формулировок.
4. Если бот не знает — он даёт контакт человека и отправляет вопрос администратору.

## Без ключа

Бот не молчит: он ищет ответ в `faq` из `content.json`. Если совпадения нет — зовёт человека. Это демо-режим, а не полноценный AI.
"""
    if template["id"] == "shop":
        return f"""# Витрина товаров — {name}

Чат-бот витрины: фото товаров, категории, корзина и заказ администратору.

## Что внутри

- `bot.py` — каталог с фото, корзина, оформление заказа.
- `content.json` — товары, категории, доставка, контакт.
- `miniapp/` — та же витрина как Mini App; пригодится на следующем этапе.
- `.env.example` — токен бота и ID администратора.

## Запуск

```bash
cp .env.example .env
# BOT_TOKEN — из @BotFather
# ADMIN_CHAT_ID — ваш Telegram ID
pip install -r requirements.txt
python bot.py
```

## Как добавить товар

В `content.json`:

```json
{{"id": 1, "title": "Медовик", "price": "3 200", "description": "...", "category": "Торты", "emoji": "🍰", "image": "https://..."}}
```

`image` — прямая ссылка на фото. Если её нет или фото не открывается, бот пришлёт карточку текстом.

## Mini App

В `miniapp/` уже лежит веб-витрина. Когда будете готовы — задеплойте её и переключите кнопку бота на WebApp.
"""
    lines = [
        f"# {template['name']} — {name}",
        "",
        f"Направление: {DIRECTIONS[template['direction']]}",
        f"Сгенерировано платформой «Школа AI-агентов».",
        "",
        "## Что внутри",
        "",
    ]
    if template["direction"] == "bot":
        lines += [
            "- `bot.py` — Telegram-бот на aiogram: меню, услуги, FAQ, контакт.",
            "- `content.json` — все тексты и цены; меняйте здесь, код трогать не нужно.",
            "- `requirements.txt`, `.env.example`, `Dockerfile` — запуск.",
        ]
    elif template["direction"] == "agent":
        lines += [
            "- `agent.py` — сбор источников и отчёт.",
            "- `prompts/system.md` — роль и формат.",
            "- `schedule.json`, `sources.json` — расписание и источники.",
            "- `sample_output.md` — пример отчёта.",
        ]
    else:
        lines += [
            "- `index.html`, `styles.css`, `app.js` — мини-приложение.",
            "- `content.json` — тексты и цены.",
        ]
    lines += [
        "",
        "## Запуск",
        "",
        "```bash",
        "cp .env.example .env",
        "# вставьте BOT_TOKEN и TELEGRAM_CHAT_ID",
    ]
    if template["direction"] == "bot":
        lines += ["pip install -r requirements.txt", "python bot.py"]
    elif template["direction"] == "agent":
        lines += ["pip install -r requirements.txt", "python agent.py"]
    else:
        lines += ["python -m http.server 8080", "# откройте http://localhost:8080"]
    lines += ["```", "", "## Бриф", ""]
    for key in ("niche", "audience", "goal", "tone", "contact"):
        value = content.get(key) if key in content else content["business"].get(key, "")
        if value:
            lines.append(f"- **{key}**: {value}")
    lines += ["", "## Что дальше", "", "1. Проверьте тексты в `content.json`.", "2. Подключите бота и протестируйте сценарий.", "3. Покажите клиенту и соберите правки."]
    return "\n".join(lines)


def _bot_files(template: dict, content: dict) -> dict[str, str]:
    files = {
        "bot.py": BOT_PY,
        "content.json": json.dumps(content, ensure_ascii=False, indent=2),
        "requirements.txt": "aiogram==3.22.0\npython-dotenv==1.2.1\n",
        ".env.example": "BOT_TOKEN=\nTELEGRAM_CHAT_ID=\n",
        "Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nCMD [\"python\", \"bot.py\"]\n",
        ".gitignore": ".env\n__pycache__/\n*.pyc\n",
        "README.md": _readme(template, content),
        "prompts/system.md": (
            f"Ты — Telegram-бот «{content['business']['name']}». "
            f"Общайся в тоне: {content['business']['tone']}. "
            "Отвечай коротко, помогай выбрать услугу и записаться. "
            "Не выдумывай цены — бери их из content.json."
        ),
    }
    if template["id"] == "ai-assistant":
        files["knowledge.md"] = (
            f"# База знаний: {content['business']['name']}\n\n"
            "Замените этот файл материалами клиента: уроками, PDF, методичками.\n\n"
            "## Частые вопросы\n\n"
            + "\n\n".join(f"### {item['q']}\n{item['a']}" for item in content["faq"])
        )
        files["prompts/system.md"] = (
            "Ты — AI-ассистент онлайн-школы. Отвечай только по материалам из knowledge.md. "
            "Если ответа нет — предложи передать вопрос куратору. Тон: спокойный, поддерживающий."
        )
    if template["id"] == "bot-funnel":
        files["funnel.json"] = json.dumps({
            "lead_magnet": "мини-гайд «5 ошибок при выборе»",
            "steps": ["Получить подарок", "Ответить на 3 вопроса", "Прогрев 5 дней", "Предложение курса"],
            "payment": content["payment"],
        }, ensure_ascii=False, indent=2)
    if template["id"] == "booking":
        files["bot.py"] = BOOKING_BOT_PY
        files["requirements.txt"] = "aiogram==3.22.0\npython-dotenv==1.2.1\n"
        files[".env.example"] = "BOT_TOKEN=\nADMIN_CHAT_ID=\n"
        files["prompts/system.md"] = (
            f"Ты — бот записи «{content['business']['name']}». Веди клиента по шагам: "
            "услуга → дата → время → имя → телефон → подтверждение. "
            "Не придумывай свободные окна: бери их из content.json."
        )
    if template["id"] == "ai-consultant":
        files["bot.py"] = AI_CONSULTANT_BOT_PY
        files["knowledge.md"] = content["knowledge"]
        files["test_questions.md"] = (
            "# Проверка консультанта\n\n"
            "Прогоните эти вопросы в Telegram и сверьте ответы с knowledge.md.\n\n"
            "1. Сколько стоит стрижка?\n"
            "2. Где вы находитесь?\n"
            "3. Что если я опоздаю на 15 минут?\n"
            "4. Можно перенести запись?\n"
            "5. Есть ли парковка?\n"
            "6. Работаете ли вы в воскресенье?\n"
            "7. Можно ли оплатить картой?\n"
            "8. Сколько идёт окрашивание?\n"
            "9. Делаете ли вы детские стрижки?\n"
            "10. Что будет, если я не приду?\n\n"
            "Правило: если ответа нет в базе — бот должен позвать человека, а не выдумывать.\n"
        )
        files["requirements.txt"] = "aiogram==3.22.0\nhttpx>=0.28\npython-dotenv==1.2.1\n"
        files[".env.example"] = "BOT_TOKEN=\nADMIN_CHAT_ID=\nLLM_API_KEY=\nLLM_BASE_URL=https://api.deepseek.com/v1\nLLM_MODEL=deepseek-chat\n"
        files["prompts/system.md"] = (
            f"Ты — консультант «{content['business']['name']}». Отвечай только по knowledge.md. "
            "Если ответа нет — дай контакт человека. Не выдумывай цены и сроки."
        )
    if template["id"] == "shop":
        files["bot.py"] = SHOP_CATALOG_BOT_PY
        files["requirements.txt"] = "aiogram==3.22.0\npython-dotenv==1.2.1\n"
        files[".env.example"] = "BOT_TOKEN=\nADMIN_CHAT_ID=\n"
        files["README.md"] = _readme(template, content)
        encoded = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")
        title = html.escape(content["business"]["name"])
        files["miniapp/index.html"] = SHOP_HTML.replace("__TITLE__", title).replace("__CONTENT_JSON__", encoded)
        files["miniapp/styles.css"] = SHOP_CSS
        files["miniapp/app.js"] = SHOP_JS
    return files


def _agent_files(template: dict, content: dict) -> dict[str, str]:
    schedule = {"time": content.get("schedule", "09:00"), "timezone": "Europe/Moscow", "days": "mon-sun"}
    sources = {"sources": content.get("sources") or ["https://example.com/rss"]}
    sample = (
        f"# Пример отчёта: {content['business']['name']}\n\n"
        f"**Дата:** сегодня, {content.get('schedule', '09:00')}\n\n"
        f"**Формат:** {content.get('format', '3 главные новости, 1 вывод, ссылки')}\n\n"
        "1. Главная новость дня — коротко, что произошло и почему это важно.\n"
        "2. Второй сигнал — цифра или изменение.\n"
        "3. Вывод: что с этим делать.\n\n"
        "---\n_Сгенерировано агентом, проверено человеком._"
    )
    return {
        "agent.py": AGENT_PY,
        "content.json": json.dumps(content, ensure_ascii=False, indent=2),
        "schedule.json": json.dumps(schedule, ensure_ascii=False, indent=2),
        "sources.json": json.dumps(sources, ensure_ascii=False, indent=2),
        "prompts/system.md": (
            f"Ты — {template['name']} для «{content['business']['name']}». "
            f"Пиши в тоне: {content['business']['tone']}. Формат: {content.get('format')}. "
            "Не выдумывай факты, давай ссылки на источники."
        ),
        "sample_output.md": sample,
        "requirements.txt": "httpx>=0.28\npython-dotenv>=1.0\n",
        ".env.example": "BOT_TOKEN=\nTELEGRAM_CHAT_ID=\n",
        "README.md": _readme(template, content),
        ".gitignore": ".env\n__pycache__/\n*.pyc\n",
    }


def _miniapp_files(template: dict, content: dict) -> dict[str, str]:
    title = html.escape(content["business"]["name"])
    if template["id"] == "shop":
        encoded = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")
        html_file = SHOP_HTML.replace("__TITLE__", title).replace("__CONTENT_JSON__", encoded)
        return {
            "index.html": html_file,
            "styles.css": SHOP_CSS,
            "app.js": SHOP_JS,
            "bot.py": SHOP_BOT_PY,
            "requirements.txt": "aiogram==3.22.0\npython-dotenv==1.2.1\n",
            ".env.example": "BOT_TOKEN=\nWEBAPP_URL=\nADMIN_CHAT_ID=\n",
            "content.json": json.dumps(content, ensure_ascii=False, indent=2),
            "README.md": _readme(template, content),
            ".gitignore": ".env\n__pycache__/\n*.pyc\n",
        }
    encoded = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")
    html_file = MINIAPP_HTML.replace("__TITLE__", title).replace("__CONTENT_JSON__", encoded)
    css = MINIAPP_CSS.replace("__ACCENT__", content["business"]["accent"])
    return {
        "index.html": html_file,
        "styles.css": css,
        "app.js": MINIAPP_JS,
        "content.json": json.dumps(content, ensure_ascii=False, indent=2),
        "README.md": _readme(template, content),
        ".gitignore": ".env\n__pycache__/\n*.pyc\n",
    }


def generate_files(template_id: str, brief: dict) -> dict[str, str]:
    template = TEMPLATES_BY_ID.get(template_id)
    if not template:
        raise ValueError(f"Неизвестный шаблон: {template_id}")
    content = build_content(template_id, brief)
    if template["direction"] == "bot":
        return _bot_files(template, content)
    if template["direction"] == "agent":
        return _agent_files(template, content)
    return _miniapp_files(template, content)


def preview_html(project: dict, files: dict[str, str]) -> str:
    """HTML для iframe-превью мини-аппа; для бота/агента возвращает заглушку."""
    template = TEMPLATES_BY_ID.get(project["template_id"], {})
    if project.get("template_id") == "shop" and files.get("miniapp/index.html"):
        index = files["miniapp/index.html"]
        css = files.get("miniapp/styles.css", "")
        js = files.get("miniapp/app.js", "")
        index = index.replace('<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>")
        index = index.replace('<script src="app.js"></script>', f"<script>{js}</script>")
        return index
    if template.get("direction") != "miniapp":
        return "<!doctype html><meta charset='utf-8'><body style='font-family:sans-serif;padding:24px'>Превью доступно во вкладке проекта.</body>"
    index = files.get("index.html", "")
    css = files.get("styles.css", "")
    js = files.get("app.js", "")
    index = index.replace('<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>")
    index = index.replace('<script src="app.js"></script>', f"<script>{js}</script>")
    return index
