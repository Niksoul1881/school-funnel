"""Render the Lesson 2 hero image for the Telegram platform bot."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
COVERS = ROOT / "platform" / "static" / "covers"
OUT = COVERS / "lesson2.png"
TMP = ROOT / "private" / "cover-render" / "lesson2.html"

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}} html,body{{margin:0;width:1200px;height:488px;overflow:hidden}}
body{{font-family:"Segoe UI",Arial,sans-serif;background:#0c0d11;color:#f6efe4}}
.scene{{position:relative;width:1200px;height:488px;overflow:hidden;background:
radial-gradient(650px 360px at 8% 0%,rgba(255,107,138,.22),transparent 65%),
radial-gradient(600px 360px at 100% 100%,rgba(167,139,250,.12),transparent 65%),#0c0d11}}
.scene:before{{content:"";position:absolute;inset:0;background-image:
linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),
linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:40px 40px;
mask-image:linear-gradient(100deg,#000,transparent 75%)}}
.brand{{position:absolute;left:50px;top:32px;display:flex;gap:9px;align-items:center;font-size:10px;
letter-spacing:.2em;text-transform:uppercase;color:#a29485}}
.brand i{{width:22px;height:22px;border-radius:6px;background:#ff6b8a;display:grid;place-items:center;
color:#100d0b;font-style:normal;font-weight:900;font-size:8px}}
.copy{{position:absolute;left:50px;top:108px;width:530px}}
.eyebrow{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:#ff6b8a;font-weight:800}}
h1{{margin:14px 0 12px;font-size:78px;line-height:.9;letter-spacing:-.06em;font-weight:800}}
h1 em{{color:#ff6b8a;font-style:normal}}
p{{margin:0;color:#aa9d8e;font-size:14px;line-height:1.5;width:400px}}
.steps{{display:flex;gap:8px;margin-top:24px;flex-wrap:wrap}}
.step{{border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.04);border-radius:999px;
padding:7px 11px;color:#c8bbac;font-size:10px}}
.step b{{color:#ff6b8a}}
.cards{{position:absolute;right:44px;top:62px;width:520px;height:370px}}
.card{{position:absolute;width:235px;height:170px;border-radius:16px;overflow:hidden;
border:1px solid rgba(255,255,255,.14);background:#17181e;box-shadow:0 24px 60px rgba(0,0,0,.45)}}
.card img{{width:100%;height:105px;object-fit:cover;display:block}}
.card div{{padding:9px 11px;font-size:11px;font-weight:800}}
.card span{{display:block;font-size:8px;color:#8f8376;margin-top:2px;font-weight:500}}
.c1{{right:250px;top:0;transform:rotate(-4deg)}}
.c2{{right:0;top:58px;transform:rotate(3deg)}}
.c3{{right:150px;top:205px;transform:rotate(-1deg)}}
.tag{{position:absolute;left:50px;bottom:30px;color:#6f655b;font-size:9px;letter-spacing:.18em;text-transform:uppercase}}
.tag b{{color:#a99c8e}}
</style></head><body><div class="scene">
<div class="brand"><i>AI</i> школа AI-агентов · платформа практики</div>
<div class="copy"><div class="eyebrow">Урок 02 · практика</div>
<h1>Чат-<em>боты</em></h1>
<p>Не смотри, как Егор собирает. Собери своего за 5 минут — по шаблону и брифу.</p>
<div class="steps"><span class="step"><b>01</b> шаблон</span><span class="step"><b>02</b> бриф</span><span class="step"><b>03</b> токен</span><span class="step"><b>04</b> бот живой</span></div></div>
<div class="cards">
<div class="card c1"><img src="{(COVERS/'booking.png').as_uri()}"><div>Запись к мастеру<span>услуги · окна · заявки</span></div></div>
<div class="card c2"><img src="{(COVERS/'ai.png').as_uri()}"><div>AI-консультант<span>отвечает по правилам</span></div></div>
<div class="card c3"><img src="{(COVERS/'shop.png').as_uri()}"><div>Витрина товаров<span>фото · корзина · заказ</span></div></div>
</div>
<div class="tag"><b>Платформа практики</b> · первый бот за 5 минут</div>
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
