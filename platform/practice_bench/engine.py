"""Local practice bench: three bot scenarios and brief-driven configuration."""
from __future__ import annotations

import re
import uuid
from copy import deepcopy
from typing import Any

TEMPLATES: dict[str, dict[str, Any]] = {
    "booking": {
        "name": "Запись к мастеру",
        "icon": "📅",
        "accent": "#ff6b8a",
        "tagline": "Услуги, окна и заявка мастеру",
        "fields": [
            {"key": "business_name", "label": "Название студии", "type": "text", "required": True},
            {"key": "services", "label": "Услуги", "type": "textarea", "hint": "Название — цена — длительность, каждая с новой строки"},
            {"key": "slots", "label": "Свободные окна", "type": "text", "hint": "Через запятую"},
            {"key": "address", "label": "Адрес", "type": "text"},
            {"key": "contact", "label": "Контакт", "type": "text"},
        ],
        "defaults": {
            "business_name": "Студия «Марина»",
            "services": "Стрижка — 3 500 ₽ — 60 мин\nОкрашивание — от 7 000 ₽ — 120 мин\nУкладка — 2 500 ₽ — 45 мин",
            "slots": "10:00, 12:00, 14:00, 16:00, 18:00",
            "address": "Москва, ул. Примерная, 10",
            "contact": "@marina_studio",
        },
    },
    "ai": {
        "name": "Умный консультант",
        "icon": "✦",
        "accent": "#a78bfa",
        "tagline": "Отвечает по тексту о бизнесе",
        "fields": [
            {"key": "business_name", "label": "Название бизнеса", "type": "text", "required": True},
            {"key": "niche", "label": "Ниша", "type": "text"},
            {"key": "knowledge", "label": "База знаний", "type": "textarea", "hint": "Всё о бизнесе: услуги, цены, адрес, правила"},
            {"key": "contact", "label": "Контакт человека", "type": "text"},
            {"key": "faq", "label": "Частые вопросы", "type": "textarea", "hint": "Вопрос|Ответ, каждый с новой строки"},
        ],
        "defaults": {
            "business_name": "Студия «Марина»",
            "niche": "салон красоты",
            "knowledge": "Студия «Марина» — салон красоты в Москве.\nАдрес: ул. Примерная, 10. Метро «Примерная», 5 минут пешком.\nРаботаем ежедневно с 10:00 до 21:00.\nСтрижка — 3 500 ₽, окрашивание — от 7 000 ₽, укладка — 2 500 ₽.\nПеренести запись можно за 24 часа. Опоздание больше 15 минут — переносим на другое время.",
            "contact": "@marina_studio",
            "faq": "Сколько стоит стрижка?|3 500 ₽.\nГде вы находитесь?|Москва, ул. Примерная, 10.\nЧто если я опоздаю на 15 минут?|Если опоздание больше 15 минут, перенесём запись на другое время — без штрафа.\nМожно перенести запись?|Да, не позднее чем за 24 часа.\nЕсть ли парковка?|Да, во дворе дома.",
        },
    },
    "shop": {
        "name": "Витрина товаров",
        "icon": "🛍️",
        "accent": "#e7a06f",
        "tagline": "Фото, корзина и заказ в чате",
        "fields": [
            {"key": "business_name", "label": "Название магазина", "type": "text", "required": True},
            {"key": "products", "label": "Товары", "type": "textarea", "hint": "Название | Цена | Описание | Категория | Эмодзи | Фото"},
            {"key": "delivery", "label": "Доставка", "type": "textarea", "hint": "Самовывоз / доставка"},
            {"key": "contact", "label": "Контакт", "type": "text"},
        ],
        "defaults": {
            "business_name": "Кондитерская «Медовый дом»",
            "products": "Медовик | 3 200 | Медовые коржи и сметанный крем | Торты | 🍰 | https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=900&q=80&auto=format&fit=crop\nКрасный бархат | 3 800 | Бисквит с крем-чизом | Торты | 🍒 | https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?w=900&q=80&auto=format&fit=crop\nНабор макарон | 1 900 | 12 штук, ассорти | Десерты | 🍬 | https://images.unsplash.com/photo-1558326567-98ae2405596b?w=900&q=80&auto=format&fit=crop\nБукет пионов | 4 500 | 15 пионов, крафт | Букеты | 🌸 | https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=900&q=80&auto=format&fit=crop",
            "delivery": "Самовывоз: Москва, ул. Примерная, 10\nДоставка по Москве: 500 ₽, от 5 000 ₽ — бесплатно",
            "contact": "@miod_dom",
        },
    },
}

