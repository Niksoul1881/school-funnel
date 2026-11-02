"""Вводный урок v3 — монтаж из дублей 28.10 (Desktop\\Курс\\Вводный: 1, 1.1, 2, 2.1, 3, 3.1, 3.2).
Из каждого блока взят лучший дубль (расшифровка whisper с таймкодами слов лежит в private/video_work_v3),
длинные паузы (> GAP) сжимаются до 2*PAD, на склейках чередуется общий и приближенный план,
слева слайды по смыслу, справа Егор, снизу субтитры.
Запуск: python scripts/build_video_intro_v3.py [--slides-only]"""
import os, sys, json, subprocess, shutil, re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P, 'scripts'))
import build_video_intro as VI   # page/body и стиль колоды v2 под панель 1200x1080

B, ic = VI.B, VI.ic
SRC_DIR = r'C:\Users\NikSouk\Desktop\Курс\Вводный'
WORK = os.path.join(P, 'private', 'video_work_v3')
OUT = os.path.join(P, 'docs', 'course', 'video', 'вводный_урок_v3.mp4')
FF = shutil.which('ffmpeg') or r'C:\ffmpeg\ffmpeg-2026-01-14-git-6c878f8b82-essentials_build\bin\ffmpeg.exe'

GAP = 0.60     # паузы длиннее — сжимаем
PAD = 0.15     # тишины до/после куска речи (пауза на стыке = 2*PAD)
SOFT = '--hard' not in sys.argv   # без куска «я трачу время только на заинтересованных… подводишь себя» (против тона сценария)

# --- монтажный лист: (дубль, начало, конец) по исходнику ---
# границы — в тишине между словами (проверены по громкости: whisper ставит начала слов с опозданием до 0.6 с)
# 4-й элемент — свой порог паузы: в 3.2 «…только действия. | Никаких…» whisper сдвинул «Никаких» на 0.7 с, кусок не режем
CUTS = [('1.1', 71.95, 88.8),      # привет + три вопроса (последний дубль 1.1, Егор: «ахуенно»)
        ('3', 21.15, 23.05),       # «Давай с тобой договоримся.»
        ('2.1', 0.5, 52.2),        # ценность — анкета и персональный разбор (чистый цельный дубль)
        ('3.2', 5.95, 19.6)] + (   # 48 часов (без фальстарта «40 минут»)
       [] if SOFT else [('3.2', 19.6, 41.2)]) + [
        ('3.2', 41.7, 66.4),       # три вещи для прохождения
        ('3.2', 66.4, 83.0, 2.5),  # …третье: только действия
        ('3.1', 20.85, 83.9)]      # не просто смотри + три правила

# --- слайды: (id, дубль, время по исходнику) ---
TIMELINE = [('s_cover', '1.1', 72.05), ('s_q1', '1.1', 77.6), ('s_q2', '1.1', 82.0), ('s_q3', '1.1', 84.1),
            ('s_deal', '3', 21.35), ('s_hw', '2.1', 4.1), ('s_razbor', '2.1', 11.4), ('s_base', '2.1', 20.9),
            ('s_honest', '2.1', 33.6), ('s_goal', '2.1', 42.9),
            ('s_48', '3.2', 6.15), ('s_need1', '3.2', 42.2), ('s_need2', '3.2', 56.4), ('s_need3', '3.2', 66.7),
            ('s_watch', '3.1', 20.95), ('s_rule1', '3.1', 31.3), ('s_rule2', '3.1', 50.9), ('s_rule3', '3.1', 63.3),
            ('s_go', '3.1', 78.55)]


def page(inner, head=None, sub=None, chip=None):
    return VI.page(inner, head=head, sub=sub, chip=chip)


def lab(t, color='var(--muted)'):
    return '<div style="font-size:17px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:%s">%s</div>' % (color, t)


S = {}
S['s_cover'] = page(
    '<div style="position:absolute;left:72px;right:72px;top:250px">%s'
    '<div style="font-size:22px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--acc);margin-top:40px">Вводный урок</div>'
    '<h1 style="font-size:78px;margin-top:16px">За 48 часов — <span class="grad">во фриланс</span></h1>'
    '<div class="sub" style="font-size:28px;margin-top:22px">Тест-драйв профессии AI-автоматизатора: за руку, с нуля, без кода</div>'
    '<div style="display:flex;gap:12px;margin-top:34px"><span class="tag acc" style="font-size:19px;padding:9px 18px">48 часов</span>'
    '<span class="tag prac" style="font-size:19px;padding:9px 18px">практика</span><span class="tag code" style="font-size:19px;padding:9px 18px">личный разбор</span></div></div>' % ic('flag', 'ic big'),
    chip='Тест-драйв')

