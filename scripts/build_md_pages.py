"""Превращает отчёты из sources/research (*.md) в страницы для сайта команды -> docs/research.
Запуск: python scripts/build_md_pages.py
"""
import os, re, html

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(P, 'sources', 'research')
OUT = os.path.join(P, 'docs', 'research')

PAGES = [  # (исходник, страница, заголовок)
    ('сайты_входы.md', 'сайты_конкурентов.html', 'Сайты конкурентов: как попасть в воронку'),
    (os.path.join('боты', 'пурвиньш_этап1.md'), 'пурвиньш_этап1.html', 'Пурвиньш: первый этап воронки по минутам'),
    (os.path.join('боты', 'журнал.md'), 'журнал_прохождения.html', 'Журнал прохождения ботов'),
    (os.path.join('боты', 'ленивая_ветка.md'), 'ленивая_ветка.html', 'Ленивая ветка: дожимы'),
    (os.path.join('боты', 'разбор_пурвиньш_шпаргалка.md'), 'шпаргалка_созвон_пурвиньш.html', 'Шпаргалка: созвон-разбор у Пурвиньша'),
]

CSS = ('body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#f4f6fb;color:#1d2433;line-height:1.55}'
       '.w{max-width:1100px;margin:0 auto;padding:24px 16px}a{color:#1c5fd6}'
       'h1{font-size:26px}h2{margin-top:32px;border-bottom:2px solid #e3e7f0;padding-bottom:6px}h3{margin-top:24px}'
       'code{background:#eef1f7;padding:1px 5px;border-radius:4px;font-size:13px}'
       '.t{overflow-x:auto;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(20,24,46,.06);margin:14px 0}'
       'table{border-collapse:collapse;font-size:13px;min-width:900px}th,td{border:1px solid #e3e7f0;padding:7px 9px;vertical-align:top;text-align:left}'
       'th{background:#fff1db;position:sticky;top:0}tr:nth-child(even) td{background:#fafbfd}'
       'hr{border:0;border-top:1px solid #dfe3ec;margin:26px 0}.back{display:inline-block;margin-bottom:10px}')


SCRUB = [  # сайт открыт без пароля — личные данные наружу не выносим
    (re.compile(r'\+?7[\s(-]*9\d{2}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}'), '[телефон]'),
    (re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'), '[почта]'),
    (re.compile(r'tg_id=\d+'), 'tg_id=…'), (re.compile(r'td_id=-?\d+'), 'td_id=…'),
    (re.compile(r'Якушев\w*\s+Никит\w*|Никит\w*\s+Якушев\w*'), '[Имя Фамилия]'),
    (re.compile(r'\bНикит[аеуы]\b|\bНикитой\b'), '[Имя]'),
    (re.compile(r'@Soulnikita|@Unseen_echo', re.I), '@[ник]'),
]


def scrub(t):
    for rx, rep in SCRUB:
        t = rx.sub(rep, t)
    return t


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<i>\1</i>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank">\1</a>', s)
    return s


def md_to_html(text):
    out, lst, para, rows = [], None, [], []

    def flush():
        nonlocal lst, para, rows
        if para:
            out.append('<p>%s</p>' % inline(' '.join(para))); para = []
        if lst:
            out.append('<%s>%s</%s>' % (lst[0], ''.join('<li>%s</li>' % inline(x) for x in lst[1]), lst[0])); lst = None
        if rows:
            cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows if not re.match(r'^\s*\|?[\s:|-]+\|?\s*$', r)]
            if cells:
                head = ''.join('<th>%s</th>' % inline(c) for c in cells[0])
                body = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in cells[1:])
                out.append('<div class="t"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body))
            rows = []

    for line in text.splitlines():
        s = line.rstrip()
        if s.startswith('|'):
            if para or lst:
                flush()
            rows.append(s); continue
        if rows:
            flush()
        m = re.match(r'^(#{1,4})\s+(.*)', s)
        if m:
            flush(); n = len(m.group(1)); out.append('<h%d>%s</h%d>' % (n, inline(m.group(2)), n)); continue
        if re.match(r'^-{3,}$', s):
            flush(); out.append('<hr>'); continue
        m = re.match(r'^\s*(?:[-*]|(\d+)\.)\s+(.*)', s)
        if m:
            tag = 'ol' if m.group(1) else 'ul'
            if para:
                flush()
            if not lst or lst[0] != tag:
                flush(); lst = (tag, [])
            lst[1].append(m.group(2)); continue
        if not s.strip():
            flush(); continue
        if lst:
            flush()
        para.append(s.strip())
    flush()
    return '\n'.join(out)


def main():
    for src, dst, title in PAGES:
        path = os.path.join(SRC, src)
        if not os.path.exists(path):
            continue
        body = md_to_html(scrub(open(path, encoding='utf-8').read()))
        page = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                '<title>%s</title><style>%s</style></head><body><div class="w"><a class="back" href="/materials.html">← Все материалы</a>%s</div></body></html>'
                % (html.escape(title), CSS, body))
        open(os.path.join(OUT, dst), 'w', encoding='utf-8').write(page)
        print('ok', dst)


if __name__ == '__main__':
    main()
