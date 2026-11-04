# Три Telegram-бота для теста

## 1. Создай три бота

В Telegram открой **@BotFather** → `/newbot` три раза:

```text
booking_test_твой_ник_bot
ai_test_твой_ник_bot
shop_test_твой_ник_bot
```

## 2. Заполни токены

Открой:

```text
private/telegram-test.env
```

Вставь:

```env
BOOKING_BOT_TOKEN=...
AI_BOT_TOKEN=...
SHOP_BOT_TOKEN=...
OWNER_TG_ID=...
```

`OWNER_TG_ID` — твой ID из **@userinfobot**. Туда будут приходить записи и заказы.

`LLM_API_KEY` можно оставить пустым — AI-бот будет отвечать по FAQ. С ключом он отвечает через нейросеть.

## 3. Запусти

Из корня `school-funnel`:

```powershell
python telegram_bots\launch.py
```

Скрипт:

- проверит каждый токен через Telegram `getMe`;
- сгенерирует три проекта в `telegram_bots/runtime/`;
- запустит три процесса с polling;
- напишет логи в `telegram_bots/launch.log`.

## 4. Проверь

Открой каждого бота и нажми `/start`:

- **booking** — выбери услугу, имя, телефон, дату, время;
- **ai** — спроси «А если я опоздаю на 15 минут?»;
- **shop** — открой товар, добавь в корзину, оформи заказ.

Заявка/заказ придут тебе в Telegram от имени соответствующего бота.

## Остановить

`Ctrl+C` в окне запуска.

## Важно

- Это polling, без вебхуков — для локального теста.
- Токены лежат в `private/`, в git не попадают.
- После теста отзови токены в BotFather.
