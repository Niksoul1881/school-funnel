"""Монтаж вводного урока: слева слайды (1200x1080, стиль колоды v2), справа Егор (720x1080), слайды переключаются по смыслу речи.
Тексты слайдов — по тому, что Егор реально говорит в записи (расшифровка whisper).
Запуск: python scripts/build_video_intro.py <видео.MOV> <папка_работы> [--slides-only]"""
import os, sys, json, subprocess

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P, 'scripts'))
import build_slides_v2 as V   # LESSONS v2 (вводный + 6), общий CSS и иконки
B = V.B
ic, todo, ARR = B.ic, B.todo, B.ARR

SRC = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\NikSouk\Desktop\Вводный\IMG_7832.MOV'
WORK = sys.argv[2] if len(sys.argv) > 2 else os.path.join(P, 'private', 'video_work')
OUT_DIR = os.path.join(P, 'docs', 'course', 'video')
SL = os.path.join(WORK, 'slides')

# --- склейки исходника (секунды): оставляем эти куски ---
KEEP = [(0.40, 44.25), (54.95, 301.10)]

# --- слайды: (id, начало по исходнику) ---
TIMELINE = [('p_cover', 0.0), ('p_system', 22.8), ('p_need', 54.95), ('p_algo', 84.0), ('p_razbor', 92.5),
            ('p_map0', 157.6), ('p_map1', 172.2), ('p_map2', 186.3), ('p_map3', 194.9), ('p_map4', 205.8),
            ('p_map5', 213.7), ('p_map6', 220.6), ('p_code', 231.6), ('p_rules1', 248.7), ('p_rules2', 265.5),
            ('p_rules3', 275.7), ('p_more', 284.5), ('p_go', 296.2)]

PANEL_CSS = ('html,body{width:1200px!important}.slide{width:1200px!important}'
             '.h{left:72px;right:72px;top:150px}.chip{left:72px}h1{font-size:54px}.sub{font-size:25px}'
             '.prog{left:60px;right:60px;bottom:40px}.prog .it{font-size:13px;gap:8px}.prog .it::after{margin:0 8px}'
             '.g h3{font-size:28px}.g p{font-size:22px}' + V.XCSS)


def page(inner, head=None, sub=None, lesson=0, chip=None, prog=True):
    return V.page(lesson, inner, head=head, sub=sub, chip=chip, progress=prog, extra_css=PANEL_CSS)


def body(html, top=330, bottom=130, cls='body', extra=''):
    return '<div class="%s" style="left:72px;right:72px;top:%dpx;bottom:%dpx;%s">%s</div>' % (cls, top, bottom, extra, html)


S = {}
S['p_cover'] = page(
    '<div style="position:absolute;left:72px;right:72px;top:250px">%s'
    '<div style="font-size:22px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--acc);margin-top:40px">Вводный урок</div>'
    '<h1 style="font-size:76px;margin-top:16px">Тест-драйв профессии <span class="grad">нового времени</span></h1>'
    '<div class="sub" style="font-size:28px;margin-top:22px">Боты, AI-агенты и мини-приложения — с нуля, без кода</div>'
    '<div style="display:flex;gap:12px;margin-top:34px"><span class="tag acc" style="font-size:19px;padding:9px 18px">6 уроков</span>'
    '<span class="tag prac" style="font-size:19px;padding:9px 18px">практика</span><span class="tag code" style="font-size:19px;padding:9px 18px">личный разбор</span></div></div>' % ic('flag', 'ic big'),
    chip='Тест-драйв')
S['p_system'] = page(body(B.cards([
    ('x', 'Без пустой теории', 'И без бесконечных обещаний'),
    ('map', 'Конкретная система', 'Покажу, как она работает'),
    ('wrench', 'Практика', 'Как применять знания на деле'),
    ('coin', 'Заработок', 'Как на этом заработать', 'hl')], cols=2, gap=24), cls='body c'),
    head='Что будет на <span class="grad">тест-драйве</span>', sub='От меня — польза и крутой контент. От тебя — внимание.')
S['p_need'] = page(body(B.cards([
    ('phone', 'Телефон или компьютер', ''), ('radio', 'Интернет', ''), ('clock', 'Несколько часов в день', '')], cols=3, gap=20), bottom=330, cls='body c')
    + '<div class="strip" style="left:72px;right:72px;bottom:140px">%s<div>Опыт программирования <span class="gold">не нужен</span>. Всё, что я покажу, ты сможешь повторить сам.</div></div>' % ic('done', 'ic sm goldc'),
    head='Что тебе <span class="grad">понадобится</span>')
S['p_algo'] = page(body(B.flow([('help', 'Кажется невозможным', 'На некоторых уроках'),
                                 ('list', 'Понять алгоритм', ''),
                                 ('wrench', 'Немного практики', 'И всё получается', 'hl')]), cls='body c'),
                   head='Сложно? <span class="grad">Это алгоритм</span>', sub='Не пропускай уроки и следи за каждым шагом — результат складывается из небольших действий.')
