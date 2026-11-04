# MVP платформы

Рабочий вертикальный срез: вход → шаблон → бриф → проект → чат с агентом → превью → деплой.

**Живая демо-ссылка:** https://school.91-184-242-178.sslip.io:8443
Вход в демо: `demo@school.local` / `demo1234`

Это постоянный деплой на сервере (Docker + Caddy + HTTPS). Обновление и инфраструктура: [`../../platform/deploy/README.md`](../../platform/deploy/README.md).

Интерфейс — VS Code-workbench в светлой дружелюбной теме: activity bar, дерево проекта с папками и иконками типов файлов, вкладки, редактор с номерами строк, правая панель AI-помощника/превью, терминал и статус-бар. Тёмная тема — переключателем.

- Код: [`platform/`](../../platform)
- План и границы: [`plan.md`](plan.md)
- Скриншоты: [`screenshots/`](screenshots)
- Как запустить: [`platform/README.md`](../../platform/README.md)

## Что открыть

```powershell
cd platform
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Открыть [http://127.0.0.1:8000](http://127.0.0.1:8000).

Демо: кнопка «Посмотреть демо». Админские доступы не публикуются.

## Скриншоты

| Экран | Файл |
|---|---|
| Вход | [`01_login.png`](screenshots/01_login.png) |
| Новый вход: hero + визуал | [`49_auth_new.png`](screenshots/49_auth_new.png) |
| Вход на мобильном | [`50_auth_mobile.png`](screenshots/50_auth_mobile.png) |
| Рабочая область | [`02_dashboard.png`](screenshots/02_dashboard.png) |
| Шаблоны | [`03_templates.png`](screenshots/03_templates.png) |
| Бриф | [`04_brief.png`](screenshots/04_brief.png) |
| Проект | [`05_project.png`](screenshots/05_project.png) |
| Чат с агентом | [`06_chat.png`](screenshots/06_chat.png) |
| Деплой | [`07_deploy.png`](screenshots/07_deploy.png) |
| Уроки | [`08_lessons.png`](screenshots/08_lessons.png) |
| Токены и счётчик | [`09_billing.png`](screenshots/09_billing.png) |
| Админка: токены и маржа | [`10_admin.png`](screenshots/10_admin.png) |
| Мини-апп | [`11_miniapp.png`](screenshots/11_miniapp.png) |
| Telegram-превью | [`12_telegram_click.png`](screenshots/12_telegram_click.png) |
| Постоянный сервер, HTTPS | [`14_server_public.png`](screenshots/14_server_public.png) |
| Своя папка с диска | [`28_imported.png`](screenshots/28_imported.png) |
| DSH создаёт файл | [`41_real_dsh.png`](screenshots/41_real_dsh.png) |
| Python-подсветка | [`42_python_diag.png`](screenshots/42_python_diag.png) |
| Профиль ученика | [`43_profile.png`](screenshots/43_profile.png) |
| Аналитика по людям | [`44_admin_analytics.png`](screenshots/44_admin_analytics.png) |
| Карточка пользователя | [`45_user_detail.png`](screenshots/45_user_detail.png) |
| Рабочее окно: ресайз, шаги, голос | [`46_workspace_improved.png`](screenshots/46_workspace_improved.png) |
| Живые шаги агента | [`48_live_steps.png`](screenshots/48_live_steps.png) |
| Файловый менеджер и меню | [`53_file_manager.png`](screenshots/53_file_manager.png) |
| Чистый блок проектов | [`54_projects_sidebar.png`](screenshots/54_projects_sidebar.png) |
| Живой терминал проекта | [`55_terminal.png`](screenshots/55_terminal.png) |
| Запуск проекта одной кнопкой | [`56_terminal_run.png`](screenshots/56_terminal_run.png) |
| Три шаблона | [`63_templates_three.png`](screenshots/63_templates_three.png) |
| Витрина товаров | [`64_shop_preview.png`](screenshots/64_shop_preview.png) |
| Витрина с фото | [`65_shop_images.png`](screenshots/65_shop_images.png) |
| Обложки шаблонов | [`71_templates_editorial.png`](screenshots/71_templates_editorial.png) |
| Бот-витрина в превью | [`68_shop_bot_preview.png`](screenshots/68_shop_bot_preview.png) |
| AI-консультант отвечает | [`69_ai_consultant_preview.png`](screenshots/69_ai_consultant_preview.png) |
| Локальный стенд практики | [`72_local_practice.png`](screenshots/72_local_practice.png) |
| Локальный AI-бот | [`73_local_ai.png`](screenshots/73_local_ai.png) |
| Локальная витрина | [`74_local_shop.png`](screenshots/74_local_shop.png) |
| Бриф в конструкторе | [`75_local_brief.png`](screenshots/75_local_brief.png) |

## Что дальше

1. DSH-агент включён: создаёт/меняет файлы, списывает фактический usage.
2. Реальный деплой бота: нужен тестовый токен из @BotFather (сервер уже есть).
3. Платежи и пакеты токенов.



