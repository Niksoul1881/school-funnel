"""Проходит ботов конкурентов от имени аккаунта Telegram и записывает всё, что они присылают.

Настройка (один раз):
  1. my.telegram.org -> API development tools -> создать приложение -> взять api_id и api_hash.
  2. Создать private/tg_api.json:  {"api_id": 123456, "api_hash": "....", "phone": "+7..."}

Команды (из корня проекта):
  python scripts/bots_recorder.py login          # Telegram пришлёт код в приложение
  python scripts/bots_recorder.py code 12345     # ввести код (и пароль 2FA вторым аргументом, если есть)
  python scripts/bots_recorder.py start          # нажать «Старт» во всех ботах из списка
  python scripts/bots_recorder.py listen         # слушать и писать всё входящее (держать запущенным 2–3 дня)
  python scripts/bots_recorder.py press <бот> <текст кнопки>   # нажать кнопку / открыть ссылку из последних сообщений
  python scripts/bots_recorder.py say <@чат> <текст>           # написать в чат (кодовое слово в личку)
  python scripts/bots_recorder.py dump           # выгрузить историю чатов с ботами (то, что уже пришло)

Всё пишется в private/bots_export/:
  log.jsonl — каждое сообщение: время, чат, отправитель, текст, кнопки, ссылки
  <чат>.json — полная история чата после команды dump
Пишутся только чаты из списка BOTS и личные сообщения от аккаунтов, которых нет в контактах
(менеджеры школ пишут именно так). Личные переписки с контактами не записываются.
"""
import asyncio, json, os, sys, re, urllib.request
from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.tl.types import KeyboardButtonUrl, KeyboardButtonCallback, User

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV = os.path.join(P, 'private')
# Второй аккаунт: переменная окружения TG_PROFILE=lazy -> private/tg_api_lazy.json, своя сессия и папка выгрузок
PROFILE = os.environ.get('TG_PROFILE', '').strip()
SUFFIX = ('_' + PROFILE) if PROFILE else ''
OUT = os.path.join(PRIV, 'bots_export', PROFILE) if PROFILE else os.path.join(PRIV, 'bots_export')
os.makedirs(OUT, exist_ok=True)
CFG = json.load(open(os.path.join(PRIV, 'tg_api%s.json' % SUFFIX), encoding='utf-8'))
# TG_SESSION — путь к копии сессии, чтобы разовая команда не мешала запущенному run
SESSION = os.environ.get('TG_SESSION') or os.path.join(PRIV, 'tg_session%s' % SUFFIX)
STATE = os.path.join(PRIV, 'tg_login_state%s.json' % SUFFIX)

BOTS = {
    # основные воронки (статьи -> тест-драйв)
    'purvinsh': 'other_digital_bot',
    'purvinsh_events': 'money_2026_bot',            # эфиры, мастер-классы, воркшопы (до 16.09.2026)
    'muratov': 'Alekseicoach_bot',
    'pautov': 'pautov_techspec_bot',
    'korablev': 'korablevtech_content_bot',
    'itgirls': 'itgirlsclub_bot',
    'bothelp_academy': 'BotHelpAcademyBot',
    'bothelp_events': 'whatshelpbot',               # вебинары BotHelp (до 21.09.2026)
    'zerocoder_meetings': 'zerocoder_offline_meetings_bot',  # до 11.10.2026
    'zerocoder_msk': 'zerocodermoscowregbot',
    'zerocoder_stream': 'mavestreambot',
    'himik_questions': 'anonimnyye_voprosy_bot',   # анонимные вопросы Химику, ничего не отправлять
    # боты мероприятий Кораблёва (каждый под свой эфир; часть может уже не отвечать)
    'korablev_communication': 'korablevtech_communication_bot',
    'korablev_mk3': 'korablevtech_mk3_bot',
    'korablev_techspec2026': 'korablevtech_techspec2026_bot',
    'korablev_intensive': 'korablevtech_intensive_bot',
    'korablev_mklegendary': 'korablevtech_mklegendary_bot',
    'korablev_masterclass': 'korablevtech_masterclass_bot',
    'korablev_newyear': 'korablevtech_newyear_bot',
    'korablev_web': 'korablevtech_web_bot',
    'korablev_mk': 'korablevtech_mk_bot',
    'korablev_faststart': 'korablevtech_faststart_bot',
    'korablev_blitz': 'korablevtech_blitzkurs_bot',
    'korablev_event': 'korablevtech_event_bot',
    'korablev_main': 'korablevtech_bot',
    # найдены дополнительно по сайтам и постам
    'danya': 'danya_vibe_bot',                      # Даня @myvibeai, готовит свой курс
    'gethelpers_vacancy': 'GH_vacancy_bot',         # GetHelpers
    'gethelpers_help': 'helpweb24bot',              # GetHelpers
    'frilans_na_legke': 'frilans_na_legke_bot',
    'zerocoder_cat': 'zero_neuro_cat_bot',
}
WATCH = set(u.lower() for u in BOTS.values()) | {'ledokol_sever', 'vlad_tehspecpro', 'vlad_techspec', 'lexs901', 'alekseiref',
                                                 'purv_vlad_spec', 'pautov_al',
                                                 'money_2026_bot', 'itgirls_admin', 'zerocoder_v1',
                                                 'andrey_111_58', 'danya_s_vibe'}

