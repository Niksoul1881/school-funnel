# school-funnel

Маркетинг онлайн-школы: разбор конкурентов, воронка (статьи, бот, тест-драйв), контент для канала и программа курса.

## Структура

```
docs/                 готовые страницы (открывать в браузере)
  research/           конкуренты, контент-план по их каналам, проверка статей, инструкция по ботам
  funnel/             статьи воронки, сообщения бота, шаблоны ботов для конструктора
  content/            стратегия канала, посты (канал Егора — 10 постов, Манекен — 55)
  course/             программа курса и каталог проектов
  final/              утверждённые статьи (v10/v9) и статья 1 v11 без совпадений с конкурентами
  strategy/           концепция школы и платформы: презентация, статья, архитектура, роудмап
  mvp/                план MVP платформы и скриншоты
platform/             код MVP: FastAPI + SQLite + SPA, запуск на 127.0.0.1:8000
sources/              исходники в Markdown, из которых собраны страницы
  research/           полные отчёты по каналам конкурентов и образцы их лучших постов
  funnel/             тексты статей и бота
  content/            посты и брифы для авторов
data/
  competitors/telegram/            выгрузки каналов конкурентов (JSON)
  competitors/articles_and_lessons статьи, уроки и страницы конкурентов (текст)
  competitors/transcripts/         расшифровки видео-уроков Паутова
  db/school.sqlite                 всё выше в одной базе
scripts/              сборка страниц, выгрузка каналов, публикация в Telegram, сборка базы
private/              НЕ в GitHub: анкеты лидов, выгрузки чатов, ключи
```

## База данных — `data/db/school.sqlite`

| Таблица | Что внутри |
|---|---|
| `channels` | 10 каналов: чей, название, подписчики, описание |
| `posts` | 4 199 постов конкурентов и Манекена: дата, просмотры, текст, ссылки |
| `competitor_texts` | 53 текста: статьи, уроки, страницы, расшифровки видео |
| `our_content` | 328 наших блоков и постов из `sources/` |

Примеры запросов (DB Browser for SQLite или `sqlite3`):

```sql
-- 20 самых просматриваемых постов Пурвиньша
SELECT post_id, date, views, substr(text,1,120) FROM posts
WHERE channel='million_on_freelance' ORDER BY views DESC LIMIT 20;

-- все посты конкурентов, где упоминается MAX
SELECT channel, date, substr(text,1,150) FROM posts WHERE text LIKE '%MAX%';
```

Пересобрать базу после изменений: `python scripts/build_db.py`.

## Личные данные

Анкеты лидов (`private/leads/`: xlsx, разбор, `leads.sqlite`) и выгрузки переписок с ботами конкурентов лежат в `private/`. Папка в `.gitignore` и в GitHub не уходит. Репозиторий всё равно держим **приватным**.

Ключи ботов не храним в репозитории. Ключ @manekken_bot, который светился в переписке, стоит перевыпустить в @BotFather командой /revoke.

## Как пересобрать страницы

Скрипты в `scripts/` собирают HTML из Markdown в `sources/` по шаблонам в `scripts/templates/`. Пример:

```
python scripts/build_mk.py scripts/templates/eg_template.html docs/content/egor_10_posts.html sources/content/eg10.md
```

## Видео уроков (монтаж записи Егора)

Готовые ролики — `docs/course/video/`. Собираются так: слева слайды 1200×1080 (стиль колоды v2), справа Егор 720×1080, снизу субтитры по словам, общий/крупный план чередуется по склейкам.

| Скрипт | Что делает |
|---|---|
| `scripts/transcribe_video.py <папка с .MOV> <папка работы>` | whisper с таймкодами **слов** → `<дубль>.wav.seg.json`. Веса качаются в `private/models/whisper` (в `~/.cache` может не быть прав). |
| `scripts/video_transcript.py <папка работы> [--full]` | сводная расшифровка в `transcript.md` — по ней выбираются дубли и резы |
| `scripts/build_video_intro_v3.py` | вводный урок, часть 1 (приветствие, ценность, анкета, 48 часов, правила) |
| `scripts/build_video_intro_v4.py` | вводный урок, часть 2 (пять причин, кому это нужно, шесть уроков, анкета) |
| `scripts/build_video_intro_v5.py` | вводный урок **целиком**, блоки в порядке утверждённого скрипта (`sources/course/вводный_модуль_скрипт.md`) |
| `scripts/build_intro_script_page.py` | страница со скриптом → `docs/course/вводный_модуль_скрипт.html` |
| `scripts/video_cutlist.py <папка работы>` | монтажный лист в человекочитаемом виде (`cutlist.md`) |