QS = [('bot', 'Кто такой AI-автоматизатор?'), ('spark', 'Кто такой техспец нового поколения?'), ('trend', 'Почему эта профессия будет нужна ещё долгие годы?')]


def questions(k):
    out = ''
    for i, (icn, t) in enumerate(QS):
        on = i + 1 == k
        out += ('<div class="g %s" style="display:flex;gap:24px;align-items:center;padding:26px 30px;%s"><div class="bnum" style="font-size:64px;min-width:90px">%02d</div>'
                '%s<h3 style="font-size:31px">%s</h3></div>') % ('hl' if on else '', '' if i + 1 <= k else 'opacity:.35', i + 1, ic(icn, 'ic sm goldc' if on else 'ic sm'), t)
    return page(VI.body('<div style="display:grid;gap:22px">%s</div>' % out, top=320, cls='body c'),
                head='Сложим пазл: <span class="grad">три ответа</span>', sub='Что ты будешь понимать после тест-драйва')


for k in (1, 2, 3):
    S['s_q%d' % k] = questions(k)

S['s_deal'] = page(
    '<div style="position:absolute;left:72px;right:72px;top:300px">%s'
    '<h1 style="font-size:80px;margin-top:40px">Давай <span class="grad">договоримся</span></h1>'
    '<div class="sub" style="font-size:32px;margin-top:26px">Ценность — не в просмотре видео</div></div>' % ic('chat', 'ic big'))
S['s_hw'] = page(VI.body(B.flow([('play', 'Дойди до конца', 'Все уроки по порядку'),
                                 ('done', 'Последнее задание', 'Оно главное'),
                                 ('list', 'Анкета', 'На персональный разбор', 'hl')]), cls='body c'),
                 head='Чтобы был <span class="grad">результат</span>')
S['s_razbor'] = page(VI.body(
    '<div class="g" style="padding:34px 40px">%s%s</div>' % (lab('На разборе смотрю твою отправную точку'), ''.join(
        '<div style="display:flex;gap:16px;align-items:center;margin-top:24px;font-size:30px;font-weight:700">%s%s</div>' % (ic(i, 'ic sm goldc' if h else 'ic sm'), t)
        for i, t, h in (('case', 'Чем ты сейчас занимаешься', 0), ('cap', 'Какие навыки уже есть', 0),
                        ('clock', 'Сколько свободного времени', 0), ('coin', 'К какому доходу хочешь прийти', 1)))), top=300),
    head='Персональный <span class="grad">разбор</span>')
S['s_base'] = page(VI.body(B.cards([
    ('book', 'Мини-обучение', 'Фундамент направления: одинаковый для всех'),
    ('map', 'Персональный разбор', 'Шаги под твою ситуацию — к постоянному доходу', 'hl')], cols=2, gap=24), cls='body c'),
    head='Уроки — база, <span class="grad">разбор — твой план</span>')
S['s_honest'] = page(VI.body(
    '<div class="g" style="padding:36px 40px">%s<h3 style="font-size:34px;margin-top:22px">Если увижу, что со мной ты точно сделаешь результат, расскажу про обучение</h3></div>'
    '<div class="strip" style="position:relative;left:auto;right:auto;bottom:auto;margin-top:26px">%s<div>Но это <span class="gold">не главная цель</span> разбора</div></div>' % (
        ic('shield', 'ic'), ic('done', 'ic sm goldc')), top=320), head='Честно, <span class="grad">на берегу</span>')
S['s_goal'] = page(
    '<div style="position:absolute;left:72px;right:72px;top:250px">%s'
    '<div style="font-size:150px;font-weight:900;line-height:1;margin-top:24px" class="grad">150 000 ₽</div>'
    '<div class="sub" style="font-size:32px;margin-top:26px">Пошаговый план, как выйти на этот доход в AI-автоматизации</div></div>' % lab('Главная цель разбора', 'var(--gold)'),
    head=None)
S['s_48'] = page(
    '<div style="position:absolute;left:72px;right:72px;top:240px">%s'
    '<div style="font-size:170px;font-weight:900;line-height:1;margin-top:24px" class="grad">48 часов</div>'
    '<div class="sub" style="font-size:30px;margin-top:26px">на прохождение тест-драйва</div>'
    '<div class="strip" style="position:relative;left:auto;right:auto;bottom:auto;margin-top:44px">%s<div>Нет активности в чате и практики — доступ закрывается</div></div></div>' % (
        ic('clock', 'ic big'), ic('lock', 'ic sm goldc')))
