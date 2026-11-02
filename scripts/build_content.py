import re, html, sys, os

TEMPLATE, OUT = sys.argv[1], sys.argv[2]
REPORTS = sys.argv[3:]  # pairs: title=path


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank">\1</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def render(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        st = ln.strip()
        if not st or st == '---':
            i += 1
            continue
        m = re.match(r'^(#{1,6})\s+(.*)', st)
        if m:
            lvl = min(len(m.group(1)) + 2, 6)
            out.append('<h%d>%s</h%d>' % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue
        if st.startswith('```'):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith('```'):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append('<pre>' + '\n'.join(buf) + '</pre>')
            continue
        if st.startswith('>'):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append('<div class="note">' + '<br>'.join(inline(b) for b in buf if b) + '</div>')
            continue
        if st.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                raw = lines[i].strip().strip('|').replace('\\|', '\u0001')
                cells = [c.strip().replace('\u0001', '|') for c in raw.split('|')]
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
                m2 = re.match(r'^(\s*)([-*]|\d+[.)])\s+(.*)', l2)
                if m2:
                    items.append([1 if len(m2.group(1)) >= 2 else 0, [m2.group(3)]])
                    i += 1
                elif l2.startswith('  ') and l2.strip() and items:
                    items[-1][1].append(l2.strip())
                    i += 1
                elif not l2.strip() and i + 1 < n and re.match(r'^\s{2,}\S', lines[i + 1]) and items:
                    i += 1
                else:
                    break
            tag = 'ol' if ordered else 'ul'
            h, sub = '<%s>' % tag, False
            for lvl, parts in items:
                if lvl == 1 and not sub:
                    h += '<ul>'; sub = True
                elif lvl == 0 and sub:
                    h += '</ul>'; sub = False
                h += '<li>' + '<br>'.join(inline(p) for p in parts) + '</li>'
            if sub:
                h += '</ul>'
            out.append(h + '</%s>' % tag)
            continue
        buf = []
        while i < n:
            s2 = lines[i].strip()
            if buf and (not s2 or s2 == '---' or re.match(r'^#{1,6}\s', s2) or s2.startswith(('>', '|', '```')) or re.match(r'^\s*([-*]|\d+[.)])\s+', lines[i])):
                break
            if not buf and not s2:
                break
            buf.append(s2)
            i += 1
        if not buf:
            i += 1
            continue
        out.append('<p>' + '<br>'.join(inline(b) for b in buf) + '</p>')
    return '\n'.join(out)


blocks = []
for arg in REPORTS:
    title, path = arg.split('=', 1)
    if not os.path.exists(path):
        continue
    md = open(path, encoding='utf-8').read().replace('\r\n', '\n')
    md = re.sub(r'\A#\s+[^\n]*\n', '', md)  # drop own H1, we use the summary title
    blocks.append('<details class="rep"><summary>%s</summary><div class="repbody">%s</div></details>' % (html.escape(title), render(md.split('\n'))))

page = open(TEMPLATE, encoding='utf-8').read().replace('%%REPORTS%%', '\n'.join(blocks))
open(OUT, 'w', encoding='utf-8').write(page)
print('reports', len(blocks))
