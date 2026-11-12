"""Render BotFather step screenshots for the practice lesson."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "platform" / "static" / "lessons"
OUT.mkdir(parents=True, exist_ok=True)

STEPS = [
    ("botfather-1", "1", "Открой BotFather", "В Telegram нажми на поиск и введи <b>@BotFather</b>. Открой официального бота с галочкой.", "search"),
    ("botfather-2", "2", "Отправь /newbot", "В чате с BotFather отправь команду <b>/newbot</b>. Он попросит имя будущего бота.", "command"),
    ("botfather-3", "3", "Придумай имя", "Напиши понятное имя, например <b>Мой первый бот</b>. Его увидят пользователи.", "name"),
    ("botfather-4", "4", "Придумай username", "Username должен заканчиваться на <b>_bot</b>. Например: <b>my_first_school_bot</b>.", "username"),
    ("botfather-5", "5", "Скопируй токен", "BotFather пришлёт токен вида <b>123456789:AA...</b>. Нажми на него, чтобы скопировать. Никому не пересылай.", "token"),
]

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;background:#0b0d12;font-family:"Segoe UI",Arial,sans-serif;color:#eef1f6}
.stage{width:900px;height:1120px;padding:34px 46px;display:flex;flex-direction:column;gap:18px;
background:radial-gradient(700px 400px at 80% 0%,rgba(90,140,255,.16),transparent 65%),#0b0d12}
.kicker{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#8ea0b8}
h1{margin:0;font-size:30px;letter-spacing:-.02em}
p{margin:0;color:#9aa8bb;font-size:14px;line-height:1.55}
.phone{margin:10px auto 0;width:470px;height:760px;border-radius:38px;background:#17212b;border:8px solid #262f3a;
box-shadow:0 30px 80px rgba(0,0,0,.55);overflow:hidden;display:flex;flex-direction:column}
.top{height:64px;background:#17212b;display:flex;align-items:center;gap:12px;padding:0 16px;border-bottom:1px solid #24303d}
.avatar{width:38px;height:38px;border-radius:50%;background:#2aabee;color:#fff;display:grid;place-items:center;font-weight:800}
.who b{display:block;font-size:14px}.who span{font-size:11px;color:#7f91a5}
.chat{flex:1;padding:16px;display:flex;flex-direction:column;gap:10px;background:#0e1621}
.msg{max-width:86%;padding:10px 13px;border-radius:14px;background:#182533;font-size:13px;line-height:1.45;color:#dce6f2}
.msg.me{align-self:flex-end;background:#2b5278;color:#fff}
.msg code{background:#0b1119;padding:2px 6px;border-radius:5px;color:#8ed0ff;font-size:12px}
.msg .token{display:block;background:#0b1119;border:1px dashed #3d6a8f;padding:10px;border-radius:8px;color:#9fe0ff;font-size:12px;margin-top:6px}
.search{margin:14px;background:#17212b;border-radius:14px;padding:12px;display:flex;gap:10px;color:#8ea0b8;font-size:14px}
.search b{color:#fff}
.result{margin:0 14px;background:#17212b;border-radius:14px;padding:14px;display:flex;align-items:center;gap:12px}
.result .avatar{width:44px;height:44px}
.result b{display:block;font-size:14px}.result span{font-size:11px;color:#7f91a5}
.btn{margin:8px 14px;background:#2aabee;color:#fff;border-radius:10px;padding:11px;text-align:center;font-weight:700;font-size:13px}
.caption{display:flex;gap:14px;align-items:flex-start;background:#121822;border:1px solid #24303d;border-radius:16px;padding:16px}
.num{width:34px;height:34px;border-radius:10px;background:#2aabee;color:#fff;display:grid;place-items:center;font-weight:800;flex:none}
</style></head><body><div class="stage">
<div class="kicker">Практика · BotFather · шаг __NUM__ из 5</div>
<h1>__TITLE__</h1>
<p>__TEXT__</p>
<div class="phone">
  <div class="top"><div class="avatar">B</div><div class="who"><b>BotFather</b><span>bot</span></div></div>
  <div class="chat">__CHAT__</div>
</div>
<div class="caption"><div class="num">__NUM__</div><div><b>__TITLE__</b><p>__TEXT__</p></div></div>
</div></body></html>"""

CHATS = {
    "search": """<div class="search">🔍 <b>@BotFather</b></div>
<div class="result"><div class="avatar">B</div><div><b>BotFather</b><span>@BotFather · бот с галочкой</span></div></div>
<div class="btn">Открыть</div>
<div class="msg">Официальный бот Telegram. Создаёт ботов и выдаёт токены.</div>""",
    "command": """<div class="msg me">/newbot</div>
<div class="msg">Alright, a new bot. How are we going to call it? Please choose a name for your bot.</div>
<div class="msg">Хорошо. Придумай имя — его увидят пользователи.</div>""",
    "name": """<div class="msg me">Мой первый бот</div>
<div class="msg">Good. Now let's choose a username for your bot. It must end in `bot`.</div>
<div class="msg">Например: <code>my_first_school_bot</code></div>""",
    "username": """<div class="msg me">my_first_school_bot</div>
<div class="msg">Done! Congratulations on your new bot.</div>
<div class="msg">Use this token to access the HTTP API:</div>
<div class="msg"><span class="token">123456789:AA...токен...</span></div>""",
    "token": """<div class="msg">Done! Congratulations on your new bot.</div>
<div class="msg">Use this token to access the HTTP API:</div>
<div class="msg"><span class="token">123456789:AA...токен...</span></div>
<div class="msg">Keep it secret and store it safely. Скопируй токен и вставь его в платформу.</div>""",
}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 900, "height": 1120}, device_scale_factor=1)
    for name, num, title, text, kind in STEPS:
        html = HTML.replace("__NUM__", num).replace("__TITLE__", title).replace("__TEXT__", text).replace("__CHAT__", CHATS[kind])
        tmp = ROOT / "private" / "lesson-render" / f"{name}.html"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(html, encoding="utf-8")
        page.goto(tmp.as_uri(), wait_until="load")
        png = OUT / f"{name}.png"
        page.screenshot(path=str(png))
        Image.open(png).convert("RGB").save(OUT / f"{name}.webp", "WEBP", quality=88, method=6)
        png.unlink()
        print("wrote", OUT / f"{name}.webp")
    browser.close()

