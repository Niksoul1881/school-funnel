"""Главный бот-платформа: доступ → шаблон → бриф → токен → бот ученика."""
from __future__ import annotations

import asyncio
import html
import json
import re
import time
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
    ReplyKeyboardRemove,
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
TENANT_USERS: dict[str, set[int]] = {}
GIFT_FOLLOWUPS: set[tuple[str, int]] = set()
GIFT_TASKS: dict[tuple[str, int], asyncio.Task] = {}


class JsonFSMStorage(BaseStorage):
    """Small durable FSM storage: survives platform-bot restarts."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        self._timer = None
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            self._data = {}

    def _flush_now(self) -> None:
        self._timer = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _flush(self, force: bool = False) -> None:
        if force:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._flush_now()
            return
        if self._timer is None:
            self._timer = asyncio.get_running_loop().call_later(0.4, self._flush_now)

    async def set_state(self, key: StorageKey, state: State | str | None = None) -> None:
        async with self._lock:
            value = getattr(state, "state", state)
            if isinstance(value, str) and value.startswith("@:"):
                value = value[2:]
            self._data.setdefault(str(key), {})["state"] = value
            self._flush()

    async def get_state(self, key: StorageKey) -> State | str | None:
        value = self._data.get(str(key), {}).get("state")
        if isinstance(value, str) and value.startswith("@:"):
            value = value[2:]
        return State(value) if value else None

    async def set_data(self, key: StorageKey, data: dict) -> None:
        async with self._lock:
            self._data.setdefault(str(key), {})["data"] = data
            self._flush()

    async def get_data(self, key: StorageKey) -> dict:
        return dict(self._data.get(str(key), {}).get("data") or {})

    async def close(self) -> None:
        self._flush(force=True)


dp = Dispatcher(storage=JsonFSMStorage(ROOT / "private" / "fsm_state.json"))


@dp.message(CommandStart())
async def priority_start(message: Message, state: FSMContext):
    await start(message, state)


@dp.message(Command("back"))
async def priority_back(message: Message, state: FSMContext):
    await go_back(message, state)

MENU_START = "🚀 Старт"
MENU_BUILD = "🛠 Собрать бота"
MENU_MY = "📦 Мои боты"
TENANTS_FILE = ROOT / "private" / "tenants.json"
STATE_FILE = ROOT / "private" / "tenant_state.json"
TEMPLATES_COVER = ROOT / "platform" / "static" / "covers" / "templates-menu.jpg"
UI_MESSAGES: dict[int, list[int]] = {}


def remember_ui(bot: Bot, chat_id: int, sent) -> None:
    if sent is None:
        return
    UI_MESSAGES.setdefault(chat_id, []).append(sent.message_id)
    UI_MESSAGES[chat_id] = UI_MESSAGES[chat_id][-12:]


async def clear_ui(bot: Bot, chat_id: int) -> None:
    for message_id in UI_MESSAGES.pop(chat_id, []):
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            pass


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


_LAST_ENGINE_SAVE = 0.0


def save_engine_state(force: bool = False) -> None:
    global _LAST_ENGINE_SAVE
    now = time.monotonic()
    if not force and now - _LAST_ENGINE_SAVE < 1.5:
        return
    _LAST_ENGINE_SAVE = now
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(engine.export_state(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(STATE_FILE)
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
    "business_name": "Marina Beauty Space",
    "services": "Стрижка, Окрашивание, Маникюр",
    "details": "Стрижка — от 2500 ₽, 1.5 часа\nОкрашивание — от 7000 ₽, 2 часа",
    "slots": "10:00, 12:00, 14:00, 16:00, 18:00",
    "address": "Москва, ул. Примерная, 10",
    "contact": "@marina_studio",
    "knowledge": "Салон красоты. Адрес, цены, правила, что можно и нельзя.",
    "faq": "Сколько стоит стрижка?|3 500 ₽",
    "products": "Медовик | 3 200 | крем | Торты | 🍰 | https://...",
    "delivery": "Самовывоз: Москва, ул. Примерная, 10",
    "niche": "салон красоты",
}

TEMPLATE_EXAMPLES = {
    "booking": {"business_name": "Marina Beauty Space", "contact": "@marina_studio"},
    "shop": {"business_name": "Крем & Ваниль", "contact": "@krem_vanil"},
    "gift": {"business_name": "Школа AI-агентов", "channel": "https://t.me/your_channel", "contact": "https://t.me/your_curator"},
}
FIELD_EMOJI = {
    "business_name": "🏷",
    "niche": "🎯",
    "services": "💅",
    "details": "💸",
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


BUILDER_STEPS = {
    "booking": [
        ("business_name", "Название проекта"),
        ("photo", "Главное фото"),
        ("description", "Описание до старта"),
        ("greeting", "Приветствие и УТП"),
        ("services", "Наполнение услугами"),
        ("slots", "Свободные окошки"),
        ("contact", "Контакт администратора"),
        ("confirmation", "Подтверждение и адрес"),
        ("summary", "Проверка данных"),
    ],
    "gift": [
        ("business_name", "Название проекта"),
        ("photo", "Главное фото / Обложка"),
        ("description", "Описание до старта"),
        ("greeting", "Приветствие и условие подписки"),
        ("channel", "Канал для проверки подписки"),
        ("timer2h", "Догонялка №1 (2 часа)"),
        ("gift", "Выдача подарка и CTA"),
        ("timer24h", "Догонялка №2 (24 часа)"),
        ("contact", "Контакт для связи"),
        ("summary", "Проверка данных"),
    ],
    "shop": [
        ("business_name", "Название магазина"),
        ("photo", "Главное фото витрины"),
        ("description", "Описание до старта"),
        ("greeting", "Приветствие на витрине"),
        ("products", "Наполнение витрины товарами"),
        ("contact", "Контакт менеджера"),
        ("summary", "Проверка данных"),
    ],
}


def builder_fields(template: str) -> list[dict]:
    if template in BUILDER_STEPS:
        return [{"key": key, "label": label, "type": "text"} for key, label in BUILDER_STEPS[template]]
    return engine.TEMPLATES[template]["fields"]


BUILDER_SECTIONS = {
    "booking": ["Название проекта", "Визуальное оформление", "Описание до старта", "Приветствие и УТП", "Наполнение услугами", "Свободные окошки", "Контакт администратора", "Подтверждение и адрес", "Сводка и Предпросмотр"],
    "gift": ["Название проекта или школы", "Визуальное оформление (Обложка)", "Описание до старта (Description)", "Приветствие и условие подписки", "Канал для проверки подписки", "Таймер №1 — Дожим до подписки", "Выдача подарка и призыв к действию", "Таймер №2 — Контрольное касание", "Контакт для связи", "Сводка и Предпросмотр"],
    "shop": ["Название магазина или бренда", "Главное фото витрины", "Описание до старта (Description)", "Приветствие на витрине", "Наполнение витрины товарами", "Контакт менеджера / продавца", "Сводка и Предпросмотр"],
}

BUILDER_PROMPTS = {
    "timer2h": "Пришли текст сообщения, которое бот отправит через 2 часа тем, кто не подписался.",
    "timer24h": "Пришли текст сообщения, которое бот отправит через 24 часа после выдачи подарка.",
    "channel": "Пришли ссылку на Telegram-канал (t.me/... или @username). Бот должен быть админом канала.",
    "description": "Пришли текст, который клиент увидит до нажатия «Старт».",
    "greeting": "Пришли приветствие и УТП, которое клиент увидит после /start.",
    "confirmation": "Пришли текст подтверждения записи и адрес студии.",
    "photo": "Пришли главное фото бота.",
    "summary": "Проверь данные и опубликуй бота.",
}

BEAUTY_PROMPTS = {
    "business_name": "Придумай красивое название для своего проекта (студии или кабинета) и отправь его мне в чат.\n\n👉 Пример: Marina Beauty Space или Кабинет массажа «Релакс»\n\n🎓 Совет профи: В реальной работе ты берешь название из брифа заказчика. А сейчас можешь просто использовать готовый шаблон.",
    "photo": "📸 Коммерция без визуала не работает! Пришли мне красивую фотографию интерьера, логотип или фото мастера, которая будет встречать клиентов в главном меню бота.\n\n🎓 Совет профи: Если фото нет под рукой, жми «Оставить шаблон» — я подставлю нейтральную базовую картинку. Идеального универсального фото не существует (для бьюти-студии это интерьер, для барбершопа — кресло), поэтому в коммерческих проектах мы всегда берем визуал строго у заказчика.",
    "description": "Что увидит клиент до того, как нажмет кнопку «Старт» в твоем боте? Скопируй шаблон ниже, заполни данные в скобках и отправь мне:\n\n📝 Шаблон для копирования:\nДобро пожаловать в пространство красоты «[название из шага 1]» ✨\nЭто место, где стиль встречается с заботой, а вы отдыхаете, пока мы подчеркиваем вашу индивидуальность.\nЗдесь вы можете посмотреть прайс, познакомиться с услугами и выбрать удобное окошко к нашим мастерам в пару кликов.\nЖмите «СТАРТ» (или /start) внизу экрана, чтобы начать! 👇\n\n🎓 Совет профи: В реальной работе тебе не придется придумывать этот текст самому. Заказчик просто пришлет готовое описание, а твоя задача — скопировать его и вставить в нужную настройку, чтобы текст красиво висел над кнопкой «Старт».",
    "greeting": "Приветствие и УТП. Бот должен продавать с первых секунд. Скопируй шаблон ниже, заполни его своими данными и отправь мне:\n\n📝 Шаблон для копирования:\nРады видеть вас в [Название из шага 1]! 🤍\n\nПочему выбирают именно нас:\n1. [Напиши причину 1. Например: Делаем услуги в 4 руки]\n2. [Напиши причину 2. Например: 100% стерильные инструменты]\n\nВыберите, чем мы можем порадовать вас сегодня:\n\n🎓 Совет профи: Тебе не нужно самому придумывать, почему этот салон лучший. Заказчик сам пришлет этот текст. Твоя задача — просто красиво его оформить: разбить на удобные абзацы и добавить пару смайликов, чтобы клиентам было приятно и легко читать.",
    "services": "📋 Теперь самое интересное — добавляем услуги! Будем собирать их как настоящий конструктор, заполняя поля по очереди. Нажми «Добавить услугу», и мы шаг за шагом впишем название, цену и описание.",
    "slots": "Свободные окошки.\n🗓 Клиенту нужно выбрать время визита. Напиши в чат 2–3 свободных времени для записи через запятую.\n\n👉 Пример: 12:00, 15:30, 19:00\n\n🎓 Совет профи: В настоящих заказах тебе не придется вписывать время руками. Мы настраиваем бота так, чтобы он сам автоматически брал актуальные окошки из электронного календаря салона. А пока для тренировки просто напишем их текстом.",
    "contact": "Контакт для связи.\n👤 Кому написать клиенту, если возникнет сложный вопрос или он захочет перенести запись? Отправь Telegram-юзернейм (обязательно с символом @).\n\n👉 Пример: @твой_никнейм\n\n🎓 Совет профи: Боты решают 90% задач, но иногда клиенту нужно поговорить с живым человеком. В настоящих проектах сюда вставляется ник реального администратора салона. А пока напиши свой юзернейм, чтобы проверить, как это работает!",
    "confirmation": "Подтверждение записи.\n📍 Клиент выбрал время и оставил телефон. Нужно подтвердить бронь и дать адрес студии. Скопируй шаблон, впиши свой адрес и отправь мне (переменные {Дата} и {Время} не трогай):\n\n📝 Шаблон для копирования:\nЗапись подтверждена! 🎉\nЖдем вас {Дата} в {Время} в «Marina Beauty Space».\n📍 Адрес: Москва, ул. Великих достижений, д. 1, кв. 1\nДо встречи! 🤍\n\n🎓 Совет профи: В настоящих коммерческих заказах мы всегда добавляем в это сообщение прямую ссылку на Яндекс.Карты или видео «как нас найти». Это невероятно повышает лояльность.",
}

SHOP_PROMPTS = {
    "business_name": "Придумай название для своего магазина или мастерской и отправь его мне в чат.\n\n👉 Пример: Студия цветов «Пион» или Мастерская кожи Craft\n\n🎓 Совет профи: Локальный бизнес массово уходит в Telegram, потому что маркетплейсы забирают до 30–40% комиссии. Поэтому такие боты-магазины — одна из самых денежных ниш для техспеца, клиенты здесь всегда с бюджетом.",
    "photo": "📸 В товарном бизнесе люди покупают глазами! Пришли мне одну общую красивую фотографию (логотип, фото ассортимента или хита продаж), которая будет встречать покупателей в главном меню бота.\n\n🎓 Совет профи: Одно сочное фото на старте повышает кликабельность кнопок каталога почти в полтора раза. Если у заказчика нет красивой общей картинки, ты всегда можешь сгенерировать стильный баннер в нейросети за пару минут.",
    "description": "Шаг 3 из 7: Описание до старта. Что увидит покупатель в пустом окне бота до того, как нажмет кнопку «Старт»? Скопируй шаблон ниже, заполни данные в скобках и отправь мне:\n\n📝 Шаблон для копирования:\nДобро пожаловать в [Название из шага 1] ✨\n[Коротко о главном преимуществе: например, создаем авторские букеты из свежих цветов с доставкой за 60 минут].\nЗдесь можно посмотреть актуальную витрину, собрать свой заказ в корзину и оформить заказ за пару кликов.\nЖмите «СТАРТ» внизу экрана, чтобы открыть меню 👇\n\n🎓 Совет профи: Большинство новичков оставляют этот экран пустым, из-за чего бот выглядит сырым. Когда ты аккуратно заполняешь описание до старта, заказчик сразу видит уровень профи и без вопросов платит высокий чек.",
    "greeting": "💬 Покупатель нажал «Старт»! Теперь нужно поприветствовать его и подвести к выбору товаров. Скопируй шаблон ниже, адаптируй под свой проект и отправь мне:\n\n📝 Шаблон для копирования:\nПривет! 👋 Рады видеть вас в [Название из шага 1].\n[1–2 предложения о качестве или фишке вашего продукта].\nВыберите позицию ниже, чтобы посмотреть фото, состав и добавить товар в корзину 👇\n\n🎓 Совет профи: Не пиши длинных простыней на старте. Человек пришел выбирать глазами, поэтому приветствие должно занимать 3–4 строчки, чтобы кнопки с товарами сразу помещались на экране телефона.",
    "products": "🧁 Теперь самое интересное — собираем каталог! Чтобы витрина выглядела аккуратно и не перегружала покупателя, оптимально добавить 3–4 ключевых товара.\n\nНажми «Добавить товар», и мы шаг за шагом заполним карточку (фото, название, цену и описание), или выбери готовый шаблон.\n\n🎓 Совет профи: Вся логика корзины — кнопки «➕ В корзину», сквозная кнопка «🛒 Перейти к оформлению», проверка на пустую корзину и автоматический подсчет суммы — уже зашита под капотом. Тебе нужно только загрузить сами товары!",
    "contact": "👤 Финальный штрих! Куда бот будет отправлять оформленные заказы и куда попадёт клиент, если нажмет кнопку «💬 Задать вопрос» в главном меню? Отправь мне Telegram-юзернейм (обязательно с символом @).\n\n👉 Пример: @твой_никнейм\n\n🎓 Совет профи: В коммерческих магазинах скорость ответа решает всё. Как только клиент заполнит корзину и оставит телефон, бот мгновенно перешлет всю сводку заказа прямо в личку менеджеру или владельцу бизнеса.",
}

GIFT_PROMPTS = {
    "business_name": "Придумай название для своей онлайн-школы, блога или авторского проекта и отправь его мне в чат.\n\n👉 Пример: Академия дизайна или Блог Алексея о маркетинге\n\n🎓 Совет профи: Тебе не придется сидеть и ломать голову над неймингом. В реальных заказах название школы или блога клиент просто скидывает в брифе — ты копируешь его за 5 секунд и идешь дальше.",
    "photo": "📸 Люди любят глазами! Пришли мне красивую картинку, которая будет встречать подписчиков сразу после нажатия кнопки «Старт». Это может быть обложка твоего гайда, логотип школы или фото эксперта.\n\n🎓 Совет профи: Если у клиента нет готовой картинки, не нужно учить Фотошоп и ждать дизайнера. Генеришь сочную обложку в нейросети за пару минут, кидаешь заголовок сверху — и заказчик в восторге от твоей скорости.",
    "description": "Шаг 3 из 10: Описание до старта. Что увидит человек до того, как нажмет кнопку «Старт» в твоем боте? Скопируй шаблон ниже, заполни данные в скобках и отправь мне:\n\n📝 Шаблон для копирования:\n🛠️ Бесплатный [гайд / чек-лист / мини-курс] от [Название из шага 1].\nВнутри — пошаговая система, которая поможет тебе [Главный результат, например: привлекать клиентов без бюджета на рекламу].\nНикакой воды и спама — только практика.\nЖми «СТАРТ» внизу экрана, чтобы забрать материал 👇\n\n🎓 Совет профи: Многие новички на фрилансе оставляют это окно пустым, и бот выглядит «голым». Когда ты красиво оформляешь экран еще до нажатия «Старт», клиент сразу видит уровень профи — и охотнее платит высокий чек.",
    "greeting": "💬 Человек запустил бота! Теперь нужно поприветствовать его и озвучить простое условие: подписка в обмен на подарок. Скопируй шаблон ниже, заполни его своими данными и отправь мне:\n\n📝 Шаблон для копирования:\nПривет! 👋 Рад видеть тебя.\nМы подготовили для тебя [Название подарка, например: пошаговый чек-лист по запуску продаж]. Внутри — концентрат практики, который можно внедрить уже сегодня.\nЧтобы забрать материал, выполни одно простое условие: подпишись на наш авторский канал [Название из шага 1] 👇, возвращайся сюда и жми кнопку «Я подписался».\n\n🎓 Совет профи: Раньше эксперты проверяли подписки вручную или теряли половину людей на неудобных ссылках. Настрой эту связку один раз за 5 минут — и дальше бот годами работает без выходных.",
    "channel": "🔗 Куда бот будет отправлять людей и где он будет проверять подписку? Пришли мне ссылку на Telegram-канал (в формате t.me/... или @username).\n\n👉 Пример: @my_expert_channel\n\n🎓 Совет профи: Чтобы бот мог проверять подписку, после создания добавь его в администраторы канала. Это делается в два клика, но именно за знание таких деталей бизнес и платит деньги.",
    "timer2h": "⏳ Человек нажал «Старт», увидел условие подписки, но отвлекся и не забрал подарок. Чтобы не терять таких людей, ставим таймер на 2 часа. Скопируй шаблон, адаптируй под свой подарок и отправь мне:\n\n📝 Шаблон для копирования:\nПривет! ✌️ Вижу, ты запустил бота, но так и не забрал свой [название подарка] 🎁\nВозможно, отвлекли дела или возникли трудности с подпиской. Просто подпишись на канал по кнопке ниже и нажми «Проверить подписку» — материал сразу появится здесь!\n\n🎓 Совет профи: Обычный бот молчит, а твой возвращает до 30% людей, которые отвлеклись.",
    "gift": "🎁 Система проверила подписку — всё супер! Теперь бот отдаёт подарок и переводит подписчика на следующий шаг. Скопируй шаблон, вставь ссылку на свой подарок и отправь мне:\n\n📝 Шаблон для копирования:\nПроверка пройдена! ✅ Добро пожаловать в комьюнити.\nДержи прямой доступ к материалу: 👉 [Вставь ссылку на подарок]\n💡 Маленький совет: начни изучение с самого главного блока — там зашита основа результата.\nИ еще кое-что. Если хочешь внедрить эти инструменты под свою ситуацию без ошибок — приходи на стратегический разбор. Жми кнопку ниже, чтобы занять место 👇\n\n🎓 Совет профи: Крутой спец сразу ведёт человека на консультацию или продажу.",
    "timer24h": "⏰ Прошли ровно сутки с момента, как человек забрал подарок. Настраиваем второе касание. Скопируй шаблон и отправь мне:\n\n📝 Шаблон для копирования:\nПривет! ✌️ Вчера бот отправил тебе [название подарка].\nУдалось посмотреть? Что оказалось самым полезным? Буду рад обратной связи — можно написать прямо сюда, мне правда интересно, как всё прошло.\nP.S. На этой неделе появилось 2 свободных окна на личный разбор. Если хочешь разобрать твою ситуацию — жми кнопку ниже, пока места еще есть 👇\n\n🎓 Совет профи: 1000 человек получат личное сообщение автоматически, пока ты спишь.",
    "contact": "👤 Финальный штрих! Куда попадёт клиент, когда нажмёт кнопки «Записаться на разбор» или «Задать вопрос»? Отправь Telegram-юзернейм (обязательно с символом @).\n\n👉 Пример: @твой_никнейм\n\n🎓 Совет профи: В реальных заказах сюда ставится аккаунт менеджера или эксперта.",
}


def field_prompt(template: str, index: int) -> str:
    fields = builder_fields(template)
    field = fields[index]
    icon = FIELD_EMOJI.get(field["key"], "✏️")
    hint = f"\n\n<i>{html.escape(field.get('hint', ''))}</i>" if field.get("hint") else ""
    example = (TEMPLATE_EXAMPLES.get(template, {}).get(field["key"]) or EXAMPLES.get(field["key"])) if not field.get("prompt") else None
    example_html = f"\n\n<i>Пример:</i>\n<pre>{html.escape(example[:300])}</pre>" if example else ""
    skip = "\n\n<i>Можно написать /skip, если не хочешь заполнять.</i>" if not field.get("required") else ""
    tip = f"\n\n🎓 <b>Совет профи:</b> {html.escape(field['tip'])}" if field.get("tip") else ""
    body = f"\n{html.escape(field['prompt'])}" if field.get("prompt") else f"\n{html.escape((GIFT_PROMPTS.get(field['key']) if template == 'gift' else SHOP_PROMPTS.get(field['key']) if template == 'shop' else BEAUTY_PROMPTS.get(field['key']) if template == 'booking' else None) or BUILDER_PROMPTS.get(field['key'], ''))}"
    sections = BUILDER_SECTIONS.get(template, [field["label"]] * len(fields))
    section = f"Шаг {index + 1}: {sections[index]}\n"
    return (
        f"{section}{icon} <b>Шаг {index + 1} из {len(fields)}</b>\n"
        f"<code>{progress(index, len(fields))}</code>\n\n"
        f"<b>{html.escape(field['label'])}</b>{body}{hint}{example_html}{skip}{tip}"
    )


async def ask_token(message: Message, state: FSMContext, template: str) -> None:
    await state.set_state(Build.token)
    await clear_ui(message.bot, message.chat.id)
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🤖 Открыть BotFather", url="https://t.me/BotFather")
    ]])
    sent = await message.answer(
        "🎉 <b>Супер! Вся информация собрана, начинка для бота готова.</b>\n\n"
        "Остался последний, самый важный шаг — нужно «поселить» твоего бота в Telegram. "
        "Для этого нам понадобится API-ключ.\n\n"
        "Вот как его получить за 1 минуту:\n"
        "1️⃣ Перейди в официального бота @BotFather.\n"
        "2️⃣ Нажми Меню и выбери команду /newbot (создать нового бота).\n"
        "3️⃣ Придумай Имя (оно будет отображаться в поиске) и Юзернейм "
        "(обязательно на английском и заканчивается на <code>bot</code>, например: <code>my_beauty_bot</code>).\n"
        "4️⃣ BotFather пришлёт тебе длинный код (API Token). Просто скопируй его и вставь на нашей платформе!\n\n"
        + ("⚠️ <b>ВАЖНО ДЛЯ ПРОВЕРКИ ПОДПИСКИ:</b> после создания бота зайди в свой Telegram-канал → Управление каналом → Администраторы → и добавь нового бота в админы. Иначе он не сможет проверять подписку!\n\n" if template == "gift" else "")
        + "📹 Посмотри короткое видео-инструкцию в уроке 1, если запутался.\n\n"
        "<i>Это ключ от бота — не публикуй его.</i>",
        parse_mode="HTML",
        reply_markup=markup,
    )
    remember_ui(message.bot, message.chat.id, sent)


async def go_back(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data or "template" not in data:
        await message.answer("Сначала выбери шаблон.")
        return
    current = await state.get_state()
    product_back = {
        Build.product_title.state: Build.product_photo,
        Build.product_price.state: Build.product_title,
        Build.product_desc.state: Build.product_price,
        Build.product_category.state: Build.product_desc,
    }
    if current in product_back:
        await state.set_state(product_back[current])
        await message.answer("Вернулся на шаг назад. Напиши значение ещё раз.")
        return
    index = int(data.get("index", 0))
    if index <= 0:
        await message.answer("Это первый шаг, назад некуда.")
        return
    await state.update_data(index=index - 1)
    await state.set_state(Build.fields)
    await message.answer("Вернулся на шаг назад.")
    await ask_next_field(message, state)


async def show_summary(message: Message, state: FSMContext, template: str) -> None:
    data = await state.get_data()
    brief = data.get("brief", {})
    lines = [f"🏢 Проект: {brief.get('business_name', '—')}"]
    if "photo" in brief:
        lines.append(f"🖼 Фото: {'загружено' if brief.get('photo') else 'шаблон'}")
    if template == "booking":
        lines += [
            f"📋 Услуг: {len(brief.get('services', '').split(',')) if brief.get('services') else 0}",
            f"🗓 Окошки: {brief.get('slots', '—')}",
            f"👤 Админ: {brief.get('contact', '—')}",
            f"📍 Адрес: {brief.get('confirmation', '—')}",
        ]
    elif template == "gift":
        lines += [
            f"🔗 Канал: {brief.get('channel', '—')}",
            f"🎁 Подарок: {brief.get('gift', '—')}",
            f"👤 Контакт: {brief.get('contact', '—')}",
        ]
    else:
        lines += [
            f"🧁 Товаров: {len(data.get('shop_products', []))}",
            f"👤 Контакт: {brief.get('contact', '—')}",
        ]
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё супер, публикуем!", callback_data="summary:publish")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="summary:edit")],
    ])
    sent = await message.answer(
        "🔍 <b>Проверка данных</b>\n\n" + "\n".join(lines) + "\n\nВсё верно?",
        parse_mode="HTML",
        reply_markup=markup,
    )
    remember_ui(message.bot, message.chat.id, sent)


async def ask_next_field(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    template = data["template"]
    index = data["index"]
    fields = builder_fields(template)
    await clear_ui(message.bot, message.chat.id)
    if index >= len(fields):
        await ask_token(message, state, template)
        return
    field = fields[index]
    if field["key"] == "services":
        await state.set_state(Build.services_menu)
        sent = await message.answer(
            field_prompt("booking", index),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить услугу", callback_data="service:add")],
                [InlineKeyboardButton(text="🪄 Оставить готовый шаблон (Добавит 4 услуги автоматически)", callback_data="service:skip")],
            ]),
        )
        remember_ui(message.bot, message.chat.id, sent)
        return
    if field["key"] == "photo":
        await state.set_state(Build.photo)
        sent = await message.answer(
            field_prompt(template, index),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🪄 Оставить шаблонное фото", callback_data="field:skip_photo"),
            ]]),
        )
        remember_ui(message.bot, message.chat.id, sent)
        return
    if field["key"] == "summary":
        await state.set_state(Build.summary)
        await show_summary(message, state, template)
        return
    if template == "shop" and field["key"] == "products":
        await state.set_state(Build.fields)
        sent = await message.answer(
            SHOP_PROMPTS["products"],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить товар", callback_data="shop:custom")],
                [InlineKeyboardButton(text="🪄 Оставить готовый шаблон", callback_data="shop:preset")],
            ]),
        )
        remember_ui(message.bot, message.chat.id, sent)
        return
    await state.set_state(Build.fields)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪄 Оставить готовый шаблон", callback_data="field:skip")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="field:back")],
    ])
    sent = await message.answer(field_prompt(template, index), parse_mode="HTML", reply_markup=markup)
    remember_ui(message.bot, message.chat.id, sent)


class Build(StatesGroup):
    template = State()
    fields = State()
    photo = State()
    summary = State()
    service_name = State()
    service_price = State()
    service_desc = State()
    services_menu = State()
    product_photo = State()
    product_batch = State()
    product_title = State()
    product_price = State()
    product_desc = State()
    product_category = State()
    product_info = State()
    token = State()


UPLOADS = ROOT / "platform" / "static" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
BATCH_TASKS: dict[int, asyncio.Task] = {}


@dp.message(Build.photo, F.photo)
async def builder_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    try:
        file = await asyncio.wait_for(message.bot.get_file(photo.file_id), timeout=15)
        name = f"{uuid.uuid4().hex}.jpg"
        await asyncio.wait_for(message.bot.download_file(file.file_path, destination=UPLOADS / name), timeout=35)
    except Exception as exc:
        await message.answer(f"⚠️ Не смог сохранить фото: {html.escape(str(exc))}", parse_mode="HTML")
        return
    data = await state.get_data()
    brief = dict(data.get("brief", {}))
    brief["photo"] = f"/static/uploads/{name}"
    index = len(builder_fields(data["template"])) - 1 if data.get("editing") else int(data.get("index", 0)) + 1
    await state.update_data(brief=brief, index=index, editing=False)
    await message.answer("✅ Фото сохранил.")
    await ask_next_field(message, state)


@dp.callback_query(F.data == "service:cancel")
async def service_cancel(call: CallbackQuery, state: FSMContext):
    await state.set_state(Build.services_menu)
    await call.message.answer(
        "Добавление отменено. Что делаем дальше?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить услугу", callback_data="service:add")],
            [InlineKeyboardButton(text="🪄 Оставить готовый шаблон", callback_data="service:skip")],
        ]),
    )
    await call.answer()


@dp.callback_query(F.data == "service:add")
async def service_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(Build.service_name)
    await call.message.answer("👇 Поле 1: Название услуги. Напиши, как будет называться услуга (этот текст появится на кнопке, поэтому пиши коротко, до 3 слов).\n👉 Пример: Ламинирование ресниц", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить добавление", callback_data="service:cancel")]]))
    await call.answer()


@dp.message(Build.service_name, F.text)
async def service_name(message: Message, state: FSMContext):
    await state.update_data(service_name=message.text.strip()[:60])
    await state.set_state(Build.service_price)
    await message.answer("👇 Поле 2: Стоимость. Отлично. Название сохранили. Теперь напиши стоимость этой услуги.\n👉 Пример: от 2000 ₽", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить добавление", callback_data="service:cancel")]]))


@dp.message(Build.service_price, F.text)
async def service_price(message: Message, state: FSMContext):
    await state.update_data(service_price=message.text.strip()[:40])
    await state.set_state(Build.service_desc)
    await message.answer("👇 Поле 3: Описание. И финальный штрих! Напиши краткое описание: в чем суть процедуры и сколько она длится.\n👉 Пример: Эффект распахнутого взгляда на 1.5 месяца. Занимает 1 час.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить добавление", callback_data="service:cancel")]]))


@dp.message(Build.service_desc, F.text)
async def service_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    items = list(data.get("services_items", []))
    items.append({
        "title": data.get("service_name", "Услуга"),
        "price": data.get("service_price", ""),
        "description": message.text.strip()[:300],
    })
    await state.update_data(services_items=items)
    await state.set_state(Build.services_menu)
    await message.answer(
        f"✅ Услуга «{items[-1]['title']}» добавлена. Всего: {len(items)}.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить еще услугу", callback_data="service:add")],
            [InlineKeyboardButton(text="➡️ Сохранить и идти дальше", callback_data="service:done")],
        ]),
    )


@dp.callback_query(F.data == "service:done")
async def service_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = list(data.get("services_items", []))
    brief = dict(data.get("brief", {}))
    brief["services"] = ", ".join(item["title"] for item in items)
    brief["details"] = "\n".join(f"{item['title']} — {item['price']}. {item['description']}" for item in items)
    index = len(builder_fields(data["template"])) - 1 if data.get("editing") else int(data.get("index", 0)) + 1
    await state.update_data(brief=brief, index=index, editing=False)
    await call.answer("Услуги сохранены")
    await ask_next_field(call.message, state)


@dp.callback_query(F.data == "service:skip")
async def service_skip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    brief = dict(data.get("brief", {}))
    brief["services"] = "Стрижка и укладка, Маникюр, SMART-педикюр, Окрашивание"
    brief["details"] = "Стрижка и укладка — от 2 500 ₽\nМаникюр — от 2 000 ₽\nSMART-педикюр — от 2 800 ₽\nОкрашивание — от 6 000 ₽"
    index = len(builder_fields(data["template"])) - 1 if data.get("editing") else int(data.get("index", 0)) + 1
    await state.update_data(brief=brief, index=index, editing=False)
    await call.answer("Добавил 4 услуги")
    await ask_next_field(call.message, state)



@dp.callback_query(F.data == "field:skip_photo")
async def skip_photo(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    brief = dict(data.get("brief", {}))
    brief["photo"] = ""
    index = len(builder_fields(data["template"])) - 1 if data.get("editing") else int(data.get("index", 0)) + 1
    await state.update_data(brief=brief, index=index, editing=False)
    await call.answer("Оставил шаблонное фото")
    await ask_next_field(call.message, state)


@dp.callback_query(F.data == "summary:publish")
async def summary_publish(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    await ask_token(call.message, state, data["template"])


@dp.callback_query(F.data == "summary:edit")
async def summary_edit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    template = data["template"]
    fields = builder_fields(template)
    rows = [
        [InlineKeyboardButton(text=field["label"], callback_data=f"edit:{i}")]
        for i, field in enumerate(fields)
        if field["key"] != "summary"
    ]
    await call.message.answer(
        "⚙️ Что именно нужно исправить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await call.answer()


@dp.callback_query(F.data.startswith("edit:"))
async def edit_step(call: CallbackQuery, state: FSMContext):
    index = int(call.data.split(":", 1)[1])
    await state.update_data(index=index, editing=True)
    await call.answer("Открываю шаг")
    await ask_next_field(call.message, state)


def _card_line(line: str, image: str) -> str:
    if "|" in line:
        parts = [part.strip() for part in line.split("|")]
    else:
        words = line.split()
        price_at = next((i for i, word in enumerate(words) if re.search(r"\d", word)), None)
        if price_at is None:
            parts = [line, "по запросу"]
        else:
            parts = [
                " ".join(words[:price_at]) or "Товар",
                words[price_at],
                " ".join(words[price_at + 1:]),
            ]
    title = parts[0] if parts and parts[0] else "Товар"
    price = parts[1] if len(parts) > 1 and parts[1] else "по запросу"
    price = re.sub(r"(?i)(руб\.?|р\.?|₽)$", "", price).strip() or price
    if price.isdigit():
        price = f"{int(price):,}".replace(",", " ") + " ₽"
    desc = parts[2] if len(parts) > 2 else ""
    category = parts[3] if len(parts) > 3 and parts[3] else "Другое"
    if category == "Другое":
        lowered = title.lower()
        if any(word in lowered for word in ("торт", "медов", "бархат", "чизкейк")):
            category = "Торты"
        elif any(word in lowered for word in ("макарон", "десерт", "пирож", "эклер", "капкейк")):
            category = "Десерты"
    emoji = parts[4].strip() if len(parts) > 4 and parts[4].strip() else ""
    if not emoji:
        emoji = {
            "Торты": "🍰", "Десерты": "🍬", "Напитки": "☕",
            "Цветы": "🌸", "Подарки": "🎁", "Выпечка": "🥐",
        }.get(category, "🛍")
    return f"{title} | {price} | {desc} | {category} | {emoji} | {image}"


def _schedule_batch(bot: Bot, chat_id: int, state: FSMContext) -> None:
    old = BATCH_TASKS.get(chat_id)
    if old and not old.done():
        old.cancel()

    async def worker():
        await asyncio.sleep(1.5)
        data = await state.get_data()
        images = list(data.get("batch_images", []))
        if not images:
            return
        caption = (data.get("batch_caption") or "").strip()
        lines = [line.strip() for line in caption.splitlines() if line.strip()]
        if len(lines) == len(images) and len(images) > 1:
            products = list(data.get("shop_products", []))
            products.extend(_card_line(line, image) for line, image in zip(lines, images))
            await state.update_data(shop_products=products, batch_images=[], batch_caption="", batch_group="")
            await state.set_state(Build.product_photo)
            await bot.send_message(chat_id, f"✅ Добавил {len(images)} товаров из подписи к пачке.")
            return
        await state.set_state(Build.product_batch)
        await bot.send_message(
            chat_id,
            f"📦 Принял {len(images)} фото.\n\n"
            "Пришли карточки одним сообщением, по одной на строку:\n"
            "<code>Название | Цена | Описание | Категория</code>\n\n"
            "Строки сопоставлю с фото по порядку.",
            parse_mode="HTML",
        )

    BATCH_TASKS[chat_id] = asyncio.create_task(worker())





def kb(items):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=action)] for label, action in items])


def templates_kb():
    return kb([(f"{value['icon']} {value['name']}", f"tpl:{key}") for key, value in engine.TEMPLATES.items()])


def reply_markup(message):
    if message.get("contact_request"):
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить мой номер телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    if message.get("remove_keyboard"):
        return ReplyKeyboardRemove()
    rows = []
    for row in message.get("button_rows") or []:
        line = []
        for button in row:
            label, action = button["label"], button["action"]
            line.append(InlineKeyboardButton(text=label, url=action[4:]) if action.startswith("url:") else InlineKeyboardButton(text=label, callback_data=action))
        if line:
            rows.append(line)
    if rows:
        return InlineKeyboardMarkup(inline_keyboard=rows)
    buttons = message.get("buttons") or []
    if not buttons:
        return None
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


async def send_platform_notify(tg_id: int, text: str) -> bool:
    if not PLATFORM_TOKEN:
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{PLATFORM_TOKEN}/sendMessage",
                json={"chat_id": tg_id, "text": text},
            )
        return response.status_code == 200
    except Exception as exc:
        print(f"platform notify error {tg_id}: {exc}")
        return False


async def emit(bot: Bot, chat_id: int, replies: list[dict], admin_chat_id: int = 0) -> None:
    for reply in replies:
        text = reply.get("text", "")
        if reply.get("admin"):
            targets = {int(OWNER_ID)} if OWNER_ID.isdigit() else set()
            if admin_chat_id:
                targets.add(int(admin_chat_id))
            for target in targets:
                if await send_platform_notify(target, text):
                    continue
                try:
                    await bot.send_message(target, text)
                except Exception as exc:
                    print(f"owner notify error {target}: {exc}")
            continue
        markup = reply_markup(reply)
        if reply.get("image"):
            image = reply["image"]
            photo = FSInputFile(ROOT / "platform" / image.lstrip("/")) if image.startswith("/static/") else image
            try:
                sent = await bot.send_photo(chat_id, photo, caption=text, reply_markup=markup)
                remember_ui(bot, chat_id, sent)
                continue
            except Exception as exc:
                print(f"photo error: {exc}")
        sent = await bot.send_message(chat_id, text, reply_markup=markup)
        remember_ui(bot, chat_id, sent)
    save_engine_state()


def schedule_gift_followup(bot: Bot, bot_id: str, chat_id: int, owner_id: int, delay: int, action: str) -> None:
    key = (bot_id, chat_id)
    old = GIFT_TASKS.get(key)
    if old and not old.done():
        old.cancel()

    async def worker():
        try:
            await asyncio.sleep(delay)
            await emit(bot, chat_id, engine.message(bot_id, action=action), owner_id)
        finally:
            GIFT_TASKS.pop(key, None)

    GIFT_TASKS[key] = asyncio.create_task(worker())


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


def tenant_dispatcher(bot_id: str, template: str, owner_tg_id: int = 0):
    tenant_dp = Dispatcher()

    @tenant_dp.message(CommandStart())
    async def start(message: Message):
        await clear_ui(message.bot, message.chat.id)
        meta = engine.TEMPLATES[template]
        try:
            brief = engine.BOTS.get(bot_id, {}).get("config", {}).get("brief", {})
            photo = (brief.get("photo") or "").strip()
            cover = ROOT / "platform" / photo.lstrip("/") if photo.startswith("/static/") else COVER_FILES[template]
            await message.answer_photo(
                FSInputFile(cover),
                caption=f"{meta['icon']} <b>{html.escape(meta['name'])}</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await emit(message.bot, message.chat.id, engine.message(bot_id, action="start", user_name=message.from_user.first_name or ""), owner_tg_id)
        if template == "gift" and (bot_id, message.chat.id) not in GIFT_FOLLOWUPS:
            schedule_gift_followup(message.bot, bot_id, message.chat.id, owner_tg_id, 2 * 60 * 60, "followup_2h")
        await message.answer("Меню бота 👇", reply_markup=tenant_menu(template))
        if message.from_user.id == owner_tg_id:
            await message.answer("⚙️ Цены и услуги: /manage")
        known = TENANT_USERS.setdefault(bot_id, set())
        uid = message.from_user.id
        if uid not in known and uid != owner_tg_id and str(uid) != OWNER_ID:
            known.add(uid)
            await emit(
                message.bot,
                message.chat.id,
                [engine._msg(
                    "🆕 Новый пользователь бота\n"
                    f"Бот: @{engine.BOTS.get(bot_id, {}).get('username', '')}\n"
                    f"Имя: {message.from_user.full_name}\n"
                    f"ID: {uid}",
                    admin=True,
                )],
                owner_tg_id,
            )

    @tenant_dp.callback_query()
    async def callback(call: CallbackQuery):
        await clear_ui(call.message.bot, call.message.chat.id)
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
                        await emit(
                            call.message.bot,
                            call.message.chat.id,
                            engine.message(bot_id, action="not_sub"),
                            owner_tg_id,
                        )
                        await call.answer()
                        return
                    action = "grant"
                except Exception as exc:
                    await notify_owner(f"⚠️ Не смог проверить подписку у @{call.from_user.username or call.from_user.id}: {exc}")
                    action = "not_sub"
        await call.answer()
        await emit(call.message.bot, call.message.chat.id, engine.message(bot_id, action=action), owner_tg_id)
        if template == "gift" and action == "grant":
            GIFT_FOLLOWUPS.add((bot_id, call.message.chat.id))
            schedule_gift_followup(call.message.bot, bot_id, call.message.chat.id, owner_tg_id, 24 * 60 * 60, "followup_24h")

    @tenant_dp.message(Command("manage"))
    async def manage_cmd(message: Message):
        if message.from_user.id != owner_tg_id and str(message.from_user.id) != OWNER_ID:
            return
        services = engine.BOTS.get(bot_id, {}).get("config", {}).get("services", [])
        if not services:
            await message.answer("У этого бота нет списка услуг.")
            return
        lines = [f"{i + 1}. {s['title']} — {s['price']} · {s['duration']}" for i, s in enumerate(services)]
        await message.answer(
            "⚙️ <b>Управление услугами</b>\n\n" + "\n".join(lines) +
            "\n\nИзменить цену:\n<code>/price 1 2500</code>",
            parse_mode="HTML",
        )

    @tenant_dp.message(Command("price"))
    async def price_cmd(message: Message):
        if message.from_user.id != owner_tg_id and str(message.from_user.id) != OWNER_ID:
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3 or not parts[1].isdigit():
            await message.answer("Формат: <code>/price 1 2500</code>", parse_mode="HTML")
            return
        index = int(parts[1]) - 1
        services = engine.BOTS.get(bot_id, {}).get("config", {}).get("services", [])
        if index < 0 or index >= len(services):
            await message.answer("Нет услуги с таким номером. Смотри /manage.")
            return
        raw = parts[2].strip()
        price = raw if ("₽" in raw or "руб" in raw.lower()) else f"{raw} ₽"
        services[index]["price"] = price
        brief = dict(TENANTS.get(bot_id, {}).get("brief") or {})
        brief["services"] = "\n".join(f"{s['title']} | {s['price']} | {s['duration']}" for s in services)
        TENANTS[bot_id]["brief"] = brief
        items = load_tenants()
        for record in items:
            if record.get("token") == TENANTS[bot_id]["token"]:
                record["brief"] = brief
        save_tenants(items)
        await message.answer(f"✅ {services[index]['title']}: <b>{price}</b>", parse_mode="HTML")

    @tenant_dp.message(Command("stats"))
    async def stats_cmd(message: Message):
        if message.from_user.id != owner_tg_id and str(message.from_user.id) != OWNER_ID:
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
        if message.from_user.id != owner_tg_id and str(message.from_user.id) != OWNER_ID:
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
        await clear_ui(message.bot, message.chat.id)
        brief = engine.BOTS.get(bot_id, {}).get("config", {}).get("brief", {})
        label = message.text
        if label in ("🚀 Старт", "💅 Записаться", "🎁 Подарок"):
            await emit(message.bot, message.chat.id, engine.message(bot_id, action="start", user_name=message.from_user.first_name or ""), owner_tg_id)
        elif label == "🛍 Каталог":
            action = "shop:start" if template == "shop" else "cat:Все"
            await emit(message.bot, message.chat.id, engine.message(bot_id, action=action), owner_tg_id)
        elif label == "🛒 Корзина":
            action = "shop:cart" if template == "shop" else "cart"
            await emit(message.bot, message.chat.id, engine.message(bot_id, action=action), owner_tg_id)
        elif label == "📣 Канал":
            channel = brief.get("channel", "")
            link = channel if str(channel).startswith("http") else f"https://t.me/{str(channel).lstrip('@')}"
            await message.answer("Канал для подписки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📣 Подписаться", url=link)]]))
        elif label == "📞 Связаться":
            contact = brief.get("contact", "владелец свяжется с вами")
            await message.answer(f"📞 {contact}")
        await message.answer("Меню бота 👇", reply_markup=tenant_menu(template))

    @tenant_dp.message(F.contact)
    async def contact(message: Message):
        phone = message.contact.phone_number if message.contact else ""
        await clear_ui(message.bot, message.chat.id)
        await emit(
            message.bot,
            message.chat.id,
            engine.message(bot_id, action=f"beauty:contact:{phone}"),
            owner_tg_id,
        )

    @tenant_dp.message(F.text)
    async def text(message: Message):
        await clear_ui(message.bot, message.chat.id)
        await emit(message.bot, message.chat.id, engine.message(bot_id, text=message.text, user_name=message.from_user.first_name or ""), owner_tg_id)

    return tenant_dp


BEAUTY_DESCRIPTION = (
    "Добро пожаловать в пространство красоты «Marina Beauty Space» ✨\n\n"
    "Это место, где стиль встречается с заботой, а вы отдыхаете, пока мы подчеркиваем вашу индивидуальность.\n\n"
    "Здесь вы можете посмотреть прайс, познакомиться с услугами и выбрать удобное окошко к нашим мастерам в пару кликов.\n\n"
    "Жмите «СТАРТ» (или /start) внизу экрана, чтобы начать! 👇"
)

SHOP_DESCRIPTION = (
    "Добро пожаловать в студию авторских десертов «Крем & Ваниль» 🍰\n\n"
    "Готовим нежные торты и пирожные из 100% натуральных ингредиентов без заменителей и лишнего сахара. "
    "Здесь можно посмотреть актуальную витрину, собрать свой набор сладостей в корзину и оформить заказ за пару кликов.\n\n"
    "Жмите «СТАРТ» внизу экрана, чтобы открыть меню 👇"
)

FUNNEL_DESCRIPTION = (
    "🛠️ Интерактивный конструктор Telegram-ботов от Школы ИИ-автоматизации.\n\n"
    "Здесь ты за 10 минут без единой строчки кода соберешь своего первого рабочего бота по готовым шаблонам "
    "(для бьюти-студии, магазина или автоворонки).\n\n"
    "Никакой воды и спама — только практика. Жми «СТАРТ» внизу экрана, чтобы запустить тренажер 👇"
)


async def apply_bot_profile(bot: Bot, template: str, brief: dict) -> None:
    if template not in ("booking", "shop", "gift"):
        return
    try:
        if template == "booking":
            await bot.set_my_description(description=BEAUTY_DESCRIPTION)
            await bot.set_my_short_description(short_description="Запись в студию красоты: услуги, цены и свободные окошки.")
        elif template == "shop":
            shop_name = (brief.get("business_name") or "Крем & Ваниль").strip()
            if "крем" in shop_name.lower():
                description = SHOP_DESCRIPTION.replace("«Крем & Ваниль»", f"«{shop_name}»")
            else:
                description = (
                    f"Добро пожаловать в «{shop_name}» 👋\n\n"
                    "Здесь можно посмотреть витрину, выбрать товар и оформить заказ прямо в Telegram за пару кликов.\n\n"
                    "Жмите «СТАРТ» внизу экрана, чтобы открыть меню 👇"
                )
            await bot.set_my_description(description=description)
            await bot.set_my_short_description(short_description=f"Витрина «{shop_name}»: товары и заказ в Telegram.")
        else:
            description = (brief.get("description") or "").strip() or FUNNEL_DESCRIPTION
            await bot.set_my_description(description=description)
            await bot.set_my_short_description(short_description="Тренажёр по сборке Telegram-ботов за 10 минут.")
    except Exception as exc:
        print(f"profile setup error: {exc}")


def success_copy(template: str, username: str, project: bool) -> str:
    link = f"https://t.me/{username}"
    if template == "booking":
        body = (
            "🥳 <b>Поздравляю! Твой первый бот для записи клиентов официально создан и работает.</b>\n\n"
            f"Скорее переходи по ссылке и нажимай /start, чтобы протестировать всю воронку вживую: 👉 {link}\n\n"
            "Ты огромный молодец! Только что ты своими руками, без единой строчки кода, собрал полноценного бота с каталогом услуг и записью на свободные окошки. "
            "На рынке фриланса сборка такого базового решения для сферы услуг стоит от 10 000 до 15 000 рублей — и делается она за один вечер!\n\n"
            "Дальше мы прокачаем твои навыки до PRO-уровня. Ты научишься докручивать именно этого бота так, чтобы он заиграл новыми красками и стоил уже от 25 000 – 40 000 рублей:\n\n"
            "🗓 Синхронизировать бота с CRM (Yclients, Dikidi, Google Календарь): чтобы свободные окошки подтягивались из реального расписания мастеров на автомате, а новая бронь сразу появлялась в графике салона.\n\n"
            "🧠 Вшить ИИ-администратора с базой знаний: чтобы бот общался как живой менеджер, отвечал на любые вопросы про противопоказания или уход после процедуры, отрабатывал возражения и сам доводил до записи.\n\n"
            "⏰ Настроить цепочку умных напоминаний: чтобы бот сам присылал клиенту схему проезда и напоминание за сутки до визита (снижая процент неявок), а через 3 недели заботливо звал на повторную процедуру.\n\n"
            "💳 Подключить онлайн-кассу и чаевые: чтобы клиенты могли вносить предоплату за сложные процедуры или оставлять благодарность мастеру прямо внутри Telegram.\n\n"
            "И это только верхушка айсберга!\n"
            "Добро пожаловать в мир AI-автоматизации — нишу, где твоя экспертность всегда будет стоить дорого! 🚀"
        )
    elif template == "gift":
        body = (
            "🥳 <b>Поздравляю! Твой бот для выдачи подарка за подписку официально создан и работает.</b>\n\n"
            f"Скорее переходи по ссылке и нажимай /start, чтобы протестировать всю воронку вживую: 👉 {link}\n\n"
            "Ты огромный молодец! Только что ты своими руками, без единой строчки кода, собрал полноценную автоворонку с проверкой подписки и двумя таймерами дожима. "
            "На рынке фриланса сборка такого базового бота стоит от 3 000 до 5 000 рублей — и делается она за один вечер!\n\n"
            "Дальше мы прокачаем твои навыки до PRO-уровня:\n\n"
            "🧠 Вшить ИИ-куратора прямо в бота.\n"
            "🎯 Добавить квалифицирующий мини-тест.\n"
            "🎬 Настроить каскадную выдачу.\n"
            "📊 Связать воронку с Google-таблицами и уведомлениями.\n\n"
            "И это только верхушка айсберга!\n"
            "Добро пожаловать в мир AI-автоматизации — нишу, где твоя экспертность всегда будет стоить дорого! 🚀"
        )
    else:
        body = (
            "🥳 <b>Поздравляю! Твой бот-витрина с полноценной корзиной официально создан и работает.</b>\n\n"
            f"Скорее переходи по ссылке и нажимай /start, чтобы протестировать свой магазин вживую: 👉 {link}\n\n"
            "Ты огромный молодец! Только что ты своими руками собрал рабочий инструмент для продаж с карточками товаров и автоматическим подсчетом корзины. "
            "На рынке фриланса сборка такого базового магазина стоит от 10 000 до 20 000 рублей — и делается она за один вечер!\n\n"
            "Дальше мы прокачаем твои навыки до PRO-уровня:\n\n"
            "💳 Подключать онлайн-оплату.\n"
            "🧠 Вшить ИИ-консультанта по ассортименту.\n"
            "📦 Синхронизировать витрину с Google-таблицами или «МойСклад».\n"
            "🚚 Настроить калькулятор доставки и промокоды.\n\n"
            "Добро пожаловать в мир AI-автоматизации! 🚀"
        )
    if project:
        body = "📁 Проект уже сохранён в твоём кабинете на платформе.\n\n" + body
    return body


async def start_tenant(token: str, template: str, brief: dict, tg_id: int = 0, project: dict | None = None, persist: bool = True) -> dict:
    bot = Bot(token)
    me = await bot.get_me()
    await apply_bot_profile(bot, template, brief)
    bot_id = engine.create_bot(template, brief)["id"]
    engine.BOTS[bot_id]["username"] = me.username
    task = asyncio.create_task(tenant_dispatcher(bot_id, template, tg_id).start_polling(bot))
    TENANTS[bot_id] = {"id": bot_id, "token": token, "username": me.username, "task": task, "template": template, "owner_tg_id": tg_id, "brief": brief, "project": project}
    if project is None and tg_id:
        project = await save_project(tg_id, template, brief, me.username)
    info = {"id": bot_id, "username": me.username, "template": template, "project": project, "owner_tg_id": tg_id}
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


async def link_telegram(message: Message, code: str) -> None:
    if not SERVICE_TOKEN:
        await message.answer("Привязка Telegram временно недоступна.")
        return
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{PLATFORM_API}/api/tg/link",
                headers={"X-Service-Token": SERVICE_TOKEN},
                json={"code": code, "tg_id": str(message.from_user.id), "username": message.from_user.username or ""},
            )
        if response.status_code != 200:
            await message.answer("Код неверный или истёк. Сгенерируй новый в профиле.")
            return
        await message.answer("✅ Telegram привязан к аккаунту школы. Проекты теперь в нём.")
    except Exception as exc:
        await message.answer(f"Не удалось привязать: {html.escape(str(exc))}")


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2 and parts[1].startswith("link_"):
        await link_telegram(message, parts[1][5:])
    text = (
        "🚀 <b>Приветствую на практике!</b>\n\n"
        "Погнали собирать твоего первого бота. Смотри, как всё просто.\n"
        "Выбирай, какой проект ты хочешь реализовать прямо сейчас:\n\n"
        "💅 <b>Студия красоты</b> — бот, который рассказывает об услугах, консультирует по ценам и автоматически записывает клиентов на свободные окошки.\n\n"
        "🛍 <b>Витрина товаров</b> — показывает красивый каталог, цены и позволяет клиентам оформить заказ прямо внутри Telegram.\n\n"
        "🎁 <b>Подарок за подписку</b> — классическая и самая востребованная воронка: бот проверяет подписку на канал и выдает лид-магнит (подарок).\n\n"
        "Жми на нужную кнопку ниже 👇"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💅 Студия красоты", callback_data="tpl2:booking")],
        [InlineKeyboardButton(text="🛍 Витрина товаров", callback_data="tpl2:shop")],
        [InlineKeyboardButton(text="🎁 Подарок за подписку", callback_data="tpl2:gift")],
    ])
    await clear_ui(message.bot, message.chat.id)
    try:
        sent = await message.answer_photo(
            FSInputFile(TEMPLATES_COVER),
            caption=text,
            parse_mode="HTML",
            reply_markup=markup,
        )
    except Exception:
        sent = await message.answer(text, parse_mode="HTML", reply_markup=markup)
    remember_ui(message.bot, message.chat.id, sent)
    menu = await message.answer("Меню бота 👇", reply_markup=main_menu())
    remember_ui(message.bot, message.chat.id, menu)


async def show_templates(message: Message) -> None:
    await clear_ui(message.bot, message.chat.id)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💅 Студия красоты", callback_data="tpl2:booking")],
        [InlineKeyboardButton(text="🎁 Подарок за подписку", callback_data="tpl2:gift")],
        [InlineKeyboardButton(text="🛍 Витрина товаров", callback_data="tpl2:shop")],
    ])
    caption = (
        "🎨 <b>Выбери шаблон</b>\n\n"
        "Три готовых сценария. Нажми кнопку — покажу бриф."
    )
    try:
        sent = await message.answer_photo(FSInputFile(TEMPLATES_COVER), caption=caption, parse_mode="HTML", reply_markup=markup)
    except Exception:
        sent = await message.answer(caption, parse_mode="HTML", reply_markup=markup)
    remember_ui(message.bot, message.chat.id, sent)


def user_bots(user_id: int) -> list[dict]:
    return [b for b in MY_BOTS if str(b.get("owner_tg_id", "")) == str(user_id)]


async def show_my_bots(message: Message, user_id: int | None = None) -> None:
    user_id = user_id or message.from_user.id
    items = user_bots(user_id)
    await clear_ui(message.bot, message.chat.id)
    if not items:
        sent = await message.answer("📦 Пока нет ботов.\n\nНажми «🛠 Собрать бота» внизу.", parse_mode="HTML", reply_markup=main_menu())
        remember_ui(message.bot, message.chat.id, sent)
        return
    lines = [f"• <b>@{html.escape(b['username'])}</b> — {html.escape(engine.TEMPLATES[b['template']]['name'])}" for b in items]
    sent = await message.answer("📦 <b>Мои боты</b>\n\n" + "\n".join(lines), parse_mode="HTML", reply_markup=main_menu())
    remember_ui(message.bot, message.chat.id, sent)


@dp.callback_query(F.data == "build")
async def build(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Build.template)
    await show_templates(call.message)
    await call.answer()


@dp.callback_query(F.data == "mybots")
async def mybots(call: CallbackQuery):
    await show_my_bots(call.message, call.from_user.id)
    await call.answer()


@dp.callback_query(F.data.startswith("tpl:"))
async def legacy_template_button(call: CallbackQuery, state: FSMContext):
    await call.answer("Это старая кнопка. Показываю актуальное меню.", show_alert=True)
    await state.clear()
    await state.set_state(Build.template)
    await show_templates(call.message)


@dp.callback_query(F.data.startswith("tpl2:"))
async def choose_template(call: CallbackQuery, state: FSMContext):
    template = call.data.split(":", 1)[1]
    if template not in engine.TEMPLATES:
        await call.answer("Неизвестный шаблон", show_alert=True)
        return
    await state.update_data(template=template, index=0, brief={})
    await state.set_state(Build.fields)
    meta = engine.TEMPLATES[template]
    await clear_ui(call.message.bot, call.message.chat.id)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🪄 Оставить готовый шаблон (Marina Beauty Space)" if template == "booking" else "🪄 Оставить готовый шаблон",
            callback_data="field:skip",
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="field:back")],
    ])
    mini = (
        "\n\n💡 <b>Мини-правило перед стартом (важно!):</b> Ты можешь собрать этого бота двумя способами:\n"
        "1️⃣ Под свой проект — тогда на каждом шаге пиши свои тексты и ссылки.\n"
        "2️⃣ На базе готового шаблона — тогда на каждом шаге нажимай «🪄 Оставить готовый шаблон».\n\n"
        "Пожалуйста, не миксуй оба варианта! Внутри готового шаблона все сообщения жестко связаны по смыслу. "
        "Если часть взять из шаблона, а часть написать от себя — картинка не сложится. Выбирай один путь и иди по нему до конца 👇"
    )
    sent = await call.message.answer(
        f"{meta['icon']} <b>{html.escape(meta['name'])}</b>\n\n"
        f"{html.escape(meta.get('welcome') or '')}"
        + mini
        + "\n\n"
        + field_prompt(template, 0),
        parse_mode="HTML",
        reply_markup=markup,
    )
    remember_ui(call.message.bot, call.message.chat.id, sent)
    await call.answer()


@dp.callback_query(F.data == "shop:preset")
async def shop_preset(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data or data.get("template") != "shop":
        await call.answer("Это доступно только для витрины.", show_alert=True)
        return
    brief = dict(data.get("brief") or {})
    brief["products"] = engine.TEMPLATES["shop"]["defaults"]["products"]
    await state.update_data(brief=brief, index=5, shop_products=[])
    await state.set_state(Build.fields)
    await ask_next_field(call.message, state)
    await call.answer("Готовое кафе подставлено")


@dp.callback_query(F.data == "shop:custom")
async def shop_custom(call: CallbackQuery, state: FSMContext):
    await clear_ui(call.message.bot, call.message.chat.id)
    await state.update_data(shop_products=[])
    await state.set_state(Build.product_photo)
    sent = await call.message.answer(
        "📸 <b>Фото товаров</b>\n\n"
        "Пришли фото и подпиши его одной строкой:\n"
        "<code>Название | Цена | Описание | Категория</code>\n\n"
        "Например: <code>Медовик | 2600 | медовые коржи | Торты</code>\n"
        "Можно несколько фото. Без подписи спрошу по шагам.\n\n"
        "Когда закончишь — напиши «Готово».",
        parse_mode="HTML",
    )
    remember_ui(call.message.bot, call.message.chat.id, sent)
    await call.answer()


@dp.callback_query(F.data == "field:back")
async def back_field(call: CallbackQuery, state: FSMContext):
    await go_back(call.message, state)
    await call.answer()


@dp.callback_query(F.data == "field:skip")
async def skip_field(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data or "template" not in data:
        await call.answer("Сначала выбери шаблон.", show_alert=True)
        return
    template = data["template"]
    index = int(data.get("index", 0))
    fields = builder_fields(template)
    if index >= len(fields):
        await call.answer()
        return
    field = fields[index]
    brief = dict(data.get("brief") or {})
    brief[field["key"]] = engine.TEMPLATES[template]["defaults"].get(field["key"], "")
    await state.update_data(index=index + 1, brief=brief)
    await ask_next_field(call.message, state)
    await call.answer("Подставил готовый шаблон")


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
    if (message.text or "").strip().lower().startswith("/start"):
        await start(message, state)
        return
    data = await state.get_data()
    print(f"[brief] text from {message.from_user.id}: {(message.text or '')[:80]!r} state={await state.get_state()} data_keys={list(data)}", flush=True)
    template = data["template"]
    index = data["index"]
    fields = builder_fields(template)
    brief = dict(data["brief"])
    value = (message.text or "").strip()
    if value.lower() in ("/skip", "пропустить"):
        value = engine.TEMPLATES[template]["defaults"].get(fields[index]["key"], "")
    if fields[index]["key"] == "contact" and value and "@" not in value and not value.startswith("http"):
        await message.answer("Кажется, ты забыл @. Попробуй еще раз!")
        return
    brief[fields[index]["key"]] = value
    index += 1
    editing = bool(data.get("editing"))
    if editing:
        index = len(fields) - 1
    await state.update_data(index=index, brief=brief, editing=False)
    await state.set_state(Build.fields)
    await ask_next_field(message, state)


@dp.message(F.photo)
async def product_photo(message: Message, state: FSMContext):
    current = await state.get_state()
    leaf = str(getattr(current, "state", current) or "").split(":")[-1]
    if leaf not in ("product_photo", "product_title", "product_price", "product_desc", "product_category"):
        return
    if leaf != "product_photo":
        await message.answer("Сначала заверши текущую карточку, потом пришли следующее фото.")
        return
    photo = message.photo[-1]
    is_group = bool(message.media_group_id)
    if not is_group:
        await message.answer("📥 Фото получил, сохраняю…")
    try:
        file = await asyncio.wait_for(message.bot.get_file(photo.file_id), timeout=15)
        name = f"{uuid.uuid4().hex}.jpg"
        await asyncio.wait_for(
            message.bot.download_file(file.file_path, destination=UPLOADS / name),
            timeout=35,
        )
    except Exception as exc:
        await message.answer(f"⚠️ Не смог сохранить фото: {html.escape(str(exc))}", parse_mode="HTML")
        return
    image = f"/static/uploads/{name}"
    if is_group:
        data = await state.get_data()
        if data.get("batch_group") != message.media_group_id:
            await state.update_data(batch_images=[], batch_caption="", batch_group=message.media_group_id)
            data = await state.get_data()
        images = list(data.get("batch_images", []))
        images.append(image)
        caption = data.get("batch_caption", "")
        if (message.caption or "").strip():
            caption = (message.caption or "").strip()
        await state.update_data(batch_images=images, batch_caption=caption)
        if len(images) == 1:
            await message.answer(f"📥 Принял пачку, сохраняю фото…")
        _schedule_batch(message.bot, message.chat.id, state)
        return
    await state.update_data(pending_image=image)
    caption = (message.caption or "").strip()
    if caption:
        card = _card_line(caption, image)
        parts = [part.strip() for part in card.split("|")]
        title = parts[0]
        price = parts[1]
        data = await state.get_data()
        products = list(data.get("shop_products", []))
        products.append(card)
        await state.update_data(shop_products=products, pending_image="")
        await state.set_state(Build.product_photo)
        await message.answer(
            f"✅ «{html.escape(title)}» — {html.escape(price)} добавлен.\n\n"
            "Пришли фото следующего товара с подписью или напиши «Готово».",
            parse_mode="HTML",
        )
        return
    await state.set_state(Build.product_title)
    await message.answer(
        "✅ Фото сохранил.\n\n"
        "Как называется товар?\n"
        "Например: <code>Медовик</code>",
        parse_mode="HTML",
    )


@dp.message(Build.product_batch, F.text)
async def product_batch(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if value.lower().startswith("/start"):
        await start(message, state)
        return
    data = await state.get_data()
    images = list(data.get("batch_images", []))
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not images:
        await state.set_state(Build.product_photo)
        await message.answer("Фото уже нет. Пришли пачку заново.")
        return
    if len(lines) != len(images):
        await message.answer(
            f"Фото: {len(images)}, строк: {len(lines)}.\n\n"
            "Нужно ровно по одной строке на каждое фото. Пришли список ещё раз."
        )
        return
    products = list(data.get("shop_products", []))
    products.extend(_card_line(line, image) for line, image in zip(lines, images))
    await state.update_data(
        shop_products=products,
        batch_images=[],
        batch_caption="",
        batch_group="",
    )
    await state.set_state(Build.product_photo)
    await message.answer(
        f"✅ Добавил {len(images)} товаров.\n\n"
        "Пришли ещё фото или напиши «Готово»."
    )


@dp.message(Build.product_photo, F.text)
async def products_done_or_text(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if value.lower().startswith("/start"):
        await start(message, state)
        return
    data = await state.get_data()
    products = list(data.get("shop_products", []))
    if value.lower() in ("готово", "хватит", "всё", "все", "/skip", "пропустить"):
        if not products:
            await state.set_state(Build.product_photo)
            await message.answer(
                "⚠️ Пока нет ни одного товара.\n\n"
                "Пришли фото с подписью:\n"
                "<code>Название | Цена | Описание | Категория</code>\n\n"
                "Или сначала фото, потом я спрошу по шагам.",
                parse_mode="HTML",
            )
            return
        brief = dict(data.get("brief", {}))
        brief["products"] = "\n".join(products)
        await state.update_data(brief=brief, index=5)
        await state.set_state(Build.fields)
        await message.answer(f"✅ Принято товаров: {len(products)}. Дальше — доставка.")
        await ask_next_field(message, state)
        return
    if "|" in value:
        image = data.get("pending_image", "")
        products.append(_card_line(value, image))
        await state.update_data(shop_products=products, pending_image="")
        await message.answer(
            f"✅ Принято: {len(products)} товар(ов).\n\n"
            "Пришли фото следующего товара с подписью или напиши «Готово»."
        )
        return
    if re.search(r"\d", value):
        image = data.get("pending_image", "")
        card = _card_line(value, image)
        parts = [part.strip() for part in card.split("|")]
        products.append(card)
        await state.update_data(shop_products=products, pending_image="")
        await message.answer(
            f"✅ Принято: «{html.escape(parts[0])}» за {html.escape(parts[1])}.\n\n"
            "Пришли фото следующего товара или напиши «Готово».",
            parse_mode="HTML",
        )
        return
    await message.answer(
        "Не понял карточку. Пришли фото и подпись в формате:\n"
        "<code>Название | Цена | Описание | Категория</code>\n\n"
        "Например: <code>Медовик | 2600 | медовые коржи | Торты</code>",
        parse_mode="HTML",
    )


@dp.message(Build.product_title, F.text)
async def product_title(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if value.lower().startswith("/start"):
        await start(message, state)
        return
    if re.search(r"\d", value):
        data = await state.get_data()
        card = _card_line(value, data.get("pending_image", ""))
        parts = [part.strip() for part in card.split("|")]
        products = list(data.get("shop_products", []))
        products.append(card)
        await state.update_data(shop_products=products, pending_image="")
        await state.set_state(Build.product_photo)
        await message.answer(
            f"✅ Принято: «{html.escape(parts[0])}» за {html.escape(parts[1])}.\n\n"
            "Пришли фото следующего товара или напиши «Готово».",
            parse_mode="HTML",
        )
        return
    if not value:
        await message.answer("Напиши название товара.")
        return
    await state.update_data(pending_title=value[:100])
    await state.set_state(Build.product_price)
    await message.answer(
        "💰 Какая цена?\nНапример: <code>2600</code> или <code>2 600 ₽</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="product:back")]]),
    )


@dp.message(Build.product_price, F.text)
async def product_price(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if value.lower().startswith("/start"):
        await start(message, state)
        return
    if not value:
        await message.answer("Напиши цену товара.")
        return
    await state.update_data(pending_price=value[:40])
    await state.set_state(Build.product_desc)
    await message.answer(
        "📝 Добавь короткое описание товара.\nМожно написать /skip.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="product:back")]]),
    )


@dp.message(Build.product_desc, F.text)
async def product_desc(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if value.lower().startswith("/start"):
        await start(message, state)
        return
    if value.lower() in ("/skip", "пропустить"):
        value = ""
    await state.update_data(pending_desc=value[:500])
    await state.set_state(Build.product_category)
    await message.answer(
        "🏷 Категория товара?\nНапример: <code>Торты</code>. Можно /skip.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="product:back")]]),
    )


@dp.message(Build.product_category, F.text)
async def product_category(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if value.lower().startswith("/start"):
        await start(message, state)
        return
    if value.lower() in ("/skip", "пропустить") or not value:
        value = "Другое"
    data = await state.get_data()
    line = (
        f"{data.get('pending_title', 'Товар')} | {data.get('pending_price', 'по запросу')} | "
        f"{data.get('pending_desc', '')} | {value[:40]} | 🛍 | {data.get('pending_image', '')}"
    )
    products = list(data.get("shop_products", []))
    products.append(line)
    await state.update_data(
        shop_products=products,
        pending_image="",
        pending_title="",
        pending_price="",
        pending_desc="",
    )
    await state.set_state(Build.product_photo)
    await message.answer(
        f"✅ «{data.get('pending_title', 'Товар')}» добавлен в витрину.\n\n"
        "Пришли фото следующего товара или напиши «Готово».",
    )


@dp.callback_query(F.data == "product:back")
async def product_back(call: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current == Build.product_title.state:
        await state.set_state(Build.product_photo)
    elif current == Build.product_price.state:
        await state.set_state(Build.product_title)
    elif current == Build.product_desc.state:
        await state.set_state(Build.product_price)
    elif current == Build.product_category.state:
        await state.set_state(Build.product_desc)
    await clear_ui(call.message.bot, call.message.chat.id)
    await call.message.answer("Вернулся на шаг назад. Напиши значение ещё раз.")
    await call.answer()



    value = (message.text or "").strip()
    if value.lower().startswith("/start"):
        await start(message, state)
        return
    data = await state.get_data()
    products = list(data.get("shop_products", []))
    if value.lower() in ("готово", "хватит", "всё", "все", "/skip", "пропустить"):
        if not products:
            await state.set_state(Build.product_photo)
            await message.answer(
                "⚠️ Пока нет ни одного товара.\n\n"
                "Пришли фото товара, затем одним сообщением:\n"
                "<code>Название | Цена | Описание | Категория</code>\n\n"
                "И только после этого пиши «Готово».",
                parse_mode="HTML",
            )
            return
        brief = dict(data.get("brief", {}))
        brief["products"] = "\n".join(products)
        await state.update_data(brief=brief, index=5)
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
    if value.lower().startswith("/start"):
        await start(message, state)
        return
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
    await call.answer("Кнопка отключена: этот токен уже занят. Создай нового бота в BotFather.", show_alert=True)
    return
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
    text = success_copy(bot["template"], bot["username"], bool(project))
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
    await show_my_bots(message, message.from_user.id)


@dp.message(F.text)
async def fallback_text(message: Message, state: FSMContext):
    current = await state.get_state()
    name = getattr(current, "state", current) or ""
    leaf = str(name).split(":")[-1]
    data = await state.get_data()
    print(f"[fallback] text from {message.from_user.id}: {(message.text or '')[:80]!r} state={current} data_keys={list(data)}", flush=True)
    if leaf == "token":
        await receive_token(message, state)
    elif leaf == "product_photo":
        await products_done_or_text(message, state)
    elif leaf == "product_info":
        await product_info(message, state)
    elif "template" in data and "index" in data:
        await fill_field(message, state)


async def restore_tenants() -> None:
    for record in load_tenants():
        try:
            info = await start_tenant(
                record["token"],
                record["template"],
                record.get("brief", {}),
                tg_id=record.get("owner_tg_id", 0),
                project=record.get("project"),
                persist=False,
            )
            MY_BOTS.append(info)
            print(f"restored @{info['username']} ({info['template']})")
        except Exception as exc:
            print(f"restore failed {record.get('username')}: {exc}")


async def sync_projects() -> None:
    """Подтягивает сохранённый content.json в работающих ботов."""
    seen: dict[str, str] = {}
    print(f"[sync] started tenants={len(TENANTS)} service_token={bool(SERVICE_TOKEN)}", flush=True)
    while True:
        for bot_id, record in list(TENANTS.items()):
            project = record.get("project") or {}
            project_id = project.get("project_id") or project.get("id") if isinstance(project, dict) else None
            if not project_id or not SERVICE_TOKEN:
                continue
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        f"{PLATFORM_API}/api/tg/project/{project_id}/brief",
                        headers={"X-Service-Token": SERVICE_TOKEN},
                    )
                if response.status_code != 200:
                    continue
                payload = response.json()
                brief = payload.get("brief") or {}
                signature = json.dumps(brief, ensure_ascii=False, sort_keys=True)
                if seen.get(bot_id) == signature:
                    continue
                seen[bot_id] = signature
                fresh = engine.create_bot(record["template"], brief)
                if engine.BOTS.get(bot_id):
                    engine.BOTS[bot_id]["config"] = fresh["config"]
                record["brief"] = brief
                items = load_tenants()
                for item in items:
                    if item.get("token") == record.get("token"):
                        item["brief"] = brief
                save_tenants(items)
                print(f"[sync] updated @{record.get('username')}", flush=True)
            except Exception:
                continue
        await asyncio.sleep(6)


async def main() -> None:
    if not PLATFORM_TOKEN:
        raise SystemExit("PLATFORM_BOT_TOKEN не задан")
    bot = Bot(token=PLATFORM_TOKEN)
    try:
        await bot.set_my_description(
            "👋 Рад видеть тебя на практике!\n\n"
            "На связи школа AI-автоматизации — мы готовим техспецов нового поколения.\n\n"
            "Ты находишься буквально в одном шаге от создания своего первого умного бота. "
            "Это будет быстро, просто и без единой строчки кода.\n\n"
            "Жми «СТАРТ» (или /start) внизу экрана, и давай творить магию! ✨"
        )
        await bot.set_my_short_description(short_description="Собери своего первого Telegram-бота по готовым шаблонам.")
    except Exception as exc:
        print(f"platform profile error: {exc}")
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="mybots", description="Мои боты"),
    ])
    await restore_tenants()
    load_engine_state()
    asyncio.create_task(sync_projects())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())






