NEED = [('laptop', 'Компьютер или телефон', 'С интернетом. Код и программирование не нужны'),
        ('clock', 'От 1 до 3 часов в день', 'Работу и учёбу бросать не нужно'),
        ('rocket', 'Только действия', 'Без «могу — не могу»')]


def need(k):
    cards = [(i_, t, d, 'hl' if n + 1 == k else '') for n, (i_, t, d) in enumerate(NEED)]
    html = B.cards(cards, cols=3, gap=20)
    # ещё не названные — притушены
    parts = html.split('<div class="g ')
    html = parts[0] + ''.join('<div %sclass="g ' % ('style="opacity:.3" ' if n + 1 > k else '') + p for n, p in enumerate(parts[1:]))
    return page(VI.body(html, cls='body c'), head='Тебе нужно <span class="grad">всего три вещи</span>')


for k in (1, 2, 3):
    S['s_need%d' % k] = need(k)
S['s_watch'] = page(VI.body(B.flow([('eye', 'Разберись', 'В каждом блоке'),
                                    ('wrench', 'Примени', 'Подумай, что поменять в своей жизни'),
                                    ('trend', 'Увеличь доход', '', 'hl')]), cls='body c'),
                    head='Не просто <span class="grad">смотри</span>')
RULES = [('eyeoff', 'Отключи внутреннего критика', 'Не «это не для меня», а «как я это применю»'),
         ('chat', 'Задавай вопросы', '48 часов — карт-бланш на любые вопросы'),
         ('list', 'Не беги впереди паровоза', 'Блок за блоком, по порядку')]


def rules(k):
    out = ''
    for i, (icn, t, d) in enumerate(RULES):
        on = i + 1 == k
        out += ('<div class="g %s" style="display:flex;gap:24px;align-items:center;padding:26px 30px;%s"><div class="bnum" style="font-size:64px;min-width:90px">%02d</div>'
                '<div><h3 style="font-size:30px">%s</h3><p style="font-size:22px;margin-top:6px">%s</p></div></div>') % (
            'hl' if on else '', '' if i + 1 <= k else 'opacity:.35', i + 1, t, d)
    return page(VI.body('<div style="display:grid;gap:20px">%s</div>' % out, top=310, cls='body c'),
                head='Три простых <span class="grad">правила</span>')


for k in (1, 2, 3):
    S['s_rule%d' % k] = rules(k)
S['s_go'] = page(
    '<div style="position:absolute;left:0;right:0;top:260px;text-align:center"><div style="display:flex;justify-content:center">%s</div>'
    '<h1 style="font-size:76px;margin-top:40px">В конце — <span class="grad">полная картина</span></h1>'
    '<div class="sub" style="margin:22px auto 0;font-size:30px">Как применить это в своей жизни</div>'
    '<div style="margin-top:40px"><span class="tag acc" style="font-size:22px;padding:12px 24px;--acc:#34d399">Дальше · Урок 1</span></div></div>' % ic('rocket', 'ic huge'))


# ---------- монтаж ----------
def words(take, a, b):
    return [w for s in json.load(open(os.path.join(WORK, take + '.wav.seg.json'), encoding='utf-8')) for w in s['words'] if a <= w['start'] < b]


_env = {}


