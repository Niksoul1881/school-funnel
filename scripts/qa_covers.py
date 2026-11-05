"""Render cover contact sheet for QA report."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "qa" / "covers.png"
TMP = ROOT / "private" / "cover-render" / "qa-covers.html"
covers = [("booking", "Запись к мастеру"), ("gift", "Подарок за подписку"), ("shop", "Витрина товаров")]
cards = "".join(
    f'<figure><img src="{(ROOT / "platform" / "static" / "covers" / (key + ".png")).as_uri()}"><figcaption>{name}</figcaption></figure>'
    for key, name in covers
)
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b0c10;color:#fff;font-family:"Segoe UI",Arial,sans-serif}}
.wrap{{padding:28px 28px 24px}}h1{{font-size:22px;margin:0 0 4px;letter-spacing:-.02em}}
p{{margin:0 0 20px;color:#8f93a3;font-size:12px}}main{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
figure{{margin:0;background:#14161d;border:1px solid #252936;border-radius:16px;overflow:hidden}}
img{{display:block;width:100%;height:auto;aspect-ratio:1200/488;object-fit:cover}}
figcaption{{padding:11px 14px;font-size:13px;font-weight:700;color:#e9e5dd}}
</style></head><body><div class="wrap"><h1>Обложки шаблонов</h1><p>3 активных сценария · web PNG, 1200×488</p><main>{cards}</main></div></body></html>"""
TMP.parent.mkdir(parents=True, exist_ok=True)
TMP.write_text(html, encoding="utf-8")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 700}, device_scale_factor=1)
    page.goto(TMP.as_uri(), wait_until="load")
    page.screenshot(path=str(OUT), full_page=True)
    browser.close()
print("wrote", OUT)
