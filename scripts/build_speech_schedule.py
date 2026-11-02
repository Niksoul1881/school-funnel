"""График тренировок речи по дням (12 недель) к программе «Продающий голос».
Выход: docs/course/график_речи.html (+ копия и PDF в папку «Программа речи» на рабочем столе).
Запуск: python scripts/build_speech_schedule.py"""
import os, shutil, html, pathlib
from datetime import date, timedelta

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(P, 'docs', 'course', 'график_речи.html')
DESK = r'C:\Users\NikSouk\Desktop\Программа речи'
START = date(2026, 11, 2)          # понедельник 1-й недели
DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

TWISTERS = [
    'На дворе трава, на траве дрова: раз дрова, два дрова — не руби дрова на траве двора',
    'Карл у Клары украл кораллы, а Клара у Карла украла кларнет',
    'Шла Саша по шоссе и сосала сушку',
    'От топота копыт пыль по полю летит',
    'Сыворотка из-под простокваши',
    'Расскажите про покупки. — Про какие про покупки? — Про покупки, про покупки, про покупочки мои',
    'Бык тупогуб, тупогубенький бычок, у быка бела губа была тупа',
    'Ехал Грека через реку, видит Грека — в реке рак. Сунул Грека руку в реку, рак за руку Греку цап',
    'Четыре чёрненьких чумазеньких чертёнка чертили чёрными чернилами чертёж',
    'Шесть мышат в шалаше шуршат',
    'Корабли лавировали, лавировали, да не вылавировали',
    'Протокол про протокол протоколом запротоколировали',
    'Купи кипу пик',
    'Белые бараны били в барабаны',
    'Жутко жуку жить на суку',
    'Цапля чахла, цапля сохла, цапля сдохла',
    'У осы не усы, не усищи, а усики',
    'Регулировщик лигуриец регулировал в Лигурии',
    'В недрах тундры выдры в гетрах тырят в вёдра ядра кедров',
    'Сшит колпак не по-колпаковски, вылит колокол не по-колоколовски',
    'Нейросеть настроишь наспех — настраивай нейросеть настойчиво',
    'Практикум по промптам прошёл — профессию приобрёл',
    'Промпт продуман — продукт продан, проект подан',
    'Бот ботает, бота бот обучает, бота бот поучает',
]

TOPICS = ['Почему стоит учить нейросети сейчас', 'Худший начальник в моей жизни', 'Как я выбираю телефон',
          'Что не так с работой в офисе', 'Лучшая покупка года', 'Как объяснить бабушке, что такое бот',
          'Почему я ушёл бы на удалёнку', 'Самый полезный навык в жизни', 'Что бы я сделал со 150 тысячами',
          'Мой идеальный рабочий день', 'Почему люди бросают курсы', 'Город, где я хотел бы жить',
          'Как нейросеть сэкономила мне час', 'Чему я научился на первой работе', 'Что я думаю про фриланс',
          'Самая странная работа, о которой я слышал', 'Почему не надо бояться ИИ', 'Как я учусь новому',
          'Лучший совет, который мне давали', 'Что бесит в рекламе курсов', 'Как начать, если ты не технарь',
          'Деньги или свободное время', 'Моя самая большая ошибка', 'Что я сделаю, когда выйду на удалёнку']
OBJECTS = ['кружку', 'ручку', 'зарядку', 'наушники', 'блокнот', 'пульт', 'бутылку воды', 'ключи', 'очки', 'книгу', 'рюкзак', 'часы']
OBJECTIONS = [('«Дорого»', '«Нет времени»'), ('«Я не технарь»', '«Нейросети скоро всех заменят»'),
              ('«Я уже покупал курс, не помогло»', '«А вдруг не получится?»'), ('«Мне 30, поздно переучиваться»', '«Надо подумать»'),
              ('«Это всё развод»', '«Посоветуюсь с женой»')]

