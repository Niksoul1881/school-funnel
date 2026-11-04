"""Главный бот-платформа: доступ → шаблон → бриф → токен → бот ученика."""
from __future__ import annotations

import asyncio
import html
import os
import sys
from pathlib import Path

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_practice import engine  # noqa: E402

load_dotenv(ROOT / "private" / "telegram-test.env")
PLATFORM_TOKEN = os.getenv("PLATFORM_BOT_TOKEN", "").strip()
OWNER_ID = os.getenv("OWNER_TG_ID", "").strip()
TENANTS: dict[str, dict] = {}
MY_BOTS: list[dict] = []
dp = Dispatcher()

PUBLIC = "https://school.91-184-242-178.sslip.io:8443"
COVERS = {
    "booking": f"{PUBLIC}/static/covers/booking.png",
    "ai": f"{PUBLIC}/static/covers/ai.png",
    "shop": f"{PUBLIC}/static/covers/shop.png",
}
FIELD_EMOJI = {
    "business_name": "🏷",
    "niche": "🎯",
    "services": "💅",
    "slots": "🕐",
    "address": "📍",
    "contact": "📞",
    "knowledge": "📚",
    "faq": "💬",
    "products": "🛍",
    "delivery": "🚚",
}


def progress(index: int, total: int) -> str:
    filled = "▰" * (index + 1)
    empty = "▱" * max(0, total - index - 1)
    return filled + empty


def field_prompt(template: str, index: int) -> str:
    fields = engine.TEMPLATES[template]["fields"]
    field = fields[index]
    icon = FIELD_EMOJI.get(field["key"], "✏️")
    hint = f"\n\n<i>{html.escape(field.get('hint', ''))}</i>" if field.get("hint") else ""
    skip = "\n\n<i>Можно написать /skip, если не хочешь заполнять.</i>" if not field.get("required") else ""
    return (
        f"{icon} <b>Шаг {index + 1} из {len(fields)}</b>\n"
        f"<code>{progress(index, len(fields))}</code>\n\n"
        f"<b>{html.escape(field['label'])}</b>{hint}{skip}"
    )


class Build(StatesGroup):
    template = State()
    fields = State()
    token = State()


def kb(items):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=action)] for label, action in items])


def templates_kb():
    return kb([(f"{value['icon']} {value['name']}", f"tpl:{key}") for key, value in engine.TEMPLATES.items()])


def reply_markup(message):
    buttons = message.get("buttons") or []
    return kb([(b["label"], b["action"]) for b in buttons]) if buttons else None


async def emit(bot: Bot, chat_id: int, replies: list[dict]) -> None:
    for reply in replies:
        text = reply.get("text", "")
        if reply.get("admin"):
            if OWNER_ID:
                try:
                    await bot.send_message(int(OWNER_ID), text)
                except Exception as exc:
                    print(f"owner notify error: {exc}")
            continue
        markup = reply_markup(reply)
        if reply.get("image"):
            try:
                await bot.send_photo(chat_id, reply["image"], caption=text, reply_markup=markup)
                continue
            except Exception as exc:
                print(f"photo error: {exc}")
        await bot.send_message(chat_id, text, reply_markup=markup)


def tenant_dispatcher(bot_id: str):
    tenant_dp = Dispatcher()

    @tenant_dp.message(CommandStart())
    async def start(message: Message):
        await emit(message.bot, message.chat.id, engine.message(bot_id, action="start"))

    @tenant_dp.callback_query()
    async def callback(call: CallbackQuery):
        await call.answer()
        await emit(call.message.bot, call.message.chat.id, engine.message(bot_id, action=call.data))

    @tenant_dp.message(F.text)
    async def text(message: Message):
        await emit(message.bot, message.chat.id, engine.message(bot_id, text=message.text))

    return tenant_dp


async def start_tenant(token: str, template: str, brief: dict) -> dict:
    me = await Bot(token).get_me()
    bot = Bot(token)
    bot_id = engine.create_bot(template, brief)["id"]
    task = asyncio.create_task(tenant_dispatcher(bot_id).start_polling(bot))
    TENANTS[bot_id] = {"id": bot_id, "token": token, "username": me.username, "task": task, "template": template}
    return {"id": bot_id, "username": me.username, "template": template}


async def validate(token: str) -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            data = (await client.get(f"https://api.telegram.org/bot{token}/getMe")).json()
        return (True, data["result"]["username"]) if data.get("ok") else (False, data.get("description", "ошибка"))
    except Exception as exc:
        return False, str(exc)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    if OWNER_ID and str(message.from_user.id) != OWNER_ID:
        await message.answer("Это тестовый конструктор. Доступ только у владельца.")
        return
    await message.answer(
        "✨ <b>Платформа практики</b>\n\n"
        "Урок 2 · <b>Чат-боты</b>\n\n"
        "Собери своего первого бота за 5 минут:\n"
        "шаблон → бриф → токен → запуск.\n\n"
        "Без кода. Всё кнопками.",
        parse_mode="HTML",
        reply_markup=kb([("🚀 Собрать бота", "build"), ("📦 Мои боты", "mybots")]),
    )


@dp.callback_query(F.data == "build")
async def build(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Build.template)
    await call.message.answer(
        "🎨 <b>Выбери шаблон</b>\n\n"
        "Три готовых сценария. Внутри — бриф и запуск.",
        parse_mode="HTML",
        reply_markup=templates_kb(),
    )
    await call.answer()