client = TelegramClient(SESSION, CFG['api_id'], CFG['api_hash'])


def peer(chat):
    """@ник или числовой id группы (-100…) -> то, что понимает Telethon."""
    return int(chat) if re.fullmatch(r'-?\d+', chat or '') else chat


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def buttons_of(msg):
    out = []
    if msg.reply_markup and getattr(msg.reply_markup, 'rows', None):
        for row in msg.reply_markup.rows:
            for b in row.buttons:
                item = {'text': b.text}
                if isinstance(b, KeyboardButtonUrl):
                    item['url'] = b.url
                elif isinstance(b, KeyboardButtonCallback):
                    item['callback'] = True
                out.append(item)
    return out


def links_of(msg):
    links = []
    for ent, txt in (msg.get_entities_text() or []):
        url = getattr(ent, 'url', None)
        links.append(url or txt) if (url or 'http' in txt or 't.me' in txt) else None
    return links


async def describe(msg):
    chat = await msg.get_chat()
    sender = await msg.get_sender()
    return {
        'time': msg.date.astimezone().isoformat(timespec='seconds'),
        'logged_at': now(),
        'chat': getattr(chat, 'username', None) or getattr(chat, 'title', None) or str(msg.chat_id),
        'chat_id': msg.chat_id,
        'from': (getattr(sender, 'username', None) or getattr(sender, 'first_name', '') or '') if sender else '',
        'out': msg.out,
        'msg_id': msg.id,
        'text': msg.message or '',
        'media': type(msg.media).__name__ if msg.media else None,
        'buttons': buttons_of(msg),
        'links': links_of(msg),
    }


async def should_record(msg):
    chat = await msg.get_chat()
    uname = (getattr(chat, 'username', '') or '').lower()
    if uname in WATCH:
        return True
    if isinstance(chat, User):
        return False  # личные чаты — только из списка WATCH (боты и известные менеджеры школ), остальное не пишем
    title = (getattr(chat, 'title', '') or '').lower()
    return any(k in title for k in ['тест-драйв', 'тест драйв', 'техспец', 'бот'])  # группы тест-драйва


