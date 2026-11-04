"""Generated files for the «Витрина товаров» Telegram Mini App."""
SHOP_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>__TITLE__</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div id="app"></div>
<script>window.__CONTENT__ = __CONTENT_JSON__;</script>
<script src="app.js"></script>
</body>
</html>
'''

SHOP_CSS = '''@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--accent:#c9825b;--ink:#211a15;--muted:#8c7d70;--soft:#f7f1e8;--line:#eadfd2;--card:#fffdf9}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--soft);color:var(--ink);font-family:Manrope,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.app{max-width:480px;margin:0 auto;min-height:100vh;background:var(--soft);padding-bottom:92px;position:relative}
.hero{padding:22px 20px 20px;background:linear-gradient(145deg,var(--accent),#8b5d45);color:#fff;border-radius:0 0 30px 30px;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;width:180px;height:180px;border-radius:50%;background:rgba(255,255,255,.12);right:-60px;top:-80px}
.hero .kicker{font-size:9px;letter-spacing:.18em;text-transform:uppercase;opacity:.75;font-weight:800}
.hero h1{font-size:29px;line-height:1.02;letter-spacing:-.04em;margin:9px 0 7px;max-width:320px}
.hero p{margin:0;font-size:12.5px;line-height:1.5;opacity:.82;max-width:300px}
.hero .top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
.hero .bag{border:1px solid rgba(255,255,255,.35);background:rgba(255,255,255,.12);color:#fff;border-radius:999px;padding:8px 12px;font:700 11px Manrope;backdrop-filter:blur(8px)}
.cats{display:flex;gap:7px;overflow:auto;padding:14px 16px 4px;scrollbar-width:none}
.cats::-webkit-scrollbar{display:none}
.cats button{white-space:nowrap;border:1px solid var(--line);background:#fffdf9;color:var(--muted);border-radius:999px;padding:8px 12px;font:700 11px Manrope;cursor:pointer}
.cats button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px 14px 20px}
.product{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;cursor:pointer;position:relative}
.product .art{height:118px;display:grid;place-items:center;font-size:44px;background:linear-gradient(135deg,#f1dfcc,#e7cdb6);overflow:hidden}
.art img,.detail-art img{width:100%;height:100%;object-fit:cover;display:block}
.product .art.c1{background:linear-gradient(135deg,#f6d9c6,#e7b89b)}
.product .art.c2{background:linear-gradient(135deg,#e8d8c4,#cdb69d)}
.product .art.c3{background:linear-gradient(135deg,#e6d6e0,#cdb4c6)}
.product .body{padding:9px 10px 10px}
.product h3{font-size:12px;line-height:1.25;margin:0 0 3px;font-weight:800}
.product .desc{font-size:9px;color:var(--muted);line-height:1.4;height:26px;overflow:hidden;margin:0}
.product .price{display:flex;align-items:center;justify-content:space-between;margin-top:7px;font-weight:800;font-size:12px;color:var(--accent)}
.product .plus{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;background:var(--ink);color:#fff;font-size:14px}
.empty{padding:40px 16px;text-align:center;color:var(--muted);font-size:12px}
.cartbar{position:fixed;left:0;right:0;bottom:0;z-index:30;max-width:480px;margin:0 auto;padding:10px 14px 18px;background:linear-gradient(transparent,rgba(247,241,232,.96) 32%);display:none}
.cartbar.on{display:block}
.cartbar button{width:100%;border:0;border-radius:16px;padding:14px 16px;background:var(--ink);color:#fff;display:flex;justify-content:space-between;align-items:center;font:800 13px Manrope;box-shadow:0 14px 30px rgba(33,26,21,.22)}
.cartbar .n{background:var(--accent);border-radius:999px;padding:2px 7px;font-size:10px;margin-right:6px}
.sheet{position:fixed;inset:0;z-index:50;background:rgba(25,18,12,.5);display:none;align-items:flex-end;justify-content:center;backdrop-filter:blur(2px)}
.sheet.on{display:flex}
.sheet .box{width:100%;max-width:480px;max-height:88vh;overflow:auto;background:var(--soft);border-radius:24px 24px 0 0;padding:10px 16px 28px;animation:up .22s ease}
@keyframes up{from{transform:translateY(30px);opacity:.6}to{transform:none;opacity:1}}
.sheet .grab{width:38px;height:4px;border-radius:99px;background:#d9c9b9;margin:4px auto 12px}
.sheet h2{font-size:22px;letter-spacing:-.04em;margin:0 0 5px}
.sheet .close{float:right;border:0;background:#fff;width:30px;height:30px;border-radius:50%;font-size:17px;color:var(--muted)}
.detail-art{height:190px;border-radius:18px;display:grid;place-items:center;font-size:82px;background:linear-gradient(135deg,#f1dfcc,#e7cdb6);margin:6px 0 12px;overflow:hidden}
.detail p{font-size:12px;line-height:1.6;color:var(--muted)}
.row{display:flex;align-items:center;justify-content:space-between;gap:10px}
.qty{display:flex;align-items:center;gap:12px;border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 10px}
.qty button{border:0;background:none;font-size:18px;color:var(--ink);width:22px}
.qty b{font-size:13px;min-width:16px;text-align:center}
.btn{border:0;border-radius:13px;padding:13px 16px;background:var(--accent);color:#fff;font:800 12px Manrope;cursor:pointer}
.btn.dark{background:var(--ink)}
.btn.full{width:100%;margin-top:10px}
.cart-item{display:flex;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)}
.cart-item .emoji{width:46px;height:46px;border-radius:12px;background:#f0dfcd;display:grid;place-items:center;font-size:23px;flex:none}
.cart-item .info{flex:1;min-width:0}
.cart-item b{display:block;font-size:11px}
.cart-item span{font-size:10px;color:var(--muted)}
.cart-item .sum{font-weight:800;font-size:11px;color:var(--accent)}
.total{display:flex;justify-content:space-between;padding:14px 0 4px;font-weight:800;font-size:15px}
.field{margin-top:9px}
.field label{display:block;font-size:10px;font-weight:700;color:#5f5247;margin-bottom:4px}
.field input,.field textarea,.field select{width:100%;border:1px solid var(--line);border-radius:10px;background:#fffdf9;padding:11px;font:12px Manrope;color:var(--ink);outline:none}
.field textarea{min-height:54px;resize:vertical}
.delivery{font-size:9.5px;color:var(--muted);line-height:1.5;white-space:pre-line;margin-top:8px}
.success{text-align:center;padding:34px 12px}
.success .big{font-size:52px;margin-bottom:8px}
.success h2{margin-bottom:5px}
.success p{font-size:12px;color:var(--muted);line-height:1.6}
'''

SHOP_JS = r'''(function(){
  const c = window.__CONTENT__;
  const app = document.getElementById('app');
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const eur = (v) => String(v ?? '').trim();
  const num = (v) => Number(String(v).replace(/[^\d]/g, '')) || 0;
  const money = (v) => new Intl.NumberFormat('ru-RU').format(v) + ' ₽';
  const priceText = (v) => /^\d/.test(String(v ?? '').trim()) ? money(num(v)) : String(v ?? '');
  const tg = window.Telegram?.WebApp;
  if (tg) { tg.ready(); tg.expand(); }
  let activeCat = 'Все';
  let cart = [];

  function categories(){ return ['Все', ...(c.categories || [])]; }
  function visible(){ return activeCat === 'Все' ? c.products : c.products.filter(p => p.category === activeCat); }
  function qtyOf(id){ return cart.find(x => x.id === id)?.qty || 0; }
  function total(){ return cart.reduce((s,x) => s + num(x.price) * x.qty, 0); }
  function count(){ return cart.reduce((s,x) => s + x.qty, 0); }

  function add(id){
    const p = c.products.find(x => x.id === id); if (!p) return;
    const row = cart.find(x => x.id === id);
    if (row) row.qty += 1; else cart.push({...p, qty: 1});
    render(); openCart(false);
  }
  function inc(id, d){
    const row = cart.find(x => x.id === id); if (!row) return;
    row.qty += d;
    if (row.qty <= 0) cart = cart.filter(x => x.id !== id);
    render(); openCart(false);
  }

  function art(p, big){
    const cls = big ? 'detail-art' : 'art c' + (Number(p.id) % 3 + 1);
    const inner = p.image ? `<img src="${esc(p.image)}" alt="">` : esc(p.emoji || '🛍️');
    return `<div class="${cls}">${inner}</div>`;
  }

  function home(){
    return `<header class="hero">
      <div class="top"><div><div class="kicker">${esc(c.business.niche)}</div><h1>${esc(c.business.name)}</h1></div><button class="bag" data-open-cart>Корзина · ${count()}</button></div>
      <p>${esc(c.greeting)}</p>
    </header>
    <div class="cats">${categories().map(cat => `<button class="${cat===activeCat?'on':''}" data-cat="${esc(cat)}">${esc(cat)}</button>`).join('')}</div>
    <div class="grid">${visible().map(p => `<article class="product" data-product="${p.id}">
      ${art(p)}
      <div class="body"><h3>${esc(p.title)}</h3><p class="desc">${esc(p.description || '')}</p>
      <div class="price"><span>${esc(priceText(p.price))}</span><span class="plus">+</span></div></div>
    </article>`).join('') || '<div class="empty">В этой категории пока пусто.</div>'}</div>
    <div class="cartbar ${count() ? 'on' : ''}"><button data-open-cart><span><span class="n">${count()}</span>Корзина</span><span>${money(total())}</span></button></div>`;
  }

  function productSheet(id){
    const p = c.products.find(x => x.id === id); if (!p) return;
    return `<div class="sheet on" data-sheet><div class="box"><div class="grab"></div><button class="close" data-close>×</button>
      ${art(p, true)}
      <h2>${esc(p.title)}</h2><p>${esc(p.description || '')}</p>
      <div class="row" style="margin-top:14px"><b style="font-size:20px;color:var(--accent)">${esc(priceText(p.price))}</b><div class="qty"><button data-minus="${p.id}">−</button><b>${qtyOf(p.id) || 1}</b><button data-add="${p.id}">+</button></div></div>
      <button class="btn full" data-add="${p.id}">В корзину · ${esc(priceText(p.price))}</button>
    </div></div>`;
  }

  function cartSheet(){
    if (!cart.length) return '';
    return `<div class="sheet on" data-sheet><div class="box"><div class="grab"></div><button class="close" data-close>×</button>
      <h2>Корзина</h2>
      ${cart.map(x => `<div class="cart-item"><div class="emoji">${esc(x.emoji || '🛍️')}</div><div class="info"><b>${esc(x.title)}</b><span>${esc(priceText(x.price))}</span></div><div class="qty"><button data-minus="${x.id}">−</button><b>${x.qty}</b><button data-add="${x.id}">+</button></div><div class="sum">${money(num(x.price)*x.qty)}</div></div>`).join('')}
      <div class="total"><span>Итого</span><span>${money(total())}</span></div>
      <form id="checkout">
        <div class="field"><label>Имя</label><input name="name" required placeholder="Как вас зовут"></div>
        <div class="field"><label>Телефон</label><input name="phone" required inputmode="tel" placeholder="+7 ..."></div>
        <div class="field"><label>Получение</label><select name="delivery"><option>Самовывоз</option><option>Доставка</option></select></div>
        <div class="field"><label>Адрес / комментарий</label><textarea name="address" placeholder="Если доставка — адрес; если самовывоз — удобное время"></textarea></div>
        <div class="delivery">${esc((c.delivery || []).join('\n'))}</div>
        <button class="btn dark full" type="submit">Оформить заказ</button>
      </form>
    </div></div>`;
  }

  function success(name){
    return `<div class="sheet on" data-sheet><div class="box"><div class="grab"></div><div class="success"><div class="big">✓</div><h2>Заказ принят</h2><p>${esc(name)}, спасибо! Мы свяжемся с вами, чтобы подтвердить заказ и время.</p><button class="btn full" data-close>Готово</button></div></div></div>`;
  }

  function render(sheet){
    app.innerHTML = `<div class="app">${home()}${sheet || ''}</div>`;
    app.querySelectorAll('[data-cat]').forEach(b => b.onclick = () => { activeCat = b.dataset.cat; render(); });
    app.querySelectorAll('[data-product]').forEach(el => el.onclick = () => render(productSheet(Number(el.dataset.product))));
    app.querySelectorAll('[data-open-cart]').forEach(b => b.onclick = () => openCart(true));
    app.querySelectorAll('[data-add]').forEach(b => b.onclick = (e) => { e.stopPropagation(); add(Number(b.dataset.add)); });
    app.querySelectorAll('[data-minus]').forEach(b => b.onclick = (e) => { e.stopPropagation(); inc(Number(b.dataset.minus), -1); });
    app.querySelectorAll('[data-close]').forEach(b => b.onclick = () => render());
    const form = app.querySelector('#checkout');
    if (form) form.onsubmit = submit;
  }

  function openCart(showEmpty){
    if (!cart.length && !showEmpty) return;
    render(cartSheet());
  }

  function submit(e){
    e.preventDefault();
    const fd = new FormData(e.target);
    const order = {name: fd.get('name'), phone: fd.get('phone'), delivery: fd.get('delivery'), address: fd.get('address'), items: cart.map(x => ({title:x.title, price:priceText(x.price), qty:x.qty})), total: money(total()), business: c.business.name};
    const text = `Заказ: ${c.business.name}\n${order.items.map(x => `${x.title} × ${x.qty} — ${x.price}`).join('\n')}\nИтого: ${order.total}\nИмя: ${order.name}\nТелефон: ${order.phone}\n${order.delivery}\n${order.address || ''}`;
    if (tg?.sendData) { tg.sendData(JSON.stringify(order)); }
    else { console.log('ORDER', order); }
    cart = [];
    render(success(order.name));
  }

  render();
})();
'''
SHOP_BOT_PY = r'''"""Бот-витрина: открывает Mini App и принимает заказ."""
import asyncio
import json
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    if not WEBAPP_URL:
        await message.answer("Витрина ещё не подключена: задайте WEBAPP_URL в .env")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Открыть витрину", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])
    await message.answer("Выбирайте товары — заказ придёт нам в Telegram.", reply_markup=keyboard)


@dp.message(F.web_app_data)
async def order(message: Message) -> None:
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("Не удалось прочитать заказ. Напишите администратору.")
        return
    lines = [f"Новый заказ: {data.get('business', '')}"]
    for item in data.get("items", []):
        lines.append(f"• {item.get('title')} × {item.get('qty')} — {item.get('price')}")
    lines += [f"Итого: {data.get('total')}", f"Имя: {data.get('name')}", f"Телефон: {data.get('phone')}", f"{data.get('delivery')}: {data.get('address', '')}"]
    text = "\n".join(lines)
    if ADMIN_CHAT_ID:
        try:
            await message.bot.send_message(int(ADMIN_CHAT_ID), text)
        except Exception as exc:
            print(f"admin send error: {exc}")
    await message.answer("Заказ принят! Мы свяжемся с вами.")


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''
SHOP_CATALOG_BOT_PY = r'''"""Витрина в чате: фото товаров, корзина и заказ администратору."""
import asyncio
import html
import json
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()
CONTENT = json.loads(Path(__file__).with_name("content.json").read_text(encoding="utf-8"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
PRODUCTS = {int(p["id"]): p for p in CONTENT["products"]}
dp = Dispatcher()
bot = None


class Checkout(StatesGroup):
    name = State()
    phone = State()
    confirm = State()


def categories_kb():
    rows = []
    cats = ["Все"] + list(CONTENT.get("categories", []))
    for index in range(0, len(cats), 2):
        rows.append([InlineKeyboardButton(text=cats[i], callback_data="cat:" + cats[i]) for i in range(index, min(index + 2, len(cats)))])
    rows.append([InlineKeyboardButton(text="Корзина", callback_data="cart")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_kb(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В корзину", callback_data=f"add:{product_id}")],
        [InlineKeyboardButton(text="← Каталог", callback_data="catalog"), InlineKeyboardButton(text="Корзина", callback_data="cart")],
    ])


def cart_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="Очистить", callback_data="clear"), InlineKeyboardButton(text="← Каталог", callback_data="catalog")],
    ])


def caption(product):
    return f"<b>{html.escape(product['title'])}</b>\n{html.escape(product['price'])}\n\n{html.escape(product.get('description', ''))}"


async def send_product(chat_id, product):
    keyboard = product_kb(product["id"])
    if product.get("image"):
        try:
            await bot.send_photo(chat_id, product["image"], caption=caption(product), parse_mode="HTML", reply_markup=keyboard)
            return
        except Exception as exc:
            print(f"photo error: {exc}")
    await bot.send_message(chat_id, caption(product), parse_mode="HTML", reply_markup=keyboard)


async def show_catalog(message, category="Все"):
    items = list(PRODUCTS.values()) if category == "Все" else [p for p in PRODUCTS.values() if p["category"] == category]
    await message.answer(f"Каталог: {category}. Выберите товар — покажу фото и цену.", reply_markup=categories_kb())
    for product in items[:12]:
        await send_product(message.chat.id, product)


def cart_total(cart):
    return sum(int("".join(ch for ch in PRODUCTS[int(pid)]["price"] if ch.isdigit()) or 0) * qty for pid, qty in cart.items())


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(CONTENT["greeting"])
    await message.answer("Выберите категорию:", reply_markup=categories_kb())
    for product in list(PRODUCTS.values())[:3]:
        await send_product(message.chat.id, product)


@dp.callback_query(F.data.startswith("cat:"))
async def choose_category(call: CallbackQuery) -> None:
    await show_catalog(call.message, call.data.split(":", 1)[1])
    await call.answer()


@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery) -> None:
    await show_catalog(call.message, "Все")
    await call.answer()


@dp.callback_query(F.data.startswith("prod:"))
async def product_card(call: CallbackQuery) -> None:
    product = PRODUCTS.get(int(call.data.split(":", 1)[1]))
    if product:
        await send_product(call.message.chat.id, product)
    await call.answer()


@dp.callback_query(F.data.startswith("add:"))
async def add_to_cart(call: CallbackQuery, state: FSMContext) -> None:
    product_id = call.data.split(":", 1)[1]
    data = await state.get_data()
    cart = dict(data.get("cart", {}))
    cart[product_id] = cart.get(product_id, 0) + 1
    await state.update_data(cart=cart)
    await call.answer("Добавлено в корзину")


@dp.callback_query(F.data == "cart")
async def show_cart(call: CallbackQuery, state: FSMContext) -> None:
    cart = (await state.get_data()).get("cart", {})
    if not cart:
        await call.message.answer("Корзина пустая. Выберите товар в каталоге.", reply_markup=categories_kb())
        await call.answer()
        return
    lines = []
    for pid, qty in cart.items():
        product = PRODUCTS[int(pid)]
        lines.append(f"• {product['title']} × {qty} — {product['price']}")
    await call.message.answer("Корзина:\n\n" + "\n".join(lines) + f"\n\nИтого: {cart_total(cart)} ₽", reply_markup=cart_kb())
    await call.answer()


@dp.callback_query(F.data == "clear")
async def clear_cart(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(cart={})
    await call.message.answer("Корзина очищена.", reply_markup=categories_kb())
    await call.answer()


@dp.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery, state: FSMContext) -> None:
    cart = (await state.get_data()).get("cart", {})
    if not cart:
        await call.answer("Сначала добавьте товар", show_alert=True)
        return
    await state.set_state(Checkout.name)
    await call.message.answer("Как вас зовут?")
    await call.answer()


@dp.message(Checkout.name)
async def checkout_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Напишите имя.")
        return
    await state.update_data(name=name)
    await state.set_state(Checkout.phone)
    await message.answer("Телефон для связи:")


@dp.message(Checkout.phone)
async def checkout_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if sum(ch.isdigit() for ch in phone) < 10:
        await message.answer("Проверьте номер и напишите ещё раз.")
        return
    data = await state.get_data()
    data["phone"] = phone
    await state.update_data(phone=phone)
    cart = data.get("cart", {})
    lines = [f"• {PRODUCTS[int(pid)]['title']} × {qty} — {PRODUCTS[int(pid)]['price']}" for pid, qty in cart.items()]
    await state.set_state(Checkout.confirm)
    await message.answer(
        f"Имя: {data.get('name')}\nТелефон: {phone}\n\n" + "\n".join(lines) + f"\n\nИтого: {cart_total(cart)} ₽",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подтвердить", callback_data="order")], [InlineKeyboardButton(text="Отменить", callback_data="clear")]]),
    )


@dp.callback_query(F.data == "order")
async def place_order(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    cart = data.get("cart", {})
    lines = [f"• {PRODUCTS[int(pid)]['title']} × {qty} — {PRODUCTS[int(pid)]['price']}" for pid, qty in cart.items()]
    text = f"Новый заказ\n\n" + "\n".join(lines) + f"\n\nИтого: {cart_total(cart)} ₽\nИмя: {data.get('name')}\nТелефон: {data.get('phone')}\nTelegram: @{call.from_user.username or '—'}"
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(int(ADMIN_CHAT_ID), text)
        except Exception as exc:
            print(f"admin error: {exc}")
    await state.clear()
    await call.message.answer(f"Заказ принят, {data.get('name')}! Мы свяжемся с вами.")
    await call.answer("Готово")


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен.")
    global bot
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''
