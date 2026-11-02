"""Лента всех сообщений конкурентов по школам и веткам (активная / ленивая) для финального отчёта.
Берёт данные так же, как доска (build_schemes.py): выгрузки folder_*/bots_* + log.jsonl обеих веток, вычищает личные данные.
Запуск: python scripts/build_funnels_report.py  -> sources/research/боты/_лента_сообщений.md"""
import os, sys, re

os.environ['NO_MEDIA'] = '1'
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P, 'scripts'))
import build_schemes as bs  # при импорте пересобирает доску — это нормально

OUT = os.path.join(P, 'sources', 'research', 'боты', '_лента_сообщений.md')
GROUPS = [  # (название в отчёте, префиксы школ из доски)
    ('Пурвиньш', ['Пурвиньш']), ('Паутов', ['Паутов']), ('Муратов', ['Муратов']), ('ITGIRLS', ['ITGIRLS']),
    ('BotHelp', ['BotHelp']), ('Zerocoder', ['Zerocoder']), ('Кораблёв', ['Кораблёв']),
    ('Даня (@myvibeai)', ['Даня']), ('GetHelpers', ['GetHelpers']), ('Фриланс налегке', ['frilans_na_legke_bot']),
]
EXTRA_SCRUB = [(re.compile(r'Якушев\w*', re.I), '[Фамилия]'), (re.compile(r'\b\d{9,11}\b'), '[ID]')]


def clean(t):
    t = bs.scrub(t or '')
    for rx, rep in EXTRA_SCRUB:
        t = rx.sub(rep, t)
    return t


def section(items):
    if not items:
        return ['_Сообщений нет._', '']
    out, t0, prev = [], bs.ts(items[0]), None
    for m in items:
        t = bs.ts(m)
        since = bs.fmt_delta(t - t0).replace('+', '') if (t and t0) else ''
        gap = (' · через ' + bs.fmt_delta(t - prev).replace('+', '')) if (t and prev and t - prev >= 60) else ''
        prev = t or prev
        who = 'Мы' if m.get('out') else bs.lane(m.get('chat'))
        k = bs.KIND_NAME.get(bs.kind(m), '')
        text = clean(m.get('text') or m.get('note') or '').strip()
        if not text:
            text = '[%s]' % bs.MEDIA_RU.get(m.get('media'), 'медиа')
        text = re.sub(r'\n{2,}', '\n', text).replace('\n', ' / ')
        if len(text) > 900:
            text = text[:900] + ' …'
        btns = [clean(b.get('text', '')) for b in (m.get('buttons') or [])]
        date = (m.get('time') or '')[5:16].replace('T', ' ')
        out.append('- **%s** (%s%s) · %s%s — %s%s' % (since or '0 сек', date, gap, who, (', ' + k) if k and not m.get('out') else '', text,
                                                   ('  `[' + ' | '.join(btns) + ']`') if btns else ''))
    out.append('')
    return out


def main():
    lines = ['# Приложение: все сообщения по порядку', '',
             'Время — от первого сообщения школы в ветке (обычно «Старт»), в скобках дата и интервал после предыдущего. '
             '«Мы» — действия нашего аккаунта. Личные данные вычищены. Сгенерировано scripts/build_funnels_report.py.', '']
    for title, prefixes in GROUPS:
        lines += ['## ' + title, '']
        for branch, data in (('Активная ветка (основной аккаунт: проходит шаги)', bs.active), ('Ленивая ветка (второй аккаунт: только «Старт»)', bs.lazy)):
            schools = sorted({m['school'] for m in data if any(m['school'].startswith(p) for p in prefixes)})
            lines += ['### ' + branch, '']
            if not schools:
                lines += ['_Сообщений нет._', '']
            for s in schools:
                items = [m for m in data if m['school'] == s]
                if len(schools) > 1:
                    lines += ['#### ' + s, '']
                lines += section(items)
    open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
    print('ok', OUT, sum(1 for l in lines if l.startswith('- **')), 'сообщений')


if __name__ == '__main__':
    main()
