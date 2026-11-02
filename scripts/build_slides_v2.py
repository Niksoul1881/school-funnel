"""Слайды v2 — под сценарий Егора «Тест-драйв: структура и текст уроков» 24.10 (вводный + 6 уроков, буквы вместо цифр).
Стиль тот же, что в build_slides.py (тёмная «светящаяся дорога»). Источник текста: sources/course/тест_драйв_v2_егор.txt
Выход: docs/course/slides/deck2/<id>.html|jpg и страница «текст + слайды» docs/course/test_drive_v2.html (с комментариями).
Запуск: python scripts/build_slides_v2.py [--no-render] [id ...]"""
import os, re, sys, html, json

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P, 'scripts'))
import build_slides as B

B.LESSONS = [
    (0, 'Вводный урок', 'Старт', '#ff8a3d'),
    (1, 'Урок 1 · Профессия', 'Техспец', '#34d399'),
    (2, 'Урок 2 · Чат-боты', 'Чат-боты', '#3ec7ff'),
    (3, 'Урок 3 · AI-агенты', 'AI-агенты', '#8b5cf6'),
    (4, 'Урок 4 · Мини-приложения', 'Mini Apps', '#ff4f8b'),
    (5, 'Урок 5 · Клиенты', 'Клиенты', '#facc15'),
    (6, 'Урок 6 · Созвон с ученицей', 'Созвон', '#e879f9'),
]
B.COVER_VIS = {
    0: lambda: B.ic('flag', 'ic huge'),
    1: lambda: B.ic('case', 'ic huge'),
    2: lambda: B.phone('kvasich.png', 370, 780, '50% 0%', 'rgba(62,199,255,.7)', 'transform:rotate(-4deg)'),
    3: lambda: B.phone('pulse.png', 370, 780, '50% 0%', 'rgba(139,92,246,.8)', 'transform:rotate(-4deg)'),
    4: lambda: (B.phone('gym.png', 330, 700, '50% 0%', 'rgba(255,79,139,.7)', 'transform:rotate(-7deg) translateY(30px);margin-right:-50px') +
                B.phone('manekken.png', 330, 700, '50% 0%', 'rgba(192,38,211,.7)', 'transform:rotate(5deg) translateY(-20px)')),
    5: lambda: B.ic('target', 'ic huge'),
    6: lambda: B.ic('users', 'ic huge'),
}
DECK = os.path.join(B.SL, 'deck2')
SRC = os.path.join(P, 'sources', 'course', 'тест_драйв_v2_егор.txt')
page, cards, flow, ic, phone, slot, todo, ARR, svg = B.page, B.cards, B.flow, B.ic, B.phone, B.slot, B.todo, B.ARR, B.svg
N_LETTERS = 6

XCSS = r'''
.app{background:#fff;height:100%;font-family:Manrope,"Segoe UI",sans-serif;color:#1d2433;display:flex;flex-direction:column}
.app .bar{padding:58px 18px 14px;background:#fdf2f8;font-weight:800;font-size:20px;color:#9d174d}
.app .sub2{padding:12px 16px 4px;font-size:14px;font-weight:800;color:#6b7280;text-transform:uppercase;letter-spacing:.06em}
.app .svc{margin:4px 14px;padding:12px 14px;border-radius:14px;background:#f4f4f5;display:flex;justify-content:space-between;font-size:16px;font-weight:700}
.app .svc.on{background:#fce7f3;outline:2px solid #ec4899}
.app .days{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;padding:6px 14px}
.app .d{text-align:center;padding:8px 0;border-radius:10px;font-size:15px;font-weight:700;background:#f4f4f5}
.app .d.on{background:#ec4899;color:#fff}.app .d.off{color:#c4c4c8;background:#fafafa}
.app .slots{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:6px 14px}
.app .s{border:2px solid #f9a8d4;border-radius:12px;text-align:center;padding:10px 0;font-weight:700;font-size:16px;color:#be185d}
.app .s.on{background:#ec4899;color:#fff;border-color:#ec4899}
.app .btn{margin:auto 14px 20px;background:#ec4899;color:#fff;border-radius:14px;text-align:center;padding:15px;font-weight:800;font-size:17px}
.tg .msgs{min-height:0;overflow:hidden}
.tg .b code{font-family:Consolas,monospace;font-size:14px;color:#8fe0ff;word-break:break-all}
.letter{width:300px;height:380px;border-radius:44px;display:flex;align-items:center;justify-content:center;font-family:Unbounded,sans-serif;font-weight:800;font-size:230px;
 color:var(--gold);border:4px solid var(--gold);background:radial-gradient(circle at 50% 30%,rgba(255,209,102,.3),rgba(255,209,102,.05) 70%);
 box-shadow:0 0 0 16px rgba(255,209,102,.08),0 0 140px rgba(255,209,102,.5);text-shadow:0 0 50px rgba(255,209,102,.8)}
'''
S = []


def add(sid, lesson, anchor, cap, htm):
    S.append((sid, lesson, anchor, cap, htm))


def P_(lesson, inner, **kw):
    kw.setdefault('extra_css', XCSS)
    return page(lesson, inner, **kw)


def tgphone(name, msgs, w=360, h=760, glow='rgba(62,199,255,.6)', av='Б', extra=''):
    body = ''
    for kind, t in msgs:
        if kind == 'kb':
            body += '<div class="kb">%s</div>' % ''.join('<div>%s</div>' % x for x in t)
        else:
            body += '<div class="b%s">%s</div>' % (' me' if kind == 'me' else '', t)
    return ('<div class="ph" style="width:%dpx;height:%dpx;--glow:%s;%s"><div class="tg"><div class="top"><div class="av">%s</div>'
            '<div><div class="nm">%s</div><div class="st">бот</div></div></div><div class="msgs">%s</div></div></div>') % (w, h, glow, extra, av, name, body)


def closer(lesson, points, nxt_title, nxt_text, letter_note=True):
    nl = B.LESSONS[lesson + 1] if lesson + 1 < len(B.LESSONS) else None
    pts = ''.join('<div class="g" style="display:flex;gap:26px;align-items:center;padding:28px 34px"><span class="n">%d</span><h3 style="font-size:29px;line-height:1.3">%s</h3></div>'
                  % (i + 1, p) for i, p in enumerate(points))
    acc = nl[3] if nl else '#ffd166'
    nx = ('<div class="g" style="--acc:%s;border-color:color-mix(in srgb,var(--acc) 60%%,transparent);box-shadow:0 0 60px color-mix(in srgb,var(--acc) 22%%,transparent)">'
          '<div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--acc)">Дальше · %s</div>'
          '<h3 style="margin-top:14px;font-size:38px">%s</h3><p>%s</p>%s</div>') % (
        acc, nl[2] if nl else 'Разбор', nxt_title, nxt_text,
        '<p style="margin-top:18px;color:var(--gold)">Буква в этом уроке уже была — собирай слово</p>' if letter_note else '')
    inner = ('<div class="body" style="top:270px;display:grid;grid-template-columns:1.3fr 1fr;gap:40px;align-items:center">'
             '<div style="display:grid;gap:22px">%s</div><div>%s</div></div>') % (pts, nx)
    return P_(lesson, inner, head='Итог урока · <span class="grad">это только верхушка</span>')


def letter(lesson):
    k = lesson
    slots = ''.join('<div class="slotd %s" style="width:130px;height:170px;font-size:90px">%s</div>' % (
        'on' if i == k else ('got' if i < k else ''), '?' if i <= k else '_') for i in range(1, N_LETTERS + 1))
    inner = ('<div style="position:absolute;left:0;right:0;top:150px;text-align:center">'
             '<div style="font-size:24px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--gold)">Собери слово · буква %d из %d</div></div>'
             '<div style="position:absolute;left:0;right:0;top:240px;display:flex;justify-content:center"><div class="letter">?</div></div>'
             '<div style="position:absolute;left:0;right:0;top:700px;display:flex;justify-content:center;gap:20px">%s</div>'
             '<div style="position:absolute;right:96px;top:62px;font-size:17px;font-weight:700;color:var(--gold);opacity:.85">? — %s</div>') % (
        k, N_LETTERS, slots, todo('вставить букву (слово решается, В16)'))
    return P_(lesson, inner)


H3 = lambda t, s=31: '<h3 style="font-size:%dpx">%s</h3>' % (s, t)

# ================= ВВОДНЫЙ =================
add('v0_cover', 0, ('p1-0', None), 'Обложка: вводный урок', B.cover(0, 'Тест-драйв профессии нового времени',
    'Боты, AI-агенты и мини-приложения с помощью нейронки — без кода и с нуля. Пару дней, по-человечески.',
    ['<span class="tag acc">≈ 10 минут</span>', '<span class="tag">6 уроков</span>', '<span class="tag code">собери слово</span>']).replace('</style>', XCSS + '</style>', 1))
MAP = [('case', 'Техспец нового времени', 'Откуда профессия, кто платит, немного обо мне'),
       ('bot', 'Чат-боты', 'Соберёшь своего бота по нашему шаблону'),
       ('spark', 'AI-агенты', 'Чем агент лучше нейронки и почему он дороже'),
       ('phone', 'Мини-приложения', 'Приложения прямо внутри Телеграма'),
       ('target', 'Клиенты', 'Кому предложить первым и что написать'),
       ('users', 'Созвон с ученицей', 'Как это у живого человека, без глянца')]
add('v0_map', 0, ('p1-1', 0), 'Карта: шесть уроков', P_(0,
    '<div class="body" style="top:290px;bottom:250px;display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:1fr 1fr;gap:22px">%s</div>'
    '<div class="strip" style="bottom:138px;border-color:rgba(255,209,102,.6);background:linear-gradient(90deg,rgba(255,209,102,.16),rgba(255,209,102,.03))">%s'
    '<div><span class="gold">★ В конце — анкета и персональный разбор.</span> От первого бота до того, как его продать: вся логика целиком.</div></div>' % (
        ''.join('<div class="g" style="--acc:%s;display:flex;gap:24px;align-items:center;padding:24px 30px;border-color:color-mix(in srgb,%s 45%%,transparent)">%s'
                '<div><div style="font-size:16px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:%s">Урок %d</div>%s<p style="margin-top:6px;font-size:20px">%s</p></div></div>'
                % (B.LESSONS[i + 1][3], B.LESSONS[i + 1][3], ic(icn, 'ic', B.LESSONS[i + 1][3]), B.LESSONS[i + 1][3], i + 1, H3(t, 28), d)
                for i, (icn, t, d) in enumerate(MAP)), ic('done', 'ic sm goldc')),
    head='Что будет <span class="grad">дальше</span>', sub='Шесть уроков, каждый минут на двадцать-тридцать.'))
add('v0_why', 0, ('p1-2', None), 'Пять причин: почему сейчас', P_(0,
    '<div class="body c" style="top:270px">%s</div>' % cards([
        ('trend', 'Бизнес уже автоматизирует', 'Нейронки на рутине — и кто-то должен их настроить'),
        ('users', 'Другие профессии сжимаются', 'А эта растёт: ты работаешь нейронкой, а не соревнуешься с ней'),
        ('spark', 'Проще, чем кажется', 'Код пишет нейронка, ты объясняешь задачу словами'),
        ('coin', 'Платят уже сейчас', 'Нормальный рынок, без сказочных сумм'),
        ('home', 'Мягкий вход', 'Вечером час-два. Работу не бросаем', 'hl')], cols=5, gap=20),
    head='Почему это и <span class="grad">почему сейчас</span>', sub='Коротко — пять причин.'))
