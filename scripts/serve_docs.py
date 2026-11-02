"""Раздаёт папку docs/ по паролю (для команды). Папка private/ наружу не попадает.
Запуск: python scripts/serve_docs.py  -> http://localhost:8787  (логин team, пароль в private/web_auth.txt)
"""
import os, base64, secrets, html, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(P, 'docs')
AUTH_FILE = os.path.join(P, 'private', 'web_auth.txt')
PORT = 8787

if not os.path.exists(AUTH_FILE):
    open(AUTH_FILE, 'w').write('team:' + secrets.token_urlsafe(9))
USER, PWD = open(AUTH_FILE).read().strip().split(':', 1)
TOKEN = base64.b64encode(('%s:%s' % (USER, PWD)).encode()).decode()

TITLES = {
    'доска_воронок.html': 'Доска воронок конкурентов (обновляется сама)',
    'воронки_конкурентов.html': 'Воронки конкурентов: всё, что известно',
    'сайты_конкурентов.html': 'Сайты конкурентов: как попасть в воронку (формы, звонки, боты)',
    'пурвиньш_этап1.html': 'Пурвиньш: первый этап воронки по минутам',
    'журнал_прохождения.html': 'Журнал прохождения ботов',
    'ленивая_ветка.html': 'Ленивая ветка: дожимы',
    'схемы_воронок.html': 'Схемы воронок по этапам: стрелки и интервалы по каждому боту',
    'хронология_воронок.html': 'Хронология воронок: все сообщения по порядку',
    'competitors.html': 'Анализ конкурентов',
    'content_plan.html': 'Каналы конкурентов: рубрики, серии, прогревы',
    'articles_final_review.html': 'Проверка финальных статей',
    'articles_v2.html': 'Статьи воронки (с комментариями)',
    'articles_v4_read.html': 'Статьи воронки — чистовик',
    'bot_messages_v2.html': 'Сообщения нашего бота',
    'bot_templates.html': 'Шаблоны ботов для конструктора',
    'funnel_texts.html': 'Тексты воронки v1',
    'content_strategy.html': 'Стратегия канала: 3 стиля',
    'egor_10_posts.html': 'Канал Егора: 10 постов',
    'manekken_relaunch.html': 'Перезапуск Манекена',
    'test_drive_plan.html': 'План тест-драйва (с комментариями)',
    'test_drive_script.html': 'Сценарий тест-драйва: что говорит Егор (с комментариями)',
    'slides_deck.html': 'Слайды тест-драйва — вся колода в одном стиле',
    'test_drive_v2.html': '★ Сценарий v2 по структуре Егора (24.10): редактор + слайды (правки сохраняются на сайт)',
    'test_drive_v2_read.html': 'Сценарий v2 — версия для чтения на съёмке (текст + слайды, комментарии)',
    'slides_v2.html': 'Слайды v2 — под сценарий Егора (вводный + 6 уроков)',
    'course_program.html': 'Программа курса',
    'course_program_full.html': 'Программа курса (полная)',
    'sales_catalog.html': 'Каталог проектов команды',
}


def build_index():
    groups = []
    for sub, name in (('research', 'Исследования'), ('funnel', 'Воронка'), ('content', 'Контент'), ('course', 'Курс'), ('final', 'Финальные статьи')):
        d = os.path.join(DOCS, sub)
        if not os.path.isdir(d):
            continue
        items = []
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith(('.html', '.pdf', '.md')):
                continue
            title = TITLES.get(f, f)
            items.append('<a href="/%s/%s">%s</a>' % (sub, urllib.parse.quote(f), html.escape(title)))
        if items:
            groups.append('<h2>%s</h2>%s' % (name, ''.join(items)))
    page = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Школа: материалы команды</title><style>body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#f4f6fb;color:#1d2433}'
            '.w{max-width:820px;margin:0 auto;padding:30px 20px}h1{margin:0 0 6px}h2{margin:26px 0 8px;font-size:18px;color:#5c6478}'
            'a{display:block;background:#fff;border-radius:12px;padding:12px 16px;margin:8px 0;color:#14182e;text-decoration:none;box-shadow:0 2px 8px rgba(20,24,46,.06)}'
            'a:hover{background:#fff1db}.hl{border-left:5px solid #f08c00;font-weight:700}</style></head><body><div class="w">'
            '<h1>Материалы команды</h1><p>Исследования конкурентов, воронка, контент и курс.</p>%s</div></body></html>') % ''.join(groups)
    page = page.replace('<a href="/research/%s"' % urllib.parse.quote('доска_воронок.html'),
                        '<a class="hl" href="/research/%s"' % urllib.parse.quote('доска_воронок.html'))
    open(os.path.join(DOCS, 'materials.html'), 'w', encoding='utf-8').write(page)


