"""Все слайды тест-драйва в едином стиле (тёмный, «светящаяся дорога» — как karta v1/v4).
Слайды -> docs/course/slides/deck/<id>.html + <id>.jpg (1920x1080),
страница колоды с комментариями -> docs/course/slides_deck.html,
картинки вставляются в сценарий (sources/course/тест_драйв_скрипт_v1.md) под нужные пункты «На экране».
Запуск: python scripts/build_slides.py [--no-render] [id ...]"""
import os, re, sys, html, json, shutil

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SL = os.path.join(P, 'docs', 'course', 'slides')
DECK = os.path.join(SL, 'deck')
MD = os.path.join(P, 'sources', 'course', 'тест_драйв_скрипт_v1.md')

LESSONS = [  # номер, чип, короткое имя для прогресса, акцент
    (0, 'Вводный урок', 'Старт', '#ff8a3d'),
    (1, 'Урок 1 · Профессия', 'Профессия', '#34d399'),
    (2, 'Урок 2 · Чат-боты', 'Чат-боты', '#3ec7ff'),
    (3, 'Урок 3 · AI-агенты', 'AI-агенты', '#8b5cf6'),
    (4, 'Урок 4 · Mini Apps', 'Mini Apps', '#ff4f8b'),
    (5, 'Урок 5 · Клиенты', 'Клиенты', '#facc15'),
]

ICON = {
    'flag': '<path d="M4 21V4"/><path d="M4 4h12l-2 4 2 4H4"/>',
    'case': '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/>',
    'bot': '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 4v4"/><circle cx="12" cy="3" r="1"/><circle cx="9" cy="14" r="1.2"/><circle cx="15" cy="14" r="1.2"/><path d="M2 13v3M22 13v3"/>',
    'spark': '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    'phone': '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M11 18h2"/>',
    'target': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    'done': '<path d="M8 4h8l1 3h2v13H5V7h2z"/><path d="M9 13l2 2 4-4"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'chat': '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    'map': '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    'lock': '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    'gift': '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v9h14v-9M12 8v13"/><path d="M12 8c-2-4-6-4-6-1.5S9 8 12 8c3 0 6-1 6-1.5S14 4 12 8z"/>',
    'cal': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    'mega': '<path d="M3 11v2a1 1 0 0 0 1 1h3l6 4V6L7 10H4a1 1 0 0 0-1 1z"/><path d="M17 8a5 5 0 0 1 0 8"/>',
    'cap': '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c3 2 9 2 12 0v-5"/>',
    'eyeoff': '<path d="M3 3l18 18"/><path d="M10.6 6.1A9.8 9.8 0 0 1 12 6c6 0 9.5 6 9.5 6a17 17 0 0 1-3.2 3.9M6.6 6.6A17 17 0 0 0 2.5 12S6 18 12 18a9.6 9.6 0 0 0 4.4-1"/>',
    'shield': '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    'help': '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7M12 17h.01"/>',
    'store': '<path d="M4 9l1.5-5h13L20 9"/><path d="M4 9h16v11H4z"/><path d="M9 20v-6h6v6"/>',
    'users': '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.5a5 5 0 0 1 5.5 5.5"/>',
    'laptop': '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M2 19h20"/>',
    'radio': '<circle cx="12" cy="12" r="2"/><path d="M8.5 15.5a5 5 0 0 1 0-7M15.5 8.5a5 5 0 0 1 0 7M5.6 18.4a9 9 0 0 1 0-12.8M18.4 5.6a9 9 0 0 1 0 12.8"/>',
    'coin': '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.6-1.5-3-1.5-1.7 0-3 .8-3 2s1.3 1.7 3 2 3 .9 3 2.1-1.3 2-3 2c-1.4 0-2.6-.6-3-1.6M12 6v2M12 16v2"/>',
    'x': '<path d="M6 6l12 12M18 6L6 18"/>',
    'camera': '<path d="M4 8h3l2-3h6l2 3h3v12H4z"/><circle cx="12" cy="13" r="4"/>',
    'wrench': '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    'trend': '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    'news': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/>',
    'chart': '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
    'heart': '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    'home': '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
    'truck': '<path d="M3 6h11v10H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    'table': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    'book': '<path d="M4 5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>',
    'list': '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
    'key': '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M15 8l2 2"/>',
    'rocket': '<path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2"/><path d="M9 15l-3-3c2-6 7-9 14-9 0 7-3 12-9 14z"/><circle cx="15" cy="9" r="1.8"/>',
    'play': '<circle cx="12" cy="12" r="9"/><path d="M10 8.5v7l6-3.5z"/>',
    'eye': '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
}


def ic(name, cls='ic', color=None):
    st = ' style="--c:%s"' % color if color else ''
    return '<div class="%s"%s><svg viewBox="0 0 24 24">%s</svg></div>' % (cls, st, ICON[name])


def svg(name):
    return '<svg viewBox="0 0 24 24">%s</svg>' % ICON[name]


def todo(t):  # то, что команда должна вставить сама (как [..] в сценарии)
    return '<span class="todo">%s</span>' % t


def phone(src, w=330, h=None, pos='top', glow=None, extra=''):
    h = h or int(w * 2.1)
    g = ';--glow:%s' % glow if glow else ''
    return ('<div class="ph" style="width:%dpx;height:%dpx%s;%s"><img src="../screens/%s" style="object-position:%s"></div>'
            % (w, h, g, extra, src, pos))


def slot(label, w, h, extra=''):
    return '<div class="slot" style="width:%dpx;height:%dpx;%s">%s<span>%s</span></div>' % (w, h, extra, svg('camera'), label)