Механика одна и переиспользуется: v4 импортирует v3 и переопределяет только `CUTS` (монтажный лист),
`TIMELINE` (какой слайд с какой секунды), тексты слайдов и `WFIX`/`LINE_FIX` (правки ослышек whisper).
v5 пересобирает блоки в один ролик по порядку скрипта и дорисовывает только свои новые слайды
(`--render-extra`). Новый урок = копия такого файла со своими `CUTS`/`TIMELINE`/слайдами.

Дубли вводного лежат в двух папках (`Курс\Вводный\1` — 28.10, `2` — 30.10), а монтаж ищет все дубли в
одной. Поэтому нужные 15 файлов сведены в `private/video_src_all` (копия ~300 МБ, в git не идёт:
хардлинки на файлы вне воркспейса песочница не разрешает). Для нового урока — та же схема: собрать
нужные дубли в одну папку.

```
python scripts/transcribe_video.py "C:\Users\NikSouk\Desktop\Курс\Вводный\2" private/video_work_v4
python scripts/video_transcript.py private/video_work_v4
python scripts/build_video_intro_v4.py                # слайды + сборка
python scripts/build_video_intro_v4.py --slides-only   # только перерисовать слайды
python scripts/build_video_intro_v4.py --no-render     # только пересобрать видео из готовых PNG
```

Важно: отрисовка слайдов поднимает Chromium через playwright, а он **не запускается под песочницей DSH**
(падает на named pipe). Поэтому `--slides-only` / первый запуск нужно делать с полными правами,
а сам монтаж (`--no-render`) спокойно идёт в песочнице. Громкость на выходе — −16 LUFS, true peak −1.5 dB.

## Стратегия школы и платформы

Концепция школы AI-агентов и платформы запуска: ученик заходит в браузер, собирает бота, агента или мини-апп по брифу и запускает в Telegram — без установки, VPN и API-ключей. Внутри — воронка, программа, архитектура на DeepSeek Harness, шаблоны из наших проектов, экономика и роудмап.

| Что | Где |
|---|---|
| Презентация, 22 слайда | [`docs/strategy/index.html`](docs/strategy/index.html) |
| Презентация в PDF | [`docs/strategy/school-ai-agents-concept.pdf`](docs/strategy/school-ai-agents-concept.pdf) |
| Полный документ | [`docs/strategy/koncepciya.md`](docs/strategy/koncepciya.md) |
| Статья в PDF | [`docs/strategy/school-ai-agents-concept-article.pdf`](docs/strategy/school-ai-agents-concept-article.pdf) |
| Инвентаризация проектов | [`data/templates_inventory.json`](data/templates_inventory.json) |

Коротко: курс 49,9–129,9 тыс. ₽, токены 390 ₽ за 1 млн (пакеты 1/5/10 млн), хостинг 490–690 ₽/мес; первый платный поток — январь 2027. Решения, которые нужны от команды, — в конце презентации и в `docs/strategy/README.md`.

## Платформа (MVP)

Рабочий вертикальный срез платформы лежит в [`platform/`](platform): вход, 7 шаблонов, бриф, проект с файлами, чат с агентом, превью, деплой по токену, токенный баланс, уроки и админка. Можно **открыть свою папку с диска** и работать с деревом файлов и AI-помощником. Интерфейс — VS Code-workbench в светлой дружелюбной теме (тёмная — переключателем).

**Живая демо-ссылка:** https://school.91-184-242-178.sslip.io:8443 (Basic Auth `demo` / `school2026`; внутри — `demo@school.local` / `demo1234`). Это постоянный деплой на нашем сервере: Docker-контейнер + Caddy + HTTPS, данные в `/opt/school-platform/data`.

```powershell
cd platform
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Открыть [http://127.0.0.1:8000](http://127.0.0.1:8000). Демо: `demo@school.local` / `demo1234`.

Документация MVP: [`docs/mvp/README.md`](docs/mvp/README.md) · план: [`docs/mvp/plan.md`](docs/mvp/plan.md) · скриншоты: [`docs/mvp/screenshots`](docs/mvp/screenshots).

## Что дальше

- [ ] Пройти ботов конкурентов и выгрузить чаты — `docs/research/как_пройти_ботов_конкурентов.md`
- [ ] Утвердить статью 1 v11 или вернуть v10 после правок (`docs/research/articles_final_review.html`)
- [ ] Заполнить реальные данные в постах и статьях: [скобки]
- [ ] Решить с каналом: новый канал Егора или переименование Манекена
- [ ] Утвердить решения по школе и платформе: бренд, цены, доступ к API, юрлицо, хостинг, первый поток (`docs/strategy/README.md`)
- [ ] Платформа: DSH уже включён; нужен тестовый токен бота и 24/7-рантайм (`docs/mvp/plan.md`)