PRICES = [('bot', 'Простой бот', '5–15', 'тыс. ₽'), ('spark', 'Бот с оплатой или AI-агент', '40–60', 'тыс. ₽'), ('wrench', 'Поддержка', '5–15', 'тыс. ₽ в месяц')]


def prices(lesson, head, sub, anchor_note=''):
    return P_(lesson, '<div class="body c" style="top:270px">%s</div>' % (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:28px">' + ''.join(
            '<div class="g" style="padding:40px 40px">%s<div style="font-size:27px;font-weight:700;color:var(--muted);margin-top:26px">%s</div>'
            '<div style="font-family:Unbounded,sans-serif;font-weight:800;font-size:84px;margin-top:10px;line-height:1" class="grad">%s</div>'
            '<div style="font-size:28px;font-weight:800;margin-top:8px">%s</div></div>' % (ic(i), t, p, u) for i, t, p, u in PRICES) + '</div>'
        + ('<div style="margin-top:34px;font-size:25px;font-weight:700;color:var(--muted)">%s</div>' % anchor_note if anchor_note else '')),
        head=head, sub=sub)


add('v0_prices', 0, ('p1-2', None), 'Сколько платят (вилка на всю серию)', prices(0, 'За это платят <span class="grad">уже сейчас</span>',
    'Это не сказочные суммы — это нормальный рынок.', 'Разовые заказы — деньги сейчас. Поддержка — каждый месяц с одного клиента.'))
add('v0_razbor', 0, ('p1-3', None), 'Главное — персональный разбор', P_(0,
    '<div class="body c" style="top:280px">%s</div>' % flow([
        ('play', 'Уроки + практикум', 'Бот, агент — руками'),
        ('list', 'Анкета', 'Кто ты, что получилось, какие были эмоции'),
        ('user', 'Персональный разбор', 'Бесплатно. Расскажем и про обучение'),
        ('map', 'Твой план', 'С чего начать именно тебе', 'hl')]),
    head='Самое ценное — <span class="grad">разбор в конце</span>', sub='Уроки нужны, чтобы на разборе тебе было легко. Пиши в анкете как есть — даже «ничего не понятно».'))
add('v0_timer', 0, ('p1-4', None), 'Правило: 48 часов', P_(0,
    '<div style="position:absolute;left:0;right:0;top:170px;text-align:center">'
    '<div style="font-size:24px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)">одно правило</div>'
    '<div style="font-family:Unbounded,sans-serif;font-weight:800;font-size:250px;line-height:1.05;margin-top:20px;letter-spacing:-.02em;'
    'background:linear-gradient(180deg,#fff,#c9d1ff);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 40px rgba(139,92,246,.55))">48:00:00</div>'
    '<div style="display:flex;justify-content:center;gap:28px;margin-top:50px">'
    '<div class="g" style="width:560px;text-align:left;display:flex;gap:22px;align-items:center">%s<div><h3 style="font-size:26px">За два дня картинка складывается</h3><p style="margin-top:6px">Отложишь «на выходные» — через неделю не вспомнишь</p></div></div>'
    '<div class="g" style="width:560px;text-align:left;display:flex;gap:22px;align-items:center">%s<div><h3 style="font-size:26px">Форс-мажор?</h3><p style="margin-top:6px">Напиши в чат — продлим. Без объяснительных</p></div></div>'
    '</div></div>' % (ic('clock', 'ic sm'), ic('chat', 'ic sm'))))
add('v0_rules', 0, ('p1-5', None), 'Как смотреть: три вещи', P_(0,
    '<div class="body" style="top:290px;bottom:250px;display:grid;grid-template-columns:repeat(3,1fr);gap:26px">%s</div>'
    '<div class="strip" style="bottom:138px">%s<div>И выключи на время внутреннего скептика: всё это ты <span class="gold">проверишь руками уже во втором уроке</span>.</div></div>' % (
        ''.join('<div class="g" style="display:flex;flex-direction:column;padding:38px 38px"><div class="bnum" style="font-size:120px">%02d</div>'
                '<div style="margin-top:auto"><h3 style="font-size:36px">%s</h3><p style="font-size:25px;margin-top:14px">%s</p></div></div>' % (i + 1, t, p)
                for i, (t, p) in enumerate((('По порядку', 'Каждый урок опирается на предыдущий'),
                                            ('Делай практику', 'Даже если «и так понятно». Это пять минут, и навык остаётся с тобой'),
                                            ('Спрашивай', 'Глупых вопросов нет. Я тоже когда-то не знал, что такое токен')))),
        ic('eyeoff', 'ic sm')),
    head='Как смотреть, чтобы был <span class="grad">толк</span>'))
add('v0_tech', 0, ('p1-6', None), 'Техническая информация', P_(0,
    '<div class="body c" style="top:270px;bottom:250px">%s</div>'
    '<div style="position:absolute;left:0;right:0;bottom:150px;text-align:center;font-family:Unbounded,sans-serif;font-weight:800;font-size:46px">Время пошло. <span class="grad">Погнали!</span></div>' % cards([
        ('laptop', 'Урок не открывается?', 'Выключи VPN и открой ссылку в браузере, а не внутри Телеграма'),
        ('x', '«Возможно, это спам»', 'Нажми крестик на плашке — ссылки станут кликабельными'),
        ('play', 'Как получить урок 1', B.todo('[что нажать после вводного]') + ' — и бот пришлёт первый урок', 'hl')]),
    head='Пара <span class="grad">технических моментов</span>'))

# ================= УРОК 1 =================
add('v1_cover', 1, ('p2-0', None), 'Обложка урока 1', B.cover(1, 'Технический специалист нового времени',
    'Кто я и как сюда пришёл, что это за профессия, кто за неё платит и почему именно сейчас.',
    ['<span class="tag acc">≈ 20–25 минут</span>', '<span class="tag code">буква №1</span>']).replace('</style>', XCSS + '</style>', 1))
add('v1_word', 1, ('p2-1', None), 'Игра: собери слово', P_(1,
    '<div style="position:absolute;left:0;right:0;top:170px;text-align:center"><h1 style="font-size:76px">Собери <span class="grad">слово</span></h1>'
    '<div class="sub" style="margin:18px auto 0">В каждом уроке в случайный момент на экране появится буква. Собери по порядку и отправь в чат.</div></div>'
    '<div style="position:absolute;left:0;right:0;top:430px;display:flex;justify-content:center;gap:28px">%s</div>'
    '<div style="position:absolute;left:50%%;transform:translateX(-50%%);top:740px;display:flex;align-items:center;gap:22px;font-size:28px;font-weight:700;white-space:nowrap">'
    '%s Слово в чат = %s</div>' % (
        ''.join('<div class="slotd" style="width:170px;height:220px"><span style="font-size:100px">_</span></div>' for _ in range(N_LETTERS)),
        ic('gift', 'ic sm goldc'), todo('[БОНУС]'))))
for k in range(1, 7):
    anchors = {1: ('p2-1', 0), 2: ('p3-7', None), 3: ('p4-7', None), 4: ('p5-5', None), 5: ('p6-7', None), 6: ('p7-3', None)}
    add('v%d_letter' % k, k, anchors[k], 'Буква %d из %d (вставить в случайный момент урока)' % (k, N_LETTERS), letter(k))
STORY = [('store', 'Официант', 'Подъём в 6 утра, смены. Денег — на квартиру и еду'),
         ('help', 'Тупик', 'Панические атаки, курсы без результата'),
         ('table', 'Задача на работе', 'Пришлось разобраться в автоматизации ' + todo('[Wildberries: из 7 осталось 2]')),
         ('bot', 'Первый бот', 'За 30 минут'),
         ('coin', 'Первый заказ', 'Запись психологу — 5 000 ₽ за один вечер'),
         ('spark', 'Сейчас', 'Боты и AI-агенты для бизнеса, ' + todo('[N]') + ' ч в день')]
add('v1_story', 1, ('p2-2', 0), 'История Егора: таймлайн + места под фото', P_(1,
    '<svg width="1920" height="1080" style="position:absolute;left:0;top:0"><defs><linearGradient id="rg" x1="0" x2="1"><stop offset="0" stop-color="#8b5cf6"/><stop offset=".4" stop-color="#3ec7ff"/>'
    '<stop offset=".75" stop-color="#ff4f8b"/><stop offset="1" stop-color="#ffd166"/></linearGradient><filter id="gl"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
    '<path d="M200 640 L1720 640" stroke="url(#rg)" stroke-width="8" stroke-linecap="round" filter="url(#gl)"/></svg>'
    + ''.join('<div style="position:absolute;left:%dpx;top:640px;transform:translate(-50%%,-50%%)">%s</div>'
              '<div style="position:absolute;left:%dpx;top:%dpx;width:280px;transform:translateX(-50%%);text-align:center">'
              '<h3 style="font-family:Unbounded;font-weight:600;font-size:25px;color:%s">%s</h3>'
              '<p style="margin-top:8px;font-size:19px;line-height:1.38;color:var(--muted);font-weight:600">%s</p></div>' % (
                  200 + i * 304, ic(icn, 'ic sm goldc' if i == 5 else 'ic sm'), 200 + i * 304, 700 if i % 2 == 0 else 330, '#ffd166' if i == 5 else '#fff', t, d)
              for i, (icn, t, d) in enumerate(STORY))
    + slot('[фото: работа]', 240, 150, 'position:absolute;left:80px;top:420px') + slot('[фото / скрин: первый бот]', 240, 150, 'position:absolute;left:688px;top:420px')
    + slot('[скрин: первый заказ]', 240, 150, 'position:absolute;left:1296px;top:420px')
    + '<div style="position:absolute;right:96px;top:62px;font-size:17px;font-weight:700;color:var(--gold);opacity:.85">' + todo('версию истории подтвердить (В19–В21)') + '</div>',
    head='Давай <span class="grad">познакомимся</span>'))
add('v1_two', 1, ('p2-3', 0), 'Техспец → техспец нового времени', P_(1,
    '<div class="body" style="top:300px;display:grid;grid-template-columns:1fr 120px 1fr;align-items:stretch">'
    '<div class="g dim" style="display:flex;flex-direction:column;padding:44px">'
    '<div style="display:flex;gap:22px;align-items:center">%s<div><span class="tag">протоптанная дорога</span><h3 style="margin-top:12px;font-size:36px">Техспец</h3></div></div>'
    '<p style="font-size:29px;margin-top:34px;line-height:1.85;color:#dfe4ff">Конструктор: блок, стрелочка, блок<br>Боты, рассылки, сайты<br>Нет в конструкторе — «развожу руками»</p></div>'
    '%s'
    '<div class="g" style="--acc:#34d399;display:flex;flex-direction:column;padding:44px;border-color:rgba(52,211,153,.6);box-shadow:0 0 90px rgba(52,211,153,.22)">'
    '<div style="display:flex;gap:22px;align-items:center">%s<div><span class="tag acc">он же — специалист по AI-автоматизации</span><h3 style="margin-top:12px;font-size:36px">Техспец нового времени</h3></div></div>'
    '<p style="font-size:29px;margin-top:34px;line-height:1.85;color:#dfe4ff">Работает с нейронкой: объясняет задачу словами<br>Нейронка пишет код — он проверяет<br>Три инструмента:</p>'
    '<div style="display:flex;gap:12px;margin-top:auto;padding-top:18px;flex-wrap:wrap"><span class="tag acc" style="font-size:21px">боты</span><span class="tag acc" style="font-size:21px">AI-агенты</span><span class="tag acc" style="font-size:21px">мини-приложения</span></div></div></div>' % (
        ic('wrench', 'ic', '#a7b0d6'), ARR, ic('spark', 'ic', '#34d399')),
    head='Кто такой <span class="grad">технический специалист</span>', sub='Ты видишь его работу каждый день: гайд по кодовому слову, ссылка перед эфиром, запись на маникюр в 11 вечера. Этот тест-драйв тоже пришёл через бота.'))
