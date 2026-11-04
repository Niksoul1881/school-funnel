const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const state = { templates: [], bots: [], current: null, selected: null, history: {}, busy: false };

async function api(url, opts) {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) {
    const data = await r.json().catch(() => ({}));
    throw new Error(data.detail || 'Ошибка');
  }
  return r.json();
}

function toast(text) {
  const el = $('#toast');
  el.textContent = text;
  el.classList.add('on');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove('on'), 2200);
}

function templateOf(id) { return state.templates.find((t) => t.id === id); }

async function loadTemplates() {
  state.templates = (await api('/api/templates')).templates;
}

async function loadBots() {
  state.bots = (await api('/api/bots')).bots;
  renderBots();
  if (!state.bots.length && state.templates.length) {
    for (const t of state.templates) {
      await createBot(t.id, t.defaults, true);
    }
    state.bots = (await api('/api/bots')).bots;
    renderBots();
  }
  if (!state.current && state.bots.length) openBot(state.bots[0].id);
}

function renderBots() {
  $('#bots').innerHTML = state.bots.map((b) => {
    const t = templateOf(b.template) || {};
    return `<button class="bot ${b.id === state.current ? 'on' : ''}" data-bot="${b.id}">
      <span class="ico">${esc(t.icon || '🤖')}</span><span><b>${esc(b.name)}</b><span>${esc(t.name || b.template)}</span></span>
    </button>`;
  }).join('');
  $$('[data-bot]').forEach((el) => el.onclick = () => openBot(el.dataset.bot));
}

async function createBot(template, brief, silent = false) {
  const data = await api('/api/bots', { method: 'POST', body: JSON.stringify({ template, brief }) });
  if (!silent) toast('Бот собран');
  return data.bot;
}

async function openBot(id) {
  state.current = id;
  renderBots();
  $('#empty').classList.add('hidden');
  $('#chat').classList.remove('hidden');
  const { bot } = await api('/api/bots/' + id);
  const t = templateOf(bot.template);
  $('#chat-avatar').textContent = (bot.name || 'Б').slice(0, 1);
  $('#chat-avatar').style.background = t?.accent || '#ff6b8a';
  $('#chat-name').textContent = bot.name;
  $('#chat-sub').textContent = `${t?.name || ''} · онлайн`;
  renderBrief(bot);
  if (!state.history[id]) {
    state.history[id] = [];
    await send('start', '', '', true);
  } else {
    renderMessages();
  }
}

function renderBrief(bot) {
  const t = templateOf(bot.template);
  const pairs = Object.entries(bot.config.brief || {});
  $('#brief-body').innerHTML = `<div class="brief-head"><span class="ico">${esc(t?.icon || '🤖')}</span><div><b>${esc(bot.name)}</b><span>${esc(t?.name || bot.template)}</span></div></div>` +
    pairs.map(([k, v]) => `<div class="brief-card"><small>${esc(labelOf(t, k))}</small><b>${esc(formatBrief(k, v))}</b></div>`).join('');
}

function formatBrief(key, value) {
  const raw = String(value ?? '');
  if (key === 'products' || key === 'services') {
    const lines = raw.split('\n').filter(Boolean);
    const short = lines.slice(0, 3).map((line) => {
      const p = line.split('|');
      return p.length > 1 ? `${p[0].trim()} — ${p[1].trim()}` : line;
    }).join('\n');
    return short + (lines.length > 3 ? `\n… ещё ${lines.length - 3}` : '');
  }
  if (key === 'faq') {
    return raw.split('\n').filter(Boolean).slice(0, 3).map((line) => line.replace('|', ' → ')).join('\n');
  }
  return raw.length > 220 ? raw.slice(0, 220) + '…' : raw;
}

function labelOf(t, key) {
  return t?.fields?.find((f) => f.key === key)?.label || key;
}

