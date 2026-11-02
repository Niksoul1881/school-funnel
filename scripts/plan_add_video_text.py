"""Вставляет текст для видео (реплики Егора + «На экране») из сценария в карточки уроков docs/course/test_drive_plan.html.
Повторный запуск заменяет вставку. Запуск: python scripts/plan_add_video_text.py"""
import os, re, html

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(P, 'sources', 'course', 'тест_драйв_скрипт_v1.md')
PLAN = os.path.join(P, 'docs', 'course', 'test_drive_plan.html')

CSS = ('<style id="vt-css">.vt{margin:14px 0 6px;border-top:2px solid #f08c00;padding-top:10px}'
       '.vt>summary{cursor:pointer;font-weight:800;font-size:18px;color:#d9480f;margin-bottom:6px}'
       '.vt h4{margin:18px 0 6px;font-size:16px;color:#14182e}.vt .scr{font-size:13.5px;color:#5c6478;background:#f1f3f5;border-radius:8px;padding:5px 10px;margin:4px 0}'
       '.vt .say{font-size:18px;line-height:1.55;background:#f3f6ff;border-left:4px solid #4263eb;border-radius:8px;padding:10px 14px;margin:6px 0}'
       '.vt mark{background:#ffe066;border-radius:3px;padding:0 2px}</style>')


def inline(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\[([^\]]{2,300})\]', r'<mark>[\1]</mark>', t)
    return t


def lesson_html(body):
    out, in_say = [], False
    for line in body.split('\n'):
        s = line.strip()
        if not s or s.startswith('!['):
            continue  # пустая строка между абзацами одной реплики — реплика продолжается
        if s.startswith('*Приём') or s.startswith('*Техническое') or s == '---' or (s.startswith('**') and not s.startswith('**На экране') and not s.startswith('**В кадре') and not s.startswith('**ДЗ')):
            in_say = False
            continue
        if s.startswith('### '):
            out.append('<h4>%s</h4>' % inline(s[4:])); in_say = False
        elif s.startswith('**На экране:**') or s.startswith('**В кадре:**') or s.startswith('**ДЗ:**'):
            out.append('<div class="scr">%s</div>' % inline(s)); in_say = False
        elif s.startswith('Егор:'):
            out.append('<div class="say"><b>Егор:</b> %s</div>' % inline(s[5:].strip()))
            in_say = not re.search(r'»\.?$', s)
        elif in_say:
            out.append('<div class="say">%s</div>' % inline(s))
            in_say = not re.search(r'»\.?$', s)
    return ''.join(out)


def main():
    md = open(SRC, encoding='utf-8').read()
    parts = re.split(r'\n(?=## )', md)
    texts = {}
    for p in parts:
        m = re.match(r'## (Вводный урок|Урок (\d))', p)
        if m:
            texts['u0' if m.group(1).startswith('Вводный') else 'u' + m.group(2)] = lesson_html(p)
    page = open(PLAN, encoding='utf-8').read()
    page = re.sub(r'<!--VT-->.*?<!--/VT-->', '', page, flags=re.S)
    page = re.sub(r'<style id="vt-css">.*?</style>', '', page, flags=re.S)
    page = page.replace('</head>', CSS + '</head>', 1)
    for bid, t in texts.items():
        start = page.find('data-block="%s"' % bid)
        nxt = page.find('<div class="card', start + 10)
        end = page.rfind('</div>', start, nxt)
        block = '<!--VT--><details class="vt" open><summary>🎬 Текст для видео</summary>%s</details><!--/VT-->' % t
        page = page[:end] + block + page[end:]
    open(PLAN, 'w', encoding='utf-8').write(page)
    print('ok', sorted(texts))


if __name__ == '__main__':
    main()
