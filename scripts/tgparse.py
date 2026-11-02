import sys, re, html
sys.stdout.reconfigure(encoding='utf-8')
posts = {}
for fn in sys.argv[1:]:
    raw = open(fn, encoding='utf-8').read()
    chunks = raw.split('<div class="tgme_widget_message_wrap')
    for c in chunks[1:]:
        m = re.search(r'data-post="[^/]+/(\d+)"', c)
        if not m:
            continue
        pid = int(m.group(1))
        dt = re.search(r'<time datetime="([^"]+)"', c)
        vw = re.search(r'tgme_widget_message_views">([^<]+)<', c)
        tx = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', c, re.S)
        t = ''
        if tx:
            t = tx.group(1)
            t = re.sub(r'<br\s*/?>', '\n', t)
            t = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'\2 [\1]', t, flags=re.S)
            t = re.sub(r'<[^>]+>', '', t)
            t = html.unescape(t)
        media = []
        if 'tgme_widget_message_photo' in c: media.append('photo')
        if 'tgme_widget_message_video' in c or 'message_video_player' in c: media.append('video')
        if 'tgme_widget_message_voice' in c: media.append('voice')
        if 'tgme_widget_message_roundvideo' in c: media.append('circle')
        if 'tgme_widget_message_document' in c: media.append('doc')
        if 'tgme_widget_message_poll' in c: media.append('poll')
        btn = re.findall(r'tgme_widget_message_inline_button[^>]*href="([^"]+)"[^>]*>.*?<div class="tgme_widget_message_inline_button_text[^"]*">(.*?)</div>', c, re.S)
        rx = re.findall(r'class="tgme_reaction"[^>]*>.*?</i>(\d+)', c, re.S)
        posts[pid] = (dt.group(1) if dt else '', vw.group(1) if vw else '', media, t, btn)
for pid in sorted(posts):
    d, v, m, t, b = posts[pid]
    print(f'--- #{pid} | {d[:16]} | views {v} | {",".join(m)} | buttons {b}')
    print(t.strip())
print('TOTAL', len(posts))
