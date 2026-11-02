"""Замер речи по записи: темп, паузы, слова-паразиты, длина фраз, мелодика (диапазон тона), динамика громкости.
Нужен для программы тренировки речи: раз в неделю пишем контрольный дубль и сравниваем цифры с прошлыми и с эталонами.

Запуск:
  python scripts/speech_check.py запись.mov                    # весь файл
  python scripts/speech_check.py запись.mov@30-90              # кусок с 30 по 90 секунду
  python scripts/speech_check.py a.mov b.mp4@0-60 --label "Егор,Эталон" --json out.json
Слова распознаёт whisper (small), тон считается автокорреляцией по кадрам 40 мс (numpy, без доп. библиотек).
Whisper часто выкидывает «э-э» и «м-м», поэтому реальных паразитов обычно больше, чем в отчёте."""
import os, sys, json, re, subprocess, shutil, tempfile, wave
import numpy as np

FF = shutil.which('ffmpeg') or r'C:\ffmpeg\ffmpeg-2026-01-14-git-6c878f8b82-essentials_build\bin\ffmpeg.exe'
SR = 16000
FILLERS1 = {'ну', 'вот', 'типа', 'короче', 'значит', 'э', 'эм', 'ээ', 'мм', 'собственно', 'блин', 'щас'}
FILLERS2 = ('как бы', 'это самое', 'так сказать', 'в общем', 'на самом деле', 'то есть')
_model = None


def extract(src, a=None, b=None):
    out = tempfile.mktemp(suffix='.wav')
    cmd = [FF, '-y', '-v', 'error']
    if a is not None:
        cmd += ['-ss', str(a)]
    cmd += ['-i', src]
    if b is not None:
        cmd += ['-t', str(b - (a or 0))]
    subprocess.run(cmd + ['-ac', '1', '-ar', str(SR), '-vn', out], check=True)
    return out


def read_wav(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x


def pitch_track(x, frame=0.04, hop=0.01, fmin=70, fmax=400):
    """F0 по кадрам: нормированная автокорреляция, кадр считаем звонким, если пик > 0.45 и кадр не тихий"""
    n, h = int(frame * SR), int(hop * SR)
    lo, hi = int(SR / fmax), int(SR / fmin)
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::h]
    rms = np.sqrt((frames ** 2).mean(1) + 1e-12)
    loud = rms > np.percentile(rms, 40)
    f0 = np.full(len(frames), np.nan)
    win = np.hanning(n)
    for i in np.where(loud)[0]:
        fr = (frames[i] - frames[i].mean()) * win
        ac = np.fft.irfft(np.abs(np.fft.rfft(fr, 2 * n)) ** 2)[:n]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.45:
            f0[i] = SR / k
    return f0, 20 * np.log10(rms + 1e-9), loud


def analyze(src, a=None, b=None, label=None):
    global _model
    import whisper
    if _model is None:
        _model = whisper.load_model('small')
    wav = extract(src, a, b)
    x = read_wav(wav)
    r = _model.transcribe(wav, language='ru', word_timestamps=True, verbose=False)
    os.remove(wav)
    ws = [w for s in r['segments'] for w in s.get('words', [])]
    if len(ws) < 5:
        return {'label': label or os.path.basename(src), 'error': 'мало речи'}
    span = ws[-1]['end'] - ws[0]['start']
    gaps = [ws[i + 1]['start'] - ws[i]['end'] for i in range(len(ws) - 1)]
    talk = sum(w['end'] - w['start'] for w in ws) + sum(g for g in gaps if g <= 0.3)
    phrases, cur = [], 1
    for g in gaps:
        if g > 0.3:
            phrases.append(cur); cur = 1
        else:
            cur += 1
    phrases.append(cur)
    text = ' '.join(w['word'].strip() for w in ws)
    toks = [re.sub(r'[^\wё-]', '', w['word'].lower()) for w in ws]
    low = ' ' + ' '.join(toks) + ' '
    fill = sum(t in FILLERS1 for t in toks) + sum(low.count(' %s ' % f) for f in FILLERS2)
    f0, db, loud = pitch_track(x)
    v = f0[~np.isnan(f0)]
    st = 12 * np.log2(v / np.median(v)) if len(v) > 20 else np.array([0.0])
    mins = span / 60
    return {
        'label': label or os.path.basename(src),
        'секунд': round(span, 1),
        'слов': len(ws),
        'темп_слов_мин': round(len(ws) / mins),
        'темп_без_пауз': round(len(ws) / (talk / 60)),
        'паузы_0.3-1с_в_мин': round(sum(0.3 < g <= 1.0 for g in gaps) / mins, 1),
        'провалы_>1с_в_мин': round(sum(g > 1.0 for g in gaps) / mins, 1),
        'слов_во_фразе': round(float(np.mean(phrases)), 1),
        'паразиты_в_мин': round(fill / mins, 1),
        'тон_медиана_Гц': round(float(np.median(v))) if len(v) else None,
        'диапазон_тона_пт': round(float(np.percentile(st, 90) - np.percentile(st, 10)), 1),
        'живость_тона_пт': round(float(np.std(st)), 1),
        'динамика_громкости_дБ': round(float(np.std(db[loud])), 1),
        'текст': text[:400],
    }


COLS = [('темп_слов_мин', 'темп'), ('темп_без_пауз', 'темп без пауз'), ('паузы_0.3-1с_в_мин', 'паузы/мин'),
        ('провалы_>1с_в_мин', 'провалы/мин'), ('слов_во_фразе', 'слов во фразе'), ('паразиты_в_мин', 'паразиты/мин'),
        ('диапазон_тона_пт', 'диапазон тона, пт'), ('живость_тона_пт', 'живость тона'), ('динамика_громкости_дБ', 'динамика, дБ')]


def main():
    args, labels, out = [], [], None
    it = iter(sys.argv[1:])
    for s in it:
        if s == '--label':
            labels = next(it).split(',')
        elif s == '--json':
            out = next(it)
        else:
            args.append(s)
    res = []
    for i, s in enumerate(args):
        a = b = None
        m = re.match(r'^(.*)@([\d.]+)-([\d.]+)$', s)
        if m:
            s, a, b = m.group(1), float(m.group(2)), float(m.group(3))
        r = analyze(s, a, b, labels[i] if i < len(labels) else None)
        res.append(r)
        print('\n==', r['label'])
        for k, name in COLS:
            print('  %-20s %s' % (name, r.get(k)))
        sys.stdout.flush()
    if out:
        json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