CSS = r'''
:root{--bg1:#070b1a;--bg2:#101a3d;--ink:#f4f6ff;--muted:#a7b0d6;--a1:#ff8a3d;--a2:#ff4f8b;--a3:#8b5cf6;--a4:#3ec7ff;--gold:#ffd166}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden;background:var(--bg1)}
.slide{position:relative;width:1920px;height:1080px;overflow:hidden;color:var(--ink);font-family:Manrope,"Segoe UI",Arial,sans-serif;
 background:radial-gradient(900px 600px at 12% 8%,rgba(139,92,246,.35),transparent 60%),radial-gradient(800px 600px at 92% 18%,rgba(255,79,139,.22),transparent 60%),
 radial-gradient(900px 700px at 70% 105%,rgba(62,199,255,.20),transparent 60%),linear-gradient(160deg,var(--bg1),var(--bg2))}
.grid{position:absolute;inset:0;opacity:.18;background-image:linear-gradient(rgba(255,255,255,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.07) 1px,transparent 1px);
 background-size:60px 60px;-webkit-mask-image:radial-gradient(ellipse at 50% 55%,#000 30%,transparent 75%);mask-image:radial-gradient(ellipse at 50% 55%,#000 30%,transparent 75%)}
.chip{position:absolute;left:96px;top:56px;display:inline-flex;align-items:center;gap:12px;font-weight:800;font-size:21px;letter-spacing:.14em;text-transform:uppercase;
 padding:11px 22px;border-radius:999px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16)}
.chip .dot{width:12px;height:12px;border-radius:50%;background:var(--acc);box-shadow:0 0 16px var(--acc)}
.h{position:absolute;left:96px;right:96px;top:138px}
h1{font-family:Unbounded,Manrope,sans-serif;font-weight:800;font-size:62px;line-height:1.08;letter-spacing:-.01em}
.grad{background:linear-gradient(90deg,var(--a1),var(--a2) 45%,var(--a3));-webkit-background-clip:text;background-clip:text;color:transparent}
.gold{color:var(--gold)}.acc{color:var(--acc)}
.sub{margin-top:16px;font-size:27px;color:var(--muted);font-weight:600;line-height:1.35;max-width:1500px}
.body{position:absolute;left:96px;right:96px;top:372px;bottom:142px}
.todo{color:var(--gold);border-bottom:2px dashed rgba(255,209,102,.7);font-style:normal}
/* прогресс-дорога внизу */
.prog{position:absolute;left:96px;right:96px;bottom:44px;display:flex;align-items:center}
.prog .it{flex:1;display:flex;align-items:center;gap:12px;font-size:17px;font-weight:800;color:rgba(167,176,214,.55);letter-spacing:.02em;white-space:nowrap}
.prog .it::after{content:"";flex:1;height:2px;margin:0 18px;border-radius:2px;background:rgba(255,255,255,.12)}
.prog .it:last-child{flex:0}.prog .it:last-child::after{display:none}
.prog .d{width:12px;height:12px;border-radius:50%;border:2px solid rgba(255,255,255,.35)}
.prog .it.past{color:rgba(205,212,240,.8)}.prog .it.past .d{background:rgba(255,255,255,.6);border-color:transparent}
.prog .it.past::after{background:linear-gradient(90deg,rgba(255,255,255,.5),rgba(255,255,255,.25))}
.prog .it.cur{color:#fff}.prog .it.cur .d{width:18px;height:18px;background:var(--acc);border:0;box-shadow:0 0 0 6px color-mix(in srgb,var(--acc) 25%,transparent),0 0 22px var(--acc)}
.prog .it.fin{color:var(--gold)}.prog .it.fin .d{border-color:var(--gold)}
/* карточки */
.g{position:relative;border-radius:28px;padding:34px 36px;background:linear-gradient(180deg,rgba(255,255,255,.085),rgba(255,255,255,.03));
 border:1px solid rgba(255,255,255,.14);box-shadow:0 30px 60px rgba(0,0,0,.35)}
.g h3{font-family:Unbounded,sans-serif;font-weight:600;font-size:31px;line-height:1.16}
.g p{margin-top:12px;font-size:24px;line-height:1.42;color:var(--muted);font-weight:600}
.body.c{display:flex;flex-direction:column;justify-content:center}
.ic.huge{width:290px;height:290px;box-shadow:0 0 0 22px rgba(255,255,255,.035),0 0 0 46px rgba(255,255,255,.02),0 0 120px color-mix(in srgb,var(--c) 60%,transparent),0 30px 60px rgba(0,0,0,.5)}
.ic.huge svg{width:130px;height:130px;stroke-width:1.5}
.bnum{font-family:Unbounded,sans-serif;font-weight:800;font-size:96px;line-height:1;background:linear-gradient(135deg,var(--a1),var(--a2) 50%,var(--a3));-webkit-background-clip:text;background-clip:text;color:transparent}
.g p b{color:var(--ink)}
.g.hl{border:2px solid rgba(255,209,102,.7);background:linear-gradient(180deg,rgba(255,209,102,.16),rgba(255,209,102,.04));box-shadow:0 0 70px rgba(255,209,102,.18),0 30px 60px rgba(0,0,0,.4)}
.g.hl h3{color:var(--gold)}
.g.dim{opacity:.55;filter:saturate(.3)}
.ic{--c:var(--acc);flex:none;width:84px;height:84px;border-radius:50%;display:flex;align-items:center;justify-content:center;
 background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.22),rgba(255,255,255,.04) 60%),#141c42;border:2px solid rgba(255,255,255,.22);
 box-shadow:0 0 0 8px rgba(255,255,255,.04),0 0 44px color-mix(in srgb,var(--c) 55%,transparent),0 14px 30px rgba(0,0,0,.45)}
.ic svg{width:40px;height:40px;fill:none;stroke:#fff;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.ic.big{width:150px;height:150px}.ic.big svg{width:70px;height:70px}
.ic.sm{width:64px;height:64px;box-shadow:0 0 0 6px rgba(255,255,255,.04),0 0 30px color-mix(in srgb,var(--c) 50%,transparent)}.ic.sm svg{width:30px;height:30px}
.ic.goldc{border:3px solid var(--gold);background:radial-gradient(circle at 35% 30%,rgba(255,209,102,.45),rgba(255,209,102,.08) 60%),#2a2340;box-shadow:0 0 0 10px rgba(255,209,102,.10),0 0 60px rgba(255,209,102,.45)}
.ic.goldc svg{stroke:var(--gold)}
.n{display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:50%;flex:none;font-family:Unbounded,sans-serif;font-weight:800;font-size:20px;
 color:#0b1020;background:linear-gradient(135deg,var(--a1),var(--a2));box-shadow:0 6px 16px rgba(255,79,139,.45)}
.n.gold{background:linear-gradient(135deg,#ffe29a,#ffb020);box-shadow:0 6px 16px rgba(255,176,32,.45)}
.tag{display:inline-block;font-size:16px;font-weight:800;padding:7px 14px;border-radius:999px;letter-spacing:.02em;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#e6e9ff}
.tag.code{background:rgba(255,209,102,.14);color:var(--gold);border-color:rgba(255,209,102,.4)}
.tag.prac{background:rgba(62,199,255,.14);color:#8fe0ff;border-color:rgba(62,199,255,.4)}
.tag.acc{background:color-mix(in srgb,var(--acc) 16%,transparent);color:color-mix(in srgb,var(--acc) 70%,#fff);border-color:color-mix(in srgb,var(--acc) 45%,transparent)}
.arr{flex:none;width:64px;display:flex;align-items:center;justify-content:center}
.arr svg{width:54px;height:54px;fill:none;stroke:url(#ag);stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 0 10px rgba(255,79,139,.7))}
.ph{position:relative;flex:none;border-radius:46px;overflow:hidden;border:10px solid #05070f;background:#05070f;
 box-shadow:0 0 0 2px rgba(255,255,255,.2),0 0 90px var(--glow,rgba(139,92,246,.55)),0 40px 80px rgba(0,0,0,.55)}
.ph img{display:block;width:100%;height:100%;object-fit:cover;border-radius:36px}
.slot{flex:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;border-radius:26px;border:2px dashed rgba(255,209,102,.6);
 background:rgba(255,209,102,.05);color:var(--gold);font-size:20px;font-weight:700;text-align:center;padding:20px;line-height:1.35}
.slot svg{width:46px;height:46px;fill:none;stroke:var(--gold);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;opacity:.85}
.strip{position:absolute;left:96px;right:96px;bottom:142px;display:flex;align-items:center;gap:26px;padding:26px 34px;border-radius:24px;
 background:linear-gradient(90deg,rgba(255,255,255,.08),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.14);font-size:25px;font-weight:700;line-height:1.35}
.strip .ic{width:64px;height:64px}.strip .ic svg{width:30px;height:30px}
.big-num{position:absolute;font-family:Unbounded,sans-serif;font-weight:800;line-height:.8;color:transparent;-webkit-text-stroke:2px rgba(255,255,255,.13)}
.slotd{width:200px;height:250px;border-radius:30px;display:flex;align-items:center;justify-content:center;font-family:Unbounded,sans-serif;font-weight:800;font-size:150px;
 background:rgba(255,255,255,.05);border:2px solid rgba(255,255,255,.16);color:rgba(255,255,255,.22)}
.slotd.on{color:var(--gold);border:3px solid var(--gold);background:radial-gradient(circle at 50% 30%,rgba(255,209,102,.28),rgba(255,209,102,.05) 70%);
 box-shadow:0 0 0 12px rgba(255,209,102,.08),0 0 90px rgba(255,209,102,.45);text-shadow:0 0 40px rgba(255,209,102,.8)}
.slotd.got{color:rgba(255,209,102,.55);border-color:rgba(255,209,102,.35)}
.tg{background:#0e1621;border-radius:0;display:flex;flex-direction:column;height:100%;font-family:"Segoe UI",Manrope,sans-serif}
.tg .top{display:flex;align-items:center;gap:14px;padding:58px 20px 16px;background:#17212b;color:#fff}
.tg .av{width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:20px;background:linear-gradient(135deg,#3ec7ff,#8b5cf6)}
.tg .nm{font-size:19px;font-weight:700}.tg .st{font-size:14px;color:#6c7883}
.tg .msgs{flex:1;padding:18px 14px;display:flex;flex-direction:column;gap:10px;justify-content:flex-end;
 background:radial-gradient(circle at 30% 20%,rgba(62,199,255,.08),transparent 50%),#0e1621}
.tg .b{max-width:88%;padding:12px 15px;border-radius:16px 16px 16px 6px;background:#182533;color:#e9eef4;font-size:17px;line-height:1.4}
.tg .b.me{align-self:flex-end;border-radius:16px 16px 6px 16px;background:#2b5278}
.tg .kb{display:grid;grid-template-columns:1fr;gap:6px}
.tg .kb div{background:rgba(43,82,120,.55);color:#fff;text-align:center;padding:11px;border-radius:10px;font-size:16px;font-weight:600}
'''

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600;800&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">')
DEFS = ('<svg width="0" height="0" style="position:absolute"><defs><linearGradient id="ag" x1="0" x2="1"><stop offset="0" stop-color="#3ec7ff"/>'
        '<stop offset=".5" stop-color="#ff4f8b"/><stop offset="1" stop-color="#ffd166"/></linearGradient></defs></svg>')
ARR = '<div class="arr"><svg viewBox="0 0 24 24"><path d="M4 12h15M13 6l6 6-6 6"/></svg></div>'


def prog(lesson):
    items = []
    for n, _, short, _c in LESSONS:
        cls = 'cur' if n == lesson else ('past' if n < lesson else '')
        items.append('<div class="it %s"><span class="d"></span>%d · %s</div>' % (cls, n, short))
    items.append('<div class="it fin"><span class="d"></span>★ Разбор</div>')
    return '<div class="prog">%s</div>' % ''.join(items)


def page(lesson, inner, head=None, sub=None, chip=None, progress=True, extra_css=''):
    n, chip0, _, acc = LESSONS[lesson]
    h = ''
    if head:
        h = '<div class="h"><h1>%s</h1>%s</div>' % (head, '<div class="sub">%s</div>' % sub if sub else '')
    return ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>слайд</title>%s<style>%s%s</style></head>'
            '<body><div class="slide" style="--acc:%s"><div class="grid"></div>%s'
            '<div class="chip"><span class="dot"></span>%s</div>%s%s%s</div></body></html>') % (
        FONTS, CSS, extra_css, acc, DEFS, chip or chip0, h, inner, prog(lesson) if progress else '')


def cards(items, cols=None, gap=28, style=''):
    """items: (icon, title, text, cls)"""
    cols = cols or len(items)
    out = []
    for it in items:
        icn, t, p, cls = (list(it) + [''] * 4)[:4]
        top = ic(icn, 'ic goldc' if 'hl' in cls else 'ic') if icn else ''
        out.append('<div class="g %s">%s<h3 style="margin-top:%dpx">%s</h3>%s</div>' % (
            cls, top, 26 if icn else 0, t, '<p>%s</p>' % p if p else ''))
    return '<div style="display:grid;grid-template-columns:repeat(%d,1fr);gap:%dpx;%s">%s</div>' % (cols, gap, style, ''.join(out))


def flow(items, style=''):
    """горизонтальная цепочка карточек со стрелками: (icon, title, text, cls)"""
    out = []
    for i, it in enumerate(items):
        icn, t, p, cls = (list(it) + [''] * 4)[:4]
        if i:
            out.append(ARR)
        out.append('<div class="g %s" style="flex:1">%s<h3 style="margin-top:26px">%s</h3>%s</div>' % (
            cls, ic(icn, 'ic goldc' if 'hl' in cls else 'ic'), t, '<p>%s</p>' % p if p else ''))
    return '<div style="display:flex;align-items:stretch;%s">%s</div>' % (style, ''.join(out))


# ---------- шаблонные слайды ----------

