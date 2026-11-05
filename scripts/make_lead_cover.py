"""Render lead-request template cover."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "platform" / "static" / "covers" / "lead.png"
TMP = ROOT / "private" / "cover-render" / "lead.html"

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;width:1200px;height:488px;overflow:hidden}
body{font-family:"Segoe UI",Arial,sans-serif;background:#0c0d11;color:#f6efe4}
.scene{position:relative;width:1200px;height:488px;overflow:hidden;background:
radial-gradient(650px 350px at 10% 0%,rgba(62,199,255,.22),transparent 65%),
radial-gradient(600px 350px at 100% 100%,rgba(62,199,255,.08),transparent 65%),#0c0d11}
.scene:before{content:"";position:absolute;inset:0;background-image:
linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),
linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:40px 40px;
mask-image:linear-gradient(100deg,#000,transparent 75%)}
.brand{position:absolute;left:50px;top:32px;display:flex;gap:9px;align-items:center;font-size:10px;
letter-spacing:.2em;text-transform:uppercase;color:#a29485}
.brand i{width:22px;height:22px;border-radius:6px;background:#3ec7ff;display:grid;place-items:center;
color:#0c0d11;font-style:normal;font-weight:900;font-size:8px}
.copy{position:absolute;left:50px;top:108px;width:560px}
.eyebrow{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:#3ec7ff;font-weight:800}
h1{margin:14px 0 12px;font-size:74px;line-height:.93;letter-spacing:-.055em;font-weight:800}
h1 em{color:#3ec7ff;font-style:normal}
p{margin:0;color:#aa9d8e;font-size:14px;line-height:1.5;width:440px}
.bottom{position:absolute;left:50px;bottom:30px;display:flex;gap:8px}
.chip{border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.04);color:#c8bbac;border-radius:999px;padding:7px 11px;font-size:10px}
.chip b{color:#3ec7ff}
.form{position:absolute;right:46px;top:54px;width:470px;border:1px solid rgba(255,255,255,.14);border-radius:22px;
background:linear-gradient(160deg,#1c222b,#12151b);box-shadow:0 30px 70px rgba(0,0,0,.5);padding:22px}
.form h3{margin:0 0 16px;font-size:17px}
.row{display:flex;align-items:center;gap:10px;border:1px solid rgba(255,255,255,.1);border-radius:11px;padding:12px 13px;margin-bottom:9px;color:#9d9184;font-size:12px}
.row b{width:24px;height:24px;border-radius:50%;background:rgba(62,199,255,.16);color:#3ec7ff;display:grid;place-items:center;font-size:11px}
.row.done{color:#e6ddd1;border-color:rgba(62,199,255,.4)}
.btn{margin-top:12px;background:#3ec7ff;color:#0b1116;border-radius:10px;text-align:center;padding:12px;font-size:11px;font-weight:900}
.tag{position:absolute;left:50px;top:430px;color:#6f655b;font-size:9px;letter-spacing:.18em;text-transform:uppercase}
.tag b{color:#a99c8e}
</style></head><body><div class="scene">
<div class="brand"><i>AI</i> школа AI-агентов · шаблон</div>
<div class="copy"><div class="eyebrow">Telegram-бот · заявка</div>
<h1>Заявка<br><em>на услугу</em></h1>
<p>Клиент оставляет имя и телефон. Заявка сразу приходит владельцу — без потерянных сообщений.</p>
</div>
<div class="form"><h3>Новая заявка</h3>
<div class="row done"><b>1</b> Что нужно · Монтаж</div>
<div class="row done"><b>2</b> Имя · Никита</div>
<div class="row"><b>3</b> Телефон · +7 ...</div>
<div class="btn">Отправить заявку</div></div>

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

