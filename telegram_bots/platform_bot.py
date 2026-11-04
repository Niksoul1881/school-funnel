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
        "Привет! Это платформа практики.\n\n"
        "Урок 2: собери своего первого Telegram-бота.\n"
        "Выбери шаблон, ответь на 4–5 вопросов и пришли токен бота из BotFather.",
        reply_markup=kb([("🚀 Собрать бота", "build"), ("📦 Мои боты", "mybots")]),
    )


@dp.callback_query(F.data == "build")
async def build(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Build.template)
    await call.message.answer("Какого бота собираем?", reply_markup=templates_kb())
    await call.answer()


@dp.callback_query(F.data == "mybots")
async def mybots(call: CallbackQuery):
    if not MY_BOTS:
        await call.message.answer("Пока нет ботов. Нажми /start → «Собрать бота».")
    else:
        lines = [f"@{b['username']} · {engine.TEMPLATES[b['template']]['name']}" for b in MY_BOTS]
        await call.message.answer("Мои боты:\n\n" + "\n".join(lines))
    await call.answer()


@dp.callback_query(F.data.startswith("tpl:"))
async def choose_template(call: CallbackQuery, state: FSMContext):
    template = call.data.split(":", 1)[1]
    if template not in engine.TEMPLATES:
        await call.answer("Неизвестный шаблон", show_alert=True)
        return
    await state.update_data(template=template, index=0, brief={})
    await state.set_state(Build.fields)
    field = engine.TEMPLATES[template]["fields"][0]
    await call.message.answer(f"Шаблон: {engine.TEMPLATES[template]['name']}\n\n{field['label']}:")
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
        field = fields[index]
        hint = f"\n\n{hint}" if (hint := field.get("hint")) else ""
        await message.answer(f"{field['label']}:{hint}")
        return
    await state.update_data(brief=brief)
    await state.set_state(Build.token)
    await message.answer(
        "Бриф готов. Теперь пришли токен нового бота из @BotFather.\n\n"
        "Он выглядит так: 123456789:AA...\n"
        "Это ключ от бота — не публикуй его."
    )


@dp.message(Build.token)
async def receive_token(message: Message, state: FSMContext):
    token = (message.text or "").strip()
    if ":" not in token:
        await message.answer("Это не похоже на токен. Скопируй строку из BotFather целиком.")
        return
    ok, username = await validate(token)
    if not ok:
        await message.answer(f"Telegram не принял токен: {username}\nПроверь и пришли ещё раз.")
        return
    data = await state.get_data()
    await message.answer("Собираю бота… ⏳")
    try:
        bot = await start_tenant(token, data["template"], data["brief"])
    except Exception as exc:
        await message.answer(f"Не получилось запустить: {exc}")
        return
    MY_BOTS.append(bot)
    await state.clear()
    await message.answer(
        f"Готово! 🎉\n\nТвой бот: @{bot['username']}\n"
        f"Шаблон: {engine.TEMPLATES[bot['template']]['name']}\n\n"
        f"Открой: https://t.me/{bot['username']}\n"
        "Нажми /start — и проверяй сценарий."
    )


@dp.message(Command("mybots"))
async def mybots_command(message: Message):
    if not MY_BOTS:
        await message.answer("Пока нет ботов.")
        return
    await message.answer("\n".join(f"@{b['username']} · {engine.TEMPLATES[b['template']]['name']}" for b in MY_BOTS))


async def main() -> None:
    if not PLATFORM_TOKEN:
        raise SystemExit("PLATFORM_BOT_TOKEN не задан")
    await dp.start_polling(Bot(token=PLATFORM_TOKEN))


if __name__ == "__main__":
    asyncio.run(main())