COVER_VIS = {
    0: lambda: ic('flag', 'ic huge'),
    1: lambda: ic('case', 'ic huge'),
    2: lambda: phone('kvasich.png', 370, 780, '50% 0%', 'rgba(62,199,255,.7)', 'transform:rotate(-4deg)'),
    3: lambda: phone('pulse.png', 370, 780, '50% 0%', 'rgba(139,92,246,.8)', 'transform:rotate(-4deg)'),
    4: lambda: (phone('gym.png', 330, 700, '50% 0%', 'rgba(255,79,139,.7)', 'transform:rotate(-7deg) translateY(30px);margin-right:-50px') +
                phone('manekken.png', 330, 700, '50% 0%', 'rgba(192,38,211,.7)', 'transform:rotate(5deg) translateY(-20px)')),
    5: lambda: ic('target', 'ic huge'),
}


def cover(lesson, title, goal, tags):
    n = LESSONS[lesson][0]
    title = re.sub(r'(\S+-\S+)', r'<span style="white-space:nowrap">\1</span>', title)
    inner = ('<div style="position:absolute;left:1000px;right:40px;top:100px;bottom:110px;display:flex;align-items:center;justify-content:center">'
             '<div class="big-num" style="font-size:600px;-webkit-text-stroke:2px rgba(255,255,255,.10)">%02d</div>%s</div>'
             '<div style="position:absolute;left:96px;top:120px;bottom:110px;width:900px;display:flex;flex-direction:column;justify-content:center">'
             '<div style="font-size:24px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--acc)">%s</div>'
             '<h1 style="font-size:80px;margin-top:20px">%s</h1><div class="sub" style="max-width:860px;font-size:29px">%s</div>'
             '<div style="display:flex;gap:12px;margin-top:34px;flex-wrap:wrap">%s</div></div>') % (
        n, COVER_VIS[lesson](), 'Вводный урок' if n == 0 else 'Урок %d' % n, title, goal,
        ''.join(t.replace('class="tag', 'style="font-size:19px;padding:9px 18px" class="tag') for t in tags))
    return page(lesson, inner, chip='Тест-драйв · 48 часов')


def summary(lesson, points, nxt, note=None):
    nl = LESSONS[lesson + 1] if lesson < 5 else None
    pts = ''.join('<div class="g" style="display:flex;gap:26px;align-items:center;padding:30px 36px"><span class="n">%d</span><h3 style="font-size:31px;line-height:1.3">%s</h3></div>'
                  % (i + 1, p) for i, p in enumerate(points))
    nx = ('<div class="g" style="--acc:%s;border-color:color-mix(in srgb,var(--acc) 60%%,transparent);box-shadow:0 0 60px color-mix(in srgb,var(--acc) 22%%,transparent)">'
          '<div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--acc)">Дальше · %s</div>'
          '<h3 style="margin-top:14px;font-size:38px">%s</h3>%s</div>') % (nl[3] if nl else '#ffd166', nl[2] if nl else 'Разбор', nxt, '<p>%s</p>' % note if note else '')
    inner = ('<div class="body" style="top:270px;display:grid;grid-template-columns:1.3fr 1fr;gap:40px;align-items:center">'
             '<div style="display:grid;gap:24px">%s</div><div>%s</div></div>') % (pts, nx)
    return page(lesson, inner, head='Итог урока')


def digit(lesson, k, caption):
    slots = ''
    for i in range(1, 5):
        cls = 'on' if i == k or k == 4 and lesson == 4 else ('got' if i < k else '')
        slots += '<div class="slotd %s">%s</div>' % (cls, 'X' if cls else '_')
    inner = ('<div style="position:absolute;left:0;right:0;top:190px;text-align:center">'
             '<div style="font-size:24px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--gold)">%s</div>'
             '<h1 style="font-size:76px;margin-top:18px">%s</h1></div>'
             '<div style="position:absolute;left:0;right:0;top:450px;display:flex;justify-content:center;gap:36px">%s</div>'
             '<div style="position:absolute;left:0;right:0;top:760px;text-align:center;font-size:28px;font-weight:700;color:var(--muted)">%s</div>'
             '<div style="position:absolute;right:96px;top:62px;font-size:17px;font-weight:700;color:var(--gold);opacity:.8">X — %s</div>') % (
        'Код · %d из 4' % k, 'Все четыре цифры <span class="grad">собраны</span>' if k == 4 and lesson == 4 else '%s цифра кода' % ['Первая', 'Вторая', 'Третья', 'Четвёртая'][k - 1],
        slots, caption, todo('вставить реальную цифру'))
    return page(lesson, inner)


# ---------- слайды ----------
S = []  # (id, урок, якорь в сценарии (подстрока заголовка ###, номер «На экране» в разделе) или None, подпись, html)


def add(sid, lesson, anchor, cap, htm):
    S.append((sid, lesson, anchor, cap, htm))


# ВВОДНЫЙ
add('l0_cover', 0, ('cover',), 'Обложка: вводный урок',
    cover(0, 'Что тебя ждёт за 48 часов', 'Правила игры, главное задание и как выжать из двух дней максимум.',
          ['<span class="tag acc">до 10 минут</span>', '<span class="tag">6 уроков</span>', '<span class="tag code">код из 4 цифр</span>']))
add('l0_map', 0, ('2. Что тебя ждёт', 0), 'Карта тест-драйва', None)  # = karta_v4
add('l0_razbor', 0, ('3. Самое главное', 0), 'Уроки → анкета → разбор → план', page(0,
    '<div class="body c" style="top:290px">%s</div>' % flow([
        ('play', 'Уроки', 'Подготовка: бот, агент, мини-приложение, клиенты'),
        ('list', 'Анкета', 'Главное домашнее задание. Честно и подробно'),
        ('user', 'Личный разбор', 'Работа · свободные часы · навыки · цель по доходу'),
        ('map', 'Твой план', 'С каких задач начать и где искать первых клиентов', 'hl')]),
    head='Самое ценное — <span class="grad">в конце</span>', sub='Уроки — подготовка. Главное — личный разбор твоей ситуации.'))
add('l0_timer', 0, ('4. Почему 48 часов', 0), 'Таймер 48:00:00', page(0,
    '<div style="position:absolute;left:0;right:0;top:170px;text-align:center">'
    '<div style="font-size:24px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)">на весь тест-драйв</div>'
    '<div style="font-family:Unbounded,sans-serif;font-weight:800;font-size:250px;line-height:1.05;margin-top:20px;letter-spacing:-.02em;'
    'background:linear-gradient(180deg,#fff,#c9d1ff);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 40px rgba(139,92,246,.55))">48:00:00</div>'
    '<svg width="1300" height="40" viewBox="0 0 1300 40" style="margin-top:10px"><defs><linearGradient id="tl" x1="0" x2="1"><stop offset="0" stop-color="#8b5cf6"/><stop offset=".5" stop-color="#3ec7ff"/><stop offset="1" stop-color="#ff4f8b"/></linearGradient></defs>'
    '<rect x="0" y="15" width="1300" height="10" rx="5" fill="rgba(255,255,255,.1)"/><rect x="0" y="15" width="1300" height="10" rx="5" fill="url(#tl)" style="filter:drop-shadow(0 0 12px #3ec7ff)"/></svg>'
    '<div style="display:flex;justify-content:center;gap:28px;margin-top:46px">'
    '<div class="g" style="width:520px;text-align:left;display:flex;gap:22px;align-items:center">%s<div><h3 style="font-size:26px">Честный темп</h3><p style="margin-top:6px">Отложишь «на потом» — интерес остынет</p></div></div>'
    '<div class="g" style="width:520px;text-align:left;display:flex;gap:22px;align-items:center">%s<div><h3 style="font-size:26px">Не успеваешь?</h3><p style="margin-top:6px">Напиши в чат — продлим</p></div></div>'
    '</div></div>' % (ic('clock', 'ic sm'), ic('chat', 'ic sm'))))
add('l0_free', 0, ('5. Мотивация', 0), 'Свобода = право выбора + фото Егора', page(0,
    '<div class="body" style="top:330px;display:grid;grid-template-columns:640px 1fr;gap:44px">'
    '<div style="display:grid;gap:20px;align-content:start">%s</div>'
    '<div style="display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:20px">%s%s%s</div></div>'
    '<div style="position:absolute;left:96px;bottom:150px;width:640px;font-size:22px;font-weight:700;color:var(--muted);line-height:1.4">'
    'Честный минус: никто не стоит над душой — график держишь сам. <span style="color:var(--ink)">Это тоже навык.</span></div>' % (
        ''.join('<div class="g" style="display:flex;gap:24px;align-items:center;padding:24px 30px">%s<h3 style="font-size:28px">%s</h3></div>' % (ic(i, 'ic sm'), t)
                for i, t in (('clock', 'Когда проснуться'), ('users', 'Сколько клиентов взять'), ('laptop', 'Откуда работать'))),
        slot('[фото Егора: рабочее место]', 0, 0, 'width:auto;height:auto;grid-row:1 / 3'), slot('[ноутбук не в офисе]', 0, 0, 'width:auto;height:auto'),
        slot('[путешествие — только если правда]', 0, 0, 'width:auto;height:auto')),
    head='Фриланс — это <span class="grad">право выбора</span>'))
add('l0_idea', 0, ('6. Глобальная идея', 0), 'Золотая жила', page(0,
    '<div class="body c" style="top:290px">%s</div>' % flow([
        ('trend', 'Бизнесу нужна автоматизация', 'Без ботов и нейросетей компании отстают'),
        ('users', 'Делать её некому', 'Людей, которые внедряют просто и понятно, мало'),
        ('rocket', 'Это делаешь ты', 'Выигрывает не самый опытный, а тот, кто зашёл раньше', 'hl')]),
    head='Золотая жила: <span class="grad">AI и техспецы</span>', sub='Одна из самых недооценённых возможностей прямо сейчас.'))
