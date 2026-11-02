"""Рисует схемы воронок конкурентов из записанных переписок (обе ветки) -> docs/research/хронология_воронок.html
(все сообщения по порядку) и доску docs/research/доска_воронок.html. Сжатые схемы по этапам — scripts/build_stage_schemes.py.
Запуск: python scripts/build_schemes.py  (вызывается автоматически после каждой выгрузки в bots_recorder.py run)
"""
import os, re, json, glob, html
from datetime import datetime

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(P, 'private', 'bots_export')
OUT = os.path.join(P, 'docs', 'research', 'хронология_воронок.html')

SCHOOL_OF = {
    'other_digital_bot': 'Пурвиньш', 'money_2026_bot': 'Пурвиньш (эфиры)', 'vlad_techspec': 'Пурвиньш',
    'vlad_tehspecpro': 'Пурвиньш', 'purv_vlad_spec': 'Пурвиньш',
    'alekseicoach_bot': 'Муратов', 'lexs901': 'Муратов', 'alekseiref': 'Муратов',
    'pautov_techspec_bot': 'Паутов', 'ledokol_sever': 'Паутов', 'pautov_al': 'Паутов',
    'itgirlsclub_bot': 'ITGIRLS', 'itgirls_admin': 'ITGIRLS',
    'botHelpacademybot'.lower(): 'BotHelp', 'whatshelpbot': 'BotHelp (вебинары)',
    'zerocoder_offline_meetings_bot': 'Zerocoder', 'zerocodermoscowregbot': 'Zerocoder', 'mavestreambot': 'Zerocoder',
    'zero_neuro_cat_bot': 'Zerocoder', 'danya_vibe_bot': 'Даня (@myvibeai)', 'danya_s_vibe': 'Даня (@myvibeai)',
    'gh_vacancy_bot': 'GetHelpers', 'helpweb24bot': 'GetHelpers', 'frilans_na_legke_bot': 'frilans_na_legke_bot',
}
ORDER = ['Пурвиньш', 'Паутов', 'Муратов', 'Кораблёв (эфиры)', 'ITGIRLS', 'BotHelp', 'BotHelp (вебинары)', 'Zerocoder',
         'Пурвиньш (эфиры)', 'Даня (@myvibeai)', 'GetHelpers', 'frilans_na_legke_bot']


def school(chat):
    c = (chat or '').lower()
    if c.startswith('korablevtech'):
        return 'Кораблёв (эфиры)'
    return SCHOOL_OF.get(c)


def lane(chat):
    c = (chat or '').lower()
    if 'тест-драйв' in c or 'тест драйв' in c:
        return 'Группа'
    if c.endswith('bot'):
        return 'Бот'
    return 'Личка'


SCRUB = [
    (re.compile(r'tg_id=\d+'), 'tg_id=…'), (re.compile(r'td_id=-?\d+'), 'td_id=…'),
    (re.compile(r'\b(1085803787|5400383268)\b'), '[ID]'),  # Telegram ID обоих аккаунтов
    (re.compile(r'(ID:?\s*)\d{6,}', re.I), r'\1[ID]'),
    (re.compile(r'\+?7[\s(-]*9\d{2}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}'), '[телефон]'),
    (re.compile(r'Якушев\s+Никита|Никита\s+Якушев', re.I), '[Имя Фамилия]'),
    (re.compile(r'@Soulnikita|@Unseen_echo', re.I), '@[ник]'),
    (re.compile(r'\bNikita\b|\bНикита\b|Silent Observer', re.I), '[Имя]'),
]


def scrub(t):
    t = t or ''
    for rx, rep in SCRUB:
        t = rx.sub(rep, t)
    return t


DOZHIM = re.compile(r'не проч|напомина|отвлек|актуально или нет|без ответа|удалось посмотр|финальное напомин|'
                    r'не спрашивайте|закрываем тему|если вы ещё не|если вы еще не|самое время', re.I)


def kind(m):
    t = (m.get('text') or '').lower()
    btn = ' '.join(b.get('text', '') for b in m.get('buttons') or []).lower()
    if m.get('out'):
        return 'act'
    if DOZHIM.search(t):
        return 'push'
    if 'номер телефона' in t or 'номер' in btn or 'телефон' in btn:
        return 'phone'
    if re.search(r'\bдарю\b|бонусный урок|забирай(те)? (гайд|бонус|подарок)|ваш подарок|лови подарок', t):
        return 'gift'
    if 'статья' in btn or 'статью' in btn or 'статья' in t[:200]:
        return 'article'
    if 'урок' in t and ('1️⃣' in t or 'lesson' in t or 'урок 1' in t):
        return 'lessons'
    if 'анкет' in t:
        return 'form'
    if 'канал' in t and ('подпиш' in t or 't.me/' in t):
        return 'channel'
    if 'эфир' in t or 'вебинар' in t or 'мастер-класс' in t:
        return 'event'
    return 'msg'