function messageHtml(m) {
  const bot = state.bots.find((b) => b.id === state.current);
  const t = templateOf(bot?.template);
  const buttons = m.buttons?.length
    ? `<div class="msg-btns">${m.buttons.map((b) => `<button data-action="${esc(b.action)}" data-label="${esc(b.label)}">${esc(b.label)}</button>`).join('')}</div>`
    : '';
  return `<div class="msg ${m.role === 'me' ? 'me' : ''}">${m.image ? `<img src="${esc(m.image)}" alt="">` : ''}${esc(m.text)}${buttons}${m.role === 'me' ? '<span class="meta">вы</span>' : ''}</div>`;
}

function renderMessages() {
  const messages = state.history[state.current] || [];
  $('#messages').innerHTML = messages.map(messageHtml).join('');
  $('#messages').scrollTop = $('#messages').scrollHeight;
  $('#quick').innerHTML = '';
  $$('[data-action]').forEach((el) => el.onclick = () => send(el.dataset.action, '', el.dataset.label));
}

async function send(action = '', text = '', display = '', silent = false) {
  if (state.busy || !state.current) return;
  state.busy = true;
  const history = state.history[state.current] || (state.history[state.current] = []);
  if (display || text) history.push({ role: 'me', text: display || text });
  if (display || text) { renderMessages(); }
  try {
    const data = await api(`/api/bots/${state.current}/message`, { method: 'POST', body: JSON.stringify({ text, action }) });
    for (const m of data.messages) history.push({ role: 'bot', ...m });
    renderMessages();
  } catch (err) {
    toast(err.message);
  } finally {
    state.busy = false;
  }
}

function openModal() {
  state.selected = state.templates[0]?.id;
  $('#modal').classList.remove('hidden');
  renderTemplateChoices();
  renderFields();
}

function closeModal() { $('#modal').classList.add('hidden'); }

function renderTemplateChoices() {
  $('#templates').innerHTML = state.templates.map((t) => `<button type="button" class="tpl ${state.selected === t.id ? 'on' : ''}" data-tpl="${t.id}">
    <span style="font-size:18px">${esc(t.icon)}</span><b>${esc(t.name)}</b><span>${esc(t.tagline)}</span>
  </button>`).join('');
  $$('[data-tpl]').forEach((el) => el.onclick = () => { state.selected = el.dataset.tpl; renderTemplateChoices(); renderFields(); });
}

function renderFields() {
  const t = templateOf(state.selected);
  if (!t) return;
  $('#brief-fields').innerHTML = t.fields.map((f) => {
    const value = t.defaults[f.key] || '';
    const input = f.type === 'textarea'
      ? `<textarea name="${esc(f.key)}">${esc(value)}</textarea>`
      : `<input name="${esc(f.key)}" value="${esc(value)}">`;
    return `<div class="field"><label>${esc(f.label)}${f.required ? ' *' : ''}</label>${input}${f.hint ? `<div class="hint">${esc(f.hint)}</div>` : ''}</div>`;
  }).join('');
}

async function submitBrief(e) {
  e.preventDefault();
  const fields = new FormData(e.target);
  const brief = {};
  for (const [k, v] of fields.entries()) brief[k] = v;
  try {
    const bot = await createBot(state.selected, brief);
    $('#modal').classList.add('hidden');
    state.bots = (await api('/api/bots')).bots;
    renderBots();
    openBot(bot.id);
  } catch (err) { toast(err.message); }
}

async function resetChat() {
  if (!state.current) return;
  try {
    const data = await api(`/api/bots/${state.current}/reset`, { method: 'POST', body: '{}' });
    state.history[state.current] = data.messages.map((m) => ({ role: 'bot', ...m }));
    renderMessages();
    toast('Сценарий сброшен');
  } catch (err) { toast(err.message); }
}

async function main() {
  await loadTemplates();
  await loadBots();
  $('#new-bot').onclick = openModal;
  $('#empty-create').onclick = openModal;
  $('#modal-close').onclick = closeModal;
  $('#brief-form').onsubmit = submitBrief;
  $('#reset-chat').onclick = resetChat;
  $('#composer').onsubmit = (e) => {
    e.preventDefault();
    const text = $('#text').value.trim();
    if (!text) return;
    $('#text').value = '';
    send('', text);
  };
}

main().catch((err) => toast(err.message));
