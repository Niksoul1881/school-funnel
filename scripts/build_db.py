"""Собирает базу data/db/school.sqlite из файлов проекта.
Запуск из корня проекта:  python scripts/build_db.py
Личные данные (анкеты) кладёт в отдельную базу private/leads/leads.sqlite.
"""
import os, re, json, glob, sqlite3

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(P, 'data', 'db', 'school.sqlite')

OWNERS = {
    'million_on_freelance': 'Влад Пурвиньш', 'techspec_pautov': 'Алексей Паутов',
    'MuratovAleksei': 'Алексей Муратов', 'korablevtech': 'Дмитрий Кораблёв',
    'yximikk': 'Химик (Freelance School)', 'freelance_start_terentevy': 'Terentev School',
    'oqode': 'Zerocoder', 'bothelp_channel': 'BotHelp', 'myvibeai': 'Даня (фрилансер)',
    'manekken': 'Манекен (наш проект)',
}


def views(v):
    if not v:
        return None
    v = str(v).replace(',', '.').strip()
    try:
        return int(float(v[:-1]) * 1000) if v.endswith('K') else int(float(v))
    except ValueError:
        return None


if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
c = con.cursor()
c.executescript('''
CREATE TABLE channels(username TEXT PRIMARY KEY, owner TEXT, title TEXT, subscribers TEXT, description TEXT, posts_saved INTEGER);
CREATE TABLE posts(channel TEXT, post_id INTEGER, date TEXT, views INTEGER, views_raw TEXT, text TEXT, links TEXT,
                   PRIMARY KEY(channel, post_id));
CREATE TABLE competitor_texts(file TEXT PRIMARY KEY, kind TEXT, text TEXT);
CREATE TABLE our_content(source TEXT, num TEXT, title TEXT, meta TEXT, text TEXT);
CREATE INDEX posts_channel_date ON posts(channel, date);
''')

for f in glob.glob(os.path.join(P, 'data', 'competitors', 'telegram', 'dump_*.json')):
    ch = os.path.basename(f)[5:-5]
    posts = json.load(open(f, encoding='utf-8'))
    meta_f = os.path.join(os.path.dirname(f), 'meta_%s.json' % ch)
    meta = json.load(open(meta_f, encoding='utf-8')) if os.path.exists(meta_f) else {}
    c.execute('INSERT OR REPLACE INTO channels VALUES(?,?,?,?,?,?)',
              (ch, OWNERS.get(ch, ''), meta.get('title'), meta.get('subs'), meta.get('desc'), len(posts)))
    for p in posts:
        c.execute('INSERT OR REPLACE INTO posts VALUES(?,?,?,?,?,?,?)',
                  (ch, p.get('id'), p.get('date'), views(p.get('views')), p.get('views'), p.get('text'),
                   json.dumps(p.get('links') or [], ensure_ascii=False)))

for kind, sub in (('статьи и уроки', 'articles_and_lessons'), ('расшифровка видео', 'transcripts')):
    for f in glob.glob(os.path.join(P, 'data', 'competitors', sub, '*.txt')):
        c.execute('INSERT OR REPLACE INTO competitor_texts VALUES(?,?,?)',
                  (os.path.basename(f), kind, open(f, encoding='utf-8', errors='replace').read()))

# our posts and funnel texts from markdown sources
for f in glob.glob(os.path.join(P, 'sources', '*', '*.md')):
    md = open(f, encoding='utf-8').read()
    for chunk in re.split(r'^(?=### )', md, flags=re.M):
        if not chunk.startswith('### '):
            continue
        head, _, body = chunk.partition('\n')
        m = re.match(r'###\s+(\S+)\s*[·•.\-—]\s*(.+)', head)
        num, title = (m.group(1), m.group(2)) if m else ('', head[4:])
        meta = '\n'.join(l for l in body.split('\n') if re.match(r'^\s*-\s*[А-ЯA-Z][^:]{1,20}:', l))
        text = '\n'.join(l for l in body.split('\n') if not re.match(r'^\s*-\s*[А-ЯA-Z][^:]{1,20}:', l)).strip()
        c.execute('INSERT INTO our_content VALUES(?,?,?,?,?)',
                  (os.path.relpath(f, P).replace('\\', '/'), num, title.strip(), meta, text))
con.commit()
for t in ('channels', 'posts', 'competitor_texts', 'our_content'):
    print(t, c.execute('SELECT COUNT(*) FROM %s' % t).fetchone()[0])
con.close()

# private leads
xlsx = glob.glob(os.path.join(P, 'private', 'leads', '*.xlsx'))
if xlsx:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(xlsx[0], data_only=True)
        ws = wb.worksheets[0]
        rows = [[('' if v is None else str(v)) for v in r] for r in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if any(x.strip() for x in r)]
        head = [h or 'col%d' % i for i, h in enumerate(rows[0])]
        keep = [i for i, h in enumerate(rows[0]) if h]
        ldb = os.path.join(P, 'private', 'leads', 'leads.sqlite')
        if os.path.exists(ldb):
            os.remove(ldb)
        lc = sqlite3.connect(ldb)
        cols = ', '.join('"%s" TEXT' % head[i] for i in keep)
        lc.execute('CREATE TABLE leads(%s)' % cols)
        lc.executemany('INSERT INTO leads VALUES(%s)' % ','.join('?' * len(keep)),
                       [[r[i] if i < len(r) else '' for i in keep] for r in rows[1:]])
        lc.commit()
        print('leads (private)', lc.execute('SELECT COUNT(*) FROM leads').fetchone()[0])
        lc.close()
    except ImportError:
        print('openpyxl не установлен: pip install openpyxl, чтобы собрать private/leads/leads.sqlite')