def log(rec):
    with open(os.path.join(OUT, 'log.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


async def cmd_login():
    await client.connect()
    r = await client.send_code_request(CFG['phone'])
    json.dump({'hash': r.phone_code_hash}, open(STATE, 'w'))
    print('Код отправлен в Telegram. Дальше: python scripts/bots_recorder.py code <код>')


async def cmd_code(code, pwd=None):
    await client.connect()
    h = json.load(open(STATE))['hash']
    try:
        await client.sign_in(CFG['phone'], code, phone_code_hash=h)
    except Exception as e:
        if 'password' in str(e).lower() and pwd:
            await client.sign_in(password=pwd)
        else:
            raise
    me = await client.get_me()
    print('Вошли как', me.first_name, '@' + (me.username or ''))


async def cmd_start():
    await client.start(phone=CFG['phone'])
    for name, bot in BOTS.items():
        try:
            already = [m async for m in client.iter_messages(bot, limit=1)]
            if already:
                print('Уже запущен, пропускаю:', bot)
                continue
            m = await client.send_message(bot, '/start')
            log({'time': now(), 'chat': bot, 'out': True, 'text': '/start', 'note': 'старт воронки'})
            print('Старт:', name, bot)
        except Exception as e:
            print('Не получилось:', bot, e)
        await asyncio.sleep(3)


async def cmd_listen():
    await client.start(phone=CFG['phone'])

    @client.on(events.NewMessage(incoming=True))
    async def on_new(ev):
        if await should_record(ev.message):
            rec = await describe(ev.message)
            log(rec)
            print(rec['time'], rec['chat'], (rec['text'] or '')[:80].replace('\n', ' '))

    @client.on(events.MessageEdited(incoming=True))
    async def on_edit(ev):
        if await should_record(ev.message):
            rec = await describe(ev.message)
            rec['edited'] = True
            log(rec)

    print('Слушаю. Не закрывай окно. Ctrl+C — остановить.')
    await client.run_until_disconnected()


async def cmd_press(bot, label):
    await client.start(phone=CFG['phone'])
    async for msg in client.iter_messages(bot, limit=20):
        for i, row in enumerate((msg.reply_markup.rows if msg.reply_markup and getattr(msg.reply_markup, 'rows', None) else [])):
            for b in row.buttons:
                if label.lower() in (b.text or '').lower():
                    if isinstance(b, KeyboardButtonUrl):
                        log({'time': now(), 'chat': bot, 'out': True, 'note': 'открыл ссылку', 'text': b.text, 'url': b.url})
                        try:
                            urllib.request.urlopen(urllib.request.Request(b.url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read()
                        except Exception as e:
                            print('Ссылка не открылась:', e)
                        print('Открыл ссылку:', b.url)
                    else:
                        await msg.click(text=b.text)
                        log({'time': now(), 'chat': bot, 'out': True, 'note': 'нажал кнопку', 'text': b.text})
                        print('Нажал:', b.text)
                    return
    print('Кнопка не найдена в последних 20 сообщениях')


async def cmd_say(chat, text):
    await client.start(phone=CFG['phone'])
    await client.send_message(peer(chat), text)
    log({'time': now(), 'chat': chat, 'out': True, 'text': text, 'note': 'написал'})
    print('Отправлено')


async def cmd_dump():
    await client.start(phone=CFG['phone'])
    async for d in client.iter_dialogs():
        ent = d.entity
        uname = (getattr(ent, 'username', '') or '').lower()
        title = (getattr(ent, 'title', '') or '').lower()
        keep = (uname in WATCH
                or (isinstance(ent, User) and not ent.contact and not ent.is_self)
                or any(k in title for k in ['тест-драйв', 'тест драйв', 'техспец']))
        if not keep:
            continue
        msgs = []
        async for m in client.iter_messages(ent, reverse=True):
            msgs.append(await describe(m))
        fn = re.sub(r'[^\w.-]', '_', uname or str(d.id))
        json.dump(msgs, open(os.path.join(OUT, fn + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Выгружено:', fn, len(msgs))


async def cmd_dump_folder(folder_title, started=False):
    """Выгружает все чаты из папки Telegram с этим названием (например, «Школа боты»)."""
    from telethon.tl.functions.messages import GetDialogFiltersRequest
    if not started:
        await client.start(phone=CFG['phone'])
    res = await client(GetDialogFiltersRequest())
    filters = getattr(res, 'filters', res)
    target = None
    for f in filters:
        title = getattr(f, 'title', None)
        title = getattr(title, 'text', title)  # в новых версиях title — объект с текстом
        if title and str(title).strip().lower() == folder_title.strip().lower():
            target = f
            break
    if not target:
        names = [str(getattr(getattr(f, 'title', ''), 'text', getattr(f, 'title', ''))) for f in filters]
        print('Папка не найдена. Есть такие:', names)
        return
    peers = list(getattr(target, 'pinned_peers', []) or []) + list(getattr(target, 'include_peers', []) or [])
    stamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    folder_out = os.path.join(OUT, 'folder_' + stamp)
    os.makedirs(folder_out, exist_ok=True)
    for peer in peers:
        try:
            ent = await client.get_entity(peer)
        except Exception as e:
            print('Не открылся чат:', e)
            continue
        if isinstance(ent, User) and ent.contact:
            continue  # личные контакты (например, коллеги) не выгружаем
        name = getattr(ent, 'username', None) or getattr(ent, 'title', None) or \
            ((getattr(ent, 'first_name', '') or '') + ' ' + (getattr(ent, 'last_name', '') or '')).strip() or str(ent.id)
        msgs = []
        async for m in client.iter_messages(ent, reverse=True):
            msgs.append(await describe(m))
        fn = re.sub(r'[^\w.-]+', '_', name)[:50] + '_' + str(abs(ent.id))[-6:]
        json.dump({'chat': name, 'messages': msgs}, open(os.path.join(folder_out, fn + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('Выгружено:', name, len(msgs))
    print('Готово:', folder_out)


async def cmd_folder_add(folder_title, started=False):
    """Кладёт в папку все чаты из WATCH (боты школ и их менеджеры), с которыми уже есть переписка. Папки нет — создаёт."""
    from telethon.tl.functions.messages import GetDialogFiltersRequest, UpdateDialogFilterRequest
    from telethon.tl.types import DialogFilter, TextWithEntities
    from telethon.utils import get_peer_id
    if not started:
        await client.start(phone=CFG['phone'])
    res = await client(GetDialogFiltersRequest())
    filters = getattr(res, 'filters', res)
    target = None
    for f in filters:
        title = getattr(f, 'title', None)
        title = getattr(title, 'text', title)
        if isinstance(f, DialogFilter) and title and str(title).strip().lower() == folder_title.strip().lower():
            target = f
            break
    if not target:
        used = [getattr(f, 'id', 0) for f in filters]
        target = DialogFilter(id=max([1] + used) + 1, title=TextWithEntities(folder_title, []),
                              pinned_peers=[], include_peers=[], exclude_peers=[])
    have = set(get_peer_id(p) for p in list(target.pinned_peers or []) + list(target.include_peers or []))
    added = []
    async for d in client.iter_dialogs():
        uname = (getattr(d.entity, 'username', None) or '').lower()
        test_drive = any(k in (d.name or '').lower() for k in ('тест-драйв', 'тест драйв'))
        if (uname in WATCH or test_drive) and d.id not in have:
            uname = uname or d.name
            target.include_peers.append(await client.get_input_entity(d.entity))
            have.add(d.id)
            added.append(uname)
    if added:
        await client(UpdateDialogFilterRequest(id=target.id, filter=target))
    print('Добавлено в «%s»: %d %s' % (folder_title, len(added), ', '.join(added)))


QUEUE = os.path.join(OUT, 'commands.txt')
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'


def open_in_browser(url):
    """Открывает страницу в невидимом браузере, чтобы на ней сработали счётчики (открыл статью / урок)."""
    import subprocess
    try:
        subprocess.run([EDGE, '--headless', '--disable-gpu', '--virtual-time-budget=60000', '--dump-dom', url],
                       capture_output=True, timeout=120)
        return True
    except Exception as e:
        print('Браузер не открыл:', e)
        return False


async def find_button(chat, label):
    async for msg in client.iter_messages(chat, limit=30):
        rows = msg.reply_markup.rows if msg.reply_markup and getattr(msg.reply_markup, 'rows', None) else []
        for row in rows:
            for b in row.buttons:
                if label.lower() in (b.text or '').lower():
                    return msg, b
    return None, None


async def run_command(line):
    parts = line.split(' ', 2)
    cmd = parts[0]
    if cmd == 'press' and len(parts) == 3:
        chat, label = parts[1], parts[2]
        msg, b = await find_button(chat, label)
        if not b:
            log({'time': now(), 'chat': chat, 'out': True, 'note': 'кнопка не найдена', 'text': label}); return
        if isinstance(b, KeyboardButtonUrl):
            if 't.me/' in b.url:
                log({'time': now(), 'chat': chat, 'out': True, 'note': 'ссылка на Telegram, не открываю автоматически', 'url': b.url})
            else:
                ok = open_in_browser(b.url)
                log({'time': now(), 'chat': chat, 'out': True, 'note': 'открыл ссылку в браузере' if ok else 'ссылка не открылась', 'text': b.text, 'url': b.url})
        else:
            await msg.click(text=b.text)
            log({'time': now(), 'chat': chat, 'out': True, 'note': 'нажал кнопку', 'text': b.text})
    elif cmd == 'say' and len(parts) == 3:
        await client.send_message(peer(parts[1]), parts[2])
        log({'time': now(), 'chat': parts[1], 'out': True, 'note': 'написал', 'text': parts[2]})
    elif cmd == 'open' and len(parts) >= 2:
        ok = open_in_browser(parts[1])
        log({'time': now(), 'out': True, 'note': 'открыл ссылку в браузере' if ok else 'ссылка не открылась', 'url': parts[1]})
    elif cmd == 'start' and len(parts) >= 2:
        await client.send_message(parts[1], '/start')
        log({'time': now(), 'chat': parts[1], 'out': True, 'text': '/start', 'note': 'старт воронки'})
    elif cmd == 'folder-add':
        await cmd_folder_add('Школа боты', started=True)
    elif cmd == 'dump':
        await dump_folder_into('Школа боты')
        await dump_watch()
    else:
        log({'time': now(), 'out': True, 'note': 'непонятная команда', 'text': line})


async def dump_watch():
    """Выгрузка чатов с ботами из списка, которых нет в папке."""
    stamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    d = os.path.join(OUT, 'bots_' + stamp)
    os.makedirs(d, exist_ok=True)
    for bot in BOTS.values():
        try:
            msgs = [await describe(m) async for m in client.iter_messages(bot, reverse=True)]
        except Exception as e:
            continue
        if msgs:
            json.dump({'chat': bot, 'messages': msgs}, open(os.path.join(d, bot + '.json'), 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)


async def dump_folder_into(folder_title):
    await cmd_dump_folder(folder_title, started=True)


async def cmd_run():
    """Постоянный режим: запись входящих + выгрузка раз в 3 часа + команды из private/bots_export/commands.txt."""
    await client.start(phone=CFG['phone'])

    @client.on(events.NewMessage(incoming=True))
    async def on_new(ev):
        if await should_record(ev.message):
            log(await describe(ev.message))

    @client.on(events.MessageEdited(incoming=True))
    async def on_edit(ev):
        if await should_record(ev.message):
            rec = await describe(ev.message); rec['edited'] = True; log(rec)

    @client.on(events.ChatAction())
    async def on_action(ev):
        try:
            chat = await ev.get_chat()
            title = getattr(chat, 'title', '') or ''
            if any(k in title.lower() for k in ['тест-драйв', 'тест драйв', 'техспец']):
                log({'time': now(), 'chat': title, 'note': 'событие в группе',
                     'kicked': bool(ev.user_kicked), 'left': bool(ev.user_left), 'joined': bool(ev.user_joined)})
        except Exception:
            pass

    async def loop():
        last_dump = 0
        while True:
            if os.path.exists(QUEUE):
                lines = [l.strip() for l in open(QUEUE, encoding='utf-8') if l.strip() and not l.startswith('#')]
                open(QUEUE, 'w', encoding='utf-8').close()
                for line in lines:
                    try:
                        await run_command(line)
                    except Exception as e:
                        log({'time': now(), 'note': 'ошибка команды', 'text': line, 'error': str(e)})
                    await asyncio.sleep(5)
            if asyncio.get_event_loop().time() - last_dump > 3 * 3600:
                try:
                    await dump_folder_into('Школа боты')
                    await dump_watch()
                except Exception as e:
                    log({'time': now(), 'note': 'ошибка выгрузки', 'error': str(e)})
                try:  # перерисовать доску воронок
                    import subprocess
                    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(P, 'scripts', 'build_schemes.py')],
                                   capture_output=True, timeout=300)
                except Exception:
                    pass
                last_dump = asyncio.get_event_loop().time()
            with open(os.path.join(OUT, 'heartbeat.txt'), 'w') as f:
                f.write(now())
            await asyncio.sleep(30)

    client.loop.create_task(loop())
    print('Работаю. Окно не закрывать.')
    await client.run_until_disconnected()


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    coro = {'login': lambda: cmd_login(), 'code': lambda: cmd_code(a[1], a[2] if len(a) > 2 else None),
            'start': lambda: cmd_start(), 'listen': lambda: cmd_listen(),
            'press': lambda: cmd_press(a[1], ' '.join(a[2:])), 'say': lambda: cmd_say(a[1], ' '.join(a[2:])),
            'dump': lambda: cmd_dump(),
            'dump-folder': lambda: cmd_dump_folder(' '.join(a[1:]) or 'Школа боты'),
            'folder-add': lambda: cmd_folder_add(' '.join(a[1:]) or 'Школа боты'),
            'run': lambda: cmd_run()}[cmd]()
    async def run():
        try:
            await coro
        finally:
            await client.disconnect()
    client.loop.run_until_complete(run())


if __name__ == '__main__':
    main()