def envelope(take):
    """громкость дубля по 10 мс (дБ) и порог «звучит»: whisper часто ставит начало слова позже, чем оно звучит"""
    if take not in _env:
        import numpy as np
        raw = subprocess.run([FF, '-v', 'error', '-i', os.path.join(SRC_DIR, take + '.MOV'), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
        fr = x[:len(x) // 160 * 160].reshape(-1, 160)
        db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
        _env[take] = (db, np.percentile(db, 15) + 14)
    return _env[take]


def widen(take, s0, s1, a, b):
    """раздвигает кусок до реального начала/конца звука (не дальше 0.5 с и границ дубля)"""
    db, thr = envelope(take)
    i = int(s0 * 100)
    lim = max(int(a * 100), i - 50)
    while i - 1 >= lim and db[i - 1] > thr:
        i -= 1
    j = int(s1 * 100)
    lim = min(int(b * 100), j + 50, len(db) - 1)
    while j + 1 <= lim and db[j + 1] > thr:
        j += 1
    return max(a, i / 100 - 0.08), min(b, j / 100 + 0.10)


def chunks():
    """куски речи по всем дублям: (дубль, начало, конец, слова)"""
    out = []
    for take, a, b, *gap in CUTS:
        gap = gap[0] if gap else GAP
        ws = words(take, a, b)
        cur = [ws[0]]
        groups = []
        for w in ws[1:]:
            if w['start'] - cur[-1]['end'] > gap:
                groups.append(cur); cur = [w]
            else:
                cur.append(w)
        groups.append(cur)
        for g in groups:
            s0, s1 = widen(take, g[0]['start'], g[-1]['end'], a, b)
            out.append((take, max(a, min(s0, g[0]['start'] - PAD)), min(b, max(s1, g[-1]['end'] + PAD)), g))
    # соседние куски одного дубля не должны перекрываться
    for i in range(1, len(out)):
        if out[i][0] == out[i - 1][0] and out[i][1] < out[i - 1][2]:
            m = (out[i][1] + out[i - 1][2]) / 2
            out[i - 1] = out[i - 1][:2] + (m,) + out[i - 1][3:]
            out[i] = (out[i][0], m) + out[i][2:]
    return out


# правки субтитров по словам (whisper ослышался), применяются до разбивки на строки — поэтому работают и на стыке строк
WFIX = [('привет', 'Привет'), ('оприланс', 'фриланс'), ('в фриланс', 'во фриланс'),
        ('технически специалист', 'технический специалист'), ('эти специальности будет актуальны', 'эта специальность будет актуальна'),
        ('просто просмотреть обучение', 'просто в просмотре обучения'), ('хочешь пойти', 'хочешь прийти'),
        ('в менее обучение', 'в мини-обучении'), ('здание', 'задание'), ('здания', 'задания'),
        ('сделаешься на', 'сделаешь со мной'), ('и яй-автоматизатором', 'AI-автоматизации'), ('чатах', 'в чатах'),
        ('с каких-то смс-ок', 'сообщения'), ('карта бланш', 'карт-бланш'), ('гораздо продуктивно', 'гораздо продуктивнее'),
        ('паровозов', 'паровоза'), ('о которой', 'о котором'), ('в праве', 'вправе'), ('все своей жизни', 'всё в своей жизни')]


def norm(s):
    return re.sub(r'[.,?!—…]', '', s.strip().lower())


def fix_words(ws):
    """склеивает «AI» + «-автоматизатор», затем применяет WFIX; время слова сохраняется"""
    out = []
    for w in ws:
        w = dict(w)
        if out and (w['word'].strip().startswith('-') or w['word'].strip() == '%'):
            out[-1]['word'] = out[-1]['word'].rstrip() + w['word'].strip(); out[-1]['end'] = w['end']
        else:
            out.append(w)
    for pat, rep in WFIX:
        p = pat.split()
        i = 0
        while i + len(p) <= len(out):
            if [norm(x['word']) for x in out[i:i + len(p)]] == p:
                tail = re.search(r'[.,?!—…]*$', out[i + len(p) - 1]['word'].strip()).group(0)
                r = rep.split()
                if len(r) >= len(p):   # по слову на место, лишнее — в последнее (чтобы строки субтитров не раздувались)
                    for k in range(len(p)):
                        out[i + k] = dict(out[i + k], word=' ' + (' '.join(r[k:]) if k == len(p) - 1 else r[k]))
                    out[i + len(p) - 1]['word'] += tail
                else:
                    out[i] = dict(out[i], word=' ' + rep + tail, end=out[i + len(p) - 1]['end'])
                    del out[i + 1:i + len(p)]
            i += 1
    return out


def join(ws):
    return ' '.join(w['word'].strip() for w in ws).strip(' ,')


def subs(ch, f, path, x=1560, y=1000, max_words=4, max_chars=24):
    def ts(t):
        h, r = divmod(t, 3600); m, s = divmod(r, 60)
        return '%d:%02d:%05.2f' % (h, m, s)
    lines = []
    for ci, (_, _, _, ws) in enumerate(ch):
        ws = fix_words(ws)
        group = []
        for i, w in enumerate(ws):
            group.append(w)
            end_phrase = w['word'].strip().endswith(('.', ',', '?', '!', '—'))
            nxt = ws[i + 1]['word'].strip() if i + 1 < len(ws) else ''
            too_long = len(join(group) + ' ' + nxt) > max_chars
            if len(group) >= max_words or too_long or (end_phrase and len(group) >= 2) or i == len(ws) - 1:
                lines.append((f(ci, group[0]['start']), f(ci, group[-1]['end']) + 0.05, join(group)))
                group = []
    hdr = ('[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\n'
           'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
           'Style: S,Arial,46,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,0,0,0,1\n\n'
           '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    ev = ''.join('Dialogue: 0,%s,%s,S,,0,0,0,,{\\pos(%d,%d)}%s\n' % (ts(a), ts(min(b, lines[i + 1][0]) if i + 1 < len(lines) else b), x, y, t)
                 for i, (a, b, t) in enumerate(lines))
    open(path, 'w', encoding='utf-8').write(hdr + ev)
    open(path + '.txt', 'w', encoding='utf-8').write('\n'.join('%6.1f %s' % (a, t) for a, b, t in lines))


def build():
    ch = chunks()
    offs, acc = [], 0.0
    for take, s0, s1, _ in ch:
        offs.append(acc); acc += s1 - s0
    total = acc

    def f(ci, t):  # время исходника внутри куска ci -> время монтажа
        return offs[ci] + min(max(t - ch[ci][1], 0), ch[ci][2] - ch[ci][1])

    def g(take, t):  # для слайдов: первый кусок этого дубля, где t <= конец
        for ci, (tk, s0, s1, _) in enumerate(ch):
            if tk == take and t <= s1:
                return f(ci, t)
        raise ValueError((take, t))

    lst = os.path.join(WORK, 'slides.txt')
    times = [(sid, g(tk, t)) for sid, tk, t in TIMELINE]
    with open(lst, 'w', encoding='utf-8') as fo:
        for i, (sid, t0) in enumerate(times):
            t1 = times[i + 1][1] if i + 1 < len(times) else total
            if t1 - t0 > 0.05:
                fo.write("file '%s'\nduration %.3f\n" % (os.path.join(WORK, 'slides', sid + '.png').replace('\\', '/'), t1 - t0))
        fo.write("file '%s'\n" % os.path.join(WORK, 'slides', times[-1][0] + '.png').replace('\\', '/'))
    sub = os.path.join(WORK, 'subs.ass')
    subs(ch, f, sub)

    takes = sorted({c[0] for c in ch}, key=lambda t: [c[0] for c in ch].index(t))
    inputs = []
    for t in takes:
        inputs += ['-i', os.path.join(SRC_DIR, t + '.MOV')]
    sl_in = len(takes)
    fc, cat = '', ''
    zoom, crop_y = 1.14, 40
    for i, (take, s0, s1, _) in enumerate(ch):
        k = takes.index(take)
        if i % 2 == 0:
            v = 'crop=720:1080:0:%d' % crop_y
        else:
            w2, h2 = int(720 / zoom) // 2 * 2, int(1080 / zoom) // 2 * 2
            v = 'crop=%d:%d:%d:%d,scale=720:1080' % (w2, h2, (720 - w2) // 2, crop_y + 10)
        fc += ('[%d:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS,%s,setsar=1[v%d];'
               '[%d:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=%.3f:d=0.04[a%d];') % (
            k, s0, s1, v, i, k, s0, s1, max(0, s1 - s0 - 0.04), i)
        cat += '[v%d][a%d]' % (i, i)
    fc += cat + 'concat=n=%d:v=1:a=1[vc][ac];' % len(ch)
    fc += ('[vc]hqdn3d=1.2:1.2:5:5,eq=contrast=1.06:brightness=0.015:saturation=1.08:gamma=1.02,'
           'colorbalance=rs=0.02:bs=-0.03,unsharp=5:5:0.45:5:5:0,fps=30[egor];'
           '[%d:v]scale=1200:1080,fps=30,format=yuv420p,setsar=1[sl];' % sl_in +
           "[sl][egor]hstack=inputs=2,subtitles='%s'[vout];" % sub.replace('\\', '/').replace(':', '\\:') +
           '[ac]highpass=f=80,lowpass=f=14000,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-16:TP=-1.5:LRA=11[aout]')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = OUT if SOFT else OUT.replace('.mp4', '_полный.mp4')
    cmd = [FF, '-y', '-v', 'error', *inputs, '-f', 'concat', '-safe', '0', '-i', lst, '-filter_complex', fc,
           '-map', '[vout]', '-map', '[aout]', '-t', '%.2f' % total, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    src_len = sum(c[2] - c[1] for c in CUTS)
    print('ok', out, 'кусков %d, из выбранных дублей %.1f c -> %.1f c' % (len(ch), src_len, total))
    json.dump({'chunks': [(c[0], round(c[1], 2), round(c[2], 2)) for c in ch], 'slides': times, 'total': total},
              open(os.path.join(WORK, 'edl.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    VI.S = S
    VI.SL = os.path.join(WORK, 'slides')
    VI.render()
    if '--slides-only' not in sys.argv:
        build()