add('v1_world', 1, ('p2-4', None), 'Мир меняется: кто-то уходит, кто-то остаётся', P_(1,
    '<div class="body" style="top:290px;bottom:300px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:26px">'
    '<div class="g">%s%s<p>Ответы клиентам, отчёты, описания товаров, разбор заявок. И сокращают штат.</p></div>'
    '<div class="g dim">%s%s<p>Тот, чью работу забрала нейронка</p></div>'
    '<div class="g hl">%s%s<p>Тот, кто нейронку настраивает, добавляет функции и проверяет, что она не выдаёт ерунду</p></div></div>'
    '<div class="strip" style="bottom:150px">%s<div>Большинство бизнесов до сих пор ничего не настроили — даже с хорошим оборотом. <span class="gold">Не потому что не хотят, а потому что некому.</span> %s</div></div>' % (
        ic('trend'), H3('Нейронки забирают рутину', 30), ic('x', 'ic', '#a7b0d6'), H3('Кто-то уходит', 30), ic('spark', 'ic goldc'), H3('Кто-то остаётся', 30),
        ic('store', 'ic sm'), todo('[пример Wildberries: из 7 человек осталось 2]')),
    head='Мир меняется <span class="grad">прямо сейчас</span>'))
SEG = [('cal', 'Мастера и салоны', 'Маникюр, брови, массаж, барбершопы: запись, напоминания, ответы'),
       ('user', 'Репетиторы, тренеры, психологи', 'Запись, оплата, выдача материалов'),
       ('store', 'Кофейни, цветочные, пекарни', 'Меню, предзаказ, бонусы'),
       ('cap', 'Эксперты и онлайн-школы', 'Уроки, рассылки, оплата, поддержка учеников'),
       ('chart', 'Селлеры и компании побольше', 'Отчёты, карточки, отзывы, аналитика — тут нужны агенты')]
add('v1_clients', 1, ('p2-5', 0), 'Кто платит: пять сегментов', P_(1,
    '<div class="body c" style="top:270px;bottom:250px">%s</div>'
    '<div class="strip" style="bottom:138px">%s<div>У половины из них <span class="gold">ты и есть клиент</span> — как устроен салон, ты знаешь изнутри.</div></div>' % (
        cards(SEG, cols=5, gap=20), ic('heart', 'ic sm')),
    head='Кто за это <span class="grad">платит</span>', sub='Любой, у кого своё дело и кто устал делать одно и то же руками.'))
add('v1_pay', 1, ('p2-5', 0), 'Почему платят + вилка цен', P_(1,
    '<div class="body" style="top:290px;bottom:330px">%s</div>'
    '<div style="position:absolute;left:96px;right:96px;bottom:150px;display:grid;grid-template-columns:repeat(3,1fr);gap:24px">%s</div>' % (
        cards([('shield', 'Страшно, что сломается', 'Как с проводкой: инструкции есть, но лезть страшно'),
               ('clock', 'Некогда разбираться', 'Весь день с клиентами'),
               ('help', 'Непонятно, с какой стороны', 'Бизнес платит не за код, а за то, чтобы проблема исчезла', 'hl')]),
        ''.join('<div class="g" style="padding:22px 28px;display:flex;align-items:center;gap:20px">%s<div><div style="font-size:20px;font-weight:700;color:var(--muted)">%s</div>'
                '<div style="font-family:Unbounded;font-weight:800;font-size:38px" class="grad">%s <span style="font-size:22px;color:var(--ink);-webkit-text-fill-color:var(--ink)">%s</span></div></div></div>'
                % (ic(i, 'ic sm'), t, p, u) for i, t, p, u in PRICES)),
    head='Почему платят, если «всё можно <span class="grad">нейронкой</span>»?'))
add('v1_fears', 1, ('p2-6', None), 'Два страха', P_(1,
    '<div class="body" style="top:270px;display:grid;grid-template-columns:1fr 1fr;gap:34px">'
    '<div class="g" style="display:flex;flex-direction:column;padding:42px">%s<div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#ff8080;margin-top:22px">Страх 1</div>'
    '<h3 style="margin-top:10px;font-size:40px">«Это нестабильно»</h3><p style="font-size:26px">В найме один источник денег: сократили — ноль. Здесь несколько клиентов, а поддержка — ровные деньги каждый месяц.</p>'
    '<p style="font-size:23px;margin-top:auto;padding-top:16px;color:var(--gold)">Честно: первые месяцы денег немного. Работу не бросаем.</p></div>'
    '<div class="g" style="display:flex;flex-direction:column;padding:42px">%s<div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#ff8080;margin-top:22px">Страх 2</div>'
    '<h3 style="margin-top:10px;font-size:40px">«Мне уже не 20»</h3><p style="font-size:26px">Заказчикам 35, 45, 50 — и договориться с ними часто проще тебе: вы говорите на одном языке.</p>'
    '<p style="font-size:23px;margin-top:auto;padding-top:16px;color:var(--gold)">Умеешь договариваться и держать слово — большая часть уже есть. Остальному научим.</p></div></div>' % (
        ic('shield', 'ic', '#ff8080'), ic('user', 'ic', '#ff8080')),
    head='Два страха — <span class="grad">разберём сразу</span>'))
add('v1_sum', 1, ('p2-7', None), 'Итог урока 1 и закрывашка', closer(1, [
    'Техспец нового времени делает ботов, агентов и мини-приложения с помощью нейронки',
    'Профессия появилась: бизнес ставит нейронки на рутину, а настраивать некому',
    'Платят мастера, салоны, эксперты, школы, магазины',
    'Вход лёгкий: по вечерам, не бросая работу'], 'Ты соберёшь своего бота', 'По нашему шаблону, за несколько минут. И разберём, кто за такого бота платит.'))

# ================= УРОК 2 =================
add('v2_cover', 2, ('p3-0', None), 'Обложка урока 2', B.cover(2, 'Чат-боты и твой первый бот',
    'Что боты делают, кто за них платит, почему это проще, чем кажется. И практика: бот по шаблону.',
    ['<span class="tag acc">≈ 20–25 минут</span>', '<span class="tag prac">практика</span>', '<span class="tag code">буква №2</span>']).replace('</style>', XCSS + '</style>', 1))
add('v2_tasks', 2, ('p3-1', 0), 'Что умеет бот: пять задач', P_(2,
    '<div class="body" style="top:330px;right:640px;display:grid;gap:16px;align-content:start">%s</div>'
    '<div style="position:absolute;right:190px;top:250px">%s</div>'
    '<div style="position:absolute;right:96px;top:958px;width:660px;text-align:center"><span class="tag prac" style="font-size:17px">наш бот · Профессор Квасич · %s</span></div>' % (
        ''.join('<div class="g" style="padding:18px 26px;display:flex;gap:22px;align-items:center">%s<div><h3 style="font-size:26px">%s</h3><p style="margin-top:4px;font-size:20px">%s</p></div></div>'
                % (ic(i, 'ic sm'), t, p) for i, t, p in (
                    ('cal', 'Записывает', 'Свободные окошки, запись, напоминание за день'),
                    ('chat', 'Отвечает на одни и те же вопросы', 'Цены, адрес, как добраться'),
                    ('coin', 'Принимает заказы и оплату', ''),
                    ('gift', 'Выдаёт материалы', 'Гайды, уроки, подарки за подписку'),
                    ('mega', 'Делает рассылки', '«У нас акция», «эфир через пять минут»'))),
        phone('kvasich.png', 330, 690, '50% 0%', 'rgba(62,199,255,.7)'), todo('[какие боты на каждую задачу]')),
    head='Бот — сотрудник, который <span class="grad">не устаёт</span>', sub='Круглосуточно, без выходных и не обижается на «а сколько стоит» в сотый раз.'))
add('v2_manicure', 2, ('p3-1', 0), 'Мастер маникюра: 2 часа секретарём', P_(2,
    '<div style="position:absolute;left:96px;right:96px;top:360px">'
    '<div style="display:flex;height:120px;border-radius:24px;overflow:hidden;border:1px solid rgba(255,255,255,.18)">'
    '<div style="flex:8;display:flex;align-items:center;justify-content:center;background:linear-gradient(90deg,rgba(62,199,255,.35),rgba(139,92,246,.35));font-size:30px;font-weight:800">8 часов — работа руками</div>'
    '<div style="flex:2.4;display:flex;align-items:center;justify-content:center;background:linear-gradient(90deg,#ff4f8b,#ff8a3d);font-size:26px;font-weight:800;color:#0b1020">+2 ч переписки</div></div>'
    '<div style="display:flex;gap:16px;margin-top:30px;flex-wrap:wrap">%s</div>'
    '<div class="g hl" style="margin-top:44px;display:flex;gap:26px;align-items:center">%s<div><h3 style="font-size:36px">Бот забирает эти два часа</h3><p style="font-size:26px">Вот за это и платят.</p></div></div></div>' % (
        ''.join('<span class="tag" style="font-size:22px;padding:12px 20px">%s</span>' % q for q in ('«А есть окошко в четверг?»', '«А можно перенести?»', '«Сколько стоит снятие?»')),
        ic('bot', 'ic goldc')),
    head='Мастер маникюра: <span class="grad">секретарь у самой себя</span>'))
add('v2_simple', 2, ('p3-2', None), 'Три этапа: программист → конструктор → нейронка', P_(2,
    '<div class="body c" style="top:270px;bottom:250px">%s</div>'
    '<div class="strip" style="bottom:138px">%s<div>Что нужно, чтобы начать: <span class="gold">телефон или компьютер, Телеграм и полчаса</span>. Английский, математика и мощный компьютер — не нужны.</div></div>' % (
        flow([('laptop', 'Раньше', 'Ботов неделями писали программисты'),
              ('wrench', 'Потом', 'Конструкторы: блок, стрелочка, блок. Проще, но чужой интерфейс'),
              ('spark', 'Сейчас', '«Сделай бота, который записывает на маникюр и напоминает за день» — код пишет нейронка', 'hl')]), ic('phone', 'ic sm')),
    head='Это не <span class="grad">программирование?</span>'))
add('v2_chain', 2, ('p3-2', None), 'Как бот устроен внутри', P_(2,
    '<div class="body" style="top:300px;display:grid;grid-template-columns:1fr 480px;gap:60px;align-items:center">'
    '<div style="display:grid;gap:22px">%s</div><div>%s</div></div>' % (
        ''.join('<div style="display:flex;align-items:center;gap:0"><div class="g" style="width:330px;padding:24px 28px;text-align:center"><h3 style="font-size:28px">%s</h3><p style="margin-top:4px;font-size:18px">нажали</p></div>%s'
                '<div class="g" style="flex:1;padding:24px 28px"><h3 style="font-size:28px">%s</h3><p style="margin-top:4px;font-size:18px">бот отвечает</p></div></div>' % (a, ARR, b)
                for a, b in (('«Прайс»', 'Список цен'), ('«Записаться»', 'Свободные окошки'), ('«Как добраться»', 'Адрес и карта'))),
        tgphone('Запись к Марине', [('bot', 'Здравствуйте! Это запись к мастеру Марине 💅'), ('kb', ['Записаться', 'Прайс', 'Как добраться']),
                                    ('me', 'Прайс'), ('bot', 'Маникюр — … ₽<br>Покрытие — … ₽<br>Снятие — … ₽')], 400, 640)),
    head='«Нажали это — <span class="grad">ответь тем»</span>', sub='Никакой магии: цепочка простых шагов.'))