add('l0_rules', 0, ('7. Как смотреть', 0), '3 правила + «+» в чат', page(0,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:1fr 1fr 1fr 430px;gap:26px">%s'
    '<div class="g hl" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">'
    '<div style="font-size:20px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)">Первое действие</div>'
    '<div style="margin-top:22px;width:190px;height:190px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-family:Unbounded,sans-serif;font-weight:800;font-size:140px;'
    'color:#0b1020;background:linear-gradient(135deg,#ffe29a,#ffb020);box-shadow:0 0 0 14px rgba(255,209,102,.12),0 0 80px rgba(255,209,102,.6)">+</div>'
    '<h3 style="margin-top:30px;font-size:30px">Напиши в чат «+»</h3><p>и я пришлю первый урок</p>'
    '<svg viewBox="0 0 24 24" style="width:70px;height:70px;margin-top:10px;fill:none;stroke:var(--gold);stroke-width:2;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 0 10px rgba(255,209,102,.8))"><path d="M12 4v15M6 13l6 6 6-6"/></svg></div></div>' % ''.join(
        '<div class="g" style="display:flex;flex-direction:column;padding:40px 38px"><div class="bnum" style="font-size:130px">%02d</div>'
        '<div style="margin-top:auto"><h3 style="font-size:36px">%s</h3><p style="font-size:26px;margin-top:16px">%s</p></div></div>' % (i + 1, t, p) for i, (t, p) in enumerate((
            ('Выключи критика', 'Не «это не для меня», а «что из этого я могу применить»'),
            ('Вопросы — в чат', 'Глупых вопросов здесь нет'),
            ('Время — тоже плата', 'Ты отдаёшь два вечера. Пусть они окупятся')))),
    head='Три правила, чтобы был <span class="grad">толк</span>'))

# УРОК 1
add('l1_cover', 1, ('cover',), 'Обложка урока 1',
    cover(1, 'Кто такой техспец и AI-автоматизатор', 'Почему бизнесу это нужно, сколько платят и какие есть два пути.',
          ['<span class="tag acc">≈20 минут</span>', '<span class="tag code">цифра кода №1</span>']))
add('l1_code', 1, ('1. Похвала', 0), 'Игра: код _ _ _ _', page(1,
    '<div style="position:absolute;left:0;right:0;top:170px;text-align:center"><h1 style="font-size:72px">Собери код из <span class="grad">4 цифр</span></h1>'
    '<div class="sub" style="margin:18px auto 0">По одной цифре в уроках 1, 2, 3 и 4. Смотри внимательно — они не повторяются.</div></div>'
    '<div style="position:absolute;left:0;right:0;top:430px;display:flex;justify-content:center;gap:36px">%s</div>'
    '<div style="position:absolute;left:50%%;transform:translateX(-50%%);top:740px;display:flex;align-items:center;gap:22px;font-size:28px;font-weight:700;white-space:nowrap">'
    '%s Код + анкета в конце = %s</div>' % (
        ''.join('<div class="slotd"><span style="font-size:110px">_</span></div>' for _ in range(4)), ic('lock', 'ic sm goldc'),
        todo('[бонус: секретное мини-приложение]'))))
add('l1_story', 1, ('2. История Егора', 0), 'История Егора: таймлайн + места под фото', page(1,
    '<svg width="1920" height="1080" style="position:absolute;left:0;top:0"><defs><linearGradient id="rg" x1="0" x2="1"><stop offset="0" stop-color="#8b5cf6"/><stop offset=".4" stop-color="#3ec7ff"/>'
    '<stop offset=".75" stop-color="#ff4f8b"/><stop offset="1" stop-color="#ffd166"/></linearGradient><filter id="gl"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
    '<path d="M180 640 L1740 640" stroke="url(#rg)" stroke-width="8" stroke-linecap="round" filter="url(#gl)"/></svg>'
    + ''.join('<div style="position:absolute;left:%dpx;top:640px;transform:translate(-50%%,-50%%)">%s</div>'
              '<div style="position:absolute;left:%dpx;top:%dpx;width:270px;transform:translateX(-50%%);text-align:center">'
              '<div style="font-family:Unbounded,sans-serif;font-weight:800;font-size:30px;color:%s">%s</div><h3 style="font-family:Unbounded;font-weight:600;font-size:23px;margin-top:8px">%s</h3>'
              '<p style="margin-top:8px;font-size:18px;line-height:1.38;color:var(--muted);font-weight:600">%s</p></div>' % (
                  x, ic(i, 'ic sm goldc' if gold else 'ic sm'), x, 720 if not up else 300, '#ffd166' if gold else '#fff', yr, t, d)
              for x, i, yr, t, d, up, gold in (
                  (180, 'truck', '2015', 'Склад', 'Подъём в 5 утра, овощи в кузове, денег меньше, чем у курьера', 0, 0),
                  (490, 'store', '5 лет', '4 бизнеса', 'Промо, мебель, производство, маркетплейсы', 1, 0),
                  (800, 'case', '2021', 'Найм в 28', 'Люди руками собирают отчёт из пяти таблиц', 0, 0),
                  (1110, 'table', 'через месяц', 'Первая автоматизация', 'Таблица → вторая → бот. Стали доплачивать', 1, 0),
                  (1420, 'coin', '2023', '300 → 400 → 500 тыс.', 'в месяц за такую работу', 0, 0),
                  (1740, 'spark', 'сейчас', 'AI-агенты', '10 часов работы → 3–4 часа. Боты и агенты для бизнеса', 1, 1)))
    + slot('[фото: склад]', 230, 150, 'position:absolute;left:65px;top:400px') + slot('[фото: офис / таблицы]', 230, 150, 'position:absolute;left:685px;top:400px')
    + slot('[фото: сейчас]', 230, 150, 'position:absolute;left:1305px;top:400px')
    + '<div style="position:absolute;right:96px;top:150px;width:720px;text-align:right;font-family:Unbounded,sans-serif;font-weight:600;font-size:30px;line-height:1.3">'
      '«Деньги лежали в соседней комнате, <span class="grad">в экселе</span>»</div>',
    head='Как я сюда пришёл'))
add('l1_market', 1, ('3. Боль рынка', 0), 'Рынок: места под скрины новостей', page(1,
    '<div class="body" style="top:340px;display:grid;grid-template-columns:1fr 1fr 640px;gap:28px">%s%s'
    '<div class="g hl" style="display:flex;flex-direction:column;justify-content:center">%s<h3 style="margin-top:28px;font-size:36px;line-height:1.25">Нейросеть сама себя в бизнес не встроит.</h3>'
    '<p style="font-size:26px;margin-top:18px"><b style="color:var(--gold)">Это делаем мы.</b></p></div></div>' % (
        slot('[скрин новости о сокращениях + источник]', 0, 0, 'width:auto;height:auto'), slot('[скрин вакансии / факт об автоматизации + источник]', 0, 0, 'width:auto;height:auto'),
        ic('spark', 'ic goldc')),
    head='Компании убирают <span class="grad">рутину</span>', sub='Одинаковые ответы, таблицы, обзвоны — это автоматизируют первым.'))
two = lambda: ('<div class="body" style="top:300px;display:grid;grid-template-columns:1fr 120px 1fr;align-items:stretch">'
               '<div class="g" style="--acc:#3ec7ff;border-color:rgba(62,199,255,.45);box-shadow:0 0 70px rgba(62,199,255,.16);display:flex;flex-direction:column;padding:44px">'
               '<div style="display:flex;gap:22px;align-items:center">%s<div><span class="tag acc">протоптанная дорога</span><h3 style="margin-top:12px;font-size:34px">Техспец · чат-боты</h3></div></div>'
               '<p style="font-size:30px;margin-top:34px;line-height:1.85;color:#dfe4ff">Запись к мастеру<br>Автоворонка к вебинару<br>Рассылки и приём оплат</p>'
               '<p style="margin-top:auto;padding-top:20px;font-size:26px;color:var(--acc)">Понятно, востребовано, работы много</p></div>'
               '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;text-align:center">%s'
               '<div style="font-size:17px;font-weight:800;color:var(--muted);line-height:1.3">второе<br>растёт<br>из первого</div></div>'
               '<div class="g" style="--acc:#8b5cf6;border-color:rgba(139,92,246,.55);box-shadow:0 0 80px rgba(139,92,246,.25);display:flex;flex-direction:column;padding:44px">'
               '<div style="display:flex;gap:22px;align-items:center">%s<div><span class="tag acc">профессия нового времени</span><h3 style="margin-top:12px;font-size:34px">AI-автоматизатор</h3></div></div>'
               '<p style="font-size:30px;margin-top:34px;line-height:1.85;color:#dfe4ff">Агенты отвечают клиентам<br>Разбирают заявки, пишут тексты<br>Считают и делают отчёты</p>'
               '<p style="margin-top:auto;padding-top:20px;font-size:26px;color:#c4b5fd">Чеки выше, конкурентов пока мало</p></div></div>') % (
    ic('bot', 'ic', '#3ec7ff'), ARR, ic('spark', 'ic', '#8b5cf6'))
add('l1_two', 1, ('4. Два направления', 0), 'Два направления', page(1, two(), head='Два пути — <span class="grad">пройдём оба</span>'))
add('l1_price', 1, ('5. Доказательства', 0), 'Прайс по услугам', page(1,
    '<div class="body c" style="top:270px;bottom:170px">%s</div><div style="position:absolute;left:96px;bottom:130px;font-size:20px;font-weight:700;color:var(--muted)">Примерные цены на рынке</div>' % (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:26px">' + ''.join(
            '<div class="g" style="padding:34px 36px">%s<div style="font-size:26px;font-weight:700;color:var(--muted);margin-top:22px">%s</div>'
            '<div style="font-family:Unbounded,sans-serif;font-weight:800;font-size:56px;margin-top:10px" class="%s">%s</div></div>' % (
                ic(i, 'ic sm'), t, 'grad' if hot else '', p) for i, t, p, hot in (
                ('gift', 'Бот-подарок за подписку', '5–10 тыс.', 0), ('cal', 'Запись к мастеру', '5–15 тыс.', 0), ('mega', 'Автоворонка к вебинару', '10–25 тыс.', 0),
                ('phone', 'Мини-приложение', '20–40 тыс.', 1), ('spark', 'AI-консультант', '50–70 тыс.', 1), ('wrench', 'Сопровождение, в месяц', '10–30 тыс.', 0))) + '</div>'),
    head='Сколько за это <span class="grad">платят</span>'))
