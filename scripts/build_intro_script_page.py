"""Страница с утверждённым скриптом вводного модуля: sources/course/вводный_модуль_скрипт.md -> docs/course/вводный_модуль_скрипт.html

По этому тексту собирается монтаж (build_video_intro_v5.py), поэтому страницу держим рядом с остальными
материалами курса и ссылку ставим в оглавление (materials.html).

Запуск: python scripts/build_intro_script_page.py
"""
import os, sys, html

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P, 'scripts'))
from build_md_pages import md_to_html, CSS

SRC = os.path.join(P, 'sources', 'course', 'вводный_модуль_скрипт.md')
OUT = os.path.join(P, 'docs', 'course', 'вводный_модуль_скрипт.html')
TITLE = 'Вводный модуль — утверждённый скрипт'

EXTRA = ('h2{margin-top:34px;font-size:20px;border-bottom:2px solid #e3e7f0;padding-bottom:6px}'
         'blockquote{margin:0 0 18px;padding:10px 16px;background:#fff1db;border-left:4px solid #f08c00;border-radius:8px;font-size:14px}'
         '.w{max-width:860px}p{font-size:16px}')


def main():
    body = md_to_html(open(SRC, encoding='utf-8').read())
    page = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s</title><style>%s%s</style></head><body><div class="w">'
            '<a class="back" href="/materials.html">← Все материалы</a>%s</div></body></html>'
            % (html.escape(TITLE), CSS, EXTRA, body))
    open(OUT, 'w', encoding='utf-8').write(page)
    print('ok', OUT)


if __name__ == '__main__':
    main()