add('v2_money', 2, ('p3-3', 0), 'Арифметика без красивых нулей', P_(2,
    '<div class="body" style="top:300px;bottom:300px;display:grid;grid-template-columns:1fr 1fr;gap:34px">%s</div>'
    '<div class="strip" style="bottom:150px">%s<div>Заказчику неважно, сколько ты собирал — пять минут или пять вечеров. <span class="gold">Ему важно, что проблема ушла.</span></div></div>' % (
        ''.join('<div class="g" style="display:flex;flex-direction:column;justify-content:center;padding:44px"><div style="font-size:28px;font-weight:700;color:var(--muted)">%s</div>'
                '<div style="font-family:Unbounded;font-weight:800;font-size:76px;margin-top:14px" class="grad">%s</div></div>' % (a, b)
                for a, b in (('3 простых бота в месяц', '15–45 тыс.'), ('2 клиента на поддержке + 1 заказ', '15–45 тыс.'))),
        ic('coin', 'ic sm')),
    head='Сколько это <span class="grad">в месяц</span>', sub='Простой бот — 5–15 тыс. ₽, поддержка — 5–15 тыс. ₽ в месяц.'))
add('v2_steps', 2, ('p3-4', 0), 'Практика: четыре шага', P_(2,
    '<div class="body" style="top:300px;right:620px;display:grid;gap:18px;align-content:start">%s</div>'
    '<div style="position:absolute;right:200px;top:250px">%s</div>' % (
        ''.join('<div class="g" style="padding:22px 28px;display:flex;gap:22px;align-items:center"><span class="n">%d</span><div><h3 style="font-size:27px">%s</h3>'
                '<p style="margin-top:4px;font-size:20px">%s</p></div></div>' % (i + 1, t, p) for i, (t, p) in enumerate((
                    ('Наш бот → «Сделать бота»', 'Шаблоны: ' + todo('[названия шаблонов]') + '. Берём «Запись к мастеру»'),
                    ('BotFather → /newbot', 'Имя, ник с «bot» на конце → токен'),
                    ('Отвечаешь на вопросы шаблона', 'Как зовут мастера, где, услуги и цены, дни работы'),
                    ('Ссылка на твоего бота → /start', 'Он живой. И он твой')))),
        tgphone('Наш бот', [('bot', 'Привет! Соберём твоего бота за пару минут.'), ('kb', ['Сделать бота']), ('me', 'Сделать бота'),
                             ('bot', 'Выбери шаблон:'), ('kb', ['Запись к мастеру', '[шаблон 2]', '[шаблон 3]'])], 380, 700, av='Н')),
    head='Делаем бота: <span class="grad">четыре шага</span>', sub='Повторять прямо сейчас не обязательно. Но лучше повтори — это пять минут.'))
add('v2_botfather', 2, ('p3-4', 1), 'Экран BotFather по шагам', P_(2,
    '<div class="body" style="top:300px;right:640px;display:grid;gap:18px;align-content:start">%s</div>'
    '<div style="position:absolute;right:200px;top:250px">%s</div>' % (
        ''.join('<div class="g" style="padding:22px 28px;display:flex;gap:22px;align-items:center"><span class="n">%s</span><div><h3 style="font-size:27px">%s</h3>'
                '<p style="margin-top:4px;font-size:20px">%s</p></div></div>' % (n, t, p) for n, t, p in (
                    ('1', 'Открой BotFather → «Старт»', 'Официальный бот Телеграма, «отец ботов»'),
                    ('2', 'Напиши /newbot', ''),
                    ('3', 'Имя — его видят люди', 'Например, «Запись к Марине»'),
                    ('4', 'Ник — латиницей, на конце «bot»', 'marina_zapis_bot. Занят — добавь цифру'),
                    ('5', 'Токен — ключ от бота', 'Копируем и отправляем нашему боту'))),
        tgphone('BotFather', [('me', '/newbot'), ('bot', 'Alright, a new bot. How are we going to call it?'), ('me', 'Запись к Марине'),
                              ('bot', 'Good. Now let\'s choose a username for your bot. It must end in `bot`.'), ('me', 'marina_zapis_bot'),
                              ('bot', 'Done! Congratulations on your new bot.<br>Use this token to access the HTTP API:<br><code>7xxxxxxx:AAH…</code>')], 380, 700, 'rgba(62,199,255,.6)', 'BF')),
    head='BotFather — <span class="grad">«отец ботов»</span>', sub=todo('[блок про безопасность токена — В38]')))
add('v2_template', 2, ('p3-4', 2), 'Вопросы шаблона и ответы', P_(2,
    '<div class="body" style="top:300px;right:640px;display:flex;flex-direction:column;justify-content:center;gap:24px">'
    '<div class="g"><h3 style="font-size:32px">Наш бот спрашивает — ты отвечаешь</h3><p style="font-size:24px">Как зовут мастера, где находишься, какие услуги и цены, в какие дни работаешь.</p></div>'
    '<div class="g hl"><h3 style="font-size:32px">Немного ждём — приходит ссылка</h3><p style="font-size:24px">Открываем, жмём /start. Пауза: это момент, ради которого урок.</p></div></div>'
    '<div style="position:absolute;right:200px;top:250px">%s</div>' % tgphone('Наш бот', [
        ('bot', 'Как зовут мастера?'), ('me', 'Марина'), ('bot', 'Где вы находитесь?'), ('me', todo('[адрес]')),
        ('bot', 'Какие услуги и цены?'), ('me', 'Маникюр — …, покрытие — …'), ('bot', 'В какие дни работаете?'), ('me', 'Пн–Пт, 10–20'),
        ('bot', 'Готово! Твой бот: @marina_zapis_bot ✨')], 380, 700, av='Н'),
    head='Шаблон спрашивает — <span class="grad">бот собирается</span>'))
add('v2_live', 2, ('p3-4', 2), 'Твой бот живой', P_(2,
    '<div class="body" style="top:300px;right:640px;display:flex;flex-direction:column;justify-content:center;gap:24px">'
    '<div class="g hl"><h3 style="font-size:40px">Он ответил. Это твой бот</h3><p style="font-size:26px">«Записаться на приём» → окошки, услуги → бот подтверждает.</p></div>'
    '<div class="g"><h3 style="font-size:30px">А теперь ломаем нарочно</h3><p style="font-size:24px">Клиенты не всегда жмут кнопки — пишем текстом «а завтра можно?» и смотрим, что ответит. %s</p></div></div>'
    '<div style="position:absolute;right:200px;top:250px">%s</div>' % (todo('[проверить шаблон — В40]'), tgphone('Запись к Марине', [
        ('me', '/start'), ('bot', 'Здравствуйте! Это запись к мастеру Марине 💅'), ('kb', ['Записаться на приём', 'Прайс']),
        ('me', 'Записаться на приём'), ('bot', 'Выберите время:'), ('kb', ['Чт 15:00', 'Пт 11:00']), ('me', 'Чт 15:00'), ('bot', 'Готово! Ждём вас в четверг в 15:00 ✅')], 380, 700, av='М')),
    head='Это момент, <span class="grad">ради которого урок</span>'))
add('v2_base', 2, ('p3-5', None), 'Почему так быстро: наша наработка', P_(2,
    '<div class="body c" style="top:270px;bottom:260px">%s</div>'
    '<div class="strip" style="bottom:140px">%s<div><span class="gold">Шаблон — это демо.</span> Профессия — когда ты можешь сделать бота, которого ещё нет в шаблонах. Этому учим на обучении.</div></div>' % (
        flow([('list', 'Шаблон', 'Уже продуман'), ('laptop', 'Сервер', 'Бот живёт у нас'), ('done', 'Проверенный код', 'Написан и протестирован'),
              ('rocket', 'Бот за минуту', 'Без базы — вечер, а то и неделя', 'hl')]), ic('cap', 'ic sm')),
    head='Почему так <span class="grad">быстро?</span>', sub='Не потому, что бот — ерунда. Под капотом наша наработка.'))
add('v2_task', 2, ('p3-6', None), 'Задание: бот + комментарий', P_(2,
    '<div class="body c" style="top:270px">%s</div>' % cards([
        ('bot', 'Сделай своего бота', 'По шаблону — кнопка под уроком'),
        ('chat', 'Напиши комментарий', todo('[что именно и куда — В42]')),
        ('gift', 'Бонус за задание', todo('[какой — В43]'), 'hl')]),
    head='Задание <span class="grad">на сегодня</span>'))
add('v2_sum', 2, ('p3-7', None), 'Закрывашка на урок 3', closer(2, [
    'Бот — сотрудник, который работает круглосуточно', 'Код пишет нейронка, ты объясняешь словами', 'Платят 5–15 тыс. за бота и каждый месяц за поддержку',
    'У тебя уже есть свой бот'], 'AI-агенты', 'Не «нажал кнопку — получил ответ», а помощник, который работает с твоими данными. Попробуешь руками.'))

# ================= УРОК 3 =================
add('v3_cover', 3, ('p4-0', None), 'Обложка урока 3', B.cover(3, 'AI-агенты простыми словами',
    'Чем агент отличается от нейронки, шесть живых агентов, команда агентов и как это продать.',
    ['<span class="tag acc">≈ 25–30 минут</span>', '<span class="tag prac">практика</span>', '<span class="tag code">буква №3</span>']).replace('</style>', XCSS + '</style>', 1))
add('v3_scheme', 3, ('p4-1', 0), 'Схема агента: данные + роль + задача', P_(3,
    '<div class="body" style="top:290px;bottom:300px;display:flex;align-items:stretch">%s%s%s%s'
    '<div class="g" style="flex:1.1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;border-color:rgba(139,92,246,.7);box-shadow:0 0 90px rgba(139,92,246,.35)">%s<h3 style="margin-top:18px;font-size:34px">Агент</h3></div>%s'
    '<div class="g hl" style="flex:1.2">%s<h3 style="margin-top:18px">Результат</h3><p>«Двенадцать. Вот список — и кто ходил каждый месяц, а теперь пропал»</p></div></div>'
    '<div class="strip" style="bottom:150px">%s<div>Салон: «Сколько клиентов не пришло в этом месяце?» Раньше — администратор и вечер с таблицей. <span class="gold">Ничего сверхъестественного.</span></div></div>' % (
        '<div style="flex:1.5;display:grid;gap:14px">' + ''.join('<div class="g" style="padding:16px 24px;display:flex;gap:18px;align-items:center">%s<div><h3 style="font-size:24px">%s</h3><p style="margin-top:2px;font-size:18px">%s</p></div></div>'
                                                                 % (ic(i, 'ic sm'), t, d) for i, t, d in (('table', 'Твои данные', 'база клиентов, файлы, отчёты'),
                                                                                                         ('user', 'Роль', '«ты аналитик рекламы»'),
                                                                                                         ('target', 'Задача', '«скажи, где мы теряем деньги»'))) + '</div>',
        '', '', ARR, ic('spark', 'ic big', '#8b5cf6'), ARR, ic('done', 'ic goldc'), ic('cal', 'ic sm')),
    head='Агент = нейронка + <span class="grad">твои данные и задача</span>'))