add('l1_100k', 1, ('5. Доказательства', 0), '100 тысяч — три способа', page(1,
    '<div class="body c" style="top:290px;bottom:300px">%s</div>'
    '<div class="strip">%s<div>Честно: первые недели — это обычно <span class="gold">15–50 тысяч</span>, а не сотни. Доход растёт с постоянными клиентами.</div></div>' % (
        flow([('bot', '%s × %s' % ('5 ботов', '20 тыс.'), 'Боты для записи, подарков, вебинаров'),
              ('spark', '2 AI-консультанта × 50 тыс.', 'Меньше клиентов — выше чек'),
              ('users', '4 клиента × 25 тыс.', 'Сопровождение каждый месяц')], 'gap:0'), ic('shield', 'ic sm')),
    head='100 000 ₽ в месяц — <span class="grad">разными путями</span>', sub='Какой путь твой — обсудим на разборе. ' + todo('[суммы — сверить с прайсом команды]')))
add('l1_digit', 1, ('5. Доказательства', 1), 'Первая цифра кода', digit(1, 1, 'Бот, через который ты получаешь уроки, — тоже работа техспеца'))
add('l1_sum', 1, ('6. Итог и переход', None), 'Итог урока 1', summary(1, [
    'Бизнесу нужна автоматизация, а делать её некому',
    'Два направления: чат-боты и AI-автоматизация. Второе растёт из первого',
    'За это платят. Порог входа — не код, а понимание задачи'],
    'Соберёшь своего первого бота', 'А первая цифра кода у тебя уже есть — запиши её'))

# УРОК 2
add('l2_cover', 2, ('cover',), 'Обложка урока 2',
    cover(2, 'Чат-боты: собираешь первого бота', 'Почему бизнес платит за простые вещи — и практика: бот-визитка за вечер.',
          ['<span class="tag acc">≈20 минут</span>', '<span class="tag prac">практика</span>', '<span class="tag code">цифра кода №2</span>']))
bot_ex = ''.join('<div class="g" style="padding:26px 28px;display:flex;gap:22px;align-items:flex-start">%s<div><h3 style="font-size:25px">%s</h3><p style="font-size:19px;margin-top:8px">%s</p></div></div>'
                 % (ic(i, 'ic sm'), t, p) for i, t, p in (
                     ('cal', 'Запись в салон', 'Услуга → время → телефон. Мастеру приходит уведомление'),
                     ('gift', 'Бот-подарок', 'Гайд за подписку на канал'),
                     ('mega', 'Бот вебинара', 'Регистрация и напоминания'),
                     ('cap', 'Бот школы', 'Уроки, задания, оплата')))
add('l2_bots', 2, ('2. Что такое чат-бот', 0), 'Примеры ботов + Профессор Квасич', page(2,
    '<div class="body" style="top:330px;right:640px;display:grid;grid-template-columns:1fr 1fr;gap:22px;align-content:start">%s</div>'
    '<div style="position:absolute;right:190px;top:110px">%s</div>'
    '<div style="position:absolute;right:120px;top:880px;width:500px;text-align:center"><span class="tag prac" style="font-size:19px">Наш бот · Профессор Квасич — репетитор по математике</span></div>' % (
        bot_ex, phone('kvasich.png', 350, 740, '50% 0%', 'rgba(62,199,255,.7)')),
    head='Чат-бот — сотрудник,<br>который <span class="grad">не устаёт</span>', sub='Работает круглые сутки: запись, подарки, напоминания, оплата.'))
add('l2_why', 2, ('3. Почему бизнес платит', 0), 'Почему не делают сами', page(2,
    '<div class="body c" style="top:280px;bottom:300px">%s</div>'
    '<div class="strip" style="bottom:150px">%s<div>Как с электриком: розетку поменять несложно, но платят за то, что всё работает. '
    '<span class="gold">Платят не за часы, а за решённую задачу.</span></div></div>' % (
        cards([('clock', 'Нет времени', 'Владелец весь день с клиентами'),
               ('shield', 'Страшно сломать', 'Бот упал в день запуска — школа теряет деньги'),
               ('help', 'Непонятно как', 'Чем меньше понимаешь, тем больше готов заплатить')]), ic('wrench', 'ic sm')),
    head='Если это просто — почему <span class="grad">не делают сами?</span>'))
vis = ('<div class="tg"><div class="top"><div class="av">Я</div><div><div class="nm">%s · визитка</div><div class="st">бот</div></div></div><div class="msgs">'
       '<div class="b">Привет! Я %s — начинающий специалист по чат-ботам 👋<br>Чем могу помочь?</div>'
       '<div class="kb"><div>Что я делаю</div><div>Цены</div><div>Оставить заявку</div></div>'
       '<div class="b me">Цены</div><div class="b">Бот-визитка — от … ₽<br>Запись к мастеру — от … ₽</div></div></div>') % ('[Имя]', '[Имя]')
add('l2_tz', 2, ('4. Практика', 0), 'ТЗ: бот-визитка за 5 шагов', page(2,
    '<div class="body" style="top:320px;right:620px;display:grid;gap:16px;align-content:start">%s</div>'
    '<div style="position:absolute;right:200px;top:110px"><div class="ph" style="width:360px;height:760px;--glow:rgba(62,199,255,.6)">%s</div></div>' % (
        ''.join('<div class="g" style="padding:18px 26px;display:flex;gap:22px;align-items:center"><span class="n">%d</span><div><h3 style="font-size:25px">%s</h3>'
                '<p style="margin-top:4px;font-size:19px">%s</p></div></div>' % (i + 1, t, p) for i, (t, p) in enumerate((
                    ('Создаём бота в Telegram', 'BotFather: имя, адрес бота, токен'),
                    ('Подключаем токен', 'в ' + todo('[конструктор / шаблон]')),
                    ('Пишем приветствие', '«[Имя], начинающий специалист по чат-ботам»'),
                    ('Добавляем кнопки', 'Что я делаю · Цены · Оставить заявку'),
                    ('Тестируем', 'Ошибка — нормально. Находим, исправляем, проверяем')))),
        vis), head='Первый заказ: <span class="grad">бот-визитка</span>', sub='Клиент — это ты сам. ТЗ одной страницей — под видео.'))
add('l2_digit', 2, ('4. Практика', 1), 'Вторая цифра кода', digit(2, 2, 'Пришли ссылку на своего бота в чат — за практику бонус'))
add('l2_sum', 2, ('5. Итог и переход', None), 'Итог урока 2', summary(2, [
    'Бизнес платит за то, что кажется простым: время, надёжность, понимание',
    'Ты собрал своего первого бота — это твоя визитка',
    'У тебя вторая цифра кода'],
    'AI-агенты: часы работы — за минуты', 'Именно там сейчас самые интересные чеки'))

# УРОК 3
add('l3_cover', 3, ('cover',), 'Обложка урока 3',
    cover(3, 'AI-агенты — золотая жила ближайших лет', 'Чем агент отличается от нейросети, живые примеры и свой первый агент.',
          ['<span class="tag acc">≈20 минут</span>', '<span class="tag prac">практика</span>', '<span class="tag code">цифра кода №3</span>']))
vs_col = lambda acc, icn, tag, title, q, a, chips, cls: (
    '<div class="g %s" style="--acc:%s;display:flex;flex-direction:column;gap:18px;%s">'
    '<div style="display:flex;gap:22px;align-items:center">%s<div><span class="tag acc">%s</span><h3 style="margin-top:10px;font-size:32px">%s</h3></div></div>'
    '<div style="background:#0e1621;border-radius:20px;padding:24px;display:flex;flex-direction:column;gap:14px;font-size:25px;line-height:1.4">'
    '<div style="align-self:flex-end;background:#2b5278;padding:12px 16px;border-radius:16px 16px 6px 16px">%s</div>'
    '<div style="background:#182533;padding:12px 16px;border-radius:16px 16px 16px 6px;max-width:92%%">%s</div></div>'
    '<div style="display:flex;gap:10px;flex-wrap:wrap">%s</div></div>') % (
    cls, acc, 'border-color:rgba(139,92,246,.6);box-shadow:0 0 90px rgba(139,92,246,.3)' if cls == '' and acc == '#8b5cf6' else '',
    ic(icn, 'ic sm', acc), tag, title, q, a, chips)
add('l3_vs', 3, ('1. Нейросеть vs агент', 0), 'Нейросеть vs агент', page(3,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:center">%s%s</div>' % (
        vs_col('#a7b0d6', 'chat', 'нейросеть', 'Отвечает «в общем»', 'Сколько стоит стрижка?', 'Обычно от 500 до 3000 ₽ — зависит от салона и города…',
               '<span class="tag">ответ для всех</span>', 'dim'),
        vs_col('#8b5cf6', 'spark', 'AI-агент', 'Знает твой бизнес и делает работу', 'Сколько стоит стрижка?',
               'По прайсу нашего салона — женская стрижка … ₽. Есть окно завтра в 15:00, записать вас?',
               '<span class="tag acc">✓ записал клиента</span><span class="tag acc">✓ отчёт руководителю</span>', '')),
    head='Нейросеть ≠ <span class="grad">агент</span>', sub='Агент — виртуальный сотрудник под конкретный бизнес.'))
add('l3_trend', 3, ('2. Почему это тренд', 0), 'Было → стало → почему заплатит', page(3,
    '<div class="body c" style="top:280px;bottom:330px">%s</div>'
    '<div style="position:absolute;left:96px;right:96px;bottom:150px;height:160px;display:flex;gap:24px">%s%s</div>' % (
        flow([('clock', 'Было', 'Менеджер тратит ' + todo('[3 часа в день]') + ' на ответы'),
              ('spark', 'Стало', 'Агент отвечает сам, круглые сутки'),
              ('coin', 'Экономия', todo('[N ₽ в месяц]')),
              ('done', 'Клиент платит', '<b style="color:var(--gold)">50–70 тыс.</b> за внедрение — и это выгодно', 'hl')]),
        slot('[факт о внедрении ИИ в бизнес + источник]', 0, 0, 'flex:1;height:auto;flex-direction:row'),
        slot('[ещё факт + источник]', 0, 0, 'flex:1;height:auto;flex-direction:row')),
    head='Почему агенты — <span class="grad">главный тренд</span>', sub='Все хотят, чтобы нейросети работали на них. Почти никто не знает, с чего начать.'))
