# Деплой MVP

## Постоянный деплой (сделан)

- URL: **https://school.91-184-242-178.sslip.io:8443**
- Basic Auth: `demo` / `school2026`
- Внутри платформы: `demo@school.local` / `demo1234`
- Сервер: `91.184.242.178`, Ubuntu 24.04, 4 vCPU (Ryzen 9), 8 ГБ RAM, 65 ГБ свободно.
- Контейнер: `school-platform`, лимит 512 МБ / 1 CPU, `--restart unless-stopped`.
- Данные: `/opt/school-platform/data/platform.db` (volume `/data`).
- Caddy: site `school.91-184-242-178.sslip.io:8443` → `127.0.0.1:8000`, сертификат Let's Encrypt получен.
- Порт 443 занят xray, поэтому Caddy слушает 8443. Позже можно повесить свой домен на 443.

Проверка:

```bash
ssh -i ~/.ssh/hogita_server root@91.184.242.178
docker ps --filter name=school-platform
curl -s http://127.0.0.1:8000/api/health
docker logs --tail 50 school-platform
```

Обновление после правок:

```powershell
# с этой машины
scp -r platform\app platform\static platform\requirements.txt platform\Dockerfile root@91.184.242.178:/opt/school-platform/
ssh -i $env:USERPROFILE\.ssh\hogita_server root@91.184.242.178 "cd /opt/school-platform && docker build -t school-agents-mvp:latest . && docker rm -f school-platform; docker run -d --name school-platform --restart unless-stopped --memory=512m --cpus=1 -p 127.0.0.1:8000:8000 -v /opt/school-platform/data:/data --env-file /opt/school-platform/.env school-agents-mvp:latest"
```

Важно: на сервере уже работают Hogita, Lizy, Kvasich и Postgres. Наш контейнер лёгкий (66 МБ), но **не запускайте тяжёлые агентные сессии** без отдельного лимита — свободно ~3 ГБ, load бывает высоким.

## Локальный туннель (резерв)

Если нужно показать с этой машины без сервера:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.\tunnel.ps1
```

Появится `https://<id>.lhr.life`. Это временно; для демо используйте сервер выше.

## Вариант A: VPS + Docker + домен (рекомендую)

Нужен любой VPS с Docker: Timeweb, Beget, Hetzner, Selectel. Минимум 2 ГБ RAM.

```bash
# на сервере
git clone <repo> school
cd school/platform
cp .env.example .env
# отредактируйте .env: SECRET_KEY, DEMO_PASSWORD, AGENT_MODE=mock
docker compose up -d --build
```

Приложение слушает `127.0.0.1:8000`. Дальше — Caddy/Nginx с HTTPS:

> Если `docker build` падает с `403 Forbidden` на `registry-1.docker.io` (бывает из РФ), используйте зеркало Docker Hub или соберите образ на VPS/в CI с доступом. Сам Dockerfile от этого не зависит.

```caddyfile
demo.example.com {
    encode gzip
    reverse_proxy 127.0.0.1:8000
}
```

Caddy сам получит сертификат. Для закрытого демо оставьте `DEMO_PASSWORD` — весь сайт будет за Basic Auth.

Данные SQLite лежат в `platform/data/platform.db` (в контейнере — `/data`). Для бэкапа достаточно копировать файл.

## Вариант B: Render

1. Запушьте репозиторий в GitHub.
2. В Render: **New → Blueprint**, выберите репозиторий.
3. Render прочитает `render.yaml`, создаст сервис и диск `/data`.
4. В Environment добавьте `DEMO_PASSWORD`.
5. После деплоя откройте выданный `onrender.com` URL.

`starter` с диском — платный; на free-плане диск не сохраняется, база будет сбрасываться при деплое.

## Вариант C: любой Docker-хостинг

Подойдёт Fly.io, Railway, Koyeb, Cloud Run (с оговоркой про SQLite). Соберите образ:

```bash
docker build -t school-agents-mvp .
docker run -p 8000:8000 -v school_data:/data \
  -e SECRET_KEY=... -e DEMO_PASSWORD=... school-agents-mvp
```

## Переменные

| Переменная | Зачем |
|---|---|
| `SECRET_KEY` | cookie и шифрование токенов. Обязательно свой. |
| `DEMO_PASSWORD` | закрывает весь сайт Basic Auth. Для публичного демо — да. |
| `DEMO_USER` | логин Basic Auth, по умолчанию `demo`. |
| `AGENT_MODE` | `mock` без затрат, `dsh` для реального агента. |
| `DEEPSEEK_API_KEY` | нужен для `AGENT_MODE=dsh`. |
| `DATA_DIR` | где лежит SQLite. В Docker — `/data`. |

## Что учесть перед продом

- SQLite — только для MVP. Для нескольких воркеров/нагрузки — Postgres.
- HTTPS обязателен: cookie сессии и токены ботов.
- `DEMO_PASSWORD` не равен паролю ученика. Это два разных уровня.
- Смените демо-пароль и админский пароль перед публичным запуском.
- Не храните `.env` и `data/` в git.
- 24/7-рантайм ботов пока не включён: деплой проверяет токен и пишет статус.