add('v3_vs', 3, ('p4-2', 0), 'Обычная нейронка vs агент', P_(3,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:center">%s%s</div>' % (
        B.vs_col('#a7b0d6', 'chat', 'обычная нейронка', 'Ничего про тебя не знает', 'Почему я поправляюсь?',
                 'Причины могут быть разные: калорийность рациона, недосып, стресс, малоподвижный образ жизни…', '<span class="tag">всё правильно — и всё мимо</span>', 'dim'),
        B.vs_col('#8b5cf6', 'spark', 'агент', 'Отвечает по твоим данным', 'Почему я поправляюсь?',
                 'Посмотрел твой дневник питания за месяц: пельмени с майонезом шесть раз в неделю. Начни с этого.', '<span class="tag acc">✓ знает твой дневник</span><span class="tag acc">✓ может сам заполнить таблицу</span>', '')),
    head='Чем агент лучше <span class="grad">обычной нейронки</span>'))
SIX = [('Для бизнеса', [('chart', 'Отчёты на Wildberries', '5 выгрузок, свести, проверить → одна фраза. 50 действий → 3 клика'),
                        ('list', 'Карточки товаров', '50 карточек руками — день работы. С агентом — одна кнопка')]),
       ('Для себя', [('heart', 'Питание', '«Почему я поправляюсь?» — дневник, подсчёт, подсказки'),
                     ('home', 'Бюджет или холодильник', '«Кабачок, морковь, лук, перец, картошка — что на ужин?»')]),
       ('Для работы', [('table', 'Помощник бухгалтера', B.todo('[что делает]')),
                       ('case', B.todo('[менеджер WB / финграмотность]'), B.todo('[решить — В44]'))])]
add('v3_six', 3, ('p4-3', 0), 'Шесть агентов: бизнес, быт, работа', P_(3,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:repeat(3,1fr);gap:24px">%s</div>' % ''.join(
        '<div style="display:grid;gap:18px;align-content:start"><div style="font-size:20px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#c4b5fd">%s</div>%s</div>' % (
            g, ''.join('<div class="g" style="padding:24px 28px">%s<h3 style="margin-top:16px;font-size:27px">%s</h3><p style="font-size:20px">%s</p></div>' % (ic(i, 'ic sm'), t, d) for i, t, d in items))
        for g, items in SIX),
    head='Шесть агентов <span class="grad">вживую</span>', sub='На каждого — живой экран 20–40 секунд: задача → что сделал агент. И это только верхушка.'))
ROLES = [('chart', 'Аналитик', 'считает цифры', 0), ('mega', 'Маркетолог', 'тексты и привлечение', 90), ('shield', 'Контролёр', 'проверяет за остальными', 180),
         ('spark', B.todo('[ещё роль]'), '', 270)]
import math
add('v3_team', 3, ('p4-4', 0), 'Команда агентов: ты в центре', P_(3,
    '<svg width="1920" height="1080" style="position:absolute;left:0;top:0">%s</svg>'
    '<div style="position:absolute;left:960px;top:610px;transform:translate(-50%%,-50%%);text-align:center">%s<div style="font-family:Unbounded;font-weight:800;font-size:34px;margin-top:14px">Ты</div>'
    '<div style="color:var(--muted);font-weight:700;font-size:20px">ставишь задачи и решаешь</div></div>%s' % (
        ''.join('<line x1="960" y1="610" x2="%d" y2="%d" stroke="rgba(139,92,246,.6)" stroke-width="3" stroke-dasharray="6 10"/>' % (
            960 + 470 * math.cos(math.radians(a - 90)), 610 + 260 * math.sin(math.radians(a - 90))) for _i, _t, _d, a in ROLES),
        ic('user', 'ic big goldc'),
        ''.join('<div class="g" style="position:absolute;left:%dpx;top:%dpx;transform:translate(-50%%,-50%%);width:340px;padding:20px 26px;display:flex;gap:18px;align-items:center">%s<div><h3 style="font-size:27px">%s</h3><p style="margin-top:2px;font-size:19px">%s</p></div></div>' % (
            960 + 470 * math.cos(math.radians(a - 90)), 610 + 260 * math.sin(math.radians(a - 90)), ic(i, 'ic sm', '#8b5cf6'), t, d) for i, t, d, a in ROLES)),
    head='Свой проект — <span class="grad">команда агентов</span>'))
add('v3_sell', 3, ('p4-5', None), 'Как продать агента', P_(3,
    '<div class="body" style="top:290px;bottom:300px;display:grid;grid-template-columns:1.3fr 1fr;gap:34px">'
    '<div class="g" style="display:flex;flex-direction:column;justify-content:center"><div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#c4b5fd">Не про «нейронки и агентов», а про время и деньги</div>'
    '<h3 style="margin-top:18px;font-size:40px;line-height:1.3">«У вас уходит <span class="grad">10 часов в неделю</span> на отчёты — агент заберёт <span class="grad">8</span>»</h3>'
    '<p style="font-size:24px;margin-top:18px">Это не уговоры, это арифметика, которую владелец понимает лучше нас.</p></div>'
    '<div class="g hl" style="display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center">%s<div style="font-size:24px;font-weight:700;color:var(--muted);margin-top:22px">Агент на рынке</div>'
    '<div style="font-family:Unbounded;font-weight:800;font-size:84px" class="grad">40–60</div><div style="font-size:28px;font-weight:800">тыс. ₽ + поддержка</div></div></div>'
    '<div class="strip" style="bottom:150px">%s<div>Кому: %s. <span class="gold">Ты приходишь не с «дайте работу», а с решением того, что болит.</span></div></div>' % (
        ic('spark', 'ic big goldc'), ic('users', 'ic sm'), todo('[селлеры, бухгалтеры, юристы, школы, салоны — В49]')),
    head='Почему это круто для <span class="grad">предпринимателя</span>'))
add('v3_practice', 3, ('p4-6', None), 'Практика по агенту (решается)', P_(3,
    '<div class="body c" style="top:270px">%s</div>' % cards([
        ('spark', 'Вариант А', 'Готовый агент в нашем боте: загружаешь своё (меню, прайс, дневник) и задаёшь вопросы'),
        ('bot', 'Вариант Б', 'Подключаешь агента к своему боту из урока 2: «отвечает по твоему прайсу»'),
        ('eye', 'Вариант В', 'Смотришь, как агент делает задачу, и пишешь, какого агента хотел бы себе')]),
    head='Практика: <span class="grad">твой агент</span>', sub=todo('[какой вариант — решить, В51]')))
add('v3_sum', 3, ('p4-7', None), 'Закрывашка на урок 4', closer(3, [
    'Агент работает на твоей информации — отвечает точно, а не вообще', 'Агент не только отвечает, но и делает', 'Агент — от 40 до 60 тыс. ₽ + поддержка',
    'Продаём время и деньги, а не «нейронки»'], 'Мини-приложения', 'Маленькие приложения прямо внутри Телеграма — с каталогом, записью и оплатой.'))

# ================= УРОК 4 =================
add('v4_cover', 4, ('p5-0', None), 'Обложка урока 4', B.cover(4, 'Мини-приложения в Телеграме',
    'Третий инструмент: результат сразу видно глазами. Что это, кому продать и как делается.',
    ['<span class="tag acc">≈ 20 минут</span>', '<span class="tag code">буква №4</span>']).replace('</style>', XCSS + '</style>', 1))
app = ('<div class="ph" style="width:380px;height:760px;--glow:rgba(236,72,153,.6)"><div class="app"><div class="bar">💅 Запись к Марине</div>'
       '<div class="sub2">Услуга</div><div class="svc on"><span>Маникюр + покрытие</span><span>… ₽</span></div><div class="svc"><span>Снятие</span><span>… ₽</span></div>'
       '<div class="sub2">Октябрь</div><div class="days">%s</div><div class="sub2">Время</div><div class="slots">%s</div><div class="btn">Записаться</div></div></div>') % (
    ''.join('<div class="d %s">%d</div>' % ('on' if d == 30 else ('off' if d in (26, 27, 28) else ''), d) for d in range(26, 33 - 0) if d <= 32 and d - 25 <= 7),
    ''.join('<div class="s %s">%s</div>' % ('on' if t == '15:00' else '', t) for t in ('10:00', '12:00', '15:00', '16:30', '18:00', '19:30')))
add('v4_bot_vs_app', 4, ('p5-1', 0), 'Бот (переписка) vs мини-приложение (экран)', P_(4,
    '<div style="position:absolute;left:330px;top:300px;text-align:center"><div style="font-size:20px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:16px">Бот — переписка</div>%s</div>'
    '<div style="position:absolute;left:928px;top:600px">%s</div>'
    '<div style="position:absolute;right:330px;top:300px;text-align:center"><div style="font-size:20px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#f9a8d4;margin-bottom:16px">Мини-приложение — экран</div>%s</div>' % (
        tgphone('Запись к Марине', [('bot', 'Выберите услугу:'), ('kb', ['Маникюр + покрытие', 'Снятие']), ('me', 'Маникюр + покрытие'), ('bot', 'Выберите день:'),
                                    ('kb', ['Чт 30.10', 'Пт 31.10']), ('me', 'Чт 30.10'), ('bot', 'Выберите время:'), ('kb', ['12:00', '15:00'])], 330, 640, 'rgba(167,176,214,.4)', 'М'),
        ARR, '<div style="zoom:.84">' + app + '</div>'),
    head='Один сценарий — <span class="grad">два способа</span>', sub='«Записаться на маникюр»: кнопка-ответ-кнопка или экран с календарём. Ничего скачивать не надо.'))
add('v4_examples', 4, ('p5-2', None), 'Примеры мини-приложений', P_(4,
    '<div style="position:absolute;left:96px;right:96px;top:290px;display:flex;gap:40px;justify-content:center;align-items:flex-start">'
    '<div style="text-align:center">%s<div style="margin-top:20px;font-family:Unbounded;font-weight:600;font-size:23px">Школа гимнастики</div><div style="color:var(--muted);font-weight:600;font-size:18px">тренер, план, прогресс</div></div>'
    '<div style="text-align:center">%s<div style="margin-top:20px;font-family:Unbounded;font-weight:600;font-size:23px">Манекен</div><div style="color:var(--muted);font-weight:600;font-size:18px">AI собирает образы → WB</div></div>'
    '<div style="text-align:center">%s<div style="margin-top:20px;font-family:Unbounded;font-weight:600;font-size:23px">Запись</div><div style="color:var(--muted);font-weight:600;font-size:18px">календарь с окошками</div></div>'
    '<div style="text-align:center">%s<div style="margin-top:20px;font-family:Unbounded;font-weight:600;font-size:23px;color:var(--gold)">[ещё пример]</div></div></div>' % (
        phone('gym.png', 270, 560, '50% 0%', 'rgba(255,79,139,.6)'), phone('manekken.png', 270, 560, '50% 0%', 'rgba(192,38,211,.6)'),
        app.replace('width:380px;height:760px', 'width:270px;height:560px;zoom:.71;width:380px;height:788px'),
        slot('[каталог / калькулятор / калории — В55]', 270, 560, 'border-radius:46px')),
    head='Что можно <span class="grad">сделать</span>', sub='И это опять только верхушка.'))