S['p_razbor'] = page(body(
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:22px;height:100%%">'
    '<div class="g"><div style="font-size:17px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)">Смотрю, где ты сейчас</div>%s</div>'
    '<div class="g hl"><div style="font-size:17px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)">Вместе составим план</div>%s</div></div>' % (
        ''.join('<div style="display:flex;gap:14px;align-items:center;margin-top:20px;font-size:24px;font-weight:700">%s%s</div>' % (ic(i, 'ic sm'), t)
                for i, t in (('case', 'Чем занимаешься'), ('clock', 'Сколько свободного времени'), ('cap', 'Какие навыки есть'), ('coin', 'Какой доход хочешь'))),
        ''.join('<div style="display:flex;gap:14px;align-items:center;margin-top:20px;font-size:24px;font-weight:700">%s%s</div>' % (ic(i, 'ic sm goldc'), t)
                for i, t in (('target', 'Какие задачи подойдут тебе'), ('flag', 'С чего начать'), ('users', 'Где искать первых клиентов'), ('rocket', 'Как действовать дальше')))),
    top=330), head='Самое ценное — <span class="grad">разбор</span>', sub='У каждого своя отправная точка — поэтому и план индивидуальный.')

MAP = [('case', 'Знакомство', 'Обо мне, моих учениках и плюшках профессии'),
       ('bot', 'Боты', 'Кому нужны, кто платит, как поставить на поток'),
       ('spark', 'AI-агенты', 'Чем круче нейронок, сколько стоят, кто платит'),
       ('phone', 'Мини-приложения', 'Зачем предпринимателям и как на этом зарабатывать'),
       ('target', 'Клиенты', 'Кто заплатит и как найти первых покупателей'),
       ('users', 'Созвон с ученицей', 'Интервью: она тоже хотела изменить жизнь')]


def map_slide(k):
    cards = ''
    for i, (icn, t, d) in enumerate(MAP):
        n = i + 1
        acc = V.B.LESSONS[n][3]
        on = (k == n)
        dim = k and not on
        cards += ('<div class="g" style="padding:20px 24px;display:flex;gap:18px;align-items:center;%s">%s'
                  '<div><div style="font-size:14px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:%s">Урок %d</div>'
                  '<h3 style="font-size:26px;margin-top:2px">%s</h3><p style="font-size:17px;margin-top:4px">%s</p></div></div>') % (
            ('border:2px solid %s;box-shadow:0 0 60px %s66;transform:scale(1.03)' % (acc, acc)) if on else ('opacity:.35' if dim else ''),
            ic(icn, 'ic sm', acc), acc, n, t, d)
    sub = 'Программа связана: после каждого урока — практика' if not k else 'Урок %d из 6' % k
    return page(body('<div style="display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(3,1fr);gap:18px;height:100%%">%s</div>' % cards, top=300),
                head='Что тебя <span class="grad">ждёт</span>', sub=sub)


for k in range(7):
    S['p_map%d' % k] = map_slide(k)
S['p_code'] = page(
    '<div style="position:absolute;left:0;right:0;top:170px;text-align:center"><h1 style="font-size:60px">Собери код из <span class="grad">4 цифр</span></h1>'
    '<div class="sub" style="margin:16px auto 0;max-width:960px">В четырёх уроках из шести покажу по цифре</div></div>'
    '<div style="position:absolute;left:0;right:0;top:390px;display:flex;justify-content:center;gap:26px">%s</div>'
    '<div style="position:absolute;left:72px;right:72px;top:690px;display:flex;align-items:center;justify-content:center;gap:0">'
    '<div class="g" style="padding:20px 24px;text-align:center"><h3 style="font-size:24px">Код</h3></div>%s'
    '<div class="g" style="padding:20px 24px;text-align:center"><h3 style="font-size:24px">В чат бота</h3></div>%s'
    '<div class="g hl" style="padding:20px 24px;text-align:center;max-width:420px"><h3 style="font-size:24px">Пошаговый гайд по поиску первых клиентов</h3></div></div>' % (
        ''.join('<div class="slotd" style="width:150px;height:190px"><span style="font-size:90px">_</span></div>' for _ in range(4)), ARR, ARR))
RULES = [('eyeoff', 'Не решай заранее «это не для меня»', 'Как велосипед или машина: сложно сначала, потом идёт само'),
         ('chat', 'Не держи вопросы при себе', 'На время тест-драйва — карт-бланш на любые вопросы'),
         ('list', 'Не пропускай этапы', 'Тест-драйв — продуманная система, каждый шаг связан')]


def rules(k):
    out = ''
    for i, (icn, t, d) in enumerate(RULES):
        on = (i + 1 == k)
        out += ('<div class="g %s" style="display:flex;gap:24px;align-items:center;padding:26px 30px;%s"><div class="bnum" style="font-size:64px;min-width:90px">%02d</div>'
                '<div><h3 style="font-size:29px">%s</h3><p style="font-size:21px;margin-top:6px">%s</p></div></div>') % (
            'hl' if on else '', '' if on or i + 1 < k else 'opacity:.4', i + 1, t, d)
    return page(body('<div style="display:grid;gap:20px">%s</div>' % out, top=310, cls='body c'),
                head='Три правила, чтобы был <span class="grad">толк</span>')


