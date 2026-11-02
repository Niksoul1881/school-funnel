"""Сводная расшифровка дублей в один читаемый файл — чтобы монтажёр (я или Егор) видел, где что сказано.
Читает *.wav.seg.json из папки работы и пишет transcript.md: по дублю — сегменты с таймкодами.

Запуск: python scripts/video_transcript.py <папка_работы> [--full]
Без --full печатает сегменты; с --full — ещё и все слова с таймкодами (для точных резов)."""
import os, sys, json

WORK = sys.argv[1]
FULL = '--full' in sys.argv


def ts(t):
    return '%d:%05.2f' % divmod(t, 60)


files = sorted([f for f in os.listdir(WORK) if f.endswith('.wav.seg.json')],
               key=lambda f: (len(f), f))
out = []
for f in files:
    take = f.replace('.wav.seg.json', '')
    segs = json.load(open(os.path.join(WORK, f), encoding='utf-8'))
    if not segs:
        continue
    ws = [w for s in segs for w in s['words']]
    span = (segs[-1]['end'] - segs[0]['start']) if segs else 0
    out.append('## %s — %.1f c речи, %d слов (%.0f сл/мин)\n' % (take, span, len(ws), len(ws) / (span / 60) if span else 0))
    if FULL:
        for s in segs:
            out.append('%s–%s  %s' % (ts(s['start']), ts(s['end']), s['text'].strip()))
        out.append('')
        out.append('```')
        for s in segs:
            out.append(' '.join('%s[%s]' % (w['word'].strip(), ts(w['start'])) for w in s['words']))
        out.append('```')
    else:
        for s in segs:
            out.append('%s–%s  %s' % (ts(s['start']), ts(s['end']), s['text'].strip()))
    out.append('')

dst = os.path.join(WORK, 'transcript.md')
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print(dst, len(files), 'дублей')