add('l3_magic', 3, ('3. Магия ИИ', 0), 'Что умеют агенты + Пульс мира', page(3,
    '<div style="position:absolute;left:150px;top:300px">%s</div>'
    '<div style="position:absolute;left:96px;top:930px;width:540px;text-align:center"><span class="tag acc" style="font-size:19px">Пульс мира — сам собирает новости и делает видео</span></div>'
    '<div style="position:absolute;left:680px;right:96px;top:330px;display:grid;gap:22px">%s</div>'
    '<div style="position:absolute;left:680px;right:96px;top:800px;font-size:26px;font-weight:700;line-height:1.4">Раньше — отдельный сотрудник на каждую задачу.<br><span class="grad">Сейчас — один настроенный агент.</span></div>' % (
        phone('pulse.png', 300, 610, '50% 0%', 'rgba(139,92,246,.8)'),
        ''.join('<div class="g" style="padding:24px 30px;display:flex;gap:24px;align-items:center">%s<div><h3 style="font-size:27px">%s</h3><p style="margin-top:6px;font-size:20px">%s</p></div></div>'
                % (ic(i, 'ic sm'), t, p) for i, t, p in (
                    ('news', 'AI-редакция', 'Каждое утро собирает новости и готовит посты'),
                    ('chat', 'Агент-консультант', 'Отвечает клиентам по базе знаний компании ' + todo('[демо команды]')),
                    ('chart', 'Агент по отчётам', 'Считает рекламу и пишет, где теряются деньги ' + todo('[демо команды]'))))),
    head='Магия: что уже <span class="grad">умеют агенты</span>'))
add('l3_steps', 3, ('4. Практика', 0), 'Свой агент за 5 шагов', page(3,
    '<div class="body" style="top:320px;right:640px;display:grid;gap:16px;align-content:start">%s</div>'
    '<div class="g hl" style="position:absolute;right:96px;top:330px;width:500px;height:520px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center">'
    '%s<div style="font-size:22px;font-weight:700;color:var(--muted);margin-top:30px">Такой агент на рынке</div>'
    '<div style="font-family:Unbounded,sans-serif;font-weight:800;font-size:78px;margin-top:10px" class="grad">50–70</div><div style="font-size:30px;font-weight:800">тысяч ₽</div></div>' % (
        ''.join('<div class="g" style="padding:18px 26px;display:flex;gap:22px;align-items:center"><span class="n">%d</span><div><h3 style="font-size:25px">%s</h3>'
                '<p style="margin-top:4px;font-size:19px">%s</p></div></div>' % (i + 1, t, p) for i, (t, p) in enumerate((
                    ('Открываем инструмент', todo('[инструмент]')),
                    ('Даём роль', '«Ты — администратор салона…»'),
                    ('Загружаем знания', 'Прайс и ответы на частые вопросы'),
                    ('Задаём правила', 'Что отвечать и когда звать живого администратора'),
                    ('Проверяем', 'Задаём вопросы как клиент')))), ic('spark', 'ic big goldc')),
    head='Практика: <span class="grad">свой AI-агент</span>', sub='Ассистент ' + todo('[салона / школы]') + ', который отвечает по прайсу и правилам.'))


def halfway_bar(done=3):
    line = lambda on: '<div style="flex:1;height:14px;border-radius:7px;margin:0 10px;background:%s"></div>' % (
        'linear-gradient(90deg,#8b5cf6,#3ec7ff)' if on else 'rgba(255,255,255,.12)')
    node = lambda k, on: ('<div style="width:72px;height:72px;border-radius:50%%;display:flex;align-items:center;justify-content:center;'
                          'font-family:Unbounded;font-weight:800;font-size:26px;%s">%d</div>') % (
        'background:linear-gradient(135deg,var(--a1),var(--a2));color:#0b1020;box-shadow:0 0 30px rgba(255,79,139,.6)' if on
        else 'border:2px solid rgba(255,255,255,.3);color:var(--muted)', k)
    out = ''.join((line(k <= done) if k else '') + node(k, k <= done) for k in range(6))
    return out + line(False) + ('<div style="width:96px;height:96px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:44px;'
                                'border:3px solid var(--gold);color:var(--gold);box-shadow:0 0 40px rgba(255,209,102,.45)">★</div>')
add('l3_digit', 3, ('4. Практика', 1), 'Третья цифра кода', digit(3, 3, 'Пришли в чат скрин диалога со своим агентом — за практику бонус'))
add('l3_anketa', 3, ('5. Напоминание', None), 'Больше половины пути + анкета', page(3,
    '<div style="position:absolute;left:96px;right:96px;top:330px;display:flex;align-items:center;gap:0">%s</div>'
    '<div class="g hl" style="position:absolute;left:96px;right:96px;top:600px;display:flex;gap:30px;align-items:center">%s'
    '<div><h3 style="font-size:32px">В конце — анкета и личный разбор</h3><p style="font-size:24px">Подумай уже сейчас: тебе ближе <b>боты</b> или <b>агенты</b>? Это один из вопросов, которые разберём вместе.</p></div></div>' % (
        halfway_bar(), ic('list', 'ic goldc')),
    head='Ты прошёл <span class="grad">больше половины</span>'))
add('l3_sum', 3, ('6. Итог и переход', None), 'Итог урока 3', summary(3, [
    'Агент — не чат с нейросетью, а виртуальный сотрудник под конкретный бизнес',
    'Рынок агентов только формируется — сейчас лучшее время зайти',
    'Ты собрал своего первого агента'],
    'Мини-приложения без кода', 'Как упаковать агента в интерфейс, чтобы клиент ахнул'))

# УРОК 4
add('l4_cover', 4, ('cover',), 'Обложка урока 4',
    cover(4, 'Мини-приложения в Telegram', 'Как выглядят, зачем бизнесу и почему для них не нужен код.',
          ['<span class="tag acc">≈20 минут</span>', '<span class="tag prac">показ</span>', '<span class="tag code">цифра кода №4</span>']))
add('l4_what', 4, ('1. Что это и зачем', 0), 'Приложение внутри Telegram', page(4,
    '<div class="body" style="top:330px;right:700px;display:grid;gap:22px;align-content:start">%s'
    '<div class="g hl" style="padding:26px 30px"><h3 style="font-size:26px">Для клиента — дорогая разработка.<br>Для тебя — задача на несколько дней.</h3></div></div>'
    '<div style="position:absolute;right:360px;top:270px">%s</div><div style="position:absolute;right:110px;top:340px">%s</div>' % (
        ''.join('<div class="g" style="padding:22px 28px;display:flex;gap:22px;align-items:center">%s<div><h3 style="font-size:25px">%s</h3><p style="margin-top:4px;font-size:19px">%s</p></div></div>'
                % (ic(i, 'ic sm'), t, p) for i, t, p in (
                    ('phone', 'Ничего не скачивать', 'Нажал кнопку в боте — открылось приложение'),
                    ('store', 'Каталог, запись, кабинет, игра', 'Всё внутри Telegram'),
                    ('users', 'Аудитория уже там', 'Подписчики → покупатели за пару нажатий'))),
        phone('gym.png', 300, 640, '50% 0%', 'rgba(255,79,139,.7)', 'transform:rotate(-4deg)'),
        phone('manekken.png', 270, 570, '50% 0%', 'rgba(192,38,211,.7)', 'transform:rotate(5deg)')),
    head='Приложение — <span class="grad">прямо в Telegram</span>'))
add('l4_gallery', 4, ('2. Визуал', 0), 'Галерея мини-приложений команды', page(4,
    '<div style="position:absolute;left:96px;top:300px;display:flex;gap:44px;align-items:flex-start">'
    '<div style="text-align:center">%s<div style="margin-top:22px;font-family:Unbounded;font-weight:600;font-size:24px">Школа гимнастики</div><div style="color:var(--muted);font-weight:600;font-size:18px;margin-top:4px">тренер, план, прогресс</div></div>'
    '<div style="text-align:center">%s<div style="margin-top:22px;font-family:Unbounded;font-weight:600;font-size:24px">Манекен</div><div style="color:var(--muted);font-weight:600;font-size:18px;margin-top:4px">AI собирает образы → WB</div></div>'
    '<div style="text-align:center">%s<div style="margin-top:22px;font-family:Unbounded;font-weight:600;font-size:24px;color:var(--gold)">[пример 3]</div></div></div>'
    '<div style="position:absolute;right:96px;top:300px;width:560px;display:grid;gap:22px">'
    '<div class="g hl"><div style="font-size:18px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)">Кейс «Манекена»</div>'
    '<div style="font-family:Unbounded,sans-serif;font-weight:800;font-size:72px;margin-top:12px" class="grad">10,7 тыс.</div>'
    '<p style="font-size:22px">подписчиков с нуля за 4 месяца → бот по коду из видео → мини-приложение с переходом на WB</p></div>'
    '<div class="g"><p style="margin:0;font-size:20px">Когда спрашивают, чем занимаешься:</p><h3 style="margin-top:12px;font-size:28px">«Я делаю мини-приложения для бизнеса»</h3></div></div>' % (
        phone('gym.png', 280, 590, '50% 0%', 'rgba(255,79,139,.6)'), phone('manekken.png', 280, 590, '50% 0%', 'rgba(192,38,211,.6)'),
        slot('[ещё мини-приложение команды: садовод / библиотека / витрина]', 280, 590, 'border-radius:46px')),
    head='Как это выглядит <span class="grad">в жизни</span>'))