@dp.callback_query(F.data == "mybots")
async def mybots(call: CallbackQuery):
    if not MY_BOTS:
        await call.message.answer("📦 Пока нет ботов.\n\nНажми /start → «Собрать бота».", parse_mode="HTML")
    else:
        lines = [f"• <b>@{html.escape(b['username'])}</b> — {html.escape(engine.TEMPLATES[b['template']]['name'])}" for b in MY_BOTS]
        await call.message.answer("📦 <b>Мои боты</b>\n\n" + "\n".join(lines), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data.startswith("tpl:"))
async def choose_template(call: CallbackQuery, state: FSMContext):
    template = call.data.split(":", 1)[1]
    if template not in engine.TEMPLATES:
        await call.answer("Неизвестный шаблон", show_alert=True)
        return
    await state.update_data(template=template, index=0, brief={})
    await state.set_state(Build.fields)
    meta = engine.TEMPLATES[template]
    caption = f"{meta['icon']} <b>{html.escape(meta['name'])}</b>\n\n{html.escape(meta['tagline'])}"
    try:
        await call.message.answer_photo(COVERS[template], caption=caption, parse_mode="HTML")
    except Exception:
        await call.message.answer(caption, parse_mode="HTML")
    await call.message.answer(field_prompt(template, 0), parse_mode="HTML")
    await call.answer()


@dp.message(Build.fields)
async def fill_field(message: Message, state: FSMContext):
    data = await state.get_data()
    template = data["template"]
    index = data["index"]
    fields = engine.TEMPLATES[template]["fields"]
    brief = dict(data["brief"])
    value = (message.text or "").strip()
    if value.lower() in ("/skip", "пропустить"):
        value = engine.TEMPLATES[template]["defaults"].get(fields[index]["key"], "")
    brief[fields[index]["key"]] = value
    index += 1
    if index < len(fields):
        await state.update_data(index=index, brief=brief)
        await message.answer(field_prompt(template, index), parse_mode="HTML")
        return
    await state.update_data(brief=brief)
    await state.set_state(Build.token)
    reuse = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔁 Взять готового booking-бота", callback_data="reuse:booking")
    ]]) if template == "booking" else None
    await message.answer(
        "🔑 <b>Последний шаг</b>\n\n"
        "Пришли токен <b>нового</b> бота из @BotFather.\n\n"
        "Он выглядит так:\n"
        "<code>123456789:AA...</code>\n\n"
        "<i>Это ключ от бота — не публикуй его.</i>",
        parse_mode="HTML",
        reply_markup=reuse,
    )


@dp.callback_query(F.data == "reuse:booking")
async def reuse_booking(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data or data.get("template") != "booking":
        await call.answer("Этот вариант доступен для шаблона записи", show_alert=True)
        return
    token = os.getenv("BOOKING_BOT_TOKEN", "").strip()
    if not token:
        await call.answer("Нет тестового booking-токена", show_alert=True)
        return
    await call.message.answer("⏳ <b>Беру готового бота…</b>\n\nПересобираю его под твой бриф.", parse_mode="HTML")
    try:
        bot = await start_tenant(token, "booking", data.get("brief", {}))
    except Exception as exc:
        await call.message.answer(f"⚠️ Не получилось: <i>{html.escape(str(exc))}</i>", parse_mode="HTML")
        await call.answer()
        return
    MY_BOTS.append(bot)
    await state.clear()
    await call.message.answer(
        "🎉 <b>Бот пересобран!</b>\n\n"
        f"🤖 <b>@{html.escape(bot['username'])}</b>\n\n"
        "Открой его и нажми /start.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚀 Открыть бота", url=f"https://t.me/{bot['username']}")
        ]]),
    )
    await call.answer()


@dp.message(Build.token)
async def receive_token(message: Message, state: FSMContext):
    token = (message.text or "").strip()
    if ":" not in token:
        await message.answer("⚠️ Это не похоже на токен.\nСкопируй строку из BotFather целиком.", parse_mode="HTML")
        return
    ok, username = await validate(token)
    if not ok:
        await message.answer(f"⚠️ Telegram не принял токен:\n<i>{html.escape(username)}</i>\n\nПроверь и пришли ещё раз.", parse_mode="HTML")
        return
    data = await state.get_data()
    await message.answer("⏳ <b>Собираю бота…</b>\n\nЗапускаю сценарий и проверяю токен.", parse_mode="HTML")
    try:
        bot = await start_tenant(token, data["template"], data["brief"])
    except Exception as exc:
        await message.answer(
            f"⚠️ Не получилось запустить:\n<i>{html.escape(str(exc))}</i>\n\n"
            "Скорее всего, этот токен уже используется другим запущенным ботом.",
            parse_mode="HTML",
        )
        return
    MY_BOTS.append(bot)
    await state.clear()
    await message.answer(
        "🎉 <b>Бот собран!</b>\n\n"
        f"🤖 <b>@{html.escape(bot['username'])}</b>\n"
        f"🧩 {html.escape(engine.TEMPLATES[bot['template']]['name'])}\n\n"
        "Нажми /start в своём боте и проверь сценарий.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚀 Открыть бота", url=f"https://t.me/{bot['username']}")
        ]]),
    )


@dp.message(Command("mybots"))
async def mybots_command(message: Message):
    if not MY_BOTS:
        await message.answer("📦 Пока нет ботов.")
        return
    await message.answer("📦 <b>Мои боты</b>\n\n" + "\n".join(
        f"• <b>@{html.escape(b['username'])}</b> — {html.escape(engine.TEMPLATES[b['template']]['name'])}" for b in MY_BOTS
    ), parse_mode="HTML")


async def main() -> None:
    if not PLATFORM_TOKEN:
        raise SystemExit("PLATFORM_BOT_TOKEN не задан")
    await dp.start_polling(Bot(token=PLATFORM_TOKEN))


if __name__ == "__main__":
    asyncio.run(main())
