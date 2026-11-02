"""Расшифровка дублей whisper'ом с таймкодами слов — основа монтажа (build_video_intro_v3.py читает эти .wav.seg.json).
Из каждого .MOV достаём звук 16 кГц, гоняем whisper (small, word_timestamps) и кладём рядом результат
в том же формате, что у v3: список сегментов, у каждого words: [{word, start, end, probability}].

Запуск:
  python scripts/transcribe_video.py <папка_с_дублями> <папка_работы>      # все *.MOV
  python scripts/transcribe_video.py <папка> <работа> --only 4,7,9          # выборочно
  python scripts/transcribe_video.py <папка> <работа> --model medium
Пропускает уже расшифрованные (файл на месте и не пустой)."""
import os, sys, json, subprocess, shutil, tempfile, argparse

FF = shutil.which('ffmpeg') or r'C:\ffmpeg\ffmpeg-2026-01-14-git-6c878f8b82-essentials_build\bin\ffmpeg.exe'
SR = 16000


def wav_of(src):
    out = tempfile.mktemp(suffix='.wav')
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-vn', '-ac', '1', '-ar', str(SR), out], check=True)
    return out


def seg_path(work, take):
    return os.path.join(work, take + '.wav.seg.json')


def transcribe(path, model):
    r = model.transcribe(path, language='ru', word_timestamps=True, verbose=False)
    segs = []
    for s in r['segments']:
        segs.append({'id': s.get('id'), 'start': s['start'], 'end': s['end'], 'text': s['text'],
                     'words': [{'word': w['word'], 'start': w['start'], 'end': w['end'],
                                'probability': w.get('probability')} for w in s.get('words', [])]})
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('srcdir')
    ap.add_argument('work')
    ap.add_argument('--only', default='')
    ap.add_argument('--model', default='small')
    ap.add_argument('--download-root', default=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'private', 'models', 'whisper'),
        help='куда качать веса (по умолчанию — в private/models/whisper: ~/.cache может быть недоступен)')
    a = ap.parse_args()

    import whisper
    model = whisper.load_model(a.model, download_root=a.download_root)
    os.makedirs(a.work, exist_ok=True)
    only = [x.strip() for x in a.only.split(',') if x.strip()]
    files = sorted([f for f in os.listdir(a.srcdir) if f.lower().endswith(('.mov', '.mp4'))],
                   key=lambda f: (len(os.path.splitext(f)[0]), os.path.splitext(f)[0]))
    todo = [f for f in files if not only or os.path.splitext(f)[0] in only]
    for f in todo:
        take = os.path.splitext(f)[0]
        dst = seg_path(a.work, take)
        if os.path.exists(dst) and os.path.getsize(dst) > 100:
            print('  skip', take)
            continue
        wav = wav_of(os.path.join(a.srcdir, f))
        try:
            segs = transcribe(wav, model)
        finally:
            if os.path.exists(wav):
                os.remove(wav)
        json.dump(segs, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
        words = sum(len(s['words']) for s in segs)
        span = (segs[-1]['end'] - segs[0]['start']) if segs else 0
        print('  %-6s %3d сегм. %5d слов  %6.1f c  -> %s' % (take, len(segs), words, span, os.path.basename(dst)))
        sys.stdout.flush()


if __name__ == '__main__':
    main()
