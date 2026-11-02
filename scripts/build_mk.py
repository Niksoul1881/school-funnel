import re, html, sys, json

TEMPLATE, OUT = sys.argv[1], sys.argv[2]
PARTS = sys.argv[3:]


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', s)
    s = re.sub(r'\[([^\]]{1,400})\]', r'<span class="ph">[\1]</span>', s)
    return s


def parse(md):
    posts = []
    section = None
    for chunk in re.split(r'^(?=### |## )', md, flags=re.M):
        if chunk.startswith('## '):
            section = chunk.split('\n', 1)[0][3:].strip()
            continue
        if not chunk.startswith('### '):
            continue
        head, _, body = chunk.partition('\n')
        m = re.match(r'###\s+(\S+)\s*[·•.\-—]\s*(.+)', head)
        num, title = (m.group(1), m.group(2).strip()) if m else ('', head[4:].strip())
        meta, text_lines, in_meta = {}, [], True
        for ln in body.split('\n'):
            mm = re.match(r'^\s*[-*]\s*(Рубрика|Зачем|Идея|Медиа|Кнопки|День|Факты|Для команды)\s*:\s*(.*)', ln)
            if in_meta and mm:
                last = mm.group(1)
                meta[last] = mm.group(2).strip()
                continue
            if in_meta and meta and ln.startswith('  ') and ln.strip():
                meta[last] += ' ' + ln.strip()
                continue
            if in_meta and not ln.strip():
                if meta:
                    in_meta = False
                continue
            in_meta = False
            text_lines.append(ln.rstrip())
        while text_lines and not text_lines[-1].strip():
            text_lines.pop()
        while text_lines and (text_lines[-1].strip() in ('---', '***')):
            text_lines.pop()
        text = '\n'.join(text_lines).strip()
        posts.append(dict(num=num, title=title, meta=meta, text=text, section=section))
    return posts


all_posts = []
for p in PARTS:
    all_posts += parse(open(p, encoding='utf-8').read().replace('\r\n', '\n'))


def card(p, idx):
    m = p['meta']
    paras = re.split(r'\n\s*\n', p['text'])
    body = ''.join('<p>' + '<br>'.join(inline(l) for l in para.split('\n')) + '</p>' for para in paras if para.strip())
    btns = ''
    k = m.get('Кнопки', '')
    if k and not k.lower().startswith('нет'):
        labels = re.findall(r'\[([^\]→]+?)\s*(?:→[^\]]*)?\]', k) or [k]
        btns = '<div class="btns">' + ''.join('<span>%s</span>' % html.escape(b.strip()) for b in labels) + '</div>'
    media = m.get('Медиа', '')
    img = '' if (not media or media.lower().startswith('без')) else '<div class="img">%s</div>' % html.escape(media)
    info = ''.join('<div><b>%s:</b> %s</div>' % (html.escape(key), inline(m[key])) for key in ('День', 'Рубрика', 'Зачем', 'Идея', 'Факты', 'Для команды') if m.get(key))
    plain = html.escape(p['text'], quote=True)
    return ('<div class="tg"><div class="lbl"><span class="no">%s</span> %s</div>'
            '<div class="bubble"><div class="ch">Манекен</div>%s%s%s<div class="ft">👁 · <a href="javascript:void(0)" class="cp" data-i="%d">скопировать текст</a></div></div>'
            '<textarea class="raw" id="raw%d">%s</textarea><div class="info">%s</div></div>') % (
        html.escape(p['num']), inline(p['title']), img, body, btns, idx, idx, plain, info)


groups = {}
order = []
for i, p in enumerate(all_posts):
    g = 'warm' if p['num'].upper().startswith('W') else 'base'
    groups.setdefault(g, []).append(card(p, i))

page = open(TEMPLATE, encoding='utf-8').read()
page = page.replace('%%BASE%%', ''.join(groups.get('base', []))).replace('%%WARM%%', ''.join(groups.get('warm', [])))
page = page.replace('%%NBASE%%', str(len(groups.get('base', [])))).replace('%%NWARM%%', str(len(groups.get('warm', []))))
open(OUT, 'w', encoding='utf-8').write(page)
print('base', len(groups.get('base', [])), 'warm', len(groups.get('warm', [])))
# also plain export
with open(OUT.replace('.html', '_posts.txt'), 'w', encoding='utf-8') as f:
    for p in all_posts:
        f.write('==== %s · %s\n%s\n\n' % (p['num'], p['title'], p['text']))