add('v4_sell', 4, ('p5-3', None), 'Кому продать и сколько стоит (решается)', P_(4,
    '<div class="body" style="top:300px;display:grid;grid-template-columns:1.4fr 1fr;gap:34px">'
    '<div class="g"><div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#f9a8d4">Кому</div>'
    '<div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:22px">%s</div><p style="margin-top:22px">%s</p></div>'
    '<div class="g hl" style="display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center">%s<div style="font-size:24px;font-weight:700;color:var(--muted);margin-top:22px">Мини-приложение на рынке</div>'
    '<div style="font-family:Unbounded;font-weight:800;font-size:64px;margin-top:8px">%s</div></div></div>' % (
        ''.join('<span class="tag" style="font-size:24px;padding:12px 22px">%s</span>' % x for x in ('Магазины', 'Салоны', 'Школы', 'Кафе')), todo('[кому в первую очередь — В57]'),
        ic('coin', 'ic big goldc'), todo('[вилка — В56]')),
    head='Кому продать и <span class="grad">сколько стоит</span>'))
add('v4_how', 4, ('p5-4', None), 'Как это делается', P_(4,
    '<div class="body c" style="top:280px">%s</div>' % flow([
        ('chat', 'Описание словами', '«Сделай запись с календарём и прайсом»'),
        ('spark', 'Нейронка пишет код', 'По твоему описанию'),
        ('eye', 'Ты проверяешь', 'И правишь тоже словами'),
        ('phone', 'Приложение в Телеграме', 'Открывается из твоего бота', 'hl')]),
    head='Как это <span class="grad">делается</span>', sub='Технику не грузим — показываем суть. ' + todo('[скринкаст сборки или только готовые — В58]')))
add('v4_sum', 4, ('p5-5', None), 'Закрывашка на урок 5', closer(4, [
    'Мини-приложение — экран внутри Телеграма: каталог, календарь, оплата', 'Ничего не скачивать — открывается из бота', 'Код пишет нейронка, ты описываешь и проверяешь',
    'Три инструмента у тебя в руках: боты, агенты, мини-приложения'], 'Кому всё это продать', 'Где брать первых клиентов и что им написать.'))

# ================= УРОК 5 =================
add('v5_cover', 5, ('p6-0', None), 'Обложка урока 5', B.cover(5, 'Где брать первых клиентов',
    'Зачем рынку новичок, кто твои первые клиенты, семь способов и как продать без кейсов.',
    ['<span class="tag acc">≈ 20–25 минут</span>', '<span class="tag code">буква №5</span>']).replace('</style>', XCSS + '</style>', 1))
add('v5_skill', 5, ('p6-1', None), '«Я не технарь» и «продавать — не моё»', P_(5,
    '<div class="body c" style="top:280px">%s</div>' % flow([
        ('help', '«Я не технарь»', 'А токен пару дней назад тоже ничего не говорил — бот у тебя уже есть'),
        ('rocket', 'Водить тоже не умел', 'Пока не сел за руль'),
        ('list', 'Продажи — навык', 'Шаги, инструкция, первая неловкая попытка и вторая — уже нормальная', 'hl')]),
    head='Навык без клиента — <span class="grad">это хобби</span>', sub='Никто не рождается с этим.'))
add('v5_newbie', 5, ('p6-2', None), 'Зачем рынку новичок', P_(5,
    '<div class="body c" style="top:280px">%s</div>' % cards([
        ('store', 'У салона нет денег на агентство', 'А бот ему нужен'),
        ('heart', 'Ты рядом и по-человечески', 'Отвечаешь быстро, объясняешь понятно — это ценнее портфолио на сто проектов'),
        ('coin', 'Первые 2–3 заказа — дешевле рынка', 'Ради отзыва. Но не бесплатно: бесплатное не ценят и не внедряют', 'hl')]),
    head='Зачем бизнесу <span class="grad">новичок?</span>'))
add('v5_clients', 5, ('p6-3', None), 'Первые клиенты: разовые → постоянные', P_(5,
    '<div class="body" style="top:290px;bottom:330px">%s</div>'
    '<div style="position:absolute;left:96px;right:96px;bottom:150px;display:flex;align-items:stretch">'
    '<div class="g" style="flex:1;display:flex;gap:22px;align-items:center">%s<div><h3>Разовые</h3><p style="margin-top:4px">Сделал бота — получил деньги</p></div></div>%s'
    '<div class="g hl" style="flex:1;display:flex;gap:22px;align-items:center">%s<div><h3>Постоянные</h3><p style="margin-top:4px">Ведёшь бота каждый месяц — это и есть стабильность</p></div></div></div>' % (
        cards([(i, t, '') for i, t, _d in SEG], cols=5, gap=16), ic('bot', 'ic sm'), ARR, ic('wrench', 'ic sm goldc')),
    head='Твой первый список — <span class="grad">у тебя в телефоне</span>', sub='Твой мастер, твой тренер, кофейня у дома, знакомая с блогом.'))
SEVEN = [('users', 'Записная книжка', '5 человек со своим делом — напиши сегодня'), ('home', 'Заведения у дома', 'Покажи бота вживую'),
         ('chat', 'Чаты с заказами', B.todo('[названия — В61]')), ('laptop', 'Биржи', 'Kwork, Авито Услуги, FL'),
         ('users', 'Смежники', 'SMM, таргетологи, дизайнеры — за процент'), ('mega', 'Свои соцсети', '«Смотрите, что получилось»'),
         ('radio', 'Сарафан', 'Отзыв + контакт знакомого после каждого заказа')]
add('v5_seven', 5, ('p6-4', None), 'Семь способов (лестница)', P_(5,
    '<div style="position:absolute;left:96px;right:96px;bottom:130px;display:flex;align-items:flex-end;gap:16px">%s</div>' % ''.join(
        '<div class="g" style="flex:1;height:%dpx;padding:22px 18px;display:flex;flex-direction:column;border-color:rgba(255,255,255,%.2f)"><span class="n">%d</span>'
        '<h3 style="font-size:23px;margin-top:14px">%s</h3><p style="font-size:17px;margin-top:6px">%s</p></div>' % (330 + i * 45, .14 + i * .04, i + 1, t, d)
        for i, (_icn, t, d) in enumerate(SEVEN)),
    head='Где искать: <span class="grad">семь способов</span>', sub='Начнём с того, который у новичков срабатывает чаще всего. Он у тебя уже в телефоне.'))
add('v5_msg', 5, ('p6-4', None), 'Текст первого сообщения', P_(5,
    '<div style="position:absolute;left:96px;top:300px;width:620px;display:grid;gap:18px">%s</div>'
    '<div style="position:absolute;left:780px;right:96px;top:310px;background:#0e1621;border-radius:30px;padding:34px;border:1px solid rgba(255,255,255,.12);box-shadow:0 40px 80px rgba(0,0,0,.5)">'
    '<div style="background:#2b5278;border-radius:22px 22px 8px 22px;padding:28px 32px;font-size:31px;line-height:1.5;font-weight:600">%s, я учусь делать ботов для записи клиентов. '
    'Хочу собрать такого для вас за %s в обмен на отзыв, займёт неделю. Показать пример?</div>'
    '<div style="text-align:right;color:#6c7883;font-size:16px;margin-top:10px">✓✓ прочитано</div></div>' % (
        ''.join('<div class="g" style="padding:20px 26px;display:flex;gap:20px;align-items:center"><span class="n">%d</span><h3 style="font-size:25px">%s</h3></div>' % (i + 1, t)
                for i, t in enumerate(('Скопируй со страницы урока', 'Подставь имя и цену', 'Пример у тебя есть — бот из урока 2', 'В отклике — конкретика про них, а не про тебя'))),
        todo('[Имя]'), todo('[цена — В60]')),
    head='Что <span class="grad">написать</span>'))
add('v5_nocase', 5, ('p6-5', None), 'Как продать без кейсов', P_(5,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:1.3fr 1fr;gap:34px;align-items:center">'
    '<div class="g hl" style="display:flex;gap:30px;align-items:center;padding:44px">%s<div><h3 style="font-size:38px">Твой бот из урока 2 — это демо</h3>'
    '<p style="font-size:26px">Пришли ссылку — пусть человек сам потыкает. Один живой бот лучше десяти красивых слов.</p></div></div>'
    '<div class="g dim" style="padding:40px">%s<h3 style="margin-top:20px;font-size:32px">Чужие работы за свои не выдаём</h3><p style="font-size:23px">На первом созвоне спросят «а как вы это делали» — и всё станет понятно.</p></div></div>' % (
        ic('bot', 'ic big goldc'), ic('x', 'ic', '#ff8080')),
    head='«А у меня нет <span class="grad">ни одного кейса</span>»'))
add('v5_money', 5, ('p6-6', None), 'Деньги и безопасность', P_(5,
    '<div class="body c" style="top:280px">%s</div>' % cards([
        ('shield', 'Как брать деньги', '<span style="display:flex;gap:8px;margin:6px 0 12px"><i style="flex:1;height:18px;border-radius:9px;background:linear-gradient(90deg,var(--a1),var(--a2))"></i>'
                                       '<i style="flex:1;height:18px;border-radius:9px;background:rgba(255,255,255,.18)"></i></span>' + todo('[50 % вперёд, 50 % после сдачи — В63]')),
        ('case', 'Не увольняйся', 'Пока несколько месяцев подряд доход не выше зарплаты — это подработка по вечерам', 'hl')], cols=2),
    head='Деньги и <span class="grad">безопасность</span>'))
add('v5_task', 5, ('p6-7', None), 'Задание и закрывашка на урок 6', P_(5,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:center">'
    '<div class="g hl" style="padding:44px">%s<h3 style="margin-top:22px;font-size:36px">Задание</h3><p style="font-size:26px">Выбери трёх человек из контактов, кому можно предложить бота, и %s. Пригодится на разборе.</p></div>'
    '<div class="g" style="--acc:#e879f9;padding:44px;border-color:rgba(232,121,249,.6);box-shadow:0 0 60px rgba(232,121,249,.22)"><div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#e879f9">Дальше · урок 6</div>'
    '<h3 style="margin-top:14px;font-size:38px">Живой разговор с ученицей</h3><p style="font-size:24px">С чего начинала, что было страшно и что получилось. Без глянца.</p></div></div>' % (
        ic('users', 'ic goldc'), todo('[куда прислать]')),
    head='Задание <span class="grad">и что дальше</span>'))

# ================= УРОК 6 =================
add('v6_cover', 6, ('p7-0', None), 'Обложка урока 6', B.cover(6, 'Созвон с ученицей',
    'Последний урок — и он не про меня. ' + '[Имя], [кто она одной фразой]' + ': как всё было у неё, без сценария и красивых цифр.',
    ['<span class="tag acc">≈ 15–25 минут</span>', '<span class="tag code">последняя буква</span>']).replace('</style>', XCSS + '</style>', 1))
CH = ['Расскажи о себе', 'Что было не так', 'Чего боялась', 'Первый бот, первая нейронка', 'Первый заказ или результат', 'Что изменилось', 'Что было тяжело', 'Что сказала бы себе в начале']
add('v6_chapters', 6, ('p7-1', 0), 'Главы созвона (оглавление)', P_(6,
    '<div class="body" style="top:290px;display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:1fr 1fr;gap:22px">%s</div>' % ''.join(
        '<div class="g" style="display:flex;flex-direction:column;justify-content:space-between;padding:30px"><div class="bnum" style="font-size:70px">%02d</div><h3 style="font-size:27px">%s</h3></div>' % (i + 1, t)
        for i, t in enumerate(CH)),
    head='Как это было <span class="grad">у живого человека</span>'))
