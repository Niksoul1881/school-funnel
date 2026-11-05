"""Visual QA: public practice stand and landing screenshots."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "qa"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://school.91-184-242-178.sslip.io:8443"

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--ignore-certificate-errors"])
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page.goto(f"{BASE}/practice", wait_until="networkidle")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT / "practice.png"), full_page=True)
    cards = page.locator("[data-template]").count()
    print("practice cards", cards)
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "landing.png"), full_page=True)
    print("title", page.title())
    browser.close()