import sys, json, re, threading
from datetime import datetime
OPEN = '--open' in sys.argv  # без пароля: python scripts/serve_docs.py --open

# Комментарии команды к страницам: хранятся в data/comments/<страница>.json (не в docs/, наружу файлом не отдаются)
COMMENTS = os.path.join(P, 'data', 'comments')
os.makedirs(COMMENTS, exist_ok=True)
LOCK = threading.Lock()


def comments_file(page):
    page = re.sub(r'[^\w-]', '_', page)[:60] or 'page'
    return os.path.join(COMMENTS, page + '.json')


def load_comments(page):
    f = comments_file(page)
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else []


def edits_file(page):
    os.makedirs(os.path.join(os.path.dirname(COMMENTS), 'edits'), exist_ok=True)
    return os.path.join(os.path.dirname(COMMENTS), 'edits', (re.sub(r'[^\w-]', '_', page)[:60] or 'page') + '.json')


def load_edits(page):
    f = edits_file(page)
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {'by': {}, 'log': []}


class H(SimpleHTTPRequestHandler):
    def _auth_ok(self):
        if not OPEN and self.headers.get('Authorization') != 'Basic ' + TOKEN:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="team"')
            self.end_headers()
            self.wfile.write('Нужен логин и пароль'.encode('utf-8'))
            return False
        return True

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if not self._auth_ok():
            return
        u = urllib.parse.urlparse(self.path)
        if u.path == '/api/edits':
            return self._post_edits()
        if u.path != '/api/comments':
            return self._json({'error': 'not found'}, 404)
        n = int(self.headers.get('Content-Length') or 0)
        if n > 100000:
            return self._json({'error': 'слишком длинно'}, 413)
        try:
            d = json.loads(self.rfile.read(n).decode('utf-8'))
        except Exception:
            return self._json({'error': 'bad json'}, 400)
        page = str(d.get('page', ''))
        with LOCK:
            items = load_comments(page)
            if d.get('delete'):  # удалить можно только свой комментарий (по секрету автора из браузера)
                items = [c for c in items if not (c['id'] == d['delete'] and c.get('key') == d.get('key'))]
            else:
                text = str(d.get('text', '')).strip()[:20000]
                if not text:
                    return self._json({'error': 'пусто'}, 400)
                items.append({'id': '%d' % (datetime.now().timestamp() * 1000), 'block': str(d.get('block', ''))[:60],
                              'name': (str(d.get('name', '')).strip() or 'Без имени')[:40], 'text': text,
                              'time': datetime.now().strftime('%d.%m %H:%M'), 'key': str(d.get('key', ''))[:40]})
            json.dump(items, open(comments_file(page), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return self._json([{k: v for k, v in c.items() if k != 'key'} for c in items])

    def _post_edits(self):
        """Правки из редактора сценария (test_drive_v2): у каждого автора своё состояние {items, added}, хранится целиком."""
        n = int(self.headers.get('Content-Length') or 0)
        if n > 1500000:
            return self._json({'error': 'слишком много'}, 413)
        try:
            d = json.loads(self.rfile.read(n).decode('utf-8'))
        except Exception:
            return self._json({'error': 'bad json'}, 400)
        page = str(d.get('page', ''))
        name = (str(d.get('name', '')).strip() or 'Без имени')[:40]
        state = d.get('state') or {}
        if not isinstance(state, dict):
            return self._json({'error': 'bad state'}, 400)
        with LOCK:
            data = load_edits(page)
            data['by'][name] = {'items': state.get('items') or {}, 'added': state.get('added') or {},
                                'savedAt': datetime.now().strftime('%d.%m %H:%M')}
            data['log'].append({'name': name, 'time': datetime.now().strftime('%d.%m %H:%M')})
            json.dump(data, open(edits_file(page), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return self._json(data)

    def do_GET(self):
        if not self._auth_ok():
            return
        u = urllib.parse.urlparse(self.path)
        if u.path == '/api/edits':
            return self._json(load_edits(urllib.parse.parse_qs(u.query).get('page', [''])[0]))
        if u.path == '/api/comments':
            page = urllib.parse.parse_qs(u.query).get('page', [''])[0]
            return self._json([{k: v for k, v in c.items() if k != 'key'} for c in load_comments(page)])
        if self.path in ('/', '/index.html'):  # по ссылке сразу доска со схемами ботов
            self.send_response(302)
            self.send_header('Location', '/research/' + urllib.parse.quote('доска_воронок.html'))
            self.end_headers()
            return
        if self.path == '/materials.html':
            build_index()
        return super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    build_index()
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), partial(H, directory=DOCS))
    print('http://localhost:%d  логин %s' % (PORT, USER))
    srv.serve_forever()
