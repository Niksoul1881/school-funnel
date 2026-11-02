"""Скачивает картинки к сообщениям ботов (фото — сжатая копия, видео/кружки/файлы — обложка) в docs/research/media/,
чтобы доска показывала их в карточках. Работает на копии сессии, запущенные рекордеры не мешают.
Запуск: python scripts/media_fetch.py   (вызывается из autoupdate.py)
"""
import asyncio, glob, io, json, os, shutil, tempfile

from PIL import Image
from telethon import TelegramClient

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV = os.path.join(P, 'private')
EXP = os.path.join(PRIV, 'bots_export')
MEDIA = os.path.join(P, 'docs', 'research', 'media')
SKIP_FILE = os.path.join(PRIV, 'media_skip.json')
MAX_SIDE, LIMIT = 480, 200
os.makedirs(MEDIA, exist_ok=True)


def media_name(profile, chat_id, msg_id):
    return '%s_%d_%d.jpg' % (profile or 'main', abs(int(chat_id)), int(msg_id))


def wanted(base):
    """Все (chat_id, msg_id) с медиа из выгрузок и журнала ветки."""
    res = set()
    files = glob.glob(os.path.join(base, 'folder_*', '*.json')) + glob.glob(os.path.join(base, 'bots_*', '*.json'))
    for f in files:
        try:
            j = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        for m in (j.get('messages') if isinstance(j, dict) else j) or []:
            if m.get('media') and m.get('chat_id') and m.get('msg_id'):
                res.add((int(m['chat_id']), int(m['msg_id'])))
    logf = os.path.join(base, 'log.jsonl')
    if os.path.exists(logf):
        for line in open(logf, encoding='utf-8'):
            try:
                m = json.loads(line)
            except Exception:
                continue
            if m.get('media') and m.get('chat_id') and m.get('msg_id'):
                res.add((int(m['chat_id']), int(m['msg_id'])))
    return res


def shrink(data):
    im = Image.open(io.BytesIO(data))
    im = im.convert('RGB')
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    im.save(out, 'JPEG', quality=72, optimize=True)
    return out.getvalue()


AV_EXT = ('.mp4', '_round.mp4', '.ogg')
MAX_VIDEO = 80 * 1024 * 1024
FFMPEG = shutil.which('ffmpeg') or r'C:\ffmpeg\ffmpeg-2026-01-14-git-6c878f8b82-essentials_build\bin\ffmpeg.exe'


async def fetch_av(client, msg, stem):
    """Видео -> лёгкий mp4 (до 640 px), кружок -> 320 px (_round.mp4), голосовое -> .ogg как есть."""
    import subprocess
    if not msg or not msg.document:
        return False
    if msg.voice:
        data = await client.download_media(msg, bytes)
        open(os.path.join(MEDIA, stem + '.ogg'), 'wb').write(data)
        return True
    if not (msg.video or msg.video_note or msg.gif) or (msg.document.size or 0) > MAX_VIDEO:
        return False
    tmp = tempfile.mkdtemp()
    try:
        src = await client.download_media(msg, os.path.join(tmp, 'src'))
        out_name = stem + ('_round.mp4' if msg.video_note else '.mp4')
        side = 320 if msg.video_note else 640
        dst = os.path.join(tmp, 'out.mp4')
        subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', src,
                        '-vf', "scale='min(%d,iw)':-2" % side, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30',
                        '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', dst], capture_output=True, timeout=600)
        if not os.path.exists(dst) or os.path.getsize(dst) == 0:
            return False
        shutil.move(dst, os.path.join(MEDIA, out_name))
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


async def fetch(profile, base, skip):
    suffix = ('_' + profile) if profile else ''
    cfg = json.load(open(os.path.join(PRIV, 'tg_api%s.json' % suffix), encoding='utf-8'))
    tmp = tempfile.mkdtemp()
    shutil.copy(os.path.join(PRIV, 'tg_session%s.session' % suffix), os.path.join(tmp, 's.session'))
    client = TelegramClient(os.path.join(tmp, 's'), cfg['api_id'], cfg['api_hash'])
    await client.connect()
    done = 0
    try:
        for chat_id, msg_id in sorted(wanted(base)):
            name = media_name(profile, chat_id, msg_id)
            stem = name[:-4]
            need_img = not os.path.exists(os.path.join(MEDIA, name)) and name not in skip
            need_av = not any(os.path.exists(os.path.join(MEDIA, stem + e)) for e in AV_EXT) and ('v:' + name) not in skip
            if not (need_img or need_av) or done >= LIMIT:
                continue
            try:
                msg = await client.get_messages(chat_id, ids=msg_id)
                if need_av:
                    if await fetch_av(client, msg, stem):
                        done += 1
                    else:
                        skip['v:' + name] = 'нет видео/аудио'
                if not need_img:
                    continue
                data = None
                if msg and msg.photo:
                    data = await client.download_media(msg, bytes)
                elif msg and msg.document:
                    data = await client.download_media(msg, bytes, thumb=-1)
                elif msg and msg.web_preview and msg.web_preview.photo:
                    data = await client.download_media(msg.web_preview.photo, bytes)
                if not data:
                    skip[name] = 'нет картинки'
                    continue
                open(os.path.join(MEDIA, name), 'wb').write(shrink(data))
                done += 1
            except Exception as e:
                skip[name] = str(e)[:120]
    finally:
        await client.disconnect()
        shutil.rmtree(tmp, ignore_errors=True)
    print(profile or 'main', 'скачано', done)


def main():
    skip = json.load(open(SKIP_FILE, encoding='utf-8')) if os.path.exists(SKIP_FILE) else {}
    for profile, base in (('', EXP), ('lazy', os.path.join(EXP, 'lazy'))):
        asyncio.run(fetch(profile, base, skip))
    json.dump(skip, open(SKIP_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
