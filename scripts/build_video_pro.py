"""«Как у продающих курсы»: монтаж говорящей головы по таймкодам слов (whisper).
- вырезает паузы (оставляет короткий «вдох» на стыке),
- на каждой склейке чередует общий и приближенный план (punch-in), чтобы склейки не были видны,
- крупные субтитры по 2–5 слов,
- слева слайды по смыслу (как build_video_intro), справа говорящий, звук — шумодав + громкость.
Запуск: python scripts/build_video_pro.py  (параметры демо — внизу файла)"""
import os, sys, json, subprocess, shutil

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P, 'scripts'))
FF = shutil.which('ffmpeg') or r'C:\ffmpeg\ffmpeg-2026-01-14-git-6c878f8b82-essentials_build\bin\ffmpeg.exe'

GAP = 0.30     # паузы длиннее — вырезаем
PAD = 0.08     # сколько тишины оставить до/после слова


def load_words(seg_json, a, b):
    return [w for s in json.load(open(seg_json, encoding='utf-8')) for w in s['words'] if a <= w['start'] < b]


def chunks_from_words(ws):
    """куски речи: слова подряд без пауз > GAP"""
    out, cur = [], [ws[0]]
    for w in ws[1:]:
        if w['start'] - cur[-1]['end'] > GAP:
            out.append(cur); cur = [w]
        else:
            cur.append(w)
    out.append(cur)
    return [(max(0, c[0]['start'] - PAD), c[-1]['end'] + PAD, c) for c in out]


def retime(chunks):
    """время исходника -> время монтажа"""
    marks, acc = [], 0.0
    for a, b, _ in chunks:
        marks.append((a, b, acc)); acc += b - a
    def f(t):
        for a, b, o in marks:
            if t < a:
                return o
            if t <= b:
                return o + t - a
        return acc
    return f, acc


FIX = [('нейросит', 'нейросет'), ('Нейросит', 'Нейросет'), ('аксел', 'Excel'), ('форумул', 'формул'), ('БПР', 'ВПР'),
       ('мини-пеллажени', 'мини-приложени'), ('роков', 'уроков'), ('тех спец', 'техспец'), ('науке', 'навык'), ('римни', 'времени')]


def fix(t):
    for a, b in FIX:
        t = t.replace(a, b)
    return t


def ass_subs(chunks, f, path, x_center, y, size=46, max_words=3, max_chars=24):
    """субтитры: короткие фразы (влезают в панель 720 px), белые, жирные, с обводкой"""
    def ts(t):
        h, r = divmod(t, 3600); m, s = divmod(r, 60)
        return '%d:%02d:%05.2f' % (h, m, s)
    lines = []
    for a, b, ws in chunks:
        group = []
        for i, w in enumerate(ws):
            group.append(w)
            end_phrase = w['word'].strip().endswith(('.', ',', '?', '!', '—'))
            nxt = ws[i + 1]['word'].strip() if i + 1 < len(ws) else ''
            too_long = len(' '.join(x['word'].strip() for x in group) + ' ' + nxt) > max_chars
            if len(group) >= max_words or too_long or (end_phrase and len(group) >= 2) or i == len(ws) - 1:
                text = fix(' '.join(x['word'].strip() for x in group).strip(' ,'))
                lines.append((f(group[0]['start']), f(group[-1]['end']) + 0.05, text))
                group = []
    hdr = ('[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\n'
           'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
           'Style: S,Arial,%d,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,0,0,0,1\n\n'
           '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n') % size
    ev = ''.join('Dialogue: 0,%s,%s,S,,0,0,0,,{\\pos(%d,%d)}%s\n' % (ts(a), ts(b), x_center, y, t.replace('\n', ' ')) for a, b, t in lines)
    open(path, 'w', encoding='utf-8').write(hdr + ev)


