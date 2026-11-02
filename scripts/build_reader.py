import re, html, sys

SRC, OUT = sys.argv[1], sys.argv[2]
md = open(SRC, encoding='utf-8').read().replace('\r\n', '\n')


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)

    def ph(m):
        t = m.group(1)
        if t.lower().startswith('кнопка'):
            label = t.split(':', 1)[1].split('→')[0].strip() if ':' in t else t
            return '<a class="btn">' + label + '</a>'
        if t.startswith('МЕМ'):
            return '<span class="mem">🖼 ' + t[4:].strip(' :') + '</span>'
        return '<span class="ph">' + t + '</span>'
    return re.sub(r'\[([^\]]{1,600})\]', ph, s)


def render(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        st = lines[i].strip()
        if not st:
            i += 1; continue
        if st.startswith('# '):
            out.append('<h1>' + inline(st[2:]) + '</h1>'); i += 1; continue
        if st.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            h = '<table>'
            for k, r in enumerate(rows):
                tag = 'th' if k == 0 else 'td'
                h += '<tr>' + ''.join('<%s>%s</%s>' % (tag, inline(c), tag) for c in r) + '</tr>'
            out.append(h + '</table>'); continue
        if re.match(r'^[—✅🤖📰📊👀📸🎓🎬📞]|^\d️⃣', st):
            items = []
            while i < n and lines[i].strip() and re.match(r'^[—✅🤖📰📊👀📸🎓🎬📞]|^\d️⃣', lines[i].strip()):
                items.append(lines[i].strip()); i += 1
            cls = 'cards' if items[0][0] in '🤖📰📊👀📸🎓🎬📞' else 'list'
            out.append('<div class="%s">' % cls + ''.join('<div class="li">%s</div>' % inline(x.lstrip('— ').strip()) if x.startswith('—') else '<div class="li">%s</div>' % inline(x) for x in items) + '</div>')
            continue
        buf = []
        while i < n and lines[i].strip() and not lines[i].strip().startswith(('# ', '|')) and not re.match(r'^[—✅🤖📰📊👀📸🎓🎬📞]|^\d️⃣', lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        txt = '<br>'.join(inline(b) for b in buf)
        if len(buf) == 1 and re.fullmatch(r'\*\*.+\*\*.*', buf[0]) and buf[0].startswith('**«'):
            out.append('<h2>' + txt + '</h2>')
        else:
            out.append('<p>' + txt + '</p>')
    return '\n'.join(out)


arts = []
for part in re.split(r'^## ', md, flags=re.M)[1:]:
    head, _, body = part.partition('\n')
    keep = []
    for ln in body.split('\n'):
        s = ln.strip()
        if s.startswith('### ') or s.startswith('Задача блока:') or s.startswith('>'):
            continue
        keep.append(ln)
    arts.append((head.strip(), render(keep)))

page = '''<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Статьи — чистовик для чтения</title>
<style>
body{margin:0;background:#f4f1ea;font-family:Georgia,"Times New Roman",serif;color:#1d1d1f;font-size:19px;line-height:1.7}
.top{position:sticky;top:0;background:#14182e;color:#fff;font:14px "Segoe UI",Arial,sans-serif;padding:10px 16px;z-index:5}
.top a{color:#ffd8a8;margin-right:14px}
article{max-width:680px;margin:28px auto 60px;background:#fff;padding:44px 48px 52px;border-radius:6px;box-shadow:0 2px 18px rgba(0,0,0,.06)}
.tag{font:12px "Segoe UI",Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#a0522d}
h1{font-family:"Segoe UI",Arial,sans-serif;font-size:32px;line-height:1.2;margin:8px 0 22px}
h2{font-family:"Segoe UI",Arial,sans-serif;font-size:23px;line-height:1.3;margin:38px 0 12px}
p{margin:0 0 20px}
.list{margin:0 0 22px}
.list .li{padding:4px 0 4px 2px}
.cards{margin:6px 0 24px}
.cards .li{background:#faf8f3;border-left:3px solid #e8a33d;border-radius:4px;padding:10px 14px;margin:0 0 10px;font-size:17.5px}
table{border-collapse:collapse;width:100%;margin:6px 0 24px;font:16px "Segoe UI",Arial,sans-serif}
th,td{border-bottom:1px solid #eee;padding:9px 8px;text-align:left}th{color:#777;font-size:13px;text-transform:uppercase}
td:last-child{font-weight:700;white-space:nowrap}
.mem{display:block;margin:26px 0;padding:34px 18px;text-align:center;background:#f0edff;border:2px dashed #b197fc;border-radius:8px;color:#5f3dc4;font:15px "Segoe UI",Arial,sans-serif}
.ph{background:#fff3bf;padding:1px 4px;border-radius:3px;font:15.5px "Segoe UI",Arial,sans-serif;color:#7a5a00}
a.btn{display:block;text-align:center;background:#e8590c;color:#fff;font:700 16px "Segoe UI",Arial,sans-serif;padding:14px;border-radius:10px;margin:22px 0;text-decoration:none}
@media(max-width:640px){article{padding:26px 18px;margin:0}body{font-size:17.5px}h1{font-size:25px}}
</style></head><body>
<div class="top">Чистовик для чтения — как статьи увидит человек · <a href="#a1">Статья 1</a><a href="#a2">Статья 2</a></div>
'''
for k, (title, body) in enumerate(arts, 1):
    page += '<article id="a%d"><div class="tag">%s</div>%s</article>\n' % (k, html.escape(title), body)
page += '</body></html>'
open(OUT, 'w', encoding='utf-8').write(page)
print('articles', len(arts))