KIND_NAME = {'act': 'действие', 'push': 'дожим', 'article': 'статья', 'lessons': 'уроки', 'form': 'анкета',
             'channel': 'канал', 'event': 'эфир', 'msg': 'сообщение', 'phone': 'запрос телефона', 'gift': 'бонус / лид-магнит'}


def load_branch(base):
    """Собирает сообщения ветки: последние выгрузки (folder_*/bots_*) + log.jsonl."""
    msgs = {}
    for d in sorted(glob.glob(os.path.join(base, 'folder_*')) + glob.glob(os.path.join(base, 'bots_*'))):
        for f in glob.glob(os.path.join(d, '*.json')):
            try:
                j = json.load(open(f, encoding='utf-8'))
            except Exception:
                continue
            chat = j.get('chat') if isinstance(j, dict) else None
            for m in (j.get('messages') if isinstance(j, dict) else j) or []:
                c = chat or m.get('chat')
                key = (c, m.get('msg_id'), m.get('time'))
                m = dict(m); m['chat'] = c
                msgs[key] = m
    logf = os.path.join(base, 'log.jsonl')
    if os.path.exists(logf):
        for line in open(logf, encoding='utf-8'):
            try:
                m = json.loads(line)
            except Exception:
                continue
            if not m.get('text') and not m.get('buttons') and not m.get('note'):
                continue
            key = (m.get('chat'), m.get('msg_id'), m.get('time'))
            msgs.setdefault(key, m)
    # сообщения, записанные по номеру группы (-100…), -> название группы
    titles = {m.get('chat_id'): m.get('chat') for m in msgs.values() if m.get('chat_id') and m.get('chat')}
    for m in msgs.values():
        c = str(m.get('chat') or '')
        if re.fullmatch(r'-?\d+', c):
            m['chat_id'] = int(c)
            m['chat'] = titles.get(int(c), c)
    # убрать дубли по (чат, время, текст)
    # одно и то же сообщение бывает и в журнале, и в выгрузке с разницей в секунды — склеиваем в пределах 2 минут
    last_seen, out = {}, []
    for m in sorted(msgs.values(), key=lambda x: x.get('time') or ''):
        k = ((m.get('chat') or '').lower(), (m.get('text') or m.get('note') or '')[:60], bool(m.get('out')))
        t = ts(m)
        if k in last_seen and t is not None and last_seen[k] is not None and abs(t - last_seen[k]) < 120:
            continue
        last_seen[k] = t
        out.append(m)
    # группы тест-драйва -> школа по отправителю
    for m in out:
        if lane(m.get('chat')) == 'Группа':
            frm = (m.get('from') or '').lower()
            m['school'] = school(frm) or m.get('school')
        else:
            m['school'] = school(m.get('chat'))
    # если в группе первое сообщение без отправителя — школа по соседям
    by_chat = {}
    for m in out:
        by_chat.setdefault(m.get('chat_id') or m.get('chat'), []).append(m)
    for lst in by_chat.values():
        sch = next((x['school'] for x in lst if x.get('school')), None)
        for x in lst:
            x['school'] = x.get('school') or sch
    # у школ с несколькими ботами (каждый под свой эфир) — отдельная схема на каждого бота
    for m in out:
        if m.get('school') in SPLIT and lane(m.get('chat')) == 'Бот':
            m['school'] = '%s · %s' % (SPLIT[m['school']], short_bot(m.get('chat')))
    return [m for m in out if m.get('school')]


SPLIT = {'Кораблёв (эфиры)': 'Кораблёв', 'Zerocoder': 'Zerocoder', 'GetHelpers': 'GetHelpers'}


def short_bot(chat):
    c = (chat or '').lower()
    for p in ('korablevtech_', 'zerocoder_'):
        if c.startswith(p):
            c = c[len(p):]
    c = c[:-4] if c.endswith('_bot') else (c[:-3] if c.endswith('bot') else c)
    return c or 'bot'