add('v6_title', 6, ('p7-1', 0), 'Титр главы (образец для монтажа)', P_(6,
    '<div style="position:absolute;left:96px;bottom:150px;display:flex;align-items:center;gap:26px;padding:26px 40px 26px 26px;border-radius:28px;'
    'background:linear-gradient(90deg,rgba(11,16,32,.85),rgba(11,16,32,.55));border:1px solid rgba(255,255,255,.18)">'
    '<div class="bnum" style="font-size:80px">03</div><div><div style="font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#e879f9">Глава</div>'
    '<div style="font-family:Unbounded;font-weight:800;font-size:44px;margin-top:6px">Чего боялась</div></div></div>'
    '%s' % slot('[кадр созвона]', 1100, 520, 'position:absolute;left:410px;top:120px;border-radius:30px'), progress=False))
add('v6_final', 6, ('p7-2', None), 'Итог тест-драйва', P_(6,
    '<div class="body" style="top:290px;bottom:300px;display:flex;align-items:center;gap:0">%s</div>'
    '<div style="position:absolute;left:0;right:0;bottom:170px;text-align:center;font-family:Unbounded;font-weight:600;font-size:36px">Это и есть вся логика: <span class="grad">от первого бота до первого клиента</span></div>' % ''.join(
        ('' if i == 0 else ARR) + '<div class="g %s" style="flex:1;text-align:center;padding:28px 18px">%s<h3 style="margin-top:16px;font-size:25px">%s</h3></div>' % (
            'hl' if i == 5 else '', ic(icn, 'ic sm goldc' if i == 5 else 'ic sm'), t)
        for i, (icn, t) in enumerate((('case', 'Профессия'), ('bot', 'Свой бот'), ('spark', 'Агенты'), ('phone', 'Мини-приложения'), ('target', 'Клиенты'), ('map', 'Разбор')))),
    head='Ну вот <span class="grad">и всё</span>'))
add('v6_anketa', 6, ('p7-3', None), 'Анкета + слово → разбор и бонус', P_(6,
    '<div style="position:absolute;left:0;right:0;top:150px;text-align:center"><h1 style="font-size:70px">Последний шаг: <span class="grad">анкета</span></h1>'
    '<div class="sub" style="margin:18px auto 0;max-width:1300px">Кто ты, что получилось на практике и какие были эмоции. Пиши честно и подробно — так разбор будет точнее.</div></div>'
    '<div style="position:absolute;left:0;right:0;top:420px;display:flex;justify-content:center;align-items:center;gap:30px">'
    '<div class="g" style="width:340px;height:240px;display:flex;flex-direction:column;align-items:center;justify-content:center">%s<h3 style="margin-top:18px">Анкета</h3></div>%s'
    '<div class="g hl" style="width:380px;height:240px;display:flex;flex-direction:column;align-items:center;justify-content:center">%s<h3 style="margin-top:18px">Персональный разбор</h3><p style="margin-top:4px;font-size:20px">и про обучение</p></div></div>'
    '<div style="position:absolute;left:0;right:0;top:740px;display:flex;justify-content:center;align-items:center;gap:14px">%s'
    '<div style="font-size:28px;font-weight:700;margin-left:20px">собери слово → в чат → %s</div></div>' % (
        ic('list'), ARR, ic('user', 'ic goldc'),
        ''.join('<div class="slotd on" style="width:90px;height:120px;font-size:64px">?</div>' for _ in range(N_LETTERS)), todo('[БОНУС]'))))


# ================= сборка =================
def render(ids):
    os.makedirs(DECK, exist_ok=True)
    B.DECK = DECK
    B.render(ids)


def parse_doc():
    """Сценарий Егора (txt из HTML) -> блоки по частям: [(part_title, sub, [(sec_id, title, [(kind, text)])])]."""
    parts, cur_part, cur_sec = [], None, None
    for raw in open(SRC, encoding='utf-8').read().split('\n'):
        line = raw.strip()
        if line.startswith('## '):
            cur_part = [line[3:], '', []]; parts.append(cur_part); cur_sec = None; continue
        if cur_part is None:
            continue
        m = re.match(r'### \[(p\d-\d)\]', line)
        if m:
            cur_sec = [m.group(1), '', []]; cur_part[2].append(cur_sec); continue
        if line.startswith('#### ') and cur_sec is not None:
            cur_sec[1] = line[5:]; continue
        m = re.match(r'(p|div)\{([^}]*)\}\s?(.*)', line)
        if not m:
            continue
        cls, text = m.group(2), m.group(3).replace('↑ к оглавлению', '').strip()
        if cls == 'part-sub':
            cur_part[1] = text; continue
        if cur_sec is None or not text and not cls.startswith('row'):
            continue
        if cls.startswith('row'):
            cur_sec[2].append(({'row scr': 'scr', 'row dir': 'dir', 'row q': 'q'}.get(cls, 'x'), text)); continue
        if re.match(r'(Пурвиньш|Встреча 23\.10|Структура Егора|Статья 2|Наш скрипт 21\.10)', text):
            cur_sec[2].append(('base', text)); continue
        if cur_sec[2] and cur_sec[2][-1][0] in ('scr', 'dir', 'q') and cur_sec[2][-1][1] in ('🎬', '▶') or (cur_sec[2] and cur_sec[2][-1][0] == 'q' and re.fullmatch(r'В\d+', cur_sec[2][-1][1])):
            k, t = cur_sec[2][-1]
            cur_sec[2][-1] = (k, (t + ' ' + text) if k == 'q' else text); continue
        cur_sec[2].append(('say', text))
    return parts


def build_page():
    tpl = open(os.path.join(P, 'docs', 'course', 'test_drive_plan.html'), encoding='utf-8').read()
    style = re.search(r'<style>(.*?)</style>', tpl, re.S).group(1)
    script = re.search(r'<script>(.*?)</script>', tpl, re.S).group(1).replace("var PAGE = 'test_drive_plan'", "var PAGE = 'test_drive_v2'")
    by_anchor = {}
    for sid, les, anchor, cap, _h in S:
        by_anchor.setdefault(anchor, []).append((sid, cap))
    esc = lambda t: re.sub(r'\[([^\]]{2,300})\]', r'<mark>[\1]</mark>', html.escape(t))

    def imgs(lst):
        return ('<div class="gallery">%s</div>' if len(lst) > 1 else '<div class="one">%s</div>') % ''.join(
            '<a class="slide" href="slides/deck2/%s.jpg" target="_blank"><img src="slides/deck2/%s.jpg" loading="lazy" alt=""><span>%s</span></a>' % (s, s, html.escape(c)) for s, c in lst)
    cards_html, toc = [], []
    for pi, (ptitle, psub, secs) in enumerate(parse_doc()):
        if ptitle.startswith('Тест-драйв') or ptitle.startswith('Открытые'):
            continue
        bid = 'v%d' % pi
        toc.append('<a href="#%s">%s</a>' % (bid, html.escape(ptitle.split(' — ')[0])))
        body = ''
        for sec_id, stitle, rows in secs:
            body += '<h3>%s</h3>' % html.escape(stitle)
            body += imgs(by_anchor.get((sec_id, None), [])) if by_anchor.get((sec_id, None)) else ''
            base = [t for k, t in rows if k == 'base']
            if base:
                body += '<details class="base"><summary>основа: Пурвиньш / встреча / структура Егора</summary>%s</details>' % ''.join('<p>%s</p>' % esc(t) for t in base)
            scr_i = 0
            for k, t in rows:
                if k == 'say':
                    body += '<p class="say">%s</p>' % esc(t)
                elif k == 'scr':
                    body += '<p class="screen"><b>🎬 На экране:</b> %s</p>' % esc(t)
                    lst = by_anchor.get((sec_id, scr_i))
                    if lst:
                        body += imgs(lst)
                    scr_i += 1
                elif k == 'dir':
                    body += '<p class="trick">▶ %s</p>' % esc(t)
                elif k == 'q':
                    body += '<p class="q">❓ %s</p>' % esc(t)
        cards_html.append('<div class="card" id="%s" data-block="%s"><div class="num">%s</div><h2>%s</h2><p class="lead2">%s</p>%s</div>' % (
            bid, bid, html.escape(ptitle.split(' — ')[0]), html.escape(ptitle.split(' — ')[-1]), esc(psub), body))
    extra = ('.w{max-width:1000px}.card h3{font-size:17px;margin:22px 0 6px;color:#14182e}.lead2{color:#5c6478;font-size:14px}'
             'p.say{font-size:17px;line-height:1.6;background:#f3f6ff;border-left:4px solid #4263eb;border-radius:8px;padding:10px 14px}'
             'p.screen{background:#f1f3f5;border-radius:8px;padding:6px 12px;font-size:14px;color:#495057}'
             'p.trick{font-size:13.5px;color:#7a5b00;background:#fff9db;border-radius:8px;padding:6px 12px}'
             'p.q{font-size:13.5px;color:#a33a00;background:#fff4e6;border-radius:8px;padding:6px 12px}'
             'details.base{font-size:13px;color:#6b7280;margin:4px 0 8px}details.base summary{cursor:pointer}'
             'mark{background:#ffe066;border-radius:3px;padding:0 2px}'
             '.one{margin:10px 0 14px}.gallery{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:10px 0 14px}@media(max-width:700px){.gallery{grid-template-columns:1fr}}'
             'a.slide{display:block;text-decoration:none}a.slide img{display:block;width:100%;border-radius:10px;box-shadow:0 6px 18px rgba(20,24,46,.25)}'
             'a.slide span{display:block;font-size:12.5px;color:#5c6478;margin-top:5px;text-align:center}'
             '.toc{background:#fff;border-radius:12px;padding:12px 16px;margin:0 0 18px;font-size:14px}.toc a{display:inline-block;margin:3px 10px 3px 0;color:#1c5fd6;text-decoration:none}')
    out = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
           '<title>Сценарий v2 Егора: текст + слайды</title><style>%s%s</style></head><body><div class="w">'
           '<h1>Тест-драйв v2: текст для видео + слайды</h1><p class="lead">По документу «Тест-драйв: структура и текст уроков» 24.10 (вводный + 6 уроков). '
           'Синее — Егор говорит в кадре. 🎬 — что на экране, под ним слайд. ▶ — пометка для записи. ❓ — открытый вопрос (ответ ещё не дан). '
           'Серую «основу» можно развернуть. Жёлтым — что подставить. %d слайдов: <a href="/course/slides_v2.html">вся колода v2</a>.</p>'
           '<div class="who">Как вас подписать: <input id="name" placeholder="Ваше имя" maxlength="40"></div><div class="toc">%s</div>%s'
           '<div class="card general" data-block="general"><div class="num">Общее</div><h2>Комментарии ко всему</h2></div>'
           '<div class="foot"><a href="/course/test_drive_script.html">Сценарий v1</a> · <a href="/materials.html">Все материалы</a></div>'
           '</div><script>%s</script></body></html>') % (style, extra, len(S), ''.join(toc), ''.join(cards_html), script)
    open(os.path.join(P, 'docs', 'course', 'test_drive_v2_read.html'), 'w', encoding='utf-8').write(out)


