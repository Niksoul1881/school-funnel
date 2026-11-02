import re, html, json

md = open('final/st1_v11.md', encoding='utf-8').read()
ov = json.load(open('final/overlap.json', encoding='utf-8'))


def inl(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'==(.+?)==', r'<mark>\1</mark>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[(МЕМ[^\]]*)\]', r'<span class="mem">🖼 \1</span>', s)
    s = re.sub(r'\[([^\]]+)\]', r'<span class="ph">[\1]</span>', s)
    return s


art = []
for para in re.split(r'\n\s*\n', md.strip()):
    if para.startswith('# '):
        art.append('<h1>%s</h1>' % inl(para[2:]))
    else:
        art.append('<p>%s</p>' % '<br>'.join(inl(l) for l in para.split('\n')))


def rows(name):
    out = ''
    for sc, ours, src, theirs in ov[name]['hits']:
        out += '<tr><td class="sc">%d%%</td><td>%s</td><td>%s<div class="src">%s</div></td></tr>' % (
            round(sc * 100), html.escape(ours), html.escape(theirs), html.escape(src))
    return out


CARDS = [
    ('red', 'Статья 1 почти наполовину повторяет Пурвиньша и Муратова.', 'Куски вроде «Дизайнеры делают бесплатные макеты, чтобы набить руку и хоть как-то собрать портфолио» совпадают слово в слово. Пурвиньш и Паутов покупают посевы в тех же каналах, что и вы, и их аудитория уже читала этот текст. Паутова поймали ровно на этом. Плюс риск по авторскому праву. Версия 11 ниже это убирает.'),
    ('red', '«Я сам был таргетологом» — фраза Пурвиньша.', 'В истории Егора из статьи 2 таргетинга нет: склад, четыре бизнеса, найм, автоматизация. Если это неправда, фразу нельзя оставлять. В версии 11 она заменена на реальное: «пять лет пытался зарабатывать на себя».'),
    ('', '«5 минут» и «7 минут».', 'В подзаголовке 7 минут чтения, а через абзац «уйдет всего 5 минут». В версии 11 везде 7.'),
    ('', '«От 5 000 до 50 000» в статье 1 и «от 5 до 70 тысяч» в статье 2.', 'Нужно одно число. В версии 11 стоит 70 000, как в статье 2 и в таблице цен.'),
    ('', '«Уже пошли сотни обычных людей».', 'Это проверяемое утверждение. Нужна реальная цифра учеников, иначе лучше «уже пошли обычные люди без опыта».'),
    ('', 'Статья 1 на «вы», статья 2 на «ты».', 'Человек читает их подряд, и смена обращения заметна. Лучше выбрать одно. Версия 11 оставлена на «вы», как у Егора, чтобы не ломать его правку.'),
    ('', 'Статья 2: «Мест в группе: 7 из 10».', 'Можно, только если счётчик живой и показывает реальные места. Цифра, поставленная руками, — тот самый фальшивый дефицит, от которого вы отстраиваетесь.'),
    ('', 'Статья 2: кейсы Сергея, Марины, Ирины, Ольги и Дмитрия', 'стоят с пометкой «пример, заменить на реальный». До публикации — заменить реальными учениками с согласия или убрать.'),
    ('', 'Статья 2: порядок уроков.', 'В статье «первого бота соберёшь на втором уроке», а в списке «за 48 часов ты» сборка бота идёт третьим пунктом. В сообщениях бота уроки так: 1 — фриланс, 2 — первый бот, 3 — профессия. Список в статье лучше выровнять.'),
    ('', 'Статья 2, мелочь.', '«В худшем случае… В лучшем — эти два дня станут началом новой жизни» и «Первый — закрыть статью и попробовать самостоятельно» почти дословно из Муратова. Вариант: «Самое большее, что ты теряешь, — два вечера. А можешь получить профессию, которая через полгода будет кормить» и «Первый вариант — разбираться самому по роликам».'),
]
cards = ''.join('<div class="card %s"><b>%s</b> %s</div>' % (c, html.escape(t), html.escape(d)) for c, t, d in CARDS)

