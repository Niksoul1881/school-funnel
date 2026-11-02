import sys, json, statistics, collections, datetime, re
sys.stdout.reconfigure(encoding='utf-8')
# usage: tgstats.py <tgdir> <channel> [lines]
d, ch = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else 'stats'
dump = json.load(open(f'{d}/dump_{ch}.json', encoding='utf-8'))
meta = json.load(open(f'{d}/meta_{ch}.json', encoding='utf-8'))
pm = meta['posts']

def v(s):
    if not s: return None
    s = s.replace(',', '.')
    m = 1
    if s.endswith('K'): m, s = 1000, s[:-1]
    if s.endswith('M'): m, s = 1000000, s[:-1]
    return int(float(s) * m)

for p in dump:
    p['v'] = v(p['views']); p['m'] = pm[str(p['id'])]
if mode == 'stats':
    print('##', ch, meta['title'], meta['subs'])
    print('desc:', meta['desc'])
    ds = [p['date'] for p in dump if p['date']]
    a, b = datetime.date.fromisoformat(min(ds)), datetime.date.fromisoformat(max(ds))
    weeks = max((b - a).days / 7, 1)
    print(f'posts {len(dump)} from {a} to {b}; per week {len(dump)/weeks:.1f}')
    vs = [p['v'] for p in dump if p['v']]
    print('views avg', int(statistics.mean(vs)), 'median', int(statistics.median(vs)))
    last = [p['v'] for p in dump[-60:] if p['v']]
    print('views last60 avg', int(statistics.mean(last)), 'median', int(statistics.median(last)))
    mc = collections.Counter(x for p in dump for x in p['m']['media'])
    print('media', dict(mc), 'textonly', sum(1 for p in dump if not p['m']['media']))
    print('with buttons', sum(1 for p in dump if p['m']['buttons']), collections.Counter(b for p in dump for b in p['m']['buttons']).most_common(12))
    print('fwd', collections.Counter(p['fwd'] for p in dump if p['fwd']).most_common(5))
    lk = collections.Counter(re.sub(r'\?.*', '', l) for p in dump for l in p['links'])
    print('links', lk.most_common(25))
    wd = collections.Counter(datetime.date.fromisoformat(p['date']).strftime('%a') for p in dump if p['date'])
    print('weekday', dict(wd))
    hrs = collections.Counter((p['m']['dt'] or '')[11:13] for p in dump)
    print('hours(UTC)', sorted(hrs.items()))
    lens = [len(p['text']) for p in dump]
    print('textlen median', int(statistics.median(lens)))
    print('TOP10:')
    for p in sorted([p for p in dump if p['v']], key=lambda p: -p['v'])[:10]:
        print(f"  #{p['id']} {p['date']} {p['views']} {p['m']['media']} | {p['text'][:160]!r}")
elif mode == 'lines':
    for p in dump:
        t = p['text'].replace('\n', ' / ')
        print(f"#{p['id']} {p['date']} {p['views']} {','.join(p['m']['media'])}{' B:'+'|'.join(p['m']['buttons']) if p['m']['buttons'] else ''} | {t[:150]}")
elif mode.startswith('full:'):
    ids = set(int(x) for x in mode[5:].split(','))
    for p in dump:
        if p['id'] in ids:
            print(f"===== #{p['id']} {p['date']} {p['views']} {p['m']} links={p['links']}\n{p['text']}\n")
elif mode.startswith('range:'):
    parts = mode[6:].split(':')
    lo, hi = map(int, parts[0].split('-'))
    n = int(parts[1]) if len(parts) > 1 else 1200
    for p in dump:
        if lo <= p['id'] <= hi:
            t = re.sub(r'\n\s*\n+', '\n', p['text'])
            print(f"===== #{p['id']} {p['date']} {p['views']} {p['m']['media']} {[re.sub(r'\?.*','',l) for l in p['links']][:4]}\n{t[:n]}\n")