TOOL_SRC = os.path.join(P, 'sources', 'course', 'тест_драйв_v2_егор_исходник.html')
TOOL_CSS = ('<style id="v2-slides">.slides{margin:6px 0 16px 34px;display:grid;grid-template-columns:1fr 1fr;gap:10px}.slides.one{grid-template-columns:1fr;max-width:760px}'
            '.slides a{display:block;text-decoration:none}.slides img{display:block;width:100%;border-radius:10px;box-shadow:0 4px 16px rgba(20,24,46,.25)}'
            '.slides span{display:block;font-size:12px;color:#6b7280;text-align:center;margin-top:4px}'
            '#teampanel{position:fixed;inset:60px 20px 20px auto;width:min(620px,92vw);background:#fff;border-radius:14px;box-shadow:0 10px 40px rgba(0,0,0,.25);'
            'z-index:1000;display:none;flex-direction:column;padding:14px}#teampanel.on{display:flex}#teampanel textarea{flex:1;width:100%;font:13px/1.45 Consolas,monospace;border:1px solid #ddd;border-radius:8px;padding:8px}'
            '#teampanel .hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-weight:700}'
            '#howto{max-width:1180px;margin:12px auto 0;padding:12px 16px;border-radius:12px;background:#fff3bf;border-left:5px solid #f08c00;font-size:15px;line-height:1.5;color:#1d2433}'
            '#howto b{color:#c2410c}'
            '.pen{color:#c2410c!important;font-weight:700;text-decoration:none!important;font-size:14px!important;border:1px solid #f3c79a!important;border-radius:999px!important;padding:3px 10px!important;background:#fff7ed!important}'
            '#tb-fab{display:none}'
            '@media (max-width:860px){html.js #tb-fab{display:block;position:fixed;left:16px;bottom:16px;z-index:6;background:#2563eb;border-color:#2563eb;color:#fff;font-weight:700;'
            'padding:10px 16px;border-radius:12px;box-shadow:0 4px 14px rgba(0,0,0,.25)}#howto{margin:10px 12px 0}}'
            '@media print{.slides{display:none}}</style>')
TOOL_HOWTO = ('<div id="howto"><b>Как писать правки.</b> Нажми на любой абзац и исправляй прямо в нём (стёр целиком — значит «убрать»). '
              'Хочешь не править, а прокомментировать — кнопка <b>«✎ комментарий»</b> под абзацем (на компьютере — поле справа). '
              'На вопросы ❓ отвечай в поле под ними. «+ добавить пункт» — новый абзац. '
              'В конце впиши имя в «Кто правит» и нажми <b>«☁ На сайт»</b> (на телефоне — синяя кнопка внизу): правки увидит вся команда в «👥 Правки команды». '
              'Можно с телефона.</div>')
TOOL_BTNS = ('<button class="btn" id="tb-send" title="Отправить мои правки и ответы на сайт — их увидит команда">☁ На сайт</button>'
             '<button class="btn" id="tb-team" title="Правки и ответы всех, кто отправил на сайт">👥 Правки команды</button>')
TOOL_JS = r'''<button class="btn" id="tb-fab">☁ Отправить правки</button>
<div id="teampanel"><div class="hd"><span id="tp-title">Правки команды</span><button class="btn" id="tp-close">✕</button></div><textarea id="tp-text" readonly></textarea></div>
<script>
(function () {
  // Синхронизация с сайтом (поверх редактора Егора): «☁ На сайт» — отправить свои правки, «👥 Правки команды» — прочитать всех.
  var PAGE = "test_drive_v2";
  var meta = JSON.parse(document.getElementById("td-meta").textContent);
  var b0 = JSON.parse(document.getElementById("td-edits").textContent || "{}");
  var LS = "testdrive-pravki:" + meta.doc + ":" + (b0.savedAt || "new");
  var ORIG = {};  // исходные тексты до правок — для списка «было / стало»
  document.querySelectorAll(".item").forEach(function (sec) {
    sec.querySelectorAll(".row").forEach(function (r) {
      var t = r.querySelector(".txt");
      ORIG[r.dataset.id] = { t: t ? t.innerText.trim() : "", q: r.classList.contains("q"), qn: r.dataset.q || "", sec: sec.dataset.part + " — " + sec.dataset.title };
    });
  });
  function req(method, url, body, cb) {
    var x = new XMLHttpRequest(); x.open(method, url);
    x.setRequestHeader("Content-Type", "application/json");
    x.onload = function () { try { cb(x.status < 300 ? null : x.status, JSON.parse(x.responseText)); } catch (e) { cb(e); } };
    x.onerror = function () { cb("сеть"); }; x.send(body ? JSON.stringify(body) : null);
  }
  function who() { var w = document.getElementById("who"); return (w && w.value.trim()) || ""; }
  function cut(s) { return s.length > 200 ? s.slice(0, 200) + "…" : s; }
  function text(data) {
    var names = Object.keys(data.by || {}); if (!names.length) return "На сайт пока никто не отправил правки.";
    var out = [];
    names.forEach(function (nm) {
      var s = data.by[nm], lines = [];
      var bySec = {};
      Object.keys(s.items || {}).forEach(function (id) {
        var r = s.items[id], o = ORIG[id] || { t: "?", sec: id }, L = bySec[o.sec] = bySec[o.sec] || [];
        if (o.q) { L.push("❓ " + cut(o.t)); if (r.n) L.push("ответ: " + r.n); }
        else {
          if (r.t === "") L.push("убрать: " + cut(o.t));
          else if (r.t != null) L.push("было: " + cut(o.t), "стало: " + r.t);
          else L.push("«" + cut(o.t) + "»");
          if (r.n) L.push("комментарий: " + r.n);
        }
        L.push("");
      });
      Object.keys(s.added || {}).forEach(function (k) {
        (s.added[k] || []).forEach(function (r) {
          if (!r.t && !r.n) return;
          var L = bySec["блок " + k] = bySec["блок " + k] || [];
          if (r.t) L.push("добавить: " + r.t); if (r.n) L.push("комментарий: " + r.n); L.push("");
        });
      });
      out.push("════ " + nm + " (отправлено " + s.savedAt + ")");
      Object.keys(bySec).forEach(function (k) { out.push("■ " + k, bySec[k].join("\n")); });
    });
    return out.join("\n").replace(/\n{3,}/g, "\n\n");
  }
  var panel = document.getElementById("teampanel"), ta = document.getElementById("tp-text");
  document.getElementById("tp-close").onclick = function () { panel.classList.remove("on"); };
  document.getElementById("tb-team").onclick = function () {
    panel.classList.add("on"); ta.value = "Загружаю…";
    req("GET", "/api/edits?page=" + PAGE, null, function (e, d) { ta.value = e ? "Не удалось загрузить (" + e + ")" : text(d); });
  };
  document.getElementById("tb-fab").onclick = function () { document.getElementById("tb-send").click(); };
  document.getElementById("tb-send").onclick = function () {
    var nm = who();
    if (!nm) {
      nm = (prompt("Как тебя подписать? (имя — чтобы команда видела, чьи правки)") || "").trim();
      if (!nm) return;
      var w = document.getElementById("who"); if (w) { w.value = nm; w.dispatchEvent(new Event("input", { bubbles: true })); }
    }
    var st; try { st = JSON.parse(localStorage.getItem(LS) || "null"); } catch (e) { st = null; }
    if (!st || (!Object.keys(st.items || {}).length && !Object.keys(st.added || {}).length)) { alert("Правок пока нет: поправь текст или ответь на вопрос, потом отправляй."); return; }
    var btn = document.getElementById("tb-send"), fab = document.getElementById("tb-fab");
    btn.disabled = true; btn.textContent = fab.textContent = "Отправляю…";
    req("POST", "/api/edits", { page: PAGE, name: nm, state: st }, function (e) {
      btn.disabled = false; btn.textContent = fab.textContent = e ? "☁ Не вышло — ещё раз" : "☁ Отправлено ✓";
      setTimeout(function () { btn.textContent = "☁ На сайт"; fab.textContent = "☁ Отправить правки"; }, 4000);
    });
  };
})();
</script>
'''


def build_tool_page():
    """Редактор Егора (правка в тексте, ответы, «+ пункт», файл и список правок) + наши слайды + отправка правок на сайт."""
    t = open(TOOL_SRC, encoding='utf-8').read()
    by_anchor = {}
    for sid, les, anchor, cap, _h in S:
        by_anchor.setdefault(anchor, []).append((sid, cap))

    def block(lst):
        return '<div class="slides%s">%s</div>' % ('' if len(lst) > 1 else ' one', ''.join(
            '<a href="slides/deck2/%s.jpg" target="_blank"><img src="slides/deck2/%s.jpg" loading="lazy" alt=""><span>%s</span></a>' % (s, s, html.escape(c)) for s, c in lst))
    # вставляем с конца файла, чтобы позиции не съезжали
    inserts = []
    for (sec, k), lst in by_anchor.items():
        a = t.find('<section class="item" id="%s"' % sec)
        if a < 0:
            print('нет блока', sec); continue
        end = t.find('</section>', a)
        if k is None:
            pos = t.find('</h3>', a) + len('</h3>')
        else:
            pos, cnt = a, -1
            while cnt < k:
                pos = t.find('<div class="row scr"', pos + 1)
                if pos < 0 or pos > end:
                    break
                cnt += 1
            if pos < 0 or pos > end:
                print('нет экрана', sec, k); continue
            pos = t.find('</div></div>', pos) + len('</div></div>')
        inserts.append((pos, block(lst)))
    for pos, b in sorted(inserts, reverse=True):
        t = t[:pos] + b + t[pos:]
    t = t.replace('</head>', TOOL_CSS + '</head>', 1)
    t = t.replace('<button class="btn main" id="save">', TOOL_BTNS + '<button class="btn main" id="save">', 1)
    t = t.replace('<div id="doc">', TOOL_HOWTO + '<div id="doc">', 1)
    i = t.rfind('<script>')
    t = t[:i] + TOOL_JS + t[i:]
    t = re.sub(r'<title>(.*?)</title>', '<title>Тест-драйв v2: редактор + слайды</title>', t, count=1)
    open(os.path.join(P, 'docs', 'course', 'test_drive_v2.html'), 'w', encoding='utf-8').write(t)
    print('редактор: вставлено блоков слайдов', len(inserts))


def deck_page():
    """B.deck_page пишет slides_deck.html (колода v1) — сохраняем v1, строим v2, переносим в slides_v2.html, v1 возвращаем."""
    f = os.path.join(P, 'docs', 'course', 'slides_deck.html')
    v1 = open(f, encoding='utf-8').read()
    B.S = S
    try:
        B.deck_page()
        t = open(f, encoding='utf-8').read()
    finally:
        open(f, 'w', encoding='utf-8').write(v1)
    t = (t.replace('slides/deck/', 'slides/deck2/').replace("'slides_deck'", "'slides_v2'")
          .replace('Слайды тест-драйва</title>', 'Слайды v2 (сценарий Егора)</title>')
          .replace('<h1>Слайды тест-драйва</h1>', '<h1>Слайды v2 — под сценарий Егора 24.10</h1>')
          .replace('/course/test_drive_script.html">Сценарий тест-драйва', '/course/test_drive_v2.html">Сценарий v2 (текст + слайды)'))
    open(os.path.join(P, 'docs', 'course', 'slides_v2.html'), 'w', encoding='utf-8').write(t)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    os.makedirs(DECK, exist_ok=True)
    ids = []
    for sid, _l, _a, _c, htm in S:
        if args and sid not in args:
            continue
        open(os.path.join(DECK, sid + '.html'), 'w', encoding='utf-8').write(htm)
        ids.append(sid)
    if '--no-render' not in sys.argv:
        render(ids)
    if not args:
        build_page()
        build_tool_page()
        deck_page()
    print('ok', len(S), 'слайдов')


if __name__ == '__main__':
    main()