BOTS: dict[str, dict[str, Any]] = {}
SESSIONS: dict[str, dict[str, Any]] = {}


def _lines(raw: str) -> list[str]:
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


def _services(raw: str) -> list[dict]:
    items = []
    for line in _lines(raw):
        parts = [p.strip() for p in re.split(r"[—|]", line)]
        if not parts:
            continue
        items.append({
            "title": parts[0],
            "price": parts[1] if len(parts) > 1 else "по запросу",
            "duration": parts[2] if len(parts) > 2 else "60 мин",
        })
    return items


def _products(raw: str) -> list[dict]:
    items = []
    for i, line in enumerate(_lines(raw)):
        parts = [p.strip() for p in line.split("|")]
        items.append({
            "id": i + 1,
            "title": parts[0] if parts else line,
            "price": parts[1] if len(parts) > 1 else "по запросу",
            "description": parts[2] if len(parts) > 2 else "",
            "category": parts[3] if len(parts) > 3 else "Другое",
            "emoji": parts[4] if len(parts) > 4 else "🛍️",
            "image": parts[5] if len(parts) > 5 else "",
        })
    return items


def _faq(raw: str) -> list[dict]:
    items = []
    for line in _lines(raw):
        q, _, a = line.partition("|")
        if q.strip():
            items.append({"q": q.strip(), "a": a.strip() or "Уточните у администратора."})
    return items


def create_bot(template: str, brief: dict) -> dict:
    if template not in TEMPLATES:
        raise ValueError("Неизвестный шаблон")
    base = deepcopy(TEMPLATES[template]["defaults"])
    base.update({k: v for k, v in (brief or {}).items() if v not in (None, "")})
    bot_id = uuid.uuid4().hex[:8]
    config: dict[str, Any] = {"template": template, "brief": base}
    if template == "booking":
        config["services"] = _services(base.get("services", ""))
        config["slots"] = [s.strip() for s in (base.get("slots") or "").split(",") if s.strip()]
    elif template == "ai":
        config["faq"] = _faq(base.get("faq", ""))
    elif template == "shop":
        config["products"] = _products(base.get("products", ""))
        config["categories"] = []
        for product in config["products"]:
            if product["category"] not in config["categories"]:
                config["categories"].append(product["category"])
    bot = {
        "id": bot_id,
        "template": template,
        "name": base.get("business_name") or TEMPLATES[template]["name"],
        "config": config,
    }
    BOTS[bot_id] = bot
    SESSIONS[bot_id] = {"stage": "start", "data": {}, "messages": []}
    return bot


def reset(bot_id: str) -> None:
    SESSIONS[bot_id] = {"stage": "start", "data": {}, "messages": []}


def _buttons(items: list[tuple[str, str]]) -> list[dict]:
    return [{"label": label, "action": action} for label, action in items]


def _msg(text: str, buttons: list[tuple[str, str]] | None = None, image: str = "", admin: bool = False) -> dict:
    out: dict[str, Any] = {"text": text}
    if buttons:
        out["buttons"] = _buttons(buttons)
    if image:
        out["image"] = image
    if admin:
        out["admin"] = True
    return out


def _start(bot: dict) -> list[dict]:
    template = bot["template"]
    brief = bot["config"]["brief"]
    if template == "booking":
        services = bot["config"]["services"]
        return [
            _msg(f"Здравствуйте! Это {bot['name']}.\nВыберите услугу — подберу свободное время."),
            _msg("Что вас интересует?", [(s["title"] + " · " + s["price"], f"service:{i}") for i, s in enumerate(services)]),
        ]
    if template == "ai":
        faq = bot["config"]["faq"]
        return [
            _msg(f"Здравствуйте! Я консультант {bot['name']}.\nСпросите что угодно — отвечу по делу."),
            _msg("Можно начать с частого вопроса:", [(f["q"], f"q:{i}") for i, f in enumerate(faq[:3])] + [("Связаться", "contact")]),
        ]
    products = bot["config"]["products"]
    cats = ["Все"] + bot["config"]["categories"]
    buttons = [(c, f"cat:{c}") for c in cats]
    buttons += [(p["title"] + " · " + p["price"], f"product:{p['id']}") for p in products[:2]]
    buttons += [("Корзина", "cart")]
    return [
        _msg(f"Здравствуйте! Это {bot['name']}.\nВыбирайте — заказ придёт нам в Telegram."),
        _msg("Категории и хиты:", buttons),
    ]


