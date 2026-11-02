import json, re, sys, time, html, urllib.request, urllib.error

TOKEN = open(sys.argv[1]).read().strip()
CHAT = int(sys.argv[2])
FILES = sys.argv[3:]
LOG = open('publish_log.txt', 'w', encoding='utf-8')


def call(method, **p):
    data = json.dumps(p).encode()
    for attempt in range(5):
        req = urllib.request.Request('https://api.telegram.org/bot%s/%s' % (TOKEN, method), data=data,
                                     headers={'Content-Type': 'application/json'})
        try:
            return json.load(urllib.request.urlopen(req, timeout=40))
        except urllib.error.HTTPError as e:
            body = json.load(e)
            ra = body.get('parameters', {}).get('retry_after')
            if ra:
                time.sleep(ra + 1)
                continue
            return body
    return {'ok': False, 'description': 'retries exhausted'}


def parse(md):
    posts, section = [], None
    for chunk in re.split(r'^(?=### |## )', md, flags=re.M):
        if chunk.startswith('## '):
            section = chunk.split('\n', 1)[0][3:].strip()
            continue
        if not chunk.startswith('### '):
            continue
        head, _, body = chunk.partition('\n')
        m = re.match(r'###\s+(\S+)\s*[·•.\-—]\s*(.+)', head)
        num, title = (m.group(1), m.group(2).strip()) if m else ('', head[4:].strip())
        meta, lines, in_meta, last = {}, [], True, None
        for ln in body.split('\n'):
            mm = re.match(r'^\s*[-*]\s*(Рубрика|Зачем|Идея|Медиа|Кнопки|День|Факты|Для команды)\s*:\s*(.*)', ln)
            if in_meta and mm:
                last = mm.group(1); meta[last] = mm.group(2).strip(); continue
            if in_meta and meta and ln.startswith('  ') and ln.strip():
                meta[last] += ' ' + ln.strip(); continue
            if in_meta and not ln.strip():
                if meta: in_meta = False
                continue
            in_meta = False
            lines.append(ln.rstrip())
        text = '\n'.join(lines).strip()
        text = re.sub(r'\n\s*(---|\*\*\*)\s*$', '', text).strip()
        posts.append(dict(num=num, title=title, meta=meta, text=text))
    return posts


def to_html(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return t


posts = []
for f in FILES:
    posts += parse(open(f, encoding='utf-8').read().replace('\r\n', '\n'))

sent = 0
divider_done = False
for p in posts:
    if p['num'].upper().startswith('W') and not divider_done:
        call('sendMessage', chat_id=CHAT, disable_notification=True,
             text='━━━━━━━━━━━━━━\nНИЖЕ: ПРОГРЕВ К ТЕСТ-ДРАЙВУ (W01–W19)\nвыходит после фундамента и посевов\n━━━━━━━━━━━━━━')
        divider_done = True
        time.sleep(3)
    kb = None
    k = p['meta'].get('Кнопки', '')
    if k and not k.lower().startswith('нет'):
        labels = [x.strip() for x in re.findall(r'\[([^\]→]+?)\s*(?:→[^\]]*)?\]', k)]
        if labels:
            kb = {'inline_keyboard': [[{'text': l, 'url': 'https://t.me/manekken_bot'}] for l in labels]}
    params = dict(chat_id=CHAT, text=to_html(p['text']), parse_mode='HTML', disable_notification=True,
                  link_preview_options={'is_disabled': True})
    if kb:
        params['reply_markup'] = kb
    r = call('sendMessage', **params)
    if not r.get('ok'):
        # fallback without formatting
        params.pop('parse_mode'); params['text'] = p['text']
        r = call('sendMessage', **params)
    LOG.write('%s %s %s\n' % (p['num'], 'OK' if r.get('ok') else 'FAIL', '' if r.get('ok') else r.get('description')))
    LOG.flush()
    if r.get('ok'):
        sent += 1
    time.sleep(3.2)

LOG.write('SENT %d of %d\n' % (sent, len(posts)))
LOG.close()