add('l4_myth', 4, ('3. Слом стереотипа', None), 'Миф: нужно программировать', page(4,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:1fr 120px 1.3fr;align-items:center">'
    '<div class="g dim" style="display:flex;flex-direction:column;justify-content:center">%s<div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;margin-top:26px;color:#ff8080">Миф</div>'
    '<h3 style="margin-top:12px;font-size:36px;text-decoration:line-through;text-decoration-color:#ff5c5c;text-decoration-thickness:4px">Чтобы сделать такое, нужно уметь программировать</h3></div>%s'
    '<div class="g hl"><div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)">Как на самом деле</div>'
    '<h3 style="margin-top:12px;font-size:36px">Код пишет нейросеть</h3><div style="display:grid;gap:14px;margin-top:26px">%s</div></div></div>' % (
        ic('x', 'ic', '#ff5c5c'), ARR, ''.join('<div style="display:flex;gap:18px;align-items:center;font-size:29px;font-weight:700"><span class="n gold">%d</span>%s</div>' % (i + 1, t)
                                                for i, t in enumerate(('Понять, что нужно клиенту', 'Поставить задачу нейросети', 'Проверить результат')))),
    head='Главный миф', sub='Я не программист — и все эти приложения сделаны именно так.'))
add('l4_combo', 4, ('4. Практика/показ', 0), 'Бот + агент + приложение = продукт', page(4,
    '<div style="position:absolute;left:96px;right:96px;top:360px;display:flex;align-items:center;justify-content:center;gap:26px">%s</div>'
    '<div style="position:absolute;left:0;right:0;top:800px;text-align:center;font-size:24px;font-weight:700;color:var(--muted)">Показ: задача нейросети → приложение → подключаем к боту из урока 2 → открываем в Telegram</div>' % (
        ''.join(('<div style="font-family:Unbounded;font-weight:800;font-size:64px;color:var(--muted)">%s</div>' % s if s else '') +
                '<div class="g %s" style="width:%dpx;text-align:center;display:flex;flex-direction:column;align-items:center">%s<h3 style="margin-top:22px;font-size:30px">%s</h3><p>%s</p></div>' % (
                    cls, w, ic(i, 'ic goldc' if cls else 'ic', c), t, p)
                for s, cls, w, i, c, t, p in (
                    ('', '', 300, 'bot', '#3ec7ff', 'Бот', 'урок 2'), ('+', '', 300, 'spark', '#8b5cf6', 'Агент', 'урок 3'),
                    ('+', '', 300, 'phone', '#ff4f8b', 'Приложение', 'урок 4'), ('=', 'hl', 420, 'done', None, 'Продукт для бизнеса', 'такие связки покупают за ' + todo('[N тыс.]'))))),
    head='Из трёх уроков — <span class="grad">один продукт</span>'))
add('l4_digit', 4, ('4. Практика/показ', 1), 'Четвёртая цифра — код собран', digit(4, 4, 'Сохрани код: он пригодится в конце. Бонус за него — тоже мини-приложение'))
add('l4_sum', 4, ('5. Итог и переход', None), 'Итог урока 4', summary(4, [
    'Мини-приложения — самый эффектный продукт для клиента и не самый сложный для тебя',
    'Код пишет нейросеть, ты ставишь задачу',
    'Бот + агент + приложение = полноценный продукт для бизнеса'],
    'Кому и как это продавать', 'Последний урок — про первых клиентов'))

# УРОК 5
add('l5_cover', 5, ('cover',), 'Обложка урока 5',
    cover(5, 'Где взять первых клиентов', 'Страх первого заказа, способы поиска, первое сообщение и цена.',
          ['<span class="tag acc">≈20–25 минут</span>', '<span class="tag code">анкета + код</span>']))
add('l5_fear', 5, ('1. Сначала про страх', 0), 'Страх → действие → уверенность (плашка к Егору в кадре)', page(5,
    '<div class="body c" style="top:290px">%s</div>' % flow([
        ('help', 'Страх', 'Написать, назвать цену, получить отказ'),
        ('rocket', 'Действие', 'Первое сообщение, первый заказ'),
        ('done', 'Результат', 'Первый ответ, первые деньги'),
        ('heart', 'Уверенность', 'Появляется после действия, а не до', 'hl')]),
    head='Дело не в знаниях. <span class="grad">Дело в страхе</span>', sub='Первую неделю страшно всем. Потом страх уменьшается.'))
add('l5_why', 5, ('2. Зачем клиенту новичок', 0), 'Почему возьмут тебя', page(5,
    '<div class="body c" style="top:280px;bottom:300px">%s</div>'
    '<div class="strip" style="bottom:150px">%s<div>«Где ваши кейсы?» — бот-визитка, агент и приложение из тест-драйва. '
    '<span class="gold">Это твоё первое портфолио.</span></div></div>' % (
        cards([('coin', 'Не у всех есть бюджет', 'Малому бизнесу нужен тот, кто сделает хорошо и дешевле'),
               ('case', 'Опытным некогда', 'Мелкие задачи они не берут'),
               ('heart', 'У тебя есть время', 'И желание сделать на совесть')]), ic('book', 'ic sm')),
    head='Почему возьмут <span class="grad">тебя</span>'))
steps = [('users', 'Ближний круг', 'тебе уже доверяют'), ('home', 'Бизнес рядом', 'кофейня, мастер, сервис'),
         ('chat', 'Чаты и сообщества', 'задачи каждый день'), ('laptop', 'Биржи фриланса', 'старт и первые отзывы'),
         ('radio', 'Сарафанное радио', 'после первых работ'), ('mega', 'Свои соцсети', 'показываешь работы')]
add('l5_ladder', 5, ('3. Где искать', 0), 'Лестница способов', page(5,
    '<div style="position:absolute;left:96px;right:96px;bottom:130px;display:flex;align-items:flex-end;gap:18px">%s</div>'
    '<div class="g" style="position:absolute;left:96px;top:300px;width:600px;padding:26px 30px;border-color:rgba(255,92,92,.45);display:flex;gap:22px">%s<div>'
    '<div style="font-size:18px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#ff8080">Не делай на старте</div>'
    '<p style="font-size:21px;margin-top:8px">✕ массовые холодные рассылки на сотни адресов<br>✕ демпинг на биржах, где побеждает самый дешёвый</p></div></div>' % (
        ''.join('<div class="g" style="flex:1;height:%dpx;padding:24px 22px;display:flex;flex-direction:column;'
                'border-color:rgba(255,255,255,%.2f)">%s<h3 style="font-size:25px;margin-top:18px">%s</h3><p style="font-size:19px;margin-top:6px">%s</p></div>'
                % (250 + i * 66, .14 + i * .05, ic(icn, 'ic sm'), t, p) for i, (icn, t, p) in enumerate(steps)),
        ic('x', 'ic sm', '#ff5c5c')),
    head='Где искать <span class="grad">первых клиентов</span>', sub='От самого простого к самому масштабному. ' + todo('[список площадок — в бонусе]')))
parts = [('#3ec7ff', 'Наблюдение', 'Вижу, запись у вас идёт через личные сообщения, и вы отвечаете вручную.'),
         ('#8b5cf6', 'Решение', 'Это можно перевести на бота: он принимает запись круглосуточно и напоминает клиенту за день.'),
         ('#ff4f8b', 'Польза', 'Меньше пропусков и меньше времени на переписку.'),
         ('#ffd166', 'Мягкий шаг', 'Могу показать, как это будет выглядеть, — это бесплатно.')]
add('l5_msg', 5, ('4. Первое сообщение', 0), 'Шаблон сообщения из 4 частей', page(5,
    '<div style="position:absolute;left:96px;top:330px;width:560px;display:grid;gap:18px">%s</div>'
    '<div style="position:absolute;left:740px;right:96px;top:330px;background:#0e1621;border-radius:30px;padding:34px;border:1px solid rgba(255,255,255,.12);box-shadow:0 40px 80px rgba(0,0,0,.5)">'
    '<div style="background:#2b5278;border-radius:22px 22px 8px 22px;padding:26px 30px;font-size:27px;line-height:1.5;font-weight:600">%s</div>'
    '<div style="text-align:right;color:#6c7883;font-size:16px;margin-top:10px">✓✓ прочитано</div></div>'
    '<div style="position:absolute;left:740px;right:96px;top:850px;font-size:25px;font-weight:700">Нет «я, я, я». <span class="grad">Всё сообщение — про клиента и его выгоду.</span></div>' % (
        ''.join('<div class="g" style="padding:20px 26px;display:flex;gap:20px;align-items:center;border-color:%s"><span class="n" style="background:%s">%d</span><h3 style="font-size:27px">%s</h3></div>'
                % (c, c, i + 1, t) for i, (c, t, _x) in enumerate(parts)),
        ' '.join('<span style="border-bottom:3px solid %s;box-shadow:inset 0 -14px 0 color-mix(in srgb,%s 22%%,transparent)">%s</span>' % (c, c, x) for c, _t, x in parts)),
    head='Первое сообщение, <span class="grad">которое не спам</span>'))
add('l5_price', 5, ('5. Цена и безопасный выход', None), 'Цена и безопасный выход', page(5,
    '<div class="body c" style="top:280px">%s</div>' % cards([
        ('coin', 'Первые заказы', '<span style="font-family:Unbounded;font-weight:800;font-size:44px;color:var(--ink)">' + todo('5–15 тыс.') + '</span><br>и это нормально'),
        ('shield', 'Предоплата', '<span style="display:flex;gap:8px;margin:6px 0 12px"><i style="flex:1;height:18px;border-radius:9px;background:linear-gradient(90deg,var(--a1),var(--a2))"></i>'
                                 '<i style="flex:1;height:18px;border-radius:9px;background:rgba(255,255,255,.18)"></i></span>Половина вперёд, половина после сдачи'),
        ('case', 'Не увольняйся завтра', 'Совмещай. Уходи, когда фриланс несколько месяцев подряд приносит больше зарплаты', 'hl')]),
    head='Цена и <span class="grad">безопасный выход</span>'))