def _booking(bot: dict, session: dict, text: str, action: str) -> list[dict]:
    brief = bot["config"]["brief"]
    services = bot["config"]["services"]
    slots = bot["config"]["slots"]
    data = session["data"]
    if action.startswith("service:"):
        index = int(action.split(":")[1])
        data["service"] = services[index]
        session["stage"] = "name"
        return [_msg(f"Выбрали: {services[index]['title']} · {services[index]['price']}.\n\nКак вас зовут?")]
    if session["stage"] == "name" and text:
        data["name"] = text
        session["stage"] = "phone"
        return [_msg("Оставьте телефон для подтверждения:")]
    if session["stage"] == "phone" and text:
        if sum(ch.isdigit() for ch in text) < 10:
            return [_msg("Похоже, в номере не хватает цифр. Напишите ещё раз.")]
        data["phone"] = text
        session["stage"] = "date"
        return [_msg("На какую дату записать?", [("Сегодня", "date:today"), ("Завтра", "date:tomorrow")])]
    if action.startswith("date:"):
        data["date"] = "сегодня" if action == "date:today" else "завтра"
        session["stage"] = "time"
        return [_msg("Выберите свободное время:", [(slot, f"time:{slot}") for slot in slots])]
    if action.startswith("time:"):
        data["time"] = action.split(":", 1)[1]
        session["stage"] = "confirm"
        return [_msg(
            f"Проверьте заявку:\n\nУслуга: {data['service']['title']}\nДата: {data['date']}\nВремя: {data['time']}\nИмя: {data['name']}\nТелефон: {data['phone']}",
            [("Подтвердить", "confirm"), ("Отменить", "reset")],
        )]
    if action == "confirm":
        session["stage"] = "done"
        return [
            _msg(f"Готово, {data['name']}! Заявка принята.\nМастер подтвердит запись по телефону {data['phone']}.\n\nСвязаться: {brief.get('contact')}"),
            _msg(f"🔔 Уведомление мастеру:\nНовая запись: {data['service']['title']}, {data['date']} в {data['time']}.\nКлиент: {data['name']}, {data['phone']}", admin=True),
        ]
    return [_msg("Нажмите /start или выберите услугу заново.")]


def _ai(bot: dict, session: dict, text: str, action: str) -> list[dict]:
    faq = bot["config"]["faq"]
    if action.startswith("q:"):
        item = faq[int(action.split(":")[1])]
        return [_msg(item["a"], [("Спросить ещё", "reset")])]
    if action == "contact":
        return [_msg("Передал человеку. Напишите: " + bot["config"]["brief"].get("contact", "@manager"))]
    if not text:
        return [_msg("Напишите вопрос текстом.")]
    lowered = text.lower()
    best = None
    best_score = 0
    user_tokens = set(re.findall(r"[a-zа-яё0-9]+", lowered))
    for item in faq:
        q_tokens = set(re.findall(r"[a-zа-яё0-9]+", item["q"].lower()))
        score = len(user_tokens & q_tokens)
        if score > best_score:
            best, best_score = item, score
    if best and best_score >= 2:
        return [_msg(best["a"], [("Спросить ещё", "reset"), ("Связаться", "contact")])]
    if "опозда" in lowered:
        return [_msg("Если опоздание больше 15 минут — перенесём запись на другое время. Без штрафа.", [("Связаться", "contact")])]
    return [_msg(
        "Этого нет в моей базе. Передам администратору — " + bot["config"]["brief"].get("contact", "@manager") + ".",
        [("Связаться", "contact"), ("Спросить ещё", "reset")],
    )]