for k in (1, 2, 3):
    S['p_rules%d' % k] = rules(k)
S['p_more'] = page(body(B.flow([('wrench', 'Выполняй задания', ''), ('eye', 'Вникай в детали', ''),
                                 ('flag', 'Доходи до конца', 'Там — полная картина и твои возможности', 'hl')]), cls='body c'),
                   head='Не просто <span class="grad">смотри</span>', sub='Последний момент: не ограничивайся просмотром уроков.')
S['p_go'] = page(
    '<div style="position:absolute;left:0;right:0;top:260px;text-align:center"><div style="display:flex;justify-content:center">%s</div>'
    '<h1 style="font-size:84px;margin-top:40px">Если готов — <span class="grad">начинаем!</span></h1>'
    '<div class="sub" style="margin:22px auto 0;font-size:30px">Впереди самое интересное</div>'
    '<div style="margin-top:40px"><span class="tag acc" style="font-size:22px;padding:12px 24px;--acc:#34d399">Дальше · Урок 1</span></div></div>' % ic('rocket', 'ic huge'))


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(SL, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge')
        pg = b.new_page(viewport={'width': 1200, 'height': 1080})
        for sid, htm in S.items():
            f = os.path.join(SL, sid + '.html')
            open(f, 'w', encoding='utf-8').write(htm.replace('../screens/', '../../../docs/course/slides/screens/'))
            pg.goto('file:///' + f.replace('\\', '/'))
            pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(250)
            pg.screenshot(path=os.path.join(SL, sid + '.png'))
            print('  ', sid)
        b.close()


def new_time(t):
    """время исходника -> время после склеек"""
    acc = 0.0
    for a, b in KEEP:
        if t <= a:
            return acc
        if t <= b:
            return acc + (t - a)
        acc += b - a
    return acc


def build_video():
    total = sum(b - a for a, b in KEEP)
    # 1) Егор: склейка + кадрирование 720x1080 + лёгкая ретушь; звук: шумодав, частоты, громкость
    parts = ''.join('[0:v]trim=%.2f:%.2f,setpts=PTS-STARTPTS[v%d];[0:a]atrim=%.2f:%.2f,asetpts=PTS-STARTPTS[a%d];' % (a, b, i, a, b, i)
                    for i, (a, b) in enumerate(KEEP))
    cat = ''.join('[v%d][a%d]' % (i, i) for i in range(len(KEEP))) + 'concat=n=%d:v=1:a=1[vc][ac];' % len(KEEP)
    vf = ('[vc]crop=720:1080:0:40,hqdn3d=1.2:1.2:5:5,'
          'eq=contrast=1.06:brightness=0.015:saturation=1.10:gamma=1.02,'
          'colorbalance=rs=0.02:bs=-0.02:rm=0.01,unsharp=5:5:0.45:5:5:0,fps=30,setsar=1[egor];')
    af = '[ac]highpass=f=80,lowpass=f=14000,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-16:TP=-1.5:LRA=11[aout]'
    # 2) слайды: список кадров с длительностями (по новому времени)
    lst = os.path.join(WORK, 'slides.txt')
    with open(lst, 'w', encoding='utf-8') as f:
        times = [(sid, new_time(t)) for sid, t in TIMELINE]
        for i, (sid, t0) in enumerate(times):
            t1 = times[i + 1][1] if i + 1 < len(times) else total
            if t1 - t0 < 0.05:
                continue
            f.write("file '%s'\nduration %.3f\n" % (os.path.join(SL, sid + '.png').replace('\\', '/'), t1 - t0))
        f.write("file '%s'\n" % os.path.join(SL, times[-1][0] + '.png').replace('\\', '/'))
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, 'вводный_урок_монтаж_v1.mp4')
    fc = parts + cat + vf + '[1:v]scale=1200:1080,fps=30,format=yuv420p,setsar=1[sl];[sl][egor]hstack=inputs=2,format=yuv420p[vout];' + af
    import shutil
    ff = shutil.which('ffmpeg') or r'C:\ffmpeg\ffmpeg-2026-01-14-git-6c878f8b82-essentials_build\bin\ffmpeg.exe'
    cmd = [ff, '-y', '-v', 'error', '-stats', '-i', SRC, '-f', 'concat', '-safe', '0', '-i', lst,
           '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]', '-t', '%.2f' % total,
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
           '-movflags', '+faststart', out]
    print(' '.join(cmd[:6]), '…')
    subprocess.run(cmd, check=True)
    print('ok', out, '%.1f сек' % total)


if __name__ == '__main__':
    render()
    if '--slides-only' not in sys.argv:
        build_video()
