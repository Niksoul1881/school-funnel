"""Generate bold editorial template covers (1200x488, readable at card size)."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "platform" / "static" / "covers"
TMP = ROOT / "private" / "cover-render"
TMP.mkdir(parents=True, exist_ok=True)

COMMON = r'''
* { box-sizing: border-box; }
html, body { margin: 0; width: 1200px; height: 488px; overflow: hidden; }
body { font-family: "Segoe UI", Arial, sans-serif; background: #0c0d11; color: #f6efe4; }
.scene {
  position: relative; width: 1200px; height: 488px; overflow: hidden;
  background:
    radial-gradient(700px 380px at 8% 10%, var(--glow), transparent 68%),
    radial-gradient(600px 380px at 100% 100%, var(--glow2), transparent 68%),
    #0c0d11;
}
.scene:before {
  content: ""; position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: linear-gradient(100deg, #000, transparent 75%);
}
.scene:after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(120% 100% at 48% 50%, transparent 35%, rgba(0,0,0,.45));
}
.brand {
  position: absolute; left: 50px; top: 32px; display: flex; gap: 9px; align-items: center;
  font-size: 10px; letter-spacing: .2em; text-transform: uppercase; color: #a29485;
}
.brand i {
  width: 22px; height: 22px; border-radius: 6px; background: var(--accent);
  display: grid; place-items: center; color: #100d0b; font-style: normal;
  font-weight: 900; font-size: 8px; letter-spacing: 0;
}
.copy { position: absolute; left: 50px; top: 108px; width: 600px; z-index: 2; }
.eyebrow { font-size: 10px; letter-spacing: .24em; text-transform: uppercase; color: var(--accent); font-weight: 800; }
h1 {
  margin: 14px 0 12px; font-size: 74px; line-height: .93;
  letter-spacing: -.055em; font-weight: 800; color: #f7f1e8; max-width: 620px;
}
h1 em { color: var(--accent); font-style: normal; }
p { margin: 0; color: #aa9d8e; font-size: 14px; line-height: 1.5; width: 430px; }
.bottom { position: absolute; left: 50px; bottom: 30px; display: flex; gap: 8px; align-items: center; }
.chip { border: 1px solid rgba(255,255,255,.14); background: rgba(255,255,255,.04); color: #c8bbac; border-radius: 999px; padding: 7px 11px; font-size: 10px; }
.chip b { color: var(--accent); }
.art { position: absolute; right: 46px; top: 36px; width: 500px; height: 416px; z-index: 3; }
.art:before {
  content: ""; position: absolute; width: 380px; height: 380px; border-radius: 50%;
  right: -20px; top: 0; background: var(--glow); filter: blur(10px);
}

/* booking */
.cal {
  position: absolute; right: 14px; top: 18px; width: 355px; border-radius: 22px;
  border: 1px solid rgba(255,255,255,.14); background: linear-gradient(160deg,#22232a,#14151a);
  box-shadow: 0 30px 70px rgba(0,0,0,.5); padding: 20px;
}
.cal-top { display: flex; justify-content: space-between; color: #a99c8e; font-size: 10px; letter-spacing: .16em; text-transform: uppercase; }
.cal-top b { color: var(--accent); }
.cal-day { font-size: 100px; line-height: .9; font-weight: 800; letter-spacing: -.07em; margin: 16px 0 10px; }
.cal-day small { font-size: 22px; letter-spacing: 0; color: #8e8276; font-weight: 600; margin-left: 5px; }
.cal-slots { display: flex; gap: 7px; }
.cal-slots span { border: 1px solid rgba(255,255,255,.12); border-radius: 8px; color: #91857a; padding: 8px 11px; font-size: 11px; }
.cal-slots b { border: 1px solid var(--accent); background: var(--accent); color: #1b1013; border-radius: 8px; padding: 8px 13px; font-size: 11px; }
.cal-btn { margin-top: 12px; background: var(--accent); color: #1b1013; border-radius: 10px; text-align: center; padding: 12px; font-size: 11px; font-weight: 900; }

/* ai */
.orb {
  position: absolute; right: 54px; top: 36px; width: 116px; height: 116px; border-radius: 50%;
  background: radial-gradient(circle at 30% 25%, #d7c6ff, var(--accent) 45%, #4c1d95 100%);
  box-shadow: 0 0 60px var(--glow), 0 20px 50px rgba(0,0,0,.35);
  display: grid; place-items: center; font-size: 36px; font-weight: 900; color: #1a1028;
}
.q { position: absolute; right: 34px; top: 174px; width: 390px; background: #a78bfa; color: #1b1224; border-radius: 16px 16px 16px 5px; padding: 15px 17px; font-size: 17px; font-weight: 700; line-height: 1.25; }
.a { position: absolute; right: 76px; top: 254px; width: 390px; background: #1d1e24; border: 1px solid rgba(167,139,250,.35); color: #ddd4c8; border-radius: 16px 16px 5px 16px; padding: 15px 17px; font-size: 16px; line-height: 1.35; }
.a b { color: #c4b5fd; }
.note { position: absolute; right: 80px; top: 360px; color: #8d8175; font-size: 10px; letter-spacing: .08em; }
.note b { color: #a78bfa; }

/* shop */
.shop-card {
  position: absolute; right: 54px; top: 22px; width: 330px; border-radius: 22px; overflow: hidden;
  border: 1px solid rgba(255,255,255,.15); background: #1a1a20; box-shadow: 0 30px 70px rgba(0,0,0,.5);
}
.shop-card .img { height: 230px; overflow: hidden; background: #2b1d18; }
.shop-card img { width: 100%; height: 100%; object-fit: cover; display: block; }
.shop-meta { padding: 14px 16px 16px; }
.shop-meta .row { display: flex; justify-content: space-between; align-items: baseline; }
.shop-meta b { font-size: 17px; }
.shop-meta span { color: var(--accent); font-weight: 900; font-size: 15px; }
.shop-meta small { display: block; margin-top: 4px; color: #8d8175; font-size: 10px; }
.mini {
  position: absolute; right: 404px; top: 290px; width: 210px; border-radius: 17px; overflow: hidden;
  border: 1px solid rgba(231,160,111,.45); background: #1a1a20; box-shadow: 0 20px 50px rgba(0,0,0,.45);
}
.mini img { width: 100%; height: 110px; object-fit: cover; display: block; }
.mini div { padding: 10px 12px; font-size: 11px; font-weight: 800; display: flex; justify-content: space-between; }
.mini span { color: var(--accent); }
'''

BOOKING = r'''
<div class="scene" style="--accent:#ff6b8a;--glow:rgba(255,80,120,.24);--glow2:rgba(255,170,110,.07)">
  <div class="brand"><i>AI</i> школа AI-агентов · шаблон</div>
  <div class="copy">
    <div class="eyebrow">Telegram-бот · запись</div>
    <h1>Запись<br>к <em>мастеру</em></h1>
    <p>Клиент выбирает услугу и время. Заявка сразу приходит мастеру.</p>
  </div>
  <div class="bottom"><span class="chip"><b>24/7</b> без администратора</span><span class="chip">0 звонков</span><span class="chip">SQLite</span></div>
  <div class="art">
    <div class="cal">
      <div class="cal-top"><span>ноябрь</span><b>свободно</b></div>
      <div class="cal-day">12<small>сб</small></div>
      <div class="cal-slots"><span>10:00</span><b>12:00</b><span>14:00</span></div>
      <div class="cal-btn">Подтвердить запись</div>
    </div>
  </div>
</div>
'''

AI = r'''
<div class="scene" style="--accent:#a78bfa;--glow:rgba(139,92,246,.26);--glow2:rgba(62,199,255,.07)">
  <div class="brand"><i>AI</i> школа AI-агентов · шаблон</div>
  <div class="copy">
    <div class="eyebrow">AI-консультант · LLM</div>
    <h1>Отвечает<br><em>по вашим</em><br>правилам</h1>
    <p>Не кнопки, а живой ответ по тексту о бизнесе. Не знает — зовёт человека.</p>
  </div>
  <div class="bottom"><span class="chip"><b>вау</b> вместо кнопок</span><span class="chip">знает цены</span><span class="chip">handoff</span></div>
  <div class="art">
    <div class="orb">AI</div>
    <div class="q">А если я опоздаю на 15 минут?</div>
    <div class="a">Если опоздание больше 15 минут — перенесём запись. <b>Без штрафа.</b></div>
    <div class="note"><b>●</b> отвечает по knowledge.md</div>
  </div>
</div>
'''

SHOP = r'''
<div class="scene" style="--accent:#e7a06f;--glow:rgba(201,130,91,.26);--glow2:rgba(255,196,120,.07)">
  <div class="brand"><i>AI</i> школа AI-агентов · шаблон</div>
  <div class="copy">
    <div class="eyebrow">Telegram-бот · витрина</div>
    <h1>Витрина<br><em>в чате</em></h1>
    <p>Фото, корзина и заказ. Клиент покупает в Telegram — без сайта.</p>
  </div>
  <div class="bottom"><span class="chip"><b>фото</b> товаров</span><span class="chip">корзина</span><span class="chip">заказ админу</span></div>
  <div class="art">
    <div class="shop-card">
      <div class="img"><img src="__CAKE__" alt=""></div>
      <div class="shop-meta"><div class="row"><b>Медовик</b><span>3 200 ₽</span></div><small>медовые коржи · сметанный крем</small></div>
    </div>
    <div class="mini"><img src="__PEONY__" alt=""><div>Пионы <span>4 500 ₽</span></div></div>
  </div>
</div>
'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 488}, device_scale_factor=1.5)
        for name, body in (("booking", BOOKING), ("ai", AI), ("shop", SHOP)):
            body = body.replace("__CAKE__", (OUT / "shop.jpg").as_uri()).replace("__PEONY__", (OUT / "shop-peony.jpg").as_uri())
            html = f"<!doctype html><html><head><meta charset='utf-8'><style>{COMMON}</style></head><body>{body}</body></html>"
            tmp = TMP / f"{name}.html"
            tmp.write_text(html, encoding="utf-8")
            page.goto(tmp.as_uri(), wait_until="load")
            page.screenshot(path=str(OUT / f"{name}.png"))
            print("wrote", OUT / f"{name}.png")
        browser.close()


if __name__ == "__main__":
    main()
