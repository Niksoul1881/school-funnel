import sys, re, html, json, time, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
# usage: tgdump.py <channel> <outdir> [maxposts]
ch, outdir = sys.argv[1], sys.argv[2]
maxp = int(sys.argv[3]) if len(sys.argv) > 3 else 400
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36'

def get(url):
    for t in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ru'})
            return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
        except Exception as e:
            print('retry', url, e); time.sleep(3)
    return ''

def clean(t):
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    return html.unescape(t).strip()

def parse(raw):
    out = {}
    for c in raw.split('<div class="tgme_widget_message_wrap')[1:]:
        m = re.search(r'data-post="[^/]+/(\d+)"', c)
        if not m: continue
        pid = int(m.group(1))
        dt = re.search(r'<time[^>]*datetime="([^"]+)"', c)
        vw = re.search(r'tgme_widget_message_views">([^<]+)<', c)
        fw = re.search(r'tgme_widget_message_forwarded_from_name"[^>]*>(.*?)</(?:a|span)>', c, re.S)
        tx = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', c, re.S)
        links = []
        text = ''
        if tx:
            body = tx.group(1)
            links = [html.unescape(h) for h in re.findall(r'<a [^>]*href="([^"]+)"', body)]
            text = clean(body)
        elif 'service_message' in c:
            sv = re.search(r'tgme_widget_message_service[^>]*>(.*?)</div>', c, re.S)
            text = clean(sv.group(1)) if sv else 'service'
        btn = re.findall(r'tgme_widget_message_inline_button[^>]*href="([^"]+)"[^>]*>.*?inline_button_text[^"]*">(.*?)</div>', c, re.S)
        for h, _ in btn:
            links.append(html.unescape(h))
        media = []
        for key, name in [('tgme_widget_message_photo', 'photo'), ('tgme_widget_message_video', 'video'),
                          ('message_video_player', 'video'), ('tgme_widget_message_voice', 'voice'),
                          ('tgme_widget_message_roundvideo', 'circle'), ('round_video', 'circle'),
                          ('tgme_widget_message_document', 'doc'), ('tgme_widget_message_poll', 'poll'),
                          ('tgme_widget_message_sticker', 'sticker'), ('tgme_widget_message_link_preview', 'linkpreview')]:
            if key in c and name not in media: media.append(name)
        if 'tgme_widget_message_grouped' in c: media.append('album')
        out[pid] = {
            'id': pid,
            'date': dt.group(1)[:10] if dt else None,
            'views': vw.group(1) if vw else None,
            'fwd': clean(fw.group(1)) if fw else None,
            'links': links,
            'text': text,
            '_meta': {'dt': dt.group(1) if dt else None, 'media': media,
                      'buttons': [clean(b) for _, b in btn]},
        }
    return out

raw = get(f'https://t.me/s/{ch}')
subs = re.search(r'tgme_header_counter">([^<]+)<', raw)
title = re.search(r'<meta property="og:title" content="([^"]*)"', raw)
desc = re.search(r'tgme_channel_info_description">(.*?)</div>', raw, re.S)
posts = parse(raw)
while len(posts) < maxp and posts:
    mn = min(posts)
    if mn <= 1: break
    time.sleep(1.1)
    page = parse(get(f'https://t.me/s/{ch}?before={mn}'))
    new = {k: v for k, v in page.items() if k not in posts}
    if not new: break
    posts.update(new)
    print(ch, 'got', len(posts), 'min', min(posts), flush=True)
ids = sorted(posts)[-maxp:]
dump, meta = [], {}
for i in ids:
    p = posts[i]; meta[i] = p.pop('_meta'); dump.append(p)
json.dump(dump, open(f'{outdir}/dump_{ch}.json', 'w', encoding='utf-8'), ensure_ascii=False)
json.dump({'channel': ch, 'title': html.unescape(title.group(1)) if title else None,
           'subs': subs.group(1) if subs else None,
           'desc': clean(desc.group(1)) if desc else None, 'posts': meta},
          open(f'{outdir}/meta_{ch}.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('DONE', ch, len(dump), 'subs', subs.group(1) if subs else None)