def fmt_delta(sec):
    if sec is None:
        return ''
    sec = int(sec)
    if sec < 60:
        return '+%d сек' % sec
    if sec < 3600:
        return '+%d мин' % round(sec / 60)
    if sec < 86400:
        h, mnt = divmod(round(sec / 60), 60)
        return '+%d ч%s' % (h, (' %d мин' % mnt) if mnt else '')
    d, rest = divmod(sec, 86400)
    return '+%d д %d ч' % (d, round(rest / 3600))


def ts(m):
    try:
        return datetime.fromisoformat(m['time']).timestamp()
    except Exception:
        return None


def render_flow(items):
    if not items:
        return '<div class="empty">Пока ничего не записано</div>'
    t0 = ts(items[0])
    prev = None
    out = []
    for m in items:
        t = ts(m)
        if prev is not None and t is not None:
            out.append('<div class="arrow"><span>%s</span></div>' % fmt_delta(t - prev))
        prev = t if t is not None else prev
        k = kind(m)
        text = scrub(m.get('text') or m.get('note') or '')
        first = text.strip().split('\n')[0][:110] if text.strip() else ('[%s]' % (m.get('media') or 'медиа'))
        btns = ''.join('<span class="b">%s</span>' % html.escape(scrub(b.get('text', ''))) for b in (m.get('buttons') or []))
        full = html.escape(text).replace('\n', '<br>')
        since = fmt_delta(t - t0) if (t is not None and t0 is not None) else ''
        out.append('<div class="box k-%s"><div class="hd"><span class="lane">%s</span><span class="kind">%s</span><span class="since">%s от старта</span></div>'
                   '<div class="t">%s</div>%s%s</div>' % (
                       k, lane(m.get('chat')), KIND_NAME[k], since.replace('+', ''), html.escape(first),
                       ('<div class="btns">%s</div>' % btns) if btns else '',
                       ('<details><summary>весь текст</summary><div class="full">%s</div></details>' % full) if len(text) > 110 else ''))
    return '\n'.join(out)


def summary_line(items):
    if not items:
        return ''
    t0 = ts(items[0])
    parts = []
    for m in items:
        k = kind(m)
        if k == 'msg':
            continue
        t = ts(m)
        parts.append('%s%s' % (KIND_NAME[k], (' ' + fmt_delta(t - t0)) if (t and t0 and t - t0 >= 60) else ''))
    # схлопнуть повторы подряд
    comp = []
    for p in parts:
        if not comp or comp[-1] != p:
            comp.append(p)
    return ' → '.join(comp[:18])


if not os.environ.get('NO_MEDIA'):  # сначала докачать картинки новых сообщений
    import subprocess, sys
    try:
        subprocess.run([sys.executable, '-X', 'utf8', os.path.join(P, 'scripts', 'media_fetch.py')], capture_output=True, timeout=240)
    except Exception:
        pass

active = load_branch(EXP)
lazy = load_branch(os.path.join(EXP, 'lazy'))
def order_key(s):
    base = s.split(' · ')[0]
    base = next((k for k, v in SPLIT.items() if v == base), base)
    return (ORDER.index(base) if base in ORDER else len(ORDER), s)


# прячем ботов, которые после «Старта» ничего не прислали ни в одной ветке
counts = {}
for m in active + lazy:
    if not m.get('out'):
        counts[m['school']] = counts.get(m['school'], 0) + 1
schools = sorted({m['school'] for m in active + lazy if counts.get(m['school'])}, key=order_key)


MEDIA_DIR = os.path.join(P, 'docs', 'research', 'media')
MEDIA_RU = {'MessageMediaPhoto': 'Фото', 'MessageMediaDocument': 'Видео / файл', 'MessageMediaWebPage': 'Ссылка с превью',
            'MessageMediaPoll': 'Опрос', 'MessageMediaGeo': 'Геоточка', 'MessageMediaContact': 'Контакт'}


def media_img(m, prof):
    """Путь к сжатой картинке (scripts/media_fetch.py), если она уже скачана."""
    if not (m.get('media') and m.get('chat_id') and m.get('msg_id')):
        return ''
    name = '%s_%d_%d.jpg' % (prof or 'main', abs(int(m['chat_id'])), int(m['msg_id']))
    return 'media/' + name if os.path.exists(os.path.join(MEDIA_DIR, name)) else ''