CSS = '''*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",Roboto,Arial,sans-serif;font-size:15.5px;line-height:1.55;color:#1d2433;background:#f4f6fb}
.wrap{max-width:1000px;margin:0 auto;padding:0 20px}
.hero{background:linear-gradient(135deg,#14182e 0%,#2b2f6b 60%,#e03131 160%);color:#fff;padding:44px 20px 40px}
.hero h1{font-size:32px;margin:0 0 10px;line-height:1.15}.hero p{margin:0;font-size:17px;opacity:.93;max-width:800px}
h2{font-size:25px;margin:34px 0 10px;color:#14182e}
.stats{display:flex;flex-wrap:wrap;margin:18px -8px 0}.stat{flex:1 1 200px;margin:0 8px 12px;background:#fff;border-radius:12px;padding:14px 18px;box-shadow:0 2px 10px rgba(31,42,90,.07)}
.stat b{display:block;font-size:26px;color:#e03131}.stat.ok b{color:#2b8a3e}.stat span{font-size:14px;color:#5c6478}
.card{background:#fff;border-radius:12px;padding:14px 18px;margin-bottom:10px;box-shadow:0 2px 10px rgba(31,42,90,.06);border-left:4px solid #f59f00}
.card.red{border-left-color:#e03131}.card b{color:#14182e}
article{background:#fff;border-radius:10px;padding:36px 44px;box-shadow:0 2px 14px rgba(31,42,90,.07);font-family:Georgia,serif;font-size:18px;line-height:1.7}
article h1{font-family:"Segoe UI",Arial,sans-serif;font-size:28px;line-height:1.25}
mark{background:#d3f9d8;padding:0 2px;border-radius:3px}
.mem{display:inline-block;background:#f3f0ff;border:1px dashed #9775fa;color:#5f3dc4;border-radius:6px;padding:2px 8px;font:14px "Segoe UI",Arial,sans-serif}
.ph{background:#fff3bf;color:#7a5a00;border-radius:3px;padding:0 3px}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}th,td{padding:8px 10px;border-bottom:1px solid #edf0f6;text-align:left;vertical-align:top}
th{background:#f7f8fc;font-size:12.5px}td.sc{font-weight:700;color:#e03131;white-space:nowrap}.src{font-size:12px;color:#8a91a5;margin-top:3px}
details{margin:10px 0}summary{cursor:pointer;font-weight:700}
.legend{font-size:14px;color:#5c6478;margin:6px 0 14px}
@media(max-width:640px){article{padding:22px 16px;font-size:16.5px}.hero h1{font-size:25px}}'''

page = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Проверка финальных статей</title><style>' + CSS + '</style></head><body>'
        '<div class="hero"><div class="wrap"><h1>Проверка финальных статей перед запуском</h1>'
        '<p>Статья 1 — правка Егора v10, статья 2 — v9. Каждое предложение сравнено со статьями Пурвиньша и Муратова. Ниже — что поправить, и статья 1 в версии 11: та же структура, те же смыслы и тот же голос, совпадающие куски переписаны своими словами.</p></div></div>'
        '<div class="wrap"><div class="stats">'
        '<div class="stat"><b>46 из 111</b><span>предложений статьи 1 (v10) почти совпадают с конкурентами</span></div>'
        '<div class="stat ok"><b>4 из 85</b><span>в версии 11, и это общие фразы</span></div>'
        '<div class="stat ok"><b>9 из 223</b><span>в статье 2: она почти полностью своя</span></div></div>'
        '<h2>Что поправить</h2>' + cards +
        '<h2>Статья 1, версия 11</h2><p class="legend">Зелёным — предложения, переписанные своими словами. Всё остальное — текст Егора без изменений. Блоки и мемы на тех же местах.</p>'
        '<article>' + '\n'.join(art) + '</article>'
        '<h2>Все совпадения в v10</h2>'
        '<details><summary>Статья 1 (v10): 46 предложений — открыть таблицу</summary><table><tr><th>Сходство</th><th>У нас (v10)</th><th>У конкурента</th></tr>' + rows('Статья 1 (v10)') + '</table></details>'
        '<details><summary>Статья 2 (v9): 9 предложений — открыть таблицу</summary><table><tr><th>Сходство</th><th>У нас (v9)</th><th>У конкурента</th></tr>' + rows('Статья 2 (v9)') + '</table></details>'
        '<p class="legend" style="margin-top:20px">Как считали: каждое предложение длиннее 35 знаков сравнивали со всеми предложениями статей Пурвиньша и Муратова. В таблицу попало всё, что похоже больше чем на 60%.</p>'
        '</div><div style="height:50px"></div></body></html>')
open(r'C:/Users/NikSouk/Desktop/Proj/articles_final_review.html', 'w', encoding='utf-8').write(page)
print('ok')