CLIPS = {  # неделя -> (эталон, файл)
    1: ('Дудь, реклама и призыв', '1_Дудь_реклама_и_призыв.mp3'), 2: ('Дудь, реклама и призыв', '1_Дудь_реклама_и_призыв.mp3'),
    3: ('Дудь, подводка про Брайтон', '1_Дудь_подводка_Брайтон.mp3'), 4: ('Собчак, справка о госте', '2_Собчак_справка_о_госте.mp3'),
    5: ('Собчак, справка о госте', '2_Собчак_справка_о_госте.mp3'), 6: ('Собчак, реклама курса', '2_Собчак_реклама_курса_нейросети.mp3'),
    7: ('Дудь, подводка ШКЯ', '3_Дудь_подводка_ШКЯ.mp3'), 8: ('Собчак, реклама курса', '2_Собчак_реклама_курса_нейросети.mp3'),
    9: ('Дудь, подводка про Брайтон', '1_Дудь_подводка_Брайтон.mp3'), 10: ('Собчак, реклама курса', '2_Собчак_реклама_курса_нейросети.mp3'),
    11: ('Дудь, реклама и призыв', '1_Дудь_реклама_и_призыв.mp3'), 12: ('свой эталон: выберите сами', ''),
}
SH_STEP = ['Слушать 5 раз, расшифровать, разметить паузы | || и ударения',
           'Говорить вместе с записью в наушниках, 10 раз',
           'Говорить вместе с записью, 10 раз. Потом 3 раза сам без записи',
           'Сам без записи, записать себя на телефон',
           'Записать себя и сравнить: эталон → ты. Найти 1 место и переделать',
           'В паре: на камеру весь отрывок в манере эталона, партнёр сравнивает']

PHASE = {1: 'Аппарат', 2: 'Аппарат', 3: 'Аппарат', 4: 'Выразительность', 5: 'Выразительность', 6: 'Выразительность',
         7: 'Кадр и свобода', 8: 'Кадр и свобода', 9: 'Кадр и свобода', 10: 'Продающая подача', 11: 'Продающая подача', 12: 'Продающая подача'}
GOAL = {1: 'Научиться дышать животом и рёбрами, а не плечами. Замерить старт.',
        2: 'Выдох длиннее, голос не садится после 15 минут чтения.',
        3: 'Счёт на выдохе 25+, «с-с-с» 30 с, три скороговорки чисто и быстро.',
        4: 'Каждое утверждение с точкой вниз, одно главное слово во фразе.',
        5: 'Паузы по смыслу вместо провалов. Темп меняется: фон быстро, главное медленно.',
        6: 'Диапазон тона 9+ полутонов на контрольной записи, паразитов меньше 2 в минуту.',
        7: 'Говорить в объектив одному человеку. Энергия на 7–8 из 10.',
        8: 'Жесты в кадре, чистые входы и выходы из дубля, 90 секунд без бумаги.',
        9: '2 минуты на камеру без суфлёра и без провалов. Взгляд в объектив 80%+.',
        10: 'Сильный хук для каждого урока, продающий блок по шести шагам.',
        11: 'Личная история на 60 секунд и интеграция «как у Дудя» без запинки.',
        12: 'Снять вводный урок блоками, максимум 3 дубля на блок. Слепой тест.'}


def block_a(w, d):
    """Аппарат, 20 мин (в этапе 4 — 12–15)"""
    if w == 1:
        st = 'Стрельникова: «Ладошки», «Погончики», «Насос» — по 4 серии × 8 вдохов'
    elif w == 2:
        st = 'Стрельникова: + «Кошка», «Обними плечи» — по 6 серий × 8'
    elif w == 3:
        st = 'Стрельникова: + «Большой маятник» — по 8–12 серий × 8'
    elif w <= 6:
        st = 'Стрельникова: «сотня» — 12 × 8 на «Ладошки», «Погончики», «Насос»; остальные по 4 серии'
    else:
        st = 'Стрельникова: 6 упражнений × 6 серий'
    if w == 1:
        br = 'Д2 диафрагма 10 вдохов · Д3 «с-с-с» 5 раз (замер) · Д4 счёт · Г1 «м» · Г2 гласные'
    elif w == 2:
        br = 'Д2 · Д3 «с-с-с» (замер) · Д4 счёт · Г1 · Г2 · Г6 «р» · Г7 зевок и жевание'
    elif w == 3:
        br = 'Д3 (замер) · Д4 · Д5 «Егорки» · Г1 · Г3 сирена · Г5 посыл · Г7'
    else:
        br = ('Д3 (замер) · Д4 · Г1 · Г3 сирена · Г5 посыл' if d % 2 == 0 else 'Д5 «Егорки» · Г1 · Г2 лесенка · Г3 сирена · Г6 «р» · Г7')
    n_new = 3
    first = ((w - 1) * n_new) % len(TWISTERS)
    tw = [TWISTERS[(first + i) % len(TWISTERS)] for i in range(n_new)]
    di = 'А1 гимнастика · А2 скороговорки недели' + (' (с пробкой, потом без)' if w >= 3 and d in (0, 3) else '')
    if w >= 2:
        di += ' · А3 окончания'
    mins = 20 if w <= 9 else 15
    if d > 0:   # полное описание — в понедельник, дальше коротко
        st = 'Стрельникова — как в Пн'
        di = 'А1 · А2' + (' с пробкой' if w >= 3 and d == 3 else '') + (' · А3' if w >= 2 else '')
    return mins, [st, br, di], tw