def _shop(bot: dict, session: dict, text: str, action: str) -> list[dict]:
    products = bot["config"]["products"]
    by_id = {p["id"]: p for p in products}
    data = session["data"]
    cart = data.setdefault("cart", {})
    if action == "cart":
        if not cart:
            return [_msg("Корзина пустая. Выберите товар в каталоге.", [("Каталог", "cat:Все")])]
        lines = [f"{by_id[int(pid)]['title']} × {qty} — {by_id[int(pid)]['price']}" for pid, qty in cart.items()]
        return [_msg("Корзина:\n\n" + "\n".join(lines) + "\n\nИтого: " + _total(by_id, cart) + " ₽", [("Оформить", "checkout"), ("Очистить", "clear")])]
    if action.startswith("cat:"):
        category = action.split(":", 1)[1]
        items = products if category == "Все" else [p for p in products if p["category"] == category]
        out = [_msg(f"Категория: {category}")]
        for product in items:
            out.append(_msg(f"{product['title']}\n{product['price']} · {product['description']}", [("Открыть", f"product:{product['id']}")], product["image"]))
        out.append(_msg("Можно открыть товар и добавить в корзину.", [("Корзина", "cart")]))
        return out
    if action.startswith("product:"):
        product = by_id[int(action.split(":")[1])]
        return [_msg(f"{product['title']}\n{product['price']}\n\n{product['description']}", [("В корзину", f"add:{product['id']}"), ("Корзина", "cart")], product["image"])]
    if action.startswith("add:"):
        pid = action.split(":")[1]
        cart[pid] = cart.get(pid, 0) + 1
        return [_msg(f"Добавлено: {by_id[int(pid)]['title']}. В корзине: {sum(cart.values())}.", [("Корзина", "cart"), ("Каталог", "cat:Все")])]
    if action == "clear":
        data["cart"] = {}
        return [_msg("Корзина очищена.", [("Каталог", "cat:Все")])]
    if action == "checkout":
        if not cart:
            return [_msg("Сначала добавьте товар.", [("Каталог", "cat:Все")])]
        session["stage"] = "name"
        return [_msg("Как вас зовут?")]
    if session["stage"] == "name" and text:
        data["name"] = text
        session["stage"] = "phone"
        return [_msg("Телефон для связи:")]
    if session["stage"] == "phone" and text:
        if sum(ch.isdigit() for ch in text) < 10:
            return [_msg("Проверьте номер и напишите ещё раз.")]
        data["phone"] = text
        lines = [f"• {by_id[int(pid)]['title']} × {qty} — {by_id[int(pid)]['price']}" for pid, qty in cart.items()]
        session["stage"] = "done"
        return [
            _msg(f"Заказ принят, {data['name']}! Мы свяжемся с вами.", [("Сделать ещё заказ", "reset")]),
            _msg("🔔 Уведомление магазину:\n" + "\n".join(lines) + f"\nИтого: {_total(by_id, cart)} ₽\nИмя: {data['name']}\nТелефон: {data['phone']}", admin=True),
        ]
    if not text:
        return [_msg("Выберите категорию или товар.", [("Каталог", "cat:Все"), ("Корзина", "cart")])]
    return [_msg("Я показываю товары кнопками. Нажмите «Каталог».", [("Каталог", "cat:Все")])]


def _total(by_id: dict, cart: dict) -> str:
    total = 0
    for pid, qty in cart.items():
        total += (int(re.sub(r"\D", "", by_id[int(pid)]["price"]) or 0)) * qty
    return f"{total:,}".replace(",", " ")


def message(bot_id: str, text: str = "", action: str = "") -> list[dict]:
    bot = BOTS.get(bot_id)
    if not bot:
        raise ValueError("Бот не найден")
    session = SESSIONS.setdefault(bot_id, {"stage": "start", "data": {}, "messages": []})
    if action in ("reset", "start") or text.strip().lower() in ("/start", "start"):
        reset(bot_id)
        return _start(BOTS[bot_id])
    if bot["template"] == "booking":
        return _booking(bot, session, text, action)
    if bot["template"] == "ai":
        return _ai(bot, session, text, action)
    return _shop(bot, session, text, action)
