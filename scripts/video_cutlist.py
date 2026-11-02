"""Монтажный лист в человекочитаемом виде: из edl.json (что уже собрано) + расшифровки дублей.
Нужен, чтобы можно было проверить монтаж, не открывая видео: какой дубль, какие секунды исходника,
что в них сказано и сколько это идёт в готовом ролике.

Запуск: python scripts/video_cutlist.py <папка работы> [имя файла]
Пишет <папка работы>/cutlist.md
"""
import os, sys, json


def ts(t):
    m, s = divmod(t, 60)
    return '%d:%05.2f' % (m, s)


WORK = sys.argv[1]
dst = os.path.join(WORK, sys.argv[2] if len(sys.argv) > 2 else 'cutlist.md')
edl = json.load(open(os.path.join(WORK, 'edl.json'), encoding='utf-8'))
total = edl['total']


def subs_lines():
    """строки субтитров уже вычитаны (WFIX/LINE_FIX), поэтому текст берём из них, а не из сырого whisper"""
    p = os.path.join(WORK, 'subs.ass.txt')
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding='utf-8').read().splitlines():
        t, _, s = line.strip().partition(' ')
        try:
            out.append((float(t), s.strip()))
        except ValueError:
            continue
    return out


LINES = subs_lines()


def text_of(t0, t1, take=None, a=0.0, b=0.0):
    if LINES:
        return ' '.join(s for t, s in LINES if t0 - 0.01 <= t < t1).strip()
    p = os.path.join(WORK, take + '.wav.seg.json')
    if not os.path.exists(p):
        return ''
    return ' '.join(w['word'].strip() for s in json.load(open(p, encoding='utf-8'))
                    for w in s['words'] if a <= w['start'] < b).strip()


out = ['# Монтажный лист', '',
       'Всего %d кусков, готовый ролик %s. Время в третьем столбце — по времени ролика, в четвёртом — по исходнику.' % (
           len(edl['chunks']), ts(total)), '',
       '| # | дубль | в ролике | в исходнике | что звучит |', '|---|---|---|---|---|']
acc = 0.0
for i, (take, a, b) in enumerate(edl['chunks'], 1):
    d = b - a
    out.append('| %d | %s | %s–%s | %s–%s | %s |' % (
        i, take, ts(acc), ts(acc + d), ts(a), ts(b), text_of(acc, acc + d, take, a, b)[:220]))
    acc += d
out += ['', '## Слайды', '', '| слайд | появляется | держится |', '|---|---|---|']
sl = edl['slides']
for i, (sid, t) in enumerate(sl):
    t1 = sl[i + 1][1] if i + 1 < len(sl) else total
    out.append('| %s | %s | %.1f c |' % (sid, ts(t), t1 - t))
open(dst, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(dst, len(edl['chunks']), 'кусков')