def block_b(w, d):
    k = (w - 1) % 3          # 0,1,2 — неделя внутри этапа
    ph = (w - 1) // 3
    lesson = ['вводного урока', 'урока 1', 'урока 2'][k]
    if ph == 0:
        return [
            ('Чтение вслух с пробкой', 'Карандаш поперёк зубов 3 мин, потом 5 мин без него. Текст: ' + ['сказка «Репка»', 'абзац урока 1', 'первый абзац вводного урока'][k]),
            ('Г5 посыл голоса', ['Слоги «Эй!», «Да!» в точки 1, 3 и 10 метров', 'Слова «Смотри!», «Работает!», «Начинаем!» в три точки', 'Фраза «Сегодня я покажу тебе, как это работает» в три точки'][k]),
            ('Д5 «Егорки» и «Репка»', 'Считай Егорок на одном выдохе, запиши число. «Репка» целиком, добирая воздух на запятых'),
            ('Г3 сирена и Г2 лесенка', 'Сирена на «у» и «нг» 5 раз, «волны» 3 раза, лесенка И-Э-А-О-У вниз и вверх'),
            ('А3 окончания', 'Абзац ' + lesson + ': дожимай последний звук каждого слова, потом читай обычно, но держа концы фраз'),
            ('Чтение вслух с записью', '10 минут любого текста на телефон. Послушать 2 минуты: где проседают концы фраз'),
        ][d]
    if ph == 1:
        phr = ['«Ты можешь освоить новую профессию за месяц»', '«Нейросети уже сейчас экономят бизнесу деньги»', '«Первый заказ можно взять через три недели»'][k]
        task = ['«Запись на тест-драйв открыта»', '«Это займёт всего месяц»', '«Опыт не нужен»'][k]
        return [
            ('В1 логическое ударение', 'Фраза ' + phr + ' — каждый раз новое главное слово. Потом 5 фраз из ' + lesson + ': найти главное слово'),
            ('В2 точка голосом', '10 утверждений о тест-драйве с понижением в конце. Записать, найти, где звучит вопросом, переделать'),
            ('В3 лесенка и В4 разметка', 'Перечисление «боты, агенты, визуализация данных и продажи этих услуг». Разметить | || ↑ ↓ абзац ' + lesson + ' и прочесть по разметке'),
            ('В5 темпо-ритм', 'Одна фраза в трёх темпах. Абзац ' + lesson + ': связки быстро, главное медленно с паузой'),
            ('В6 одна фраза, семь задач', task + ': обрадовать, предупредить, соблазнить, успокоить, поторопить, удивить, поддеть'),
            ('В7 видения и В8 подтекст', '5 фраз ' + lesson + ' с картинкой перед глазами. «Ну это же просто» с тремя подтекстами'),
        ][d]
    if ph == 2:
        return [
            ('Разметка и запись', 'Разметить ' + lesson + ' целиком (паузы, ударения, глагол-задача на абзац) и записать первый абзац'),
            ('К1 второй круг и К2 энергия', 'Фото человека у объектива. Один абзац на энергию 4, 6 и 8 из 10, сравнить'),
            ('К4 жесты и К5 вход и выход', 'Один жест на мысль, руки в кадре. 5 дублей: 2 с тишины → вдох → сразу с энергией → держать взгляд 2 с'),
            ('И2 продай предмет', 'Продать ' + OBJECTS[(w * 6 + d) % len(OBJECTS)] + ' за 60 секунд: для кого, какая боль, почему сейчас. 3 дубля'),
            ('И3 возражения', 'По 30 секунд на %s и %s: согласиться с чувством → факт → шаг' % OBJECTIONS[(w + d) % len(OBJECTIONS)]),
            ('К6 блоки без бумаги', 'Блок ' + lesson + ' на 30–60 с: только 3–4 ключевых слова у камеры, 3 дубля, выбрать лучший'),
        ][d]
    # этап 4
    return [
        ('П1 хук за 3 секунды', '10 вариантов первой фразы ' + lesson + ': вопрос, цифра, неожиданное утверждение. Записать все, выбрать в паре'),
        ('П2 продающий блок', 'Шесть шагов: боль → история → решение → доказательство → предложение → призыв. По 10–20 с, на каждый свой глагол-задача'),
        ('П3 личная история', 'Дубль №%d истории «как я пришёл в нейросети». Убрать лишнее, добавить одну конкретную деталь' % ((w - 10) * 2 + 1)),
        ('П4 интеграция «как у Дудя»', '60 секунд про тест-драйв как совет другу: свой опыт, что внутри, одна честная оговорка, призыв'),
        ('Съёмка блока урока', 'Снять 2 блока ' + lesson + ' по 30–60 с, не больше 3 дублей на блок. Скинуть в монтаж'),
        ('Съёмка блока урока' if w < 12 else 'П5 слепой тест', 'Снять ещё 2 блока ' + lesson + ' и личную историю (дубль №%d)' % ((w - 10) * 2 + 2) if w < 12 else
         'Трём людям вне команды показать наш урок и урок конкурента без названий. Кто увереннее, кому верите, у кого бы купили'),
    ][d]