add('l5_paths', 5, ('6. Два пути', 0), 'Два пути', page(5,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:1fr 1.35fr;gap:40px;align-items:center">'
    '<div class="g dim" style="display:flex;flex-direction:column;justify-content:center">%s<h3 style="margin-top:26px;font-size:36px">Закрыть видео</h3>'
    '<p style="font-size:24px">и вернуться к этому «когда-нибудь»</p></div>'
    '<div class="g hl">%s<h3 style="margin-top:26px;font-size:36px">Сделать следующий шаг</h3>'
    '<div style="display:flex;align-items:center;gap:14px;margin-top:22px;font-size:24px;font-weight:800;flex-wrap:wrap"><span class="tag code" style="font-size:20px">Анкета</span>→'
    '<span class="tag code" style="font-size:20px">Личный разбор</span>→<span class="tag code" style="font-size:20px">Твой план</span></div>'
    '<p style="font-size:22px;margin-top:22px">Какие задачи брать первыми, сколько просить и где искать клиентов — именно тебе. Не нужно обучение — так и скажу.</p></div></div>' % (
        ic('x', 'ic', '#a7b0d6'), ic('rocket', 'ic goldc')),
    head='Дальше — <span class="grad">два пути</span>', sub='Бросают не ленивые, а те, кому некому задать вопрос.'))
add('l5_final', 5, ('6. Два пути', 1), 'Финал: анкета + код → бонус', page(5,
    '<div style="position:absolute;left:0;right:0;top:150px;text-align:center"><h1 style="font-size:74px">Пришли в чат <span class="grad">анкету + код</span></h1></div>'
    '<div style="position:absolute;left:0;right:0;top:340px;display:flex;justify-content:center;align-items:center;gap:30px">'
    '<div class="g" style="width:360px;height:250px;display:flex;flex-direction:column;align-items:center;justify-content:center">%s<h3 style="margin-top:20px">Анкета</h3></div>'
    '<div style="font-family:Unbounded;font-weight:800;font-size:64px;color:var(--muted)">+</div>'
    '<div style="display:flex;gap:14px">%s</div>%s'
    '<div class="g hl" style="width:360px;height:250px;display:flex;flex-direction:column;align-items:center;justify-content:center">%s<h3 style="margin-top:20px">%s</h3></div></div>'
    '<div style="position:absolute;left:0;right:0;top:700px;text-align:center;font-family:Unbounded,sans-serif;font-weight:600;font-size:34px;line-height:1.4">'
    'Спасибо, что дошёл до конца.<br><span style="color:var(--muted)">Ты уже сделал больше, чем большинство. До встречи на разборе.</span></div>' % (
        ic('list'), ''.join('<div class="slotd on" style="width:110px;height:150px;font-size:80px">X</div>' for _ in range(4)), ARR, ic('gift', 'ic goldc'), todo('[бонус]')),
    chip='Урок 5 · Финал'))


# ---------- сборка ----------

def render(ids):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge')
        pg = b.new_page(viewport={'width': 1920, 'height': 1080})
        for sid in ids:
            pg.goto('file:///' + os.path.join(DECK, sid + '.html').replace('\\', '/'))
            pg.evaluate('document.fonts.ready')
            pg.wait_for_timeout(250)
            pg.screenshot(path=os.path.join(DECK, sid + '.jpg'), type='jpeg', quality=90)
            print('  ', sid)
        b.close()


def map_slide():
    from PIL import Image
    Image.open(os.path.join(SL, 'karta_v4.png')).convert('RGB').save(os.path.join(DECK, 'l0_map.jpg'), quality=90)


def inject_md():
    """вставить картинки слайдов в сценарий под нужные пункты (повторный запуск ничего не дублирует)"""
    md = open(MD, encoding='utf-8').read()
    lines = [l for l in md.split('\n') if 'slides/deck/' not in l]
    lessons = {0: 'Вводный урок', 1: 'Урок 1.', 2: 'Урок 2.', 3: 'Урок 3.', 4: 'Урок 4.', 5: 'Урок 5.'}
    plan = {}  # индекс строки -> [картинки]
    for sid, les, anchor, cap, _ in S:
        start = next(i for i, l in enumerate(lines) if l.startswith('## ' + lessons[les]))
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
        if anchor[0] == 'cover':
            at = next(i for i in range(start, end) if lines[i].startswith('**Цель урока'))
        else:
            h = next(i for i in range(start, end) if lines[i].startswith('### ') and anchor[0] in lines[i])
            hend = next((i for i in range(h + 1, end) if lines[i].startswith('### ')), end)
            scr = [i for i in range(h, hend) if lines[i].startswith('**На экране:**')]
            at = scr[anchor[1]] if anchor[1] is not None and len(scr) > anchor[1] else h
        plan.setdefault(at, []).append('![%s](slides/deck/%s.jpg)' % (cap, sid))
    out = []
    for i, l in enumerate(lines):
        out.append(l)
        if i in plan:
            out += [''] + plan[i]
    txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(out))
    open(MD, 'w', encoding='utf-8').write(txt)


def deck_page():
    """страница колоды: все слайды по урокам, просмотр стрелками, комментарии по урокам"""
    tpl = open(os.path.join(P, 'docs', 'course', 'test_drive_plan.html'), encoding='utf-8').read()
    style = re.search(r'<style>(.*?)</style>', tpl, re.S).group(1)
    script = re.search(r'<script>(.*?)</script>', tpl, re.S).group(1).replace("var PAGE = 'test_drive_plan'", "var PAGE = 'slides_deck'")
    blocks, flat = [], []
    for n, chip, short, acc in LESSONS:
        items = [s for s in S if s[1] == n]
        tiles = ''
        for sid, _l, _a, cap, _h in items:
            tiles += '<a class="sl" href="slides/deck/%s.jpg" data-i="%d"><img src="slides/deck/%s.jpg" loading="lazy" alt=""><span>%s</span></a>' % (
                sid, len(flat), sid, html.escape(cap))
            flat.append(['slides/deck/%s.jpg' % sid, cap])
        blocks.append('<div class="card" id="u%d" data-block="u%d"><div class="num" style="color:%s">%s</div><h2>%d слайдов</h2><div class="tiles">%s</div></div>'
                      % (n, n, acc, html.escape(chip), len(items), tiles))
    extra = ('.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:10px 0 6px}@media(max-width:800px){.tiles{grid-template-columns:1fr 1fr}}'
             '.sl{display:block;text-decoration:none;color:var(--muted);font-size:13px}.sl img{display:block;width:100%;border-radius:10px;box-shadow:0 4px 14px rgba(20,24,46,.25)}'
             '.sl span{display:block;margin-top:5px;line-height:1.3}.w{max-width:1100px}'
             '#lb{position:fixed;inset:0;background:rgba(5,7,15,.94);display:none;align-items:center;justify-content:center;flex-direction:column;z-index:99}'
             '#lb img{max-width:96vw;max-height:84vh;border-radius:10px}#lb div{color:#fff;margin-top:14px;font-size:15px}'
             '#lb button{position:absolute;top:50%;background:rgba(255,255,255,.12);color:#fff;border:0;font-size:34px;width:56px;height:56px;border-radius:50%;cursor:pointer}'
             '#lb .p{left:16px}#lb .nx{right:16px}#lb .c{top:16px;right:16px}')
    lb = ('<div id="lb"><img><div></div><button class="p">‹</button><button class="nx">›</button><button class="c">×</button></div>'
          '<script>(function(){var S=%s,i=0,lb=document.getElementById("lb"),im=lb.querySelector("img"),cp=lb.querySelector("div");'
          'function show(k){i=(k+S.length)%%S.length;im.src=S[i][0];cp.textContent=(i+1)+" / "+S.length+" · "+S[i][1];lb.style.display="flex";}'
          'document.querySelectorAll(".sl").forEach(function(a){a.onclick=function(e){e.preventDefault();show(+a.dataset.i);};});'
          'lb.querySelector(".p").onclick=function(){show(i-1)};lb.querySelector(".nx").onclick=function(){show(i+1)};'
          'lb.querySelector(".c").onclick=function(){lb.style.display="none"};'
          'document.addEventListener("keydown",function(e){if(lb.style.display!=="flex")return;if(e.key==="ArrowRight")show(i+1);if(e.key==="ArrowLeft")show(i-1);if(e.key==="Escape")lb.style.display="none";});})();</script>'
          ) % json.dumps(flat, ensure_ascii=False)
    out = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
           '<title>Слайды тест-драйва</title><style>%s%s</style></head><body><div class="w">'
           '<h1>Слайды тест-драйва</h1><p class="lead">Все слайды всех видео в одном стиле (тёмный, «светящаяся дорога» — как карта v1/v4). %d слайдов. '
           'Нажмите на слайд — откроется на весь экран, листать стрелками. Жёлтым пунктиром — что нужно вставить команде. Правки — в комментариях под уроком.</p>'
           '<div class="who">Как вас подписать: <input id="name" placeholder="Ваше имя" maxlength="40"></div>%s'
           '<div class="card general" data-block="general"><div class="num">Общее</div><h2>Комментарии к стилю в целом</h2></div>'
           '<div class="foot"><a href="/course/test_drive_script.html">Сценарий тест-драйва</a> · <a href="/materials.html">Все материалы</a></div>'
           '</div><script>%s</script>%s</body></html>') % (style, extra, len(flat), ''.join(blocks), script, lb)
    open(os.path.join(P, 'docs', 'course', 'slides_deck.html'), 'w', encoding='utf-8').write(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    os.makedirs(DECK, exist_ok=True)
    ids = []
    for sid, _l, _a, _c, htm in S:
        if htm is None or (args and sid not in args):
            continue
        open(os.path.join(DECK, sid + '.html'), 'w', encoding='utf-8').write(htm)
        ids.append(sid)
    if '--no-render' not in sys.argv:
        render(ids)
        map_slide()
    if not args:
        inject_md()
        deck_page()
    print('ok', len(S), 'слайдов')


if __name__ == '__main__':
    main()