def media_av(m, prof):
    """Видео / кружок / голосовое, если скачаны: (путь, тип)."""
    if not (m.get('media') and m.get('chat_id') and m.get('msg_id')):
        return '', ''
    stem = '%s_%d_%d' % (prof or 'main', abs(int(m['chat_id'])), int(m['msg_id']))
    for ext, kind_ in (('_round.mp4', 'round'), ('.mp4', 'video'), ('.ogg', 'audio')):
        if os.path.exists(os.path.join(MEDIA_DIR, stem + ext)):
            return 'media/' + stem + ext, kind_
    return '', ''


def board_items(items, prof=''):
    """Данные для доски: карточки с дорожкой, типом, временем от старта и от предыдущей карточки."""
    res = []
    t0 = ts(items[0]) if items else None
    prev = None
    prev_out = True
    for m in items:
        t = ts(m)
        text = scrub(m.get('text') or m.get('note') or '').strip()
        k = kind(m)
        # дожим = бот написал сам: предыдущее событие не было действием человека и прошло >= 3 минут
        if not m.get('out') and not prev_out and t is not None and prev is not None and t - prev >= 180 and k in ('msg', 'article', 'channel', 'event'):
            k = 'push'
        prev_out = bool(m.get('out'))
        res.append({
            'lane': lane(m.get('chat')),
            'kind': k,
            'since': fmt_delta(t - t0).replace('+', '') if (t is not None and t0 is not None) else '',
            'sec': int(t - t0) if (t is not None and t0 is not None) else None,
            'gap': fmt_delta(t - prev) if (t is not None and prev is not None) else '',
            'title': (text.split('\n')[0][:120] if text else MEDIA_RU.get(m.get('media'), 'Медиа')),
            'text': text,
            'buttons': [scrub(b.get('text', '')) for b in (m.get('buttons') or [])],
            'img': media_img(m, prof),
            'av': media_av(m, prof)[0], 'avk': media_av(m, prof)[1],
        })
        if res[-1]['avk'] and not text:
            res[-1]['title'] = {'round': 'Видео-кружок', 'video': 'Видео', 'audio': 'Голосовое'}[res[-1]['avk']]
        prev = t if t is not None else prev
    return res


BOARD = {s: {'active': board_items([m for m in active if m['school'] == s]),
             'lazy': board_items([m for m in lazy if m['school'] == s], 'lazy'),
             'sumA': summary_line([m for m in active if m['school'] == s]),
             'sumL': summary_line([m for m in lazy if m['school'] == s])} for s in schools}
# школы, которые продают через сайт: схема собрана вручную по коду страниц (scripts/site_funnels.py)
from site_funnels import SITES
for name, steps in SITES.items():
    BOARD[name] = {'site': True, 'active': steps, 'lazy': [], 'sumA': ' → '.join(x['title'] for x in steps[:4]), 'sumL': ''}
tpl = open(os.path.join(P, 'scripts', 'templates', 'board_template.html'), encoding='utf-8').read()
board_html = (tpl.replace('/*DATA*/null', json.dumps(BOARD, ensure_ascii=False))
                 .replace('/*ORDER*/[]', json.dumps(schools + list(SITES), ensure_ascii=False))
                 .replace('%%UPDATED%%', datetime.now().strftime('%d.%m.%Y %H:%M')))
open(os.path.join(P, 'docs', 'research', 'доска_воронок.html'), 'w', encoding='utf-8').write(board_html)

sections, nav = [], []
for i, s in enumerate(schools):
    a = [m for m in active if m['school'] == s]
    z = [m for m in lazy if m['school'] == s]
    nav.append('<a href="#s%d">%s</a>' % (i, html.escape(s)))
    sections.append(
        '<section id="s%d"><h2>%s</h2>'
        '<div class="sum"><b>Активная ветка:</b> %s</div><div class="sum"><b>Ленивая ветка:</b> %s</div>'
        '<div class="cols"><div class="col"><h3>Активная ветка <small>основной аккаунт: проходит шаги сразу</small></h3>%s</div>'
        '<div class="col"><h3>Ленивая ветка <small>второй аккаунт: «Старт» и ничего не делает</small></h3>%s</div></div></section>' % (
            i, html.escape(s), html.escape(summary_line(a)) or '—', html.escape(summary_line(z)) or '—',
            render_flow(a), render_flow(z)))

