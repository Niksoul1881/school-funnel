"""Generated files for the «Запись к мастеру» bot."""
BOOKING_BOT_PY = r'''"""Запись к мастеру: услуга → дата → время → имя → телефон → заявка."""
import asyncio
import json
import os
import sqlite3
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()
CONTENT = json.loads(Path(__file__).with_name("content.json").read_text(encoding="utf-8"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "") or str(CONTENT.get("admin_chat_id", ""))
DB_PATH = Path(__file__).with_name("bookings.db")
dp = Dispatcher()
bot = None


class Booking(StatesGroup):
    service = State()
    date = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()


def services_kb():
    rows = []
    for index, service in enumerate(CONTENT["services"]):
        label = f"{service['title']} · {service['price']}"
        rows.append([InlineKeyboardButton(text=label[:64], callback_data=f"svc:{index}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def slots_kb():
    slots = CONTENT["slots"]
    rows = []
    for index in range(0, len(slots), 3):
        rows.append([InlineKeyboardButton(text=slot, callback_data=f"slot:{slot}") for slot in slots[index:index + 3]])
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="book:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="book:confirm")],
        [InlineKeyboardButton(text="Отменить", callback_data="book:cancel")],
    ])


def save_booking(data):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, service TEXT, date TEXT, time TEXT, name TEXT, phone TEXT, username TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        cur = conn.execute(
            "INSERT INTO bookings(service, date, time, name, phone, username) VALUES (?,?,?,?,?,?)",
            (data.get("service", ""), data.get("date", ""), data.get("time", ""), data.get("name", ""), data.get("phone", ""), data.get("username", "")),
        )
        return int(cur.lastrowid)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = CONTENT["greeting"]
    if CONTENT.get("address"):
        text += "\n\nАдрес: " + CONTENT["address"]
    await message.answer(text, reply_markup=services_kb())


@dp.callback_query(F.data.startswith("svc:"))
async def choose_service(call: CallbackQuery, state: FSMContext) -> None:
    service = CONTENT["services"][int(call.data.split(":", 1)[1])]
    await state.update_data(service=f"{service['title']} — {service['price']}")
    await state.set_state(Booking.date)
    await call.message.edit_text(
        f"Выбрали: {service['title']} · {service['price']} · {service['duration']}\n\nНапишите дату в формате ДД.ММ, например 12.11:"
    )
    await call.answer()


@dp.message(Booking.date)
async def choose_date(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 4:
        await message.answer("Напишите дату в формате ДД.ММ, например 12.11")
        return
    await state.update_data(date=value)
    await state.set_state(Booking.time)
    await message.answer(f"Дата: {value}. Выберите свободное время:", reply_markup=slots_kb())


@dp.callback_query(F.data.startswith("slot:"))
async def choose_time(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(time=call.data.split(":", 1)[1])
    await state.set_state(Booking.name)
    await call.message.edit_text("Как вас зовут?")
    await call.answer()


@dp.message(Booking.name)
async def choose_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Напишите имя — хотя бы 2 буквы.")
        return
    await state.update_data(name=name)
    await state.set_state(Booking.phone)
    await message.answer("Оставьте телефон для подтверждения:")


@dp.message(Booking.phone)
async def choose_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if sum(ch.isdigit() for ch in phone) < 10:
        await message.answer("Похоже, в номере не хватает цифр. Напишите телефон ещё раз.")
        return
    await state.update_data(phone=phone)
    data = await state.get_data()
    await state.set_state(Booking.confirm)
    await message.answer(
        "Проверьте заявку:\n\n"
        f"Услуга: {data.get('service')}\nДата: {data.get('date')}\nВремя: {data.get('time')}\n"
        f"Имя: {data.get('name')}\nТелефон: {data.get('phone')}",
        reply_markup=confirm_kb(),
    )


@dp.callback_query(F.data == "book:cancel")
async def cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("Хорошо, отменили. Если захотите — нажмите /start.")
    await call.answer()


@dp.callback_query(F.data == "book:confirm")
async def confirm(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    data["username"] = call.from_user.username or ""
    booking_id = save_booking(data)
    if bot and ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                int(ADMIN_CHAT_ID),
                "Новая запись\n\n"
                f"Услуга: {data.get('service')}\nДата: {data.get('date')}\nВремя: {data.get('time')}\n"
                f"Имя: {data.get('name')}\nТелефон: {data.get('phone')}\n"
                f"Telegram: @{data.get('username') or '—'}\nЗаявка #{booking_id}",
            )
        except Exception as exc:
            print(f"Не удалось отправить заявку администратору: {exc}")
    await state.clear()
    await call.message.edit_text(
        f"Готово, {data.get('name')}! Заявка #{booking_id} принята.\n"
        f"Мастер подтвердит запись по телефону {data.get('phone')}.\n\n"
        f"Связаться: {CONTENT['contact']}"
    )
    await call.answer("Заявка отправлена")


@dp.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer("Чтобы записаться, нажмите /start. Или напишите администратору: " + CONTENT["contact"])


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен.")
    global bot
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''
