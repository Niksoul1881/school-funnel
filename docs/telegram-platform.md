# Telegram-платформа практики

Документация для разработчика/друга. Здесь главный бот и три активных шаблона. AI-консультант отключён: код остался, но в каталоге и конструкторе его нет.

## Активные боты

| # | Бот | Роль | Код |
|---|---|---|---|
| 1 | **@platform_test_soulnik_bot** | главный: урок, выбор шаблона, бриф, токен, запуск | `telegram_bots/platform_bot.py` |
| 2 | **Запись к мастеру** | бот ученика: услуги, дата, время, имя, телефон | `local_practice/engine.py` (`_booking`) |
| 3 | **Подарок за подписку** | бот ученика: подписка на канал → подарок | `local_practice/engine.py` (`_gift`) |
| 4 | **Витрина товаров** | бот ученика: каталог, загрузка фото, корзина, заказ | `local_practice/engine.py` (`_shop`) |

**AI-консультант** (`_ai`) и **Заявка** (`_lead`) оставлены в коде как legacy, но убраны из каталога и карточек конструктора.

Главный бот создаёт активных ботов как **арендаторов в одном процессе**. Отдельные процессы для каждого не нужны.

## Как это работает

```text
/start
  → «Собрать бота»
  → шаблон
  → 4–5 вопросов брифа
  → токен нового бота из BotFather
  → бот ученика начинает polling
  → проект создаётся в веб-кабинете
  → владельцу приходит уведомление от главного бота
```

### Файлы

```text
telegram_bots/
  platform_bot.py       главный бот + арендаторы + persistence
  launch.py             запуск трёх прямых ботов (альтернативный режим)
  README.md             быстрый старт
  env.example           пример переменных
  tenants.example.json  пример сохранённых ботов без токенов

local_practice/
  engine.py             сценарии трёх ботов, текст, LLM, handoff
  app.py                веб-стенд /practice
  static/               интерфейс стенда

platform/
  app/main.py           API платформы, magic-link, сервисные endpoints
  app/catalog.py        генерация проектов из шаблонов
  app/template_*.py     standalone-версии шаблонов
  practice_bench/       копия веб-стенда для публичного /practice
```

## Запуск

1. Установить зависимости:

```bash
pip install -r platform/requirements.txt
pip install aiogram python-dotenv
```

2. Создать `private/telegram-test.env` по примеру `telegram_bots/env.example`.

3. Запустить главного бота:

```powershell
python telegram_bots\platform_bot.py
```

Главный бот сам поднимет трёх арендаторов из `private/tenants.json`.

### Режим трёх прямых ботов

Если не нужен конструктор:

```powershell
python telegram_bots\launch.py
```

Не запускай одновременно `launch.py` и `platform_bot.py` на одинаковых токенах — Telegram отдаст `Conflict: terminated by other getUpdates`.

## Брифы

| Шаблон | Вопросы |
|---|---|
| Запись | название, услуги, окна, адрес, контакт |
| AI | название, ниша, база знаний, контакт, FAQ |
| Витрина | название, товары, доставка, контакт |

Товары и услуги — построчно:

```text
Стрижка — 3 500 ₽ — 60 мин
Кекс «Ваниль» | 250 | ванильный | Кексы | 🧁 | https://...
```

### Фото товаров без ссылок

В витрине фото загружаются **прямо в Telegram**:

1. На шаге «Товары» пользователь присылает фото.
2. Бот скачивает его и сохраняет в `platform/static/uploads/*.jpg`.
3. Спрашивает: `Название | Цена | Описание | Категория`.
4. Повторяет для следующих товаров.
5. «Готово» — бриф сохраняется, фото уходят в карточки.

Ссылки на изображения не нужны.

## AI

AI-бот использует OpenAI-совместимый API:

```env
LLM_API_KEY=...
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

Если ключа нет — работает FAQ-fallback. Если ответа нет в базе — бот пишет контакт человека и отправляет уведомление владельцу.

## Уведомления владельцу

Арендатор не пишет уведомление клиенту. Он вызывает сервисный endpoint:

```text
POST /api/tg/notify_owner
X-Service-Token: ...
```

Сервер отправляет сообщение **от главного бота** в `OWNER_TG_ID`. Поэтому клиент не видит служебные сообщения.

## Проекты в кабинете

При создании бота вызывается:

```text
POST /api/tg/create_project
```

Создаётся/находится пользователь по `tg_id`, генерируется проект и magic-ссылка входа. Кнопка «Открыть в кабинете» логинит без пароля на 15 минут.

## Persistence

`private/tenants.json`:

```json
[
  {
    "username": "booking_test_bot",
    "template": "booking",
    "brief": {},
    "token": "REPLACE_WITH_TOKEN",
    "owner_tg_id": 0,
    "project": {}
  }
]
```

Токены здесь **не коммитить**. Файл в `.gitignore` через `private/`.

При старте `platform_bot.py` вызывает `restore_tenants()` и поднимает всех.

## Где править тексты

- Приветствие, меню, бриф, прогресс: `telegram_bots/platform_bot.py`.
- Сценарии клиента: `local_practice/engine.py`.
- Шаблоны standalone: `platform/app/template_booking.py`, `template_ai.py`, `template_shop.py`.
- Обложки: `platform/static/covers/*.png`, генератор `scripts/make_*.py`.
- Тексты уроков и ТЗ: `docs/`.

## Безопасность

- Токены ботов — только в `private/telegram-test.env` и `private/tenants.json`.
- Не коммитить `private/`.
- `TELEGRAM_SERVICE_TOKEN` — отдельный секрет для API.
- После теста токены отозвать в BotFather.
- Репозиторий публичный: не вставлять токены в код, тесты, Markdown.


## QA

Полный прогон: [qa/telegram-bots-qa.md](qa/telegram-bots-qa.md). Запуск: `python scripts/qa_bots.py`.