updated = datetime.now().strftime('%d.%m.%Y %H:%M')
page = '''<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Схемы воронок конкурентов</title><style>
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",Roboto,Arial,sans-serif;font-size:14.5px;color:#1d2433;background:#f4f6fb}
.hero{background:linear-gradient(135deg,#14182e 0%%,#2b2f6b 60%%,#f08c00 160%%);color:#fff;padding:34px 24px 28px}
.hero h1{margin:0 0 8px;font-size:30px}.hero p{margin:0;opacity:.92;max-width:900px}
.nav{position:sticky;top:0;background:#fff;border-bottom:1px solid #e1e5ee;padding:8px 18px;z-index:5;display:flex;flex-wrap:wrap}
.nav a{color:#3a4257;text-decoration:none;padding:5px 10px;margin:2px;border-radius:8px;font-size:13.5px;background:#f4f6fb}
.legend{padding:12px 24px;font-size:13px;color:#5c6478}.legend span{display:inline-block;margin:3px 10px 3px 0;padding:2px 8px;border-radius:6px}
section{max-width:1200px;margin:0 auto;padding:26px 18px 10px}h2{font-size:24px;margin:0 0 8px;color:#14182e}
.sum{background:#fff;border-radius:10px;padding:8px 12px;margin:0 0 6px;font-size:13.5px;color:#3a4257}
.cols{display:flex;flex-wrap:wrap;margin:10px -8px 0}.col{flex:1 1 440px;margin:0 8px}
.col h3{font-size:15px;margin:6px 0 10px;color:#14182e}.col h3 small{font-weight:400;color:#8a91a5}
.box{background:#fff;border-radius:12px;padding:9px 12px;box-shadow:0 1px 6px rgba(31,42,90,.08);border-left:5px solid #adb5bd}
.box .hd{font-size:11.5px;color:#8a91a5;margin-bottom:3px}.box .hd span{margin-right:8px}
.lane{font-weight:700;color:#3a4257}.kind{text-transform:uppercase;letter-spacing:.04em;font-weight:700}
.box .t{font-size:14px;color:#1d2433}.btns{margin-top:5px}.b{display:inline-block;background:#e7f0ff;color:#1c4fa0;border-radius:7px;padding:2px 8px;margin:2px 4px 0 0;font-size:12.5px}
details{margin-top:4px;font-size:12.5px}summary{cursor:pointer;color:#5c6478}.full{margin-top:4px;color:#3a4257;white-space:normal}
.arrow{text-align:center;height:34px;position:relative}.arrow:before{content:"";position:absolute;left:50%%;top:0;bottom:6px;border-left:2px solid #c5cbe0}
.arrow:after{content:"";position:absolute;left:calc(50%% - 5px);bottom:0;border:5px solid transparent;border-top:7px solid #c5cbe0}
.arrow span{position:relative;top:7px;background:#f4f6fb;padding:0 6px;font-size:12px;font-weight:700;color:#d9480f}
.k-act{border-left-color:#868e96;background:#f8f9fa}.k-act .kind{color:#868e96}
.k-push{border-left-color:#e03131}.k-push .kind{color:#e03131}
.k-article{border-left-color:#1c7ed6}.k-article .kind{color:#1c7ed6}
.k-lessons{border-left-color:#2b8a3e}.k-lessons .kind{color:#2b8a3e}
.k-form{border-left-color:#f08c00}.k-form .kind{color:#f08c00}
.k-channel{border-left-color:#7048e8}.k-channel .kind{color:#7048e8}
.k-event{border-left-color:#c2255c}.k-event .kind{color:#c2255c}
.empty{color:#8a91a5;font-style:italic;padding:10px}
footer{text-align:center;color:#8a91a5;font-size:12.5px;padding:30px}
</style></head><body>
<div class="hero"><h1>Схемы воронок конкурентов</h1><p>Строится автоматически из записанных переписок и обновляется после каждой выгрузки, раз в 3 часа. Слева — «активная» ветка (человек сразу проходит шаги), справа — «ленивая» (нажал «Старт» и пропал). На стрелках — сколько прошло между сообщениями. Обновлено: %s.</p></div>
<div class="nav">%s</div>
<div class="legend"><span style="background:#e7f5ff">статья</span><span style="background:#fff5f5">дожим</span><span style="background:#ebfbee">уроки</span><span style="background:#fff4e6">анкета</span><span style="background:#f3f0ff">канал</span><span style="background:#fff0f6">эфир</span><span style="background:#f1f3f5">действие человека</span> · Метки типов ставятся автоматически по тексту, могут ошибаться — финальная версия будет вычитана вручную.</div>
%s
<footer>Личные данные (имя, ник, телефон, ID) скрыты автоматически.</footer>
</body></html>''' % (updated, ''.join(nav), '\n'.join(sections))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(page)
print('schools', len(schools), 'active', len(active), 'lazy', len(lazy))
