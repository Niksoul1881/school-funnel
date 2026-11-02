import re, html, sys

SRC = sys.argv[1]
OUT = sys.argv[2]
md = open(SRC, encoding='utf-8').read().replace('\r\n', '\n')


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank">\1</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)

    def ph(m):
        t = m.group(1)
        if t.lower().startswith('кнопка'):
            return '<span class="btn-ph">' + t + '</span>'
        if t.startswith('МЕМ'):
            return '<span class="mem">🖼 ' + t + '</span>'
        return '<span class="ph">[' + t + ']</span>'
    s = re.sub(r'\[([^\]<>]{1,400})\]', ph, s)
    return s


def render(lines):
    out = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        st = ln.strip()
        if not st or st == '---':
            i += 1
            continue
        if st.startswith('# '):
            out.append('<h3 class="art">' + inline(st[2:]) + '</h3>')
            i += 1
            continue
        if st.startswith('#### '):
            out.append('<h4>' + inline(st[5:]) + '</h4>')
            i += 1
            continue
        if st.startswith('Задача блока:'):
            out.append('<div class="goal"><b>Задача блока</b>' + inline(st[len('Задача блока:'):].strip()) + '</div>')
            i += 1
            continue
        if st.startswith('>'):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append('<div class="team">' + '<br>'.join(inline(b) for b in buf if b) + '</div>')
            continue
        if st.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            h = '<div class="tbl"><table>'
            for k, r in enumerate(rows):
                tag = 'th' if k == 0 else 'td'
                h += '<tr>' + ''.join('<%s>%s</%s>' % (tag, inline(c), tag) for c in r) + '</tr>'
            out.append(h + '</table></div>')
            continue
        if re.match(r'^(\s*)([-*]|\d+[.)])\s+', ln):
            ordered = bool(re.match(r'^\s*\d+[.)]\s+', ln))
            items = []
            while i < n:
                l2 = lines[i]
                m = re.match(r'^(\s*)([-*]|\d+[.)])\s+(.*)', l2)
                if m:
                    lvl = 1 if len(m.group(1)) >= 2 else 0
                    items.append([lvl, m.group(3)])
                    i += 1
                elif l2.startswith('  ') and l2.strip() and items:
                    items[-1][1] += '<br>' + l2.strip()
                    i += 1
                else:
                    break
            tag = 'ol' if ordered else 'ul'
            h = '<%s>' % tag
            open_sub = False
            for lvl, t in items:
                txt = t if '<br>' not in t else t
                parts = txt.split('<br>')
                rendered = '<br>'.join(inline(p) for p in parts)
                if lvl == 1 and not open_sub:
                    h += '<ul>'
                    open_sub = True
                elif lvl == 0 and open_sub:
                    h += '</ul>'
                    open_sub = False
                h += '<li>' + rendered + '</li>'
            if open_sub:
                h += '</ul>'
            out.append(h + '</%s>' % tag)
            continue
        buf = []
        while i < n:
            s2 = lines[i].strip()
            if not s2 or s2.startswith(('#', '>', '|', 'Задача блока:')) or re.match(r'^\s*([-*]|\d+[.)])\s+', lines[i]) or s2 == '---':
                break
            buf.append(s2)
            i += 1
        out.append('<p>' + '<br>'.join(inline(b) for b in buf) + '</p>')
    return '\n'.join(out)


# split into preamble / sections / blocks
parts = re.split(r'^## ', md, flags=re.M)
pre = parts[0]
pre_lines = [l for l in pre.split('\n') if not l.startswith('# ')]
sections = []
for p in parts[1:]:
    head, _, body = p.partition('\n')
    m = re.match(r'([A-ZА-Я])\.\s*(.*)', head.strip())
    letter, title = (m.group(1), m.group(2)) if m else ('?', head.strip())
    bl = re.split(r'^### ', body, flags=re.M)
    intro = bl[0]
    blocks = []
    for b in bl[1:]:
        bh, _, bb = b.partition('\n')
        mm = re.match(r'Блок\s+(\d+)\s*[—-]\s*(.*)', bh.strip())
        num, btitle = (mm.group(1), mm.group(2)) if mm else (str(len(blocks) + 1), bh.strip())
        blocks.append((num, btitle, bb))
    sections.append((letter, title, intro, blocks))

total = sum(len(s[3]) for s in sections)

nav = ''.join('<a href="#sec-%s"><b>%s</b> %s</a>' % (s[0], s[0], html.escape(s[1])) for s in sections)

body = []
for letter, title, intro, blocks in sections:
    body.append('<section id="sec-%s"><div class="wrap">' % letter)
    body.append('<h2><span class="letter">%s</span>%s</h2>' % (letter, inline(title)))
    ir = render(intro.split('\n'))
    if ir.strip():
        body.append('<div class="intro">' + ir + '</div>')
    for num, btitle, bb in blocks:
        bid = '%s-%s' % (letter, num)
        body.append('<div class="block" id="b-%s" data-id="%s" data-title="%s">' % (bid, bid, html.escape(title + ' · ' + btitle, quote=True)))
        body.append('<div class="bhead"><span class="bid">%s</span><span class="btitle">%s</span></div>' % (bid, inline(btitle)))
        body.append('<div class="btext">' + render(bb.split('\n')) + '</div>')
        body.append('<div class="cbox"><label for="c-%s">Комментарий к %s</label><textarea id="c-%s" data-id="%s" rows="2" placeholder="Что добавить, убрать или переписать в этом блоке…"></textarea></div>' % (bid, bid, bid, bid))
        body.append('</div>')
    gid = '%s-общее' % letter
    body.append('<div class="block general" data-id="%s" data-title="%s"><div class="cbox"><label for="c-%s">Общий комментарий к разделу %s</label><textarea id="c-%s" data-id="%s" rows="2" placeholder="Замечания ко всему разделу целиком…"></textarea></div></div>' % (gid, html.escape(title + ' · весь раздел', quote=True), gid, letter, gid, gid))
    body.append('</div></section>')

TEMPLATE = open(sys.argv[3], encoding='utf-8').read()
page = (TEMPLATE
        .replace('%%NAV%%', nav)
        .replace('%%PRE%%', render(pre_lines))
        .replace('%%BODY%%', '\n'.join(body))
        .replace('%%TOTAL%%', str(total)))
open(OUT, 'w', encoding='utf-8').write(page)
print('sections', len(sections), 'blocks', total)