def block_g(w, d):
    topic = TOPICS[((w - 1) * 6 + d) % len(TOPICS)]
    if w <= 3:
        cam = 'Только звук: записать на телефон и послушать'
    elif w <= 6:
        cam = 'На камеру 1 дубль, посмотреть без звука: глаза и лицо'
    elif w <= 9:
        cam = 'На камеру, 2 минуты к 9-й неделе (сейчас %d с)' % (60 + (w - 7) * 30)
    else:
        cam = 'На камеру, с хуком в первой фразе'
    return 'И1 60 с на тему: «%s». Сказал «ну», «вот», «э-э» — заново. %s' % (topic, cam)


def sunday(w):
    return ('<b>Контрольная запись.</b> Без разминки: первый абзац вводного урока на камеру (60 с) и 60 с на тему «Зачем учиться нейросетям». '
            'Замеры: «с-с-с» в секундах, счёт на выдохе, число Егорок. Записи прогнать через speech_check или скинуть Claude. '
            'Цифры вписать в журнал программы.' + (' <b>Раз в 3 недели:</b> посмотреть запись нулевого дня рядом с сегодняшней.' if w % 3 == 0 else '')
            + ' Остальное время — отдых для голоса.')


def esc(s):
    return html.escape(s, quote=False)


def week_html(w):
    rows = []
    for d in range(7):
        dt = START + timedelta(days=(w - 1) * 7 + d)
        did = 'w%dd%d' % (w, d)
        head = '<td class="day"><b>%s</b><span>%s</span><span class="dn">день %d</span></td>' % (DAYS[d], dt.strftime('%d.%m'), (w - 1) * 7 + d + 1)
        if d == 6:
            rows.append('<tr class="sun" data-date="%s">%s<td colspan="4">%s %s</td></tr>' % (dt.isoformat(), head, cb(did + 'k'), sunday(w)))
            continue
        ma, la, tw = block_a(w, d)
        bt, bd = block_b(w, d)
        clip, _ = CLIPS[w]
        a = cb(did + 'a') + '<b>%d мин</b><ul>%s</ul>' % (ma, ''.join('<li>%s</li>' % esc(x) for x in la))
        b = cb(did + 'b') + '<b>15 мин · %s</b><p>%s</p>' % (esc(bt), esc(bd))
        v = cb(did + 'v') + '<b>15 мин · %s</b><p>%s</p>' % (esc(clip), esc(SH_STEP[d]))
        g = cb(did + 'g') + '<b>10 мин</b><p>%s</p>' % esc(block_g(w, d))
        rows.append('<tr data-date="%s">%s<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (dt.isoformat(), head, a, b, v, g))
    _, _, tw = block_a(w, 0)
    tws = ''.join('<li>%s</li>' % esc(t) for t in tw)
    d0 = START + timedelta(days=(w - 1) * 7)
    return ('<section class="week" id="w%d"><div class="wh"><div><div class="eyebrow">Неделя %d · %s – %s</div><h2>Этап «%s»</h2></div>'
            '<p class="goal"><b>Цель недели.</b> %s</p></div>'
            '<div class="tw"><b>Скороговорки недели</b> (новые; прошлые повторяй по одной)<ul>%s</ul></div>'
            '<div class="tbl"><table><colgroup><col class="c0"><col><col><col><col></colgroup>'
            '<tr><th></th><th>А. Аппарат</th><th>Б. Упражнение этапа</th><th>В. Shadowing</th><th>Г. Импровизация</th></tr>%s</table></div></section>') % (
        w, w, d0.strftime('%d.%m'), (d0 + timedelta(days=6)).strftime('%d.%m'), PHASE[w], esc(GOAL[w]), tws, ''.join(rows))


def cb(i):
    return '<input type="checkbox" id="%s" aria-label="сделано">' % i


CSS = """
:root{--paper:#fbfaf7;--ink:#1d2433;--muted:#5d6577;--line:#dcdfe6;--navy:#22305c;--accent:#e0662a;--soft:#f1f3f8;--today:#fff1e8;
  --display:"Unbounded","Arial Black",sans-serif;--body:"Manrope","Segoe UI",Arial,sans-serif}
*{box-sizing:border-box}
html{background:var(--paper)}
body{margin:0;background:var(--paper);color:var(--ink);font:13.5px/1.45 var(--body);
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px}
main{max-width:1180px;margin:0 auto}
h1,h2{font-family:var(--display);color:var(--navy);text-wrap:balance;line-height:1.2;margin:0}
h1{font-size:30px;margin-bottom:8px}
h2{font-size:19px}
.eyebrow{font:700 11px/1 var(--body);letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-bottom:8px}
.lead{font-size:15px;color:var(--muted);max-width:70ch}
.intro{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0 8px}
.intro div{background:var(--soft);border-radius:10px;padding:12px 14px;min-width:0}
.intro b.t{display:block;font-family:var(--display);font-size:13px;color:var(--navy);margin-bottom:6px}
.intro ul,.intro ol{margin:0;padding-left:18px}
.week{margin-top:28px;padding-top:14px;border-top:2px solid var(--navy)}
.wh{display:flex;flex-wrap:wrap;gap:6px 24px;align-items:flex-end;justify-content:space-between}
.goal{margin:0;max-width:60ch}
.tw{font-size:12.5px;color:var(--muted);margin:8px 0}
.tw ul{margin:2px 0 0;padding-left:18px;columns:3;column-gap:18px}
.tbl{overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:760px;font-size:12.5px}
col.c0{width:66px}
th,td{border:1px solid var(--line);padding:6px 7px;vertical-align:top;text-align:left}
th{background:var(--navy);color:#fff;font-weight:700;font-size:12px}
td b{color:var(--navy)}
td p{margin:2px 0 0}
td ul{margin:2px 0 0;padding-left:16px}
td li{margin:1px 0}
td.day{background:var(--soft);white-space:nowrap}
td.day b{display:block;font-family:var(--display);font-size:13px;color:var(--navy)}
td.day span{display:block;color:var(--muted);font-size:11.5px}
tr.sun td{background:#fff7f1}
tr.today td{background:var(--today)}
tr.today td.day{box-shadow:inset 4px 0 0 var(--accent)}
input[type=checkbox]{float:right;width:16px;height:16px;margin:0 0 4px 6px;accent-color:var(--accent)}
td:has(input:checked){opacity:.55}
.small{font-size:12px;color:var(--muted)}
@media (max-width:700px){.intro{grid-template-columns:1fr}.tw ul{columns:1}h1{font-size:24px}}
@media print{body{padding:0;font-size:10px}table{font-size:9px;line-height:1.3;min-width:0}th,td{padding:3px 5px}td ul{padding-left:12px}
  .tw{margin:4px 0;font-size:9.5px}h2{font-size:15px}.goal{font-size:10px}.week{break-before:page;margin-top:0;padding-top:0;border-top:0}
  tr{break-inside:avoid}input[type=checkbox]{appearance:none;-webkit-appearance:none;border:1.2px solid var(--navy);border-radius:3px}}
@page{size:A4 landscape;margin:9mm 9mm}
"""

JS = """
<script>
(function(){
  var t=new Date(), iso=t.getFullYear()+'-'+String(t.getMonth()+1).padStart(2,'0')+'-'+String(t.getDate()).padStart(2,'0');
  var row=document.querySelector('tr[data-date="'+iso+'"]');
  if(row){row.classList.add('today');}
  document.querySelectorAll('input[type=checkbox]').forEach(function(c){
    try{c.checked=localStorage.getItem('speech:'+c.id)==='1';}catch(e){}
    c.addEventListener('change',function(){try{localStorage.setItem('speech:'+c.id,c.checked?'1':'0');}catch(e){}});
  });
  var b=document.getElementById('go-today');
  if(b){ if(row){b.onclick=function(){row.scrollIntoView({behavior:'smooth',block:'center'});};} else {b.hidden=true;} }
})();
</script>"""


def build():
    weeks = ''.join(week_html(w) for w in range(1, 13))
    intro = """
<div class="eyebrow">К программе «Продающий голос»</div>
<h1>График тренировок</h1>
<p class="lead">Что делать каждый день 12 недель, по блокам и минутам. Неделя 1 начинается в понедельник 2 ноября. Если начинаете в другой день, идите по номерам дней. Галочки сохраняются в этом браузере, сегодняшний день подсвечен.</p>
<p><button id="go-today" type="button" style="font:600 13px var(--body);background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer">К сегодняшнему дню</button></p>
<div class="intro">
<div><b class="t">День 0, до 1 ноября: стартовая запись</b>
<ol><li>Без разминки на камеру: первый абзац вводного урока (60 с) и 60 с на тему «Зачем учиться нейросетям».</li>
<li>Замерить: «с-с-с» в секундах, счёт на одном выдохе, число Егорок.</li>
<li>Скинуть записи Claude: посчитаю темп, паузы, тон. С этим будем сравнивать всё дальше.</li>
<li>Пройти все упражнения из программы по одному разу медленно, по описанию.</li></ol></div>
<div><b class="t">Как устроен день, 60 минут</b>
<ul><li><b>А. Аппарат, 20 мин</b> — утром: Стрельникова, дыхание, голос, дикция.</li>
<li><b>Б. Упражнение этапа, 15 мин</b> — своё на каждый день.</li>
<li><b>В. Shadowing, 15 мин</b> — эталон недели из папки «эталоны»; шаг метода зависит от дня.</li>
<li><b>Г. Импровизация, 10 мин</b> — тема дня, 60 секунд.</li>
<li><b>Нет часа?</b> Минимум 30 минут: А, В и Г по 10.</li>
<li><b>Суббота — вдвоём:</b> один говорит, второй снимает и сравнивает с эталоном. Потом меняетесь.</li></ul></div>
</div>
<p class="small">Коды упражнений (Д1, Г3, В2…) — как в программе «Продающий голос», там описано, как делать каждое.</p>"""
    page = ('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>График тренировок речи</title><link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Manrope:wght@400;600;700&display=swap">'
            '<style>%s</style></head><body><main>%s%s</main>%s</body></html>') % (CSS, intro, weeks, JS)
    open(OUT, 'w', encoding='utf-8').write(page)
    print('ok', OUT)
    if os.path.isdir(DESK):
        dst = os.path.join(DESK, 'График_тренировок.html')
        shutil.copy(OUT, dst)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge')
            pg = b.new_page()
            pg.goto(pathlib.Path(dst).resolve().as_uri(), wait_until='networkidle')
            pg.evaluate("document.querySelectorAll('tr.today').forEach(r=>r.classList.remove('today'));document.getElementById('go-today').hidden=true")
            pg.pdf(path=os.path.join(DESK, 'График_тренировок.pdf'), format='A4', landscape=True, print_background=True, prefer_css_page_size=True)
            b.close()
        print('pdf ok')


if __name__ == '__main__':
    build()
