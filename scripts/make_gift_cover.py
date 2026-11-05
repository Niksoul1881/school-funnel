"""Render gift-for-subscription template cover."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "platform" / "static" / "covers" / "gift.png"
TMP = ROOT / "private" / "cover-render" / "gift.html"

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;width:1200px;height:488px;overflow:hidden}
body{font-family:"Segoe UI",Arial,sans-serif;background:#0d0b12;color:#f6efe4}
.scene{position:relative;width:1200px;height:488px;overflow:hidden;background:
radial-gradient(700px 360px at 85% 15%,rgba(255,122,69,.22),transparent 65%),
radial-gradient(600px 350px at 0% 100%,rgba(255,122,69,.08),transparent 65%),#0d0b12}
.scene:before{content:"";position:absolute;inset:0;background-image:
linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),
linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:40px 40px;
mask-image:linear-gradient(100deg,#000,transparent 78%)}
.brand{position:absolute;left:50px;top:32px;display:flex;gap:9px;align-items:center;font-size:10px;
letter-spacing:.2em;text-transform:uppercase;color:#a29485}
.brand i{width:22px;height:22px;border-radius:6px;background:#ff7a45;display:grid;place-items:center;
color:#0d0b12;font-style:normal;font-weight:900;font-size:8px}
.copy{position:absolute;left:50px;top:100px;width:620px}
.eyebrow{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:#ff7a45;font-weight:800}
h1{margin:14px 0 14px;font-size:68px;line-height:.94;letter-spacing:-.055em;font-weight:800}
h1 em{color:#ff7a45;font-style:normal}
p{margin:0;color:#aa9d8e;font-size:14px;line-height:1.5;width:460px}
.gift{position:absolute;right:72px;top:74px;width:340px;height:340px;border-radius:26px;
background:linear-gradient(160deg,#2a1a17,#151117);border:1px solid rgba(255,122,69,.35);
box-shadow:0 35px 80px rgba(0,0,0,.55);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px}
.box{width:150px;height:120px;position:relative}
.box .lid{position:absolute;left:0;right:0;top:0;height:34px;background:#ff7a45;border-radius:8px}
.box .body{position:absolute;left:12px;right:12px;top:34px;bottom:0;background:#ff9a70;border-radius:0 0 10px 10px}
.box .ribbon{position:absolute;left:50%;top:0;bottom:0;width:16px;margin-left:-8px;background:#0d0b12;opacity:.85}
.box .bow{position:absolute;left:50%;top:-22px;width:60px;height:28px;margin-left:-30px;border:10px solid #ff7a45;border-radius:50%;border-bottom:0}
.gift span{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#c9b8a8}
.pill{position:absolute;left:50px;bottom:34px;display:flex;gap:8px}
.pill b{border:1px solid rgba(255,122,69,.35);background:rgba(255,122,69,.08);color:#ffb08f;border-radius:999px;padding:7px 12px;font-size:10px;font-weight:700}
</style></head><body><div class="scene">
<div class="brand"><i>AI</i> школа AI-агентов · шаблон</div>
<div class="copy"><div class="eyebrow">Telegram-бот · подписка</div>
<h1>Подарок<br><em>за подписку</em></h1>
<p>Человек подписывается на канал, нажимает «Я подписался» — и получает гайд, промокод или файл.</p>
</div>
<div class="gift"><div class="box"><div class="bow"></div><div class="lid"></div><div class="body"></div><div class="ribbon"></div></div><span>ваш подарок</span></div>
</div></body></html>"""


def main() -> None:
    TMP.parent.mkdir(parents=True, exist_ok=True)
    TMP.write_text(HTML, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 488}, device_scale_factor=1.5)
        page.goto(TMP.as_uri(), wait_until="load")
        page.screenshot(path=str(OUT))
        browser.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()

