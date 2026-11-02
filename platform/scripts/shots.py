import httpx
from playwright.sync_api import sync_playwright

out = r"C:\Users\NikSouk\Desktop\Proj\school-funnel\docs\mvp\screenshots"
base = "https://school.91-184-242-178.sslip.io:8443"

# Демо «своя папка»: создаём через API, чтобы на скриншотах был импортированный проект.
api = httpx.Client(base_url=base, timeout=30, auth=("demo", "school2026"))
api.post("/api/auth/login", json={"email": "demo@school.local", "password": "demo1234"})
imported = api.post("/api/projects/import", json={
    "name": "Моя папка",
    "files": [
        {"path": "main.py", "content": "def main():\n    print('Привет из моего проекта')\n\nif __name__ == '__main__':\n    main()\n"},
        {"path": "src/app.js", "content": "const app = document.getElementById('app');\napp.textContent = 'Мой проект';\n"},
        {"path": "README.md", "content": "# Моя папка\n\nНебольшой проект, который я открыл в платформе.\n"},
    ],
}).json()
imported_id = imported.get("id")
api.post("/api/billing/topup", json={"package_id": "start"})
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        device_scale_factor=1,
        http_credentials={"username": "demo", "password": "school2026"},
    )
    page = ctx.new_page()
    page.on("console", lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
    page.goto(base, wait_until="networkidle", timeout=60000)
    page.screenshot(path=out + r"\01_login.png")
    page.fill('input[name="email"]', "demo@school.local")
    page.fill('input[name="password"]', "demo1234")
    page.click('#auth-form button[type="submit"]')
    page.wait_for_selector(".vsc", timeout=20000)
    page.wait_for_timeout(900)
    page.screenshot(path=out + r"\02_dashboard.png")
    page.click('.vsc-sidebar [data-go="#/templates"]')
    page.wait_for_selector(".template-card", timeout=10000)
    page.wait_for_timeout(400)
    page.screenshot(path=out + r"\03_templates.png")
    page.click('button[data-go^="#/new/"]')
    page.wait_for_selector("#brief-form", timeout=10000)
    page.wait_for_timeout(400)
    page.screenshot(path=out + r"\04_brief.png")
    page.goto(base + "/#/project/1", wait_until="networkidle", timeout=60000)
    page.wait_for_selector(".ide-main", timeout=15000)
    page.wait_for_timeout(700)
    page.screenshot(path=out + r"\05_project.png")
    page.fill("#chat-form textarea", "добавь меню: Услуги, Записаться, Цены, Связаться")
    page.click('#chat-form button[type="submit"]')
    page.wait_for_timeout(1600)
    page.screenshot(path=out + r"\06_chat.png")
    page.click('[data-action="open-deploy"]')
    page.wait_for_selector("#deploy-form", timeout=5000)
    page.wait_for_timeout(300)
    page.screenshot(path=out + r"\07_deploy.png")
    page.click("#deploy-close")
    page.click('.vsc-activity [data-go="#/lessons"]')
    page.wait_for_selector(".lesson-card-v2", timeout=10000)
    page.wait_for_timeout(4500)
    page.screenshot(path=out + r"\08_lessons.png")
    page.click('.vsc-activity [data-go="#/billing"]')
    page.wait_for_selector("table.table", timeout=10000)
    page.wait_for_timeout(400)
    page.screenshot(path=out + r"\09_billing.png")
    page.goto(base + "/#/project/2", wait_until="networkidle", timeout=60000)
    page.click('[data-aux="preview"]')
    page.wait_for_selector(".miniapp-frame", timeout=10000)
    page.wait_for_timeout(900)
    page.screenshot(path=out + r"\11_miniapp.png")
    page.goto(base + "/#/project/1", wait_until="networkidle", timeout=60000)
    page.click('[data-aux="preview"]')
    page.wait_for_selector(".phone", timeout=10000)
    page.wait_for_timeout(500)
    page.click('button[data-tg-action="services"]')
    page.wait_for_timeout(700)
    page.screenshot(path=out + r"\12_telegram_click.png")
    if imported_id:
        page.goto(base + f"/#/project/{imported_id}", wait_until="networkidle", timeout=60000)
        page.wait_for_selector(".ide-main", timeout=10000)
        page.wait_for_timeout(700)
        page.screenshot(path=out + r"\28_imported.png")
    ctx2 = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        http_credentials={"username": "demo", "password": "school2026"},
    )
    page2 = ctx2.new_page()
    page2.goto(base, wait_until="networkidle", timeout=60000)
    page2.fill('input[name="email"]', "admin@school.local")
    page2.fill('input[name="password"]', "admin1234")
    page2.click('#auth-form button[type="submit"]')
    page2.wait_for_selector(".vsc", timeout=20000)
    page2.goto(base + "/#/admin", wait_until="networkidle", timeout=60000)
    page2.wait_for_timeout(900)
    page2.screenshot(path=out + r"\10_admin.png")
    browser.close()
print("errors", [e for e in errors if "401" not in e][:10])
print("done")




