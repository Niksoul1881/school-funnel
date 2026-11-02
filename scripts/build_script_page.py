"""Сценарий тест-драйва (sources/course/*.md) -> страница с комментариями по урокам (docs/course/test_drive_script.html).
Стили и движок комментариев берутся из docs/course/test_drive_plan.html.
Запуск: python scripts/build_script_page.py"""
import os, re, sys, html

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P, 'scripts'))
from build_md_pages import md_to_html

SRC = os.path.join(P, 'sources', 'course', 'тест_драйв_скрипт_v1.md')
OUT = os.path.join(P, 'docs', 'course', 'test_drive_script.html')
TPL = open(os.path.join(P, 'docs', 'course', 'test_drive_plan.html'), encoding='utf-8').read()
STYLE = re.search(r'<style>(.*?)</style>', TPL, re.S).group(1)
SCRIPT = re.search(r'<script>(.*?)</script>', TPL, re.S).group(1).replace("var PAGE = 'test_drive_plan'", "var PAGE = 'test_drive_script'")

EXTRA = '''
.card h3 { font-size: 16px; margin: 18px 0 6px; color: var(--dark); }
.card h3:first-of-type { margin-top: 10px; }
p.say { background: #f3f6ff; border-left: 4px solid #4263eb; border-radius: 8px; padding: 9px 12px; }
p.screen { background: #f1f3f5; border-radius: 8px; padding: 6px 12px; font-size: 14px; color: #495057; }
p.trick { font-size: 13px; color: #7a5b00; background: #fff9db; border-radius: 8px; padding: 6px 12px; }
a.slide { display: block; margin: 8px 0 12px; text-decoration: none; }
.gallery { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 10px 0 14px; }
.gallery a.slide { margin: 0; }
@media (max-width: 700px) { .gallery { grid-template-columns: 1fr; } }
a.slide img { display: block; width: 100%; border-radius: 12px; box-shadow: 0 6px 20px rgba(20,24,46,.25); }
a.slide span { display: block; font-size: 13px; color: var(--muted); margin-top: 6px; text-align: center; }
mark { background: #ffe066; border-radius: 3px; padding: 0 2px; }
.toc { background: var(--card); border-radius: 12px; padding: 12px 16px; margin: 0 0 18px; box-shadow: 0 2px 8px rgba(20,24,46,.06); font-size: 14px; }
.toc a { display: inline-block; margin: 3px 10px 3px 0; color: #1c5fd6; text-decoration: none; }
'''


def decorate(h):
    # картинки слайдов: ![подпись](путь) -> превью со ссылкой на полный размер
    def gallery(m):
        imgs = re.findall(r'!\[([^\]]*)\]\(([^)\s]+)\)', m.group(1))
        cards = ''.join('<a class="slide" href="%s" target="_blank"><img src="%s" alt="%s" loading="lazy"><span>%s · открыть</span></a>'
                        % (src, src, alt, alt) for alt, src in imgs)
        return ('<div class="gallery">%s</div>' if len(imgs) > 1 else '%s') % cards
    h = re.sub(r'<p>((?:!\[[^\]]*\]\([^)\s]+\)\s*)+)</p>', gallery, h)
    h = re.sub(r'<p>Егор: ', '<p class="say"><b>Егор:</b> ', h)
    h = re.sub(r'<p><b>На экране:</b>', '<p class="screen"><b>На экране:</b>', h)
    h = re.sub(r'<p><b>В кадре:</b>', '<p class="screen"><b>В кадре:</b>', h)
    h = re.sub(r'<p><i>(Приём|Техническое):</i>', r'<p class="trick"><i>\1:</i>', h)
    h = re.sub(r'\[([^\]<>]{2,300})\]', r'<mark>[\1]</mark>', h)
    # реплика Егора в несколько абзацев: продолжаем подсветку до закрывающей кавычки
    out, in_say = [], False
    for line in h.split('\n'):
        if line.startswith('<p class="say">'):
            in_say = not re.search(r'»\.?</p>$', line)
        elif in_say and line.startswith('<p>'):
            line = '<p class="say">' + line[3:]
            in_say = not re.search(r'»\.?</p>$', line)
        elif in_say and not line.startswith('<p>'):
            in_say = False
        out.append(line)
    return '\n'.join(out)


def main():
    md = open(SRC, encoding='utf-8').read()
    title = md.splitlines()[0].lstrip('# ').strip()
    parts = re.split(r'\n(?=## )', md.split('\n', 1)[1])
    cards, toc = [], []
    for i, part in enumerate(parts):
        part = part.strip().strip('-').strip()
        if not part:
            continue
        m = re.match(r'## (.+)', part)
        if m:
            head = m.group(1).strip()
            body = part[m.end():].strip().rstrip('-').strip()
            bid = 'b%d' % i
            num, _, name = head.partition('. ')
            toc.append('<a href="#%s">%s</a>' % (bid, html.escape(num if name else head)))
            cards.append('<div class="card" id="%s" data-block="%s"><div class="num">%s</div><h2>%s</h2>%s</div>' % (
                bid, bid, html.escape(num if name else ''), html.escape(name or head), decorate(md_to_html(body))))
        else:  # вступление: как читать
            cards.append('<div class="card general" data-block="intro"><div class="num">Перед чтением</div><h2>Как устроен сценарий</h2>%s</div>'
                         % decorate(md_to_html(part)))
    page = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Сценарий тест-драйва</title><style>%s%s</style></head><body><div class="w">'
            '<h1>Сценарий тест-драйва</h1><p class="lead">%s. Что говорит Егор в каждом уроке. Комментируйте под каждым уроком — правки увидят все.</p>'
            '<div class="who">Как вас подписать: <input id="name" placeholder="Ваше имя" maxlength="40"></div>'
            '<div class="toc">%s</div>%s'
            '<div class="card general" data-block="general"><div class="num">Общее</div><h2>Комментарии ко всему сценарию</h2></div>'
            '<div class="foot">Комментарии обновляются сами каждые 20 секунд. <a href="/course/test_drive_plan.html">План тест-драйва</a></div>'
            '</div><script>%s</script></body></html>') % (STYLE, EXTRA, html.escape(title), ''.join(toc), ''.join(cards), SCRIPT)
    open(OUT, 'w', encoding='utf-8').write(page)
    print('ok', OUT, len(cards), 'блоков')


if __name__ == '__main__':
    main()