def build(src, seg_json, a, b, slides_dir, slide_timeline, out, work, crop_y=40, zoom=1.14):
    ws = load_words(seg_json, a, b)
    ch = chunks_from_words(ws)
    f, total = retime(ch)
    # слайды: список кадров по новому времени
    lst = os.path.join(work, 'pro_slides.txt')
    times = [(sid, f(t)) for sid, t in slide_timeline]
    with open(lst, 'w', encoding='utf-8') as fo:
        for i, (sid, t0) in enumerate(times):
            t1 = times[i + 1][1] if i + 1 < len(times) else total
            if t1 - t0 > 0.05:
                fo.write("file '%s'\nduration %.3f\n" % (os.path.join(slides_dir, sid + '.png').replace('\\', '/'), t1 - t0))
        fo.write("file '%s'\n" % os.path.join(slides_dir, times[-1][0] + '.png').replace('\\', '/'))
    # субтитры поверх правой панели (говорящий), внизу
    subs = os.path.join(work, 'pro_subs.ass')
    ass_subs(ch, f, subs, 1200 + 360, 1000)
    # говорящий: куски с чередованием планов
    fc, cat = '', ''
    for i, (s0, s1, _) in enumerate(ch):
        if i % 2 == 0:   # общий план 720x1080
            v = 'crop=720:1080:0:%d' % crop_y
        else:            # приближение: вырезаем меньший кадр у лица и растягиваем
            w2, h2 = int(720 / zoom) // 2 * 2, int(1080 / zoom) // 2 * 2
            v = 'crop=%d:%d:%d:%d,scale=720:1080' % (w2, h2, (720 - w2) // 2, crop_y + 10)
        fc += ('[0:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS,%s,setsar=1[v%d];'
               '[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=%.3f:d=0.03[a%d];') % (
            s0, s1, v, i, s0, s1, max(0, s1 - s0 - 0.03), i)
        cat += '[v%d][a%d]' % (i, i)
    fc += cat + 'concat=n=%d:v=1:a=1[vc][ac];' % len(ch)
    fc += ('[vc]hqdn3d=1.2:1.2:5:5,eq=contrast=1.06:brightness=0.015:saturation=1.10:gamma=1.02,'
           'colorbalance=rs=0.02:bs=-0.02,unsharp=5:5:0.45:5:5:0,fps=30[egor];'
           '[1:v]scale=1200:1080,fps=30,format=yuv420p,setsar=1[sl];'
           "[sl][egor]hstack=inputs=2,subtitles='%s'[vout];" % subs.replace('\\', '/').replace(':', '\\:') +
           '[ac]highpass=f=80,lowpass=f=14000,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-16:TP=-1.5:LRA=11[aout]')
    cmd = [FF, '-y', '-v', 'error', '-i', src, '-f', 'concat', '-safe', '0', '-i', lst, '-filter_complex', fc,
           '-map', '[vout]', '-map', '[aout]', '-t', '%.2f' % total, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    orig = ws[-1]['end'] - ws[0]['start']
    print('ok', out, 'было %.1f c речи с паузами -> стало %.1f c, кусков %d, темп %.0f слов/мин' % (orig, total, len(ch), len(ws) / total * 60))


if __name__ == '__main__':
    import build_video_intro as VI
    W = sys.argv[1]
    SRC = sys.argv[2]
    # слайды демо (дубль 25.10, последний заход 136.5–218)
    S = VI.S
    B = VI.B
    S2 = {
        'd_cover': S['p_cover'],
        'd_remote': VI.page(VI.body(B.cards([('laptop', 'Удалённо', 'Работаешь из любой точки'), ('spark', 'Новая профессия', 'Техспец нового поколения'),
                                             ('rocket', 'Спрос растёт', 'Бизнесу нужны те, кто умеет с нейросетями', 'hl')], cols=1, gap=18), top=300, cls='body c'),
                            head='Техспец <span class="grad">нового поколения</span>'),
        'd_tools': VI.page(VI.body(B.cards([('bot', 'Боты', ''), ('spark', 'AI-агенты', ''), ('chart', 'Визуализация данных', ''), ('coin', 'Как это продавать', '', 'hl')], cols=2, gap=20), cls='body c'),
                           head='Учимся работать <span class="grad">с нейросетями</span>'),
        'd_pc': VI.page(VI.body(B.flow([('laptop', '10–15 лет назад', 'Уверенный пользователь ПК — уже повод взять на работу'),
                                        ('table', 'Потом', 'Excel, формулы, ВПР'),
                                        ('spark', 'Сейчас', 'Уверенный пользователь нейросетей', 'hl')]), cls='body c'),
                        head='История <span class="grad">повторяется</span>'),
        'd_now': VI.page('<div style="position:absolute;left:0;right:0;top:330px;text-align:center"><div style="display:flex;justify-content:center">%s</div>'
                         '<h1 style="font-size:72px;margin-top:40px">Изучать нейросети<br><span class="grad">сейчас — это круто</span></h1></div>' % B.ic('trend', 'ic huge')),
    }
    VI.S = S2
    VI.SL = os.path.join(W, 'slides')
    VI.render()
    out = os.path.join(P, 'docs', 'course', 'video', 'вводный_дубль2_демо_как_у_них.mp4')
    build(SRC, os.path.join(W, 'segments_w.json'), 136.5, 220, VI.SL,
          [('d_cover', 136.5), ('d_remote', 147.2), ('d_tools', 162.9), ('d_pc', 177.9), ('d_now', 213.3)], out, W)
