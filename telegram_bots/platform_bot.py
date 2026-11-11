"""Главный бот-платформа: доступ → шаблон → бриф → токен → бот ученика."""
from __future__ import annotations

import asyncio
import html
import json
import os
import sys
import uuid
from pathlib import Path

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_practice import engine  # noqa: E402

load_dotenv(ROOT / "private" / "telegram-test.env")
PLATFORM_TOKEN = os.getenv("PLATFORM_BOT_TOKEN", "").strip()
OWNER_ID = os.getenv("OWNER_TG_ID", "").strip()
TENANTS: dict[str, dict] = {}
MY_BOTS: list[dict] = []


class JsonFSMStorage(BaseStorage):
    """Small durable FSM storage: survives platform-bot restarts."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            self._data = {}

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def set_state(self, key: StorageKey, state: State | str | None = None) -> None:
        async with self._lock:
            value = getattr(state, "state", state)
            self._data.setdefault(str(key), {})["state"] = value
            self._flush()

    async def get_state(self, key: StorageKey) -> State | str | None:
        value = self._data.get(str(key), {}).get("state")
        return State(value) if value else None

    async def set_data(self, key: StorageKey, data: dict) -> None:
        async with self._lock:
            self._data.setdefault(str(key), {})["data"] = data
            self._flush()

    async def get_data(self, key: StorageKey) -> dict:
        return dict(self._data.get(str(key), {}).get("data") or {})

    async def close(self) -> None:
        self._flush()


dp = Dispatcher(storage=JsonFSMStorage(ROOT / "private" / "fsm_state.json"))

MENU_START = "🚀 Старт"
MENU_BUILD = "🛠 Собрать бота"
MENU_MY = "📦 Мои боты"
TENANTS_FILE = ROOT / "private" / "tenants.json"
STATE_FILE = ROOT / "private" / "tenant_state.json"


def load_tenants() -> list[dict]:
    try:
        return json.loads(TENANTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_tenants(items: list[dict]) -> None:
    TENANTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TENANTS_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def remember_tenant(record: dict) -> None:
    items = load_tenants()
    items = [item for item in items if item.get("username") != record.get("username")]
    items.append(record)
    save_tenants(items)


def save_engine_state() -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(engine.export_state(), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"state save failed: {exc}")


def load_engine_state() -> None:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return
    usernames = {
        bot.get("username"): bot_id
        for bot_id, bot in engine.BOTS.items()
        if bot.get("username")
    }
    engine.import_state(data, usernames)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_START), KeyboardButton(text=MENU_BUILD)],
            [KeyboardButton(text=MENU_MY)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие…",
    )

PUBLIC = "https://school.91-184-242-178.sslip.io:8443"
PLATFORM_API = os.getenv("PLATFORM_API_URL", PUBLIC).rstrip("/")
SERVICE_TOKEN = os.getenv("PLATFORM_SERVICE_TOKEN", "").strip()
COVERS = {
    "booking": f"{PUBLIC}/static/covers/booking.jpg",
    "gift": f"{PUBLIC}/static/covers/gift.jpg",
    "lead": f"{PUBLIC}/static/covers/lead.jpg",
    "ai": f"{PUBLIC}/static/covers/ai.jpg",
    "shop": f"{PUBLIC}/static/covers/shop.jpg",
}
COVER_FILES = {
    "booking": ROOT / "platform" / "static" / "covers" / "booking.jpg",
    "gift": ROOT / "platform" / "static" / "covers" / "gift.jpg",
    "lead": ROOT / "platform" / "static" / "covers" / "lead.jpg",
    "ai": ROOT / "platform" / "static" / "covers" / "ai.jpg",
    "shop": ROOT / "platform" / "static" / "covers" / "shop.jpg",
}
LESSON_COVER = ROOT / "platform" / "static" / "covers" / "lesson2.png"
EXAMPLES = {
    "business_name": "Студия «Марина»",
    "services": "Стрижка — 3 500 ₽ — 60 мин\nОкрашивание — от 7 000 ₽ — 120 мин",
    "slots": "10:00, 12:00, 14:00, 16:00, 18:00",
    "address": "Москва, ул. Примерная, 10",
    "contact": "@marina_studio",
    "knowledge": "Салон красоты. Адрес, цены, правила, что можно и нельзя.",
    "faq": "Сколько стоит стрижка?|3 500 ₽",
    "products": "Медовик | 3 200 | крем | Торты | 🍰 | https://...",
    "delivery": "Самовывоз: Москва, ул. Примерная, 10",
    "niche": "салон красоты",
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
    example = EXAMPLES.get(field["key"])
    example_html = f"\n\n<i>Пример:</i>\n<pre>{html.escape(example[:300])}</pre>" if example else ""
    skip = "\n\n<i>Можно написать /skip, если не хочешь заполнять.</i>" if not field.get("required") else ""
    return (
        f"{icon} <b>Шаг {index + 1} из {len(fields)}</b>\n"
        f"<code>{progress(index, len(fields))}</code>\n\n"
        f"<b>{html.escape(field['label'])}</b>{hint}{example_html}{skip}"
    )


async def ask_token(message: Message, state: FSMContext, template: str) -> None:
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


async def ask_next_field(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    template = data["template"]
    index = data["index"]
    fields = engine.TEMPLATES[template]["fields"]
    if index >= len(fields):
        await ask_token(message, state, template)
        return
    field = fields[index]
    if template == "shop" and field["key"] == "products":
        await state.update_data(shop_products=[])
        await state.set_state(Build.product_photo)
        await message.answer(
            "📸 <b>Фото товаров</b>\n\n"
            "Пришли фото товара — я сохраню его в веб-формате.\n"
            "Можно несколько. После каждого фото спрошу название, цену и описание.\n\n"
            "Когда закончишь — напиши «Готово».",
            parse_mode="HTML",
        )
        return
    await state.set_state(Build.fields)
    await message.answer(field_prompt(template, index), parse_mode="HTML")


class Build(StatesGroup):
    template = State()
    fields = State()
    product_photo = State()
    product_info = State()
    token = State()


UPLOADS = ROOT / "platform" / "static" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)


def kb(items):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=action)] for label, action in items])


def templates_kb():
    return kb([(f"{value['icon']} {value['name']}", f"tpl:{key}") for key, value in engine.TEMPLATES.items()])


def reply_markup(message):
    buttons = message.get("buttons") or []
    if not buttons:
        return None
    rows = []
    for button in buttons:
        label, action = button["label"], button["action"]
        if action.startswith("url:"):
            rows.append([InlineKeyboardButton(text=label, url=action[4:])])
        else:
            rows.append([InlineKeyboardButton(text=label, callback_data=action)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def notify_owner(text: str) -> bool:
    if not SERVICE_TOKEN:
        return False
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{PLATFORM_API}/api/tg/notify_owner",
                headers={"X-Service-Token": SERVICE_TOKEN},
                json={"text": text},
            )
            return response.status_code == 200
    except Exception as exc:
        print(f"owner notify api error: {exc}")
        return False


async def emit(bot: Bot, chat_id: int, replies: list[dict]) -> None:
    for reply in replies:
        text = reply.get("text", "")
        if reply.get("admin"):
            if await notify_owner(text):
                continue
            if OWNER_ID:
                try:
                    await bot.send_message(int(OWNER_ID), text)
                except Exception as exc:
                    print(f"owner notify error: {exc}")
            continue
        markup = reply_markup(reply)
        if reply.get("image"):
            image = reply["image"]
            photo = FSInputFile(ROOT / "platform" / image.lstrip("/")) if image.startswith("/static/") else image
            try:
                await bot.send_photo(chat_id, photo, caption=text, reply_markup=markup)
                continue
            except Exception as exc:
                print(f"photo error: {exc}")
        await bot.send_message(chat_id, text, reply_markup=markup)
    save_engine_state()


def tenant_menu(template: str) -> ReplyKeyboardMarkup:
    if template == "shop":
        rows = [[KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="🛒 Корзина")], [KeyboardButton(text="🚀 Старт"), KeyboardButton(text="📞 Связаться")]]
    elif template == "gift":
        rows = [[KeyboardButton(text="🚀 Старт"), KeyboardButton(text="🎁 Подарок")], [KeyboardButton(text="📣 Канал"), KeyboardButton(text="📞 Связаться")]]
    else:
        rows = [[KeyboardButton(text="🚀 Старт"), KeyboardButton(text="💅 Записаться")], [KeyboardButton(text="📞 Связаться")]]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие…",
    )


def tenant_dispatcher(bot_id: str, template: str):
    tenant_dp = Dispatcher()

    @tenant_dp.message(CommandStart())
    async def start(message: Message):
        meta = engine.TEMPLATES[template]
        try:
            await message.answer_photo(
                FSInputFile(COVER_FILES[template]),
                caption=f"{meta['icon']} <b>{html.escape(meta['name'])}</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await emit(message.bot, message.chat.id, engine.message(bot_id, action="start"))
        await message.answer("Меню бота 👇", reply_markup=tenant_menu(template))

    @tenant_dp.callback_query()
    async def callback(call: CallbackQuery):
        action = call.data
        if action == "check" and template == "gift":
            raw = (engine.BOTS.get(bot_id, {}).get("config", {}).get("brief", {}).get("channel") or "").strip()
            channel = raw.split("t.me/")[-1].strip("/") if "t.me/" in raw else raw
            if channel and not channel.startswith("@"):
                channel = "@" + channel
            if not channel:
                action = "grant"
            else:
                try:
                    member = await call.bot.get_chat_member(channel, call.from_user.id)
                    status = getattr(member, "status", "")
                    if status not in ("member", "administrator", "creator"):
                        await call.answer("Сначала подпишитесь на канал.", show_alert=True)
                        return
                    action = "grant"
                except Exception as exc:
                    await notify_owner(f"⚠️ Не смог проверить подписку у @{call.from_user.username or call.from_user.id}: {exc}")
                    action = "grant"
        await call.answer()
        await emit(call.message.bot, call.message.chat.id, engine.message(bot_id, action=action))

    @tenant_dp.message(Command("stats"))
    async def stats_cmd(message: Message):
        if OWNER_ID and message.from_user.id != OWNER_ID:
            return
        data = engine.stats(bot_id)
        await message.answer(
            "📊 <b>Статистика бота</b>\n\n"
            f"Записей: <b>{data.get('bookings', 0)}</b>\n"
            f"Заказов: <b>{data.get('orders', 0)}</b>\n"
            f"Подарков: <b>{data.get('gifts', 0)}</b>",
            parse_mode="HTML",
        )

    @tenant_dp.message(Command("orders"))
    async def orders_cmd(message: Message):
        if OWNER_ID and message.from_user.id != OWNER_ID:
            return
        rows = engine.orders(bot_id, 8)
        if not rows:
            await message.answer("📭 Заявок и заказов пока нет.")
            return
        lines = []
        for row in reversed(rows):
            if row.get("type") == "booking":
                lines.append(f"📅 {row.get('date')} {row.get('time')} · {row.get('name')} · {row.get('phone')}")
            elif row.get("type") == "order":
                lines.append(f"🛍 {row.get('order_id')} · {row.get('total')} ₽ · {row.get('name')} · {row.get('phone')}")
            else:
                lines.append(f"🎁 {row.get('gift', '')[:60]}")
        await message.answer("🧾 <b>Последние заявки</b>\n\n" + "\n".join(lines), parse_mode="HTML")

    @tenant_dp.message(F.text.in_({"🚀 Старт", "💅 Записаться", "🎁 Подарок", "🛍 Каталог", "🛒 Корзина", "📣 Канал", "📞 Связаться"}))
    async def menu_action(message: Message):
        brief = engine.BOTS.get(bot_id, {}).get("config", {}).get("brief", {})
        label = message.text
        if label in ("🚀 Старт", "💅 Записаться", "🎁 Подарок"):
            await emit(message.bot, message.chat.id, engine.message(bot_id, action="start"))
        elif label == "🛍 Каталог":
            await emit(message.bot, message.chat.id, engine.message(bot_id, action="cat:Все"))
        elif label == "🛒 Корзина":
            await emit(message.bot, message.chat.id, engine.message(bot_id, action="cart"))
        elif label == "📣 Канал":
            channel = brief.get("channel", "")
            link = channel if str(channel).startswith("http") else f"https://t.me/{str(channel).lstrip('@')}"
            await message.answer("Канал для подписки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📣 Подписаться", url=link)]]))
        elif label == "📞 Связаться":
            contact = brief.get("contact", "владелец свяжется с вами")
            await message.answer(f"📞 {contact}")
        await message.answer("Меню бота 👇", reply_markup=tenant_menu(template))

    @tenant_dp.message(F.text)
    async def text(message: Message):
        await emit(message.bot, message.chat.id, engine.message(bot_id, text=message.text))

    return tenant_dp


async def start_tenant(token: str, template: str, brief: dict, tg_id: int = 0, project: dict | None = None, persist: bool = True) -> dict:
    bot = Bot(token)
    me = await bot.get_me()
    bot_id = engine.create_bot(template, brief)["id"]
    engine.BOTS[bot_id]["username"] = me.username
    task = asyncio.create_task(tenant_dispatcher(bot_id, template).start_polling(bot))
    TENANTS[bot_id] = {"id": bot_id, "token": token, "username": me.username, "task": task, "template": template}
    if project is None and tg_id:
        project = await save_project(tg_id, template, brief, me.username)
    info = {"id": bot_id, "username": me.username, "template": template, "project": project}
    if persist:
        remember_tenant({
            "username": me.username,
            "template": template,
            "brief": brief,
            "token": token,
            "owner_tg_id": tg_id,
            "project": project,
        })
    return info


async def validate(token: str) -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            data = (await client.get(f"https://api.telegram.org/bot{token}/getMe")).json()
        return (True, data["result"]["username"]) if data.get("ok") else (False, data.get("description", "ошибка"))
    except Exception as exc:
        return False, str(exc)


async def save_project(tg_id: int, template: str, brief: dict, username: str) -> dict | None:
    if not SERVICE_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                f"{PLATFORM_API}/api/tg/create_project",
                headers={"X-Service-Token": SERVICE_TOKEN},
                json={"tg_id": str(tg_id), "template_id": template, "brief": brief, "username": username},
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        print(f"project sync error: {exc}")
        return None


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    if OWNER_ID and str(message.from_user.id) != OWNER_ID:
        await message.answer("Это тестовый конструктор. Доступ только у владельца.")
        return
    text = (
        "✨ <b>Платформа практики</b>\n\n"
        "Урок 2 · <b>Чат-боты</b>\n\n"
        "Собери своего первого бота за 5 минут:\n"
        "шаблон → бриф → токен → запуск.\n\n"
        "Без кода. Всё кнопками."
    )
    markup = main_menu()
    try:
        await message.answer_photo(FSInputFile(LESSON_COVER), caption=text, parse_mode="HTML", reply_markup=markup)
    except Exception:
        await message.answer(text, parse_mode="HTML", reply_markup=markup)


async def show_templates(message: Message) -> None:
    await message.answer(
        "🎨 <b>Выбери шаблон</b>\n\n"
        "Готовые сценарии. Внутри — бриф, запуск и проект в кабинете.",
        parse_mode="HTML",
    )
    for key, meta in engine.TEMPLATES.items():
        if key in ("ai", "lead"):
            continue
        caption = (
            f"{meta['icon']} <b>{html.escape(meta['name'])}</b>\n"
            f"<i>{html.escape(meta['tagline'])}</i>\n\n"
            "• 4–5 вопросов\n• запуск за 5 минут\n• проект сразу в кабинете"
        )
        try:
            await message.answer_photo(
                FSInputFile(COVER_FILES[key]),
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb([("Выбрать этот шаблон", f"tpl:{key}")]),
            )
        except Exception:
            await message.answer(caption, parse_mode="HTML", reply_markup=kb([("Выбрать этот шаблон", f"tpl:{key}")]))


async def show_my_bots(message: Message) -> None:
    if not MY_BOTS:
        await message.answer("📦 Пока нет ботов.\n\nНажми «🛠 Собрать бота» внизу.", parse_mode="HTML", reply_markup=main_menu())
        return
    lines = [f"• <b>@{html.escape(b['username'])}</b> — {html.escape(engine.TEMPLATES[b['template']]['name'])}" for b in MY_BOTS]
    await message.answer("📦 <b>Мои боты</b>\n\n" + "\n".join(lines), parse_mode="HTML", reply_markup=main_menu())


@dp.callback_query(F.data == "build")
async def build(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Build.template)
    await show_templates(call.message)
    await call.answer()


@dp.callback_query(F.data == "mybots")
async def mybots(call: CallbackQuery):
    await show_my_bots(call.message)
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
    await call.message.answer(
        f"{meta['icon']} <b>{html.escape(meta['name'])}</b>\n\nЗаполним бриф.",
        parse_mode="HTML",
    )
    await call.message.answer(field_prompt(template, 0), parse_mode="HTML")
    await call.answer()


@dp.message(F.text == MENU_START)
async def menu_start(message: Message, state: FSMContext):
    await start(message, state)


@dp.message(F.text == MENU_BUILD)
async def menu_build(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Build.template)
    await show_templates(message)


@dp.message(F.text == MENU_MY)
async def menu_my(message: Message):
    await show_my_bots(message)


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
    await state.update_data(index=index, brief=brief)
    await ask_next_field(message, state)


@dp.message(Build.product_photo, F.photo)
async def product_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    try:
        file = await message.bot.get_file(photo.file_id)
        name = f"{uuid.uuid4().hex}.jpg"
        await message.bot.download_file(file.file_path, destination=UPLOADS / name)
    except Exception as exc:
        await message.answer(f"⚠️ Не смог сохранить фото: {html.escape(str(exc))}", parse_mode="HTML")
        return
    await state.update_data(pending_image=f"/static/uploads/{name}")
    await state.set_state(Build.product_info)
    await message.answer(
        "✅ Фото сохранил.\n\n"
        "Теперь напиши товар в формате:\n"
        "<code>Название | Цена | Описание | Категория</code>\n\n"
        "Например:\n"
        "<code>Медовик | 3200 | медовые коржи | Торты</code>",
        parse_mode="HTML",
    )


@dp.message(Build.product_photo, F.text)
async def products_done_or_text(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    data = await state.get_data()
    products = list(data.get("shop_products", []))
    if value.lower() in ("готово", "хватит", "всё", "все", "/skip", "пропустить"):
        brief = dict(data.get("brief", {}))
        brief["products"] = "\n".join(products)
        await state.update_data(brief=brief, index=2)
        await state.set_state(Build.fields)
        await message.answer(f"🛍 Товаров: {len(products)}. Дальше — доставка.", parse_mode="HTML")
        await ask_next_field(message, state)
        return
    if "|" in value:
        products.extend(line.strip() for line in value.splitlines() if line.strip())
        data["shop_products"] = products
        await state.update_data(shop_products=products)
        await message.answer("Добавил. Пришли ещё фото или напиши «Готово».")
        return
    await message.answer("Пришли фото товара или напиши «Готово».")


@dp.message(Build.product_info, F.text)
async def product_info(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    data = await state.get_data()
    image = data.get("pending_image", "")
    parts = [p.strip() for p in value.split("|")]
    title = parts[0] if parts else "Товар"
    price = parts[1] if len(parts) > 1 else "по запросу"
    desc = parts[2] if len(parts) > 2 else ""
    category = parts[3] if len(parts) > 3 else "Другое"
    line = f"{title} | {price} | {desc} | {category} | 🛍 | {image}"
    products = list(data.get("shop_products", []))
    products.append(line)
    await state.update_data(shop_products=products, pending_image="")
    await state.set_state(Build.product_photo)
    await message.answer(
        f"✅ {html.escape(title)} добавлен.\n\n"
        "Пришли фото следующего товара или напиши «Готово».",
        parse_mode="HTML",
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
        bot = await start_tenant(token, "booking", data.get("brief", {}), call.from_user.id)
    except Exception as exc:
        await call.message.answer(f"⚠️ Не получилось: <i>{html.escape(str(exc))}</i>", parse_mode="HTML")
        await call.answer()
        return
    MY_BOTS.append(bot)
    await state.clear()
    project = bot.get("project")
    buttons = [[InlineKeyboardButton(text="🚀 Открыть бота", url=f"https://t.me/{bot['username']}")]]
    if project:
        buttons.append([InlineKeyboardButton(text="🌐 Открыть в кабинете", url=project["magic_url"])])
    text = (
        "🎉 <b>Бот пересобран!</b>\n\n"
        f"🤖 <b>@{html.escape(bot['username'])}</b>\n\n"
        + ("📁 Проект обновлён в твоём кабинете.\n\n" if project else "")
        + "Открой его и нажми /start."
    )
    try:
        await call.message.answer_photo(
            FSInputFile(COVER_FILES["booking"]),
            caption=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
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
        bot = await start_tenant(token, data["template"], data["brief"], message.from_user.id)
    except Exception as exc:
        await message.answer(
            f"⚠️ Не получилось запустить:\n<i>{html.escape(str(exc))}</i>\n\n"
            "Скорее всего, этот токен уже используется другим запущенным ботом.",
            parse_mode="HTML",
        )
        return
    MY_BOTS.append(bot)
    await state.clear()
    project = bot.get("project")
    buttons = [[InlineKeyboardButton(text="🚀 Открыть бота", url=f"https://t.me/{bot['username']}")]]
    if project:
        buttons.append([InlineKeyboardButton(text="🌐 Открыть в кабинете", url=project["magic_url"])])
    text = (
        "🎉 <b>Бот собран!</b>\n\n"
        f"🤖 <b>@{html.escape(bot['username'])}</b>\n"
        f"🧩 {html.escape(engine.TEMPLATES[bot['template']]['name'])}\n\n"
        + ("📁 Проект уже сохранён в твоём кабинете на платформе.\n\n" if project else "")
        + "Нажми /start в своём боте и проверь сценарий."
    )
    try:
        await message.answer_photo(
            FSInputFile(COVER_FILES[bot["template"]]),
            caption=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
    except Exception:
        await message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.message(Command("mybots"))
async def mybots_command(message: Message):
    if not MY_BOTS:
        await message.answer("📦 Пока нет ботов.")
        return
    await message.answer("📦 <b>Мои боты</b>\n\n" + "\n".join(
        f"• <b>@{html.escape(b['username'])}</b> — {html.escape(engine.TEMPLATES[b['template']]['name'])}" for b in MY_BOTS
    ), parse_mode="HTML")


async def restore_tenants() -> None:
    for record in load_tenants():
        try:
            info = await start_tenant(
                record["token"],
                record["template"],
                record.get("brief", {}),
                tg_id=0,
                project=record.get("project"),
                persist=False,
            )
            MY_BOTS.append(info)
            print(f"restored @{info['username']} ({info['template']})")
        except Exception as exc:
            print(f"restore failed {record.get('username')}: {exc}")


async def main() -> None:
    if not PLATFORM_TOKEN:
        raise SystemExit("PLATFORM_BOT_TOKEN не задан")
    bot = Bot(token=PLATFORM_TOKEN)
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="mybots", description="Мои боты"),
    ])
    await restore_tenants()
    load_engine_state()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


