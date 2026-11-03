/* Школа AI-агентов · MVP. Vanilla SPA без сборки. */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = {
  user: null,
  templates: [],
  projects: [],
  lessons: [],
  usage: [],
  packages: [],
  project: null,
  activeFile: 'content.json',
  fileFilter: '',
  activeTab: 'chat',
  auxTab: 'chat',
  dirty: false,
  folderHandle: null,
  folderProjectId: null,
  auxWidth: Number(localStorage.getItem('school-aux-w')) || 380,
  panelHeight: Number(localStorage.getItem('school-panel-h')) || 210,
  sideWidth: Number(localStorage.getItem('school-side-w')) || 248,
  focusMode: localStorage.getItem('school-focus') === '1',
  collapsedDirs: new Set(),
  filter: 'all',
  authMode: 'login',
  preview: null,
  sending: false,
  liveSteps: [],
  chatImage: null,
  termSocket: null,
  lesson: null,
  admin: null,
};

const ICONS = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  templates: '<rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><path d="M17 13v8M13 17h8"/>',
  lessons: '<path d="M4 5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-2V5Z"/><path d="M8 7h6M8 11h6"/>',
  wallet: '<rect x="2" y="6" width="20" height="14" rx="3"/><path d="M2 10h20M16 15h2"/>',
  admin: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/>',
  folder: '<path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6Z"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6"/>',
  bot: '<rect x="4" y="7" width="16" height="12" rx="3"/><path d="M12 3v4M8 13h.01M16 13h.01M9 17h6"/>',
  agent: '<circle cx="12" cy="12" r="3"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M6.5 6.5 9.5 9.5M17.5 6.5 14.5 9.5M6.5 17.5 9.5 14.5M17.5 17.5 14.5 14.5"/>',
  app: '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 5h4M11 19h2"/>',
  arrow: '<path d="M4 12h16M14 6l6 6-6 6"/>',
  check: '<path d="m4 12 5 5L20 6"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  rocket: '<path d="M5 15c-1 3-1 5-1 5s2 0 5-1M9 19l-4-4c1-6 5-11 13-12 1 8-4 12-9 16Z"/><circle cx="14" cy="8" r="1.5"/>',
  spark: '<path d="M12 2v6M12 16v6M2 12h6M16 12h6M5 5l4 4M15 15l4 4M19 5l-4 4M9 15l-4 4"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  send: '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/>',
  save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
  trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"/>',
  external: '<path d="M14 3h7v7M21 3l-9 9"/><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/>',
  back: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
  code: '<path d="m8 8-5 4 5 4M16 8l5 4-5 4M14 4l-4 16"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
  play: '<path d="M8 5v14l11-7-11-7Z"/>',
  shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9M17 3l4 4M14 6l3 3"/>',
  db: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  terminal: '<path d="m4 17 6-6-6-6M12 19h8"/>',
  braces: '<path d="M8 3H6a2 2 0 0 0-2 2v4a2 2 0 0 1-2 2 2 2 0 0 1 2 2v4a2 2 0 0 0 2 2h2M16 3h2a2 2 0 0 1 2 2v4a2 2 0 0 0 2 2 2 2 0 0 0-2 2v4a2 2 0 0 1-2 2h-2"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v4M8 21h8"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9" r="1.5"/><path d="m21 15-5-5L5 20"/>',
  paperclip: '<path d="M21.4 11.6 12.3 20.7a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5"/>',
};

function svg(name, cls = '') {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ICONS.spark}</svg>`;
}
function ic(name, cls = '') {
  return `<span class="ico ${cls}">${svg(name)}</span>`;
}

const PY_SVG = `<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="#3776ab" d="M8 1c-2.9 0-3 1.3-3 2.5V5h3.2v.7H4.3C2.9 5.7 2 6.6 2 8s.9 2.3 2.3 2.3H5V9c0-1.5 1.2-2.6 2.6-2.6h2.8c1.1 0 2-.9 2-2V4c0-1.3-1.4-3-4.4-3Z"/><path fill="#ffd43b" d="M8 15c2.9 0 3-1.3 3-2.5V11H7.8v-.7h3.9C13.1 10.3 14 9.4 14 8s-.9-2.3-2.3-2.3H11V7c0 1.5-1.2 2.6-2.6 2.6H5.6c-1.1 0-2 .9-2 2V12c0 1.3 1.4 3 4.4 3Z"/><circle cx="5.6" cy="3.4" r=".7" fill="#fff"/><circle cx="10.4" cy="12.6" r=".7" fill="#fff"/></svg>`;

const FILE_TYPES = {
  py: { cls: 'py', raw: PY_SVG },
  json: { cls: 'json', icon: 'braces' },
  md: { cls: 'md', icon: 'book' },
  env: { cls: 'env', icon: 'key' },
  gitignore: { cls: 'git', icon: 'settings' },
  docker: { cls: 'docker', label: 'D' },
  js: { cls: 'js', label: 'JS' },
  ts: { cls: 'ts', label: 'TS' },
  html: { cls: 'html', label: '<>' },
  css: { cls: 'css', label: '#' },
  sql: { cls: 'sql', icon: 'db' },
  yml: { cls: 'yml', label: 'Y' },
  yaml: { cls: 'yml', label: 'Y' },
  sh: { cls: 'sh', icon: 'terminal' },
  bat: { cls: 'bat', label: 'B' },
  log: { cls: 'log', icon: 'file' },
  txt: { cls: 'txt', icon: 'file' },
  toml: { cls: 'toml', label: 'T' },
  ini: { cls: 'ini', label: 'I' },
};

function fileIcon(path) {
  const base = path.split('/').pop().toLowerCase();
  let key = base.split('.').pop();
  if (base === 'dockerfile' || base.startsWith('dockerfile.')) key = 'docker';
  if (base === '.env.example' || base === '.env' || base.startsWith('.env.')) key = 'env';
  if (base === '.gitignore' || base === '.dockerignore') key = 'gitignore';
  if (base === 'requirements.txt') key = 'txt';
  if (base === 'readme.md') key = 'md';
  const t = FILE_TYPES[key] || { cls: 'default', icon: 'file' };
  const inner = t.raw ? t.raw : t.icon ? svg(t.icon) : `<b>${t.label || '?'}</b>`;
  return `<span class="ficon ${t.cls}">${inner}</span>`;
}

function folderIcon(open = false) {
  return `<span class="ficon folder ${open ? 'open' : ''}">${svg('folder')}</span>`;
}

function chevron(open) {
  return `<span class="chev">${open ? '▾' : '▸'}</span>`;
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function rub(value) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(Number(value || 0)) + ' ₽';
}
function plural(n, one, few, many) {
  const abs = Math.abs(Number(n)) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return many;
  if (last === 1) return one;
  if (last >= 2 && last <= 4) return few;
  return many;
}
function filesWord(n) {
  return `${n} ${plural(n, 'файл', 'файла', 'файлов')}`;
}
function tokensFull(n) {
  return new Intl.NumberFormat('ru-RU').format(Number(n || 0)).replace(/[\u00a0\u202f]/g, ' ');
}
function tokensShort(n) {
  const v = Number(n || 0);
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(v % 1_000_000 ? 1 : 0).replace('.', ',') + ' млн';
  if (v >= 1_000) return Math.round(v / 1_000) + ' тыс.';
  return String(v);
}
function money(value) {
  const n = Math.abs(Number(value) || 0);
  if (n < 100) return new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n) + ' ₽';
  return rub(n);
}
function dateShort(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
}
function ago(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'только что';
  if (diff < 3600) return Math.floor(diff / 60) + ' мин назад';
  if (diff < 86400) return Math.floor(diff / 3600) + ' ч назад';
  return dateShort(iso);
}
function directionLabel(d) {
  return { bot: 'Чат-бот', agent: 'AI-агент', miniapp: 'Мини-апп', code: 'Мой проект' }[d] || d;
}
function directionBadge(d) {
  const cls = d === 'bot' ? 'pink' : d === 'agent' ? 'violet' : d === 'code' ? 'gold' : 'blue';
  return `<span class="badge ${cls}">${directionLabel(d)}</span>`;
}
function statusBadge(status) {
  const map = {
    draft: ['', 'Черновик'],
    deployed: ['green', 'Опубликован'],
    error: ['red', 'Ошибка'],
  };
  const [cls, label] = map[status] || ['', status];
  return `<span class="badge ${cls}">${label}</span>`;
}

function toast(text, type = 'ok') {
  const box = $('#toast');
  const el = document.createElement('div');
  el.className = 't ' + type;
  el.textContent = text;
  box.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

async function api(path, options = {}) {
  const opts = { credentials: 'same-origin', ...options };
  if (opts.body && typeof opts.body !== 'string') {
    opts.headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(path, opts);
  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    data = { detail: 'Сервер вернул не JSON' };
  }
  if (!res.ok) {
    if (res.status === 401 && !path.includes('/auth/')) {
      state.user = null;
      location.hash = '#/login';
    }
    throw new Error(data.detail || 'Ошибка запроса');
  }
  return data;
}

function track(kind, meta = {}, projectId = null) {
  try {
    fetch('/api/events', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind, meta, project_id: projectId }),
    }).catch(() => {});
  } catch (_) {}
}

/* ---------- auth ---------- */
function renderAuth() {
  const isLogin = state.authMode === 'login';
  document.body.classList.add('auth-mode');
  $('#app').innerHTML = `
  <div class="auth auth-v2">
    <section class="auth-hero">
      <div class="auth-brand">
        <div class="auth-brand-mark">AI</div>
        <div><b>Школа AI-агентов</b><span>платформа запуска</span></div>
      </div>

      <div class="auth-copy">
        <div class="auth-kicker"><i></i> школа + платформа · 2026</div>
        <h1>Собери <em>бота</em>,<br>агента или <span class="auth-serif">мини-апп</span><br><span class="auth-serif">за вечер.</span></h1>
        <p>Бриф, AI-агент, превью и кнопка «Опубликовать» — в одном браузере. Без установки, VPN и API-ключей.</p>
        <div class="auth-pills">
          <span>DSH внутри</span><span>Telegram</span><span>без VPN</span><span>токены</span>
        </div>
        <button class="auth-demo-btn" id="demo-enter">Посмотреть демо ${svg('arrow')}</button>
        <div class="auth-stats">
          <div><b>37</b><span>проектов в базе</span></div>
          <div><b>7</b><span>шаблонов</span></div>
          <div><b>0 ₽</b><span>за установку</span></div>
        </div>
      </div>

      <div class="auth-visual" aria-hidden="true">
        <div class="av-glow av-glow-1"></div>
        <div class="av-glow av-glow-2"></div>
        <div class="av-window">
          <div class="av-bar">
            <span class="av-dots"><i></i><i></i><i></i></span>
            <span class="av-tab">agent.ts</span>
            <span class="av-live">● live</span>
          </div>
          <div class="av-body">
            <div class="av-files">
              <span class="av-folder">src</span>
              <span class="av-file active">agent.ts</span>
              <span class="av-file">bot.py</span>
              <span class="av-file">content.json</span>
              <span class="av-file">prompts</span>
            </div>
            <div class="av-code">
              <div><span class="av-ln">1</span><span class="av-kw">export</span> <span class="av-fn">async function</span> <span class="av-fn2">run</span>() {</div>
              <div><span class="av-ln">2</span>  <span class="av-kw">const</span> agent = <span class="av-kw">await</span> <span class="av-fn2">create</span>({</div>
              <div><span class="av-ln">3</span>    model: <span class="av-str">'deepseek'</span>,</div>
              <div><span class="av-ln">4</span>    tools: [<span class="av-str">'files'</span>, <span class="av-str">'shell'</span>],</div>
              <div><span class="av-ln">5</span>    workspace: <span class="av-str">'./salon'</span></div>
              <div><span class="av-ln">6</span>  })</div>
              <div><span class="av-ln">7</span>  <span class="av-kw">return</span> agent.<span class="av-fn2">deploy</span>()</div>
              <div><span class="av-ln">8</span>}</div>
            </div>
          </div>
          <div class="av-terminal"><span>$</span> agent actions <b>✓ bot.py</b> <b>✓ content.json</b></div>
        </div>

        <div class="av-chat">
          <div class="av-chat-head"><span>✦ AI-помощник</span><i>DSH</i></div>
          <div class="av-bubble">Собрал бота-визитку: меню, услуги, запись и ответы на вопросы.</div>
          <div class="av-chat-foot">✓ изменён bot.py <span>6 632 токена</span></div>
        </div>

        <div class="av-phone">
          <div class="av-phone-top"><span>Салон «Лотос»</span><i>бот</i></div>
          <div class="av-phone-msg">Здравствуйте! Помогу с выбором и записью.</div>
          <div class="av-phone-btn">Услуги</div>
          <div class="av-phone-btn">Записаться</div>
          <div class="av-phone-btn">Цены</div>
        </div>
        <div class="av-badge">✓ deployed <span>@lotos_bot</span></div>
      </div>
    </section>

    <section class="auth-side">
      <div class="auth-card">
        <div class="auth-card-head">
          <div><div class="eyebrow">Личный кабинет</div><h2>${isLogin ? 'С возвращением' : 'Создать аккаунт'}</h2></div>
          <div class="auth-mini-mark">AI</div>
        </div>
        <div class="sub">${isLogin ? 'Войди, чтобы продолжить проект.' : '1 млн токенов уже внутри — можно пробовать.'}</div>
        <div class="tabs">
          <button class="${isLogin ? 'on' : ''}" data-auth="login">Вход</button>
          <button class="${!isLogin ? 'on' : ''}" data-auth="register">Регистрация</button>
        </div>
        <form id="auth-form">
          ${!isLogin ? `<div class="field"><label>Имя</label><input name="name" placeholder="Как тебя зовут" autocomplete="name"></div>` : ''}
          <div class="field"><label>Email</label><input name="email" type="email" required placeholder="you@example.com" autocomplete="email"></div>
          <div class="field"><label>Пароль</label><input name="password" type="password" required ${!isLogin ? 'minlength="8"' : ''} placeholder="${isLogin ? 'Твой пароль' : 'Минимум 8 символов'}" autocomplete="${isLogin ? 'current-password' : 'new-password'}"></div>
          <div id="auth-error"></div>
          <button class="btn primary auth-submit" type="submit">${isLogin ? 'Войти' : 'Зарегистрироваться'} ${svg('arrow')}</button>
        </form>
        <div class="demo-note">Нет аккаунта? Нажми «Регистрация» — внутри 1 млн токенов.<br>Демо-режим — кнопкой «Посмотреть демо».</div>
        <div class="auth-legal">Безопасный вход · данные не передаются третьим лицам</div>
      </div>
    </section>
  </div>`;

  $$('[data-auth]').forEach((b) => b.onclick = () => { state.authMode = b.dataset.auth; renderAuth(); });
  const demoBtn = $('#demo-enter');
  if (demoBtn) demoBtn.onclick = () => {
    if (!isLogin) { state.authMode = 'login'; renderAuth(); }
    const f = $('#auth-form');
    if (!f) return;
    f.email.value = 'demo@school.local';
    f.password.value = 'demo1234';
    f.requestSubmit();
  };
  $('#auth-form').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    const btn = e.target.querySelector('button[type=submit]');
    btn.disabled = true;
    $('#auth-error').innerHTML = '';
    try {
      const data = await api('/api/auth/' + (isLogin ? 'login' : 'register'), { method: 'POST', body });
      state.user = data.user;
      document.body.classList.remove('auth-mode');
      await refreshBase();
      location.hash = '#/dashboard';
      render();
    } catch (err) {
      $('#auth-error').innerHTML = `<div class="form-error">${esc(err.message)}</div>`;
      btn.disabled = false;
    }
  };
}

/* ---------- VS Code shell ---------- */
function pageTitle(hash) {
  if (hash.startsWith('#/project/')) return state.project?.name || 'Проект';
  if (hash.startsWith('#/new/')) return 'Новый проект';
  if (hash.startsWith('#/lesson/')) return 'Урок';
  if (hash.startsWith('#/templates')) return 'Шаблоны';
  if (hash.startsWith('#/lessons')) return 'Уроки';
  if (hash.startsWith('#/billing')) return 'Баланс';
  if (hash.startsWith('#/profile')) return 'Профиль';
  if (hash.startsWith('#/admin')) return 'Админка';
  return 'Дашборд';
}

function routeIcon(hash) {
  if (hash.startsWith('#/templates') || hash.startsWith('#/new')) return 'templates';
  if (hash.startsWith('#/lessons') || hash.startsWith('#/lesson')) return 'book';
  if (hash.startsWith('#/billing')) return 'wallet';
  if (hash.startsWith('#/profile')) return 'user';
  if (hash.startsWith('#/admin')) return 'admin';
  if (hash.startsWith('#/project')) return 'code';
  return 'dashboard';
}

function activityBar(current) {
  const items = [
    ['#/dashboard', 'folder', 'Проводник'],
    ['#/templates', 'templates', 'Шаблоны'],
    ['#/lessons', 'book', 'Обучение'],
    ['#/billing', 'wallet', 'Баланс'],
    ['#/profile', 'user', 'Профиль'],
  ];
  if (state.user?.role === 'admin') items.push(['#/admin', 'admin', 'Админка']);
  const active = (href) => current === href || current.startsWith(href + '/')
    || (href === '#/lessons' && current.startsWith('#/lesson/'))
    || (href === '#/templates' && current.startsWith('#/new/'))
    || (href === '#/dashboard' && current.startsWith('#/project/'));
  return `<div class="vsc-activity">
    ${items.map(([href, icon, title]) => `<button class="vsc-act ${active(href) ? 'active' : ''}" data-go="${href}" title="${title}">${svg(icon)}</button>`).join('')}
    <button class="vsc-act" data-action="open-folder" title="Открыть папку с диска">${svg('folder')}</button>
    <div class="spacer"></div>
    <button class="vsc-act" data-action="toggle-theme" title="Светлая / тёмная тема">${svg('sun')}</button>
    <button class="vsc-act" data-action="logout" title="Выйти">${svg('logout')}</button>
  </div>`;
}

function defaultSidebar(current) {
  const done = state.lessons.filter((l) => l.done).length;
  const total = state.lessons.length || 6;
  const nav = [
    ['#/dashboard', 'dashboard', 'Дашборд'],
    ['#/templates', 'templates', 'Шаблоны'],
    ['#/lessons', 'lessons', 'Уроки'],
    ['#/billing', 'wallet', 'Баланс'],
    ['#/profile', 'user', 'Профиль'],
  ];
  if (state.user?.role === 'admin') nav.push(['#/admin', 'admin', 'Админка']);
  const isActive = (href) => current === href || current.startsWith(href + '/')
    || (href === '#/lessons' && current.startsWith('#/lesson/'))
    || (href === '#/templates' && current.startsWith('#/new/'));
  return `<div class="vsc-side-head">Навигация</div>
  <div class="vsc-side-scroll">
    <div class="vsc-side-section">
      <div class="vsc-side-title">Школа AI-агентов</div>
      ${nav.map(([href, icon, label]) => `<a class="tree-row ${isActive(href) ? 'active' : ''}" data-go="${href}">${svg(icon)}${label}</a>`).join('')}
    </div>
    <div class="vsc-side-section">
      <div class="vsc-side-title">Проекты <span class="grow">${state.projects.length}</span><button data-go="#/templates" title="Новый проект">+</button></div>
      <button class="tree-row open-folder-row" data-action="open-folder">${svg('folder')}Открыть папку с диска</button>
      ${state.projects.length ? state.projects.map((p) => `<div class="project-item ${current === '#/project/' + p.id ? 'active' : ''}"><a class="tree-row" data-go="#/project/${p.id}">${svg(p.template?.icon || 'bot')}<span class="tree-name">${esc(p.name)}</span>${p.is_shared ? '<span class="shared-badge">общий</span>' : ''}<span class="project-count">${p.files_count || 0}</span></a><button class="tree-more project-more" data-project-menu="${p.id}" title="Действия">⋯</button></div>`).join('') : `<div class="vsc-side-empty">Пока нет проектов. Создай первый из шаблона.</div>`}
    </div>
    <div class="vsc-side-section">
      <div class="vsc-side-title">Обучение <span class="grow">${done}/${total}</span></div>
      <a class="tree-row ${isActive('#/lessons') ? 'active' : ''}" data-go="#/lessons">${svg('book')}Уроки <span class="badge-n">${done}/${total}</span></a>
    </div>
    <div class="vsc-side-section">
      <div class="vsc-side-title">Статус</div>
      <div class="vsc-side-empty" style="padding:6px 16px">AI-помощник: <span class="green">${state.user?.agent_mode === 'dsh' ? 'DSH' : 'демо'}</span><br>Токены: ${tokensShort(state.user?.token_balance || 0)}<br>${esc(state.user?.email || '')}</div>
    </div>
  </div>`;
}

function defaultPanel() {
  return `<div class="vsc-panel-head"><span class="on">Терминал</span><span class="grow"></span><button data-action="toggle-panel" title="Свернуть">⌄</button></div>
  <div class="vsc-panel-body"><div class="term-line"><span class="term-prompt">$</span> ready — выбери шаблон или открой проект</div></div>`;
}

function layout(content, opts = {}) {
  const current = location.hash || '#/dashboard';
  const title = opts.title || pageTitle(current);
  const crumbs = opts.breadcrumbs || ['Школа AI-агентов', title];
  const tabs = opts.tabs || [{ label: title, icon: routeIcon(current), active: true }];
  const sidebar = opts.sidebar || defaultSidebar(current);
  const panel = opts.panel === null ? '' : (opts.panel || defaultPanel());
  const actions = opts.actions || '';
  return `<div class="vsc">
    <div class="vsc-titlebar">
      <button class="vsc-brand" data-go="#/dashboard" title="На главную"><span class="vsc-logo">AI</span><span class="vsc-brand-name">Школа AI-агентов</span></button>
      <div class="vsc-title">${esc(title)}</div>
      <div class="vsc-token-chip" data-go="#/billing" title="Баланс токенов">${svg('wallet')}<b>${tokensShort(state.user?.token_balance || 0)}</b><span>токенов</span></div>
    </div>
    <div class="vsc-workbench ${state.focusMode ? 'focus-mode' : ''}" style="--side-w:${state.sideWidth}px">
      ${activityBar(current)}
      <aside class="vsc-sidebar">${sidebar}</aside>
      <div class="sidebar-resizer" data-resize="sidebar" title="Потяни, чтобы изменить ширину проводника"></div>
      <main class="vsc-editor-area" style="--panel-h:${state.panelHeight}px">
        <div class="vsc-tabs">
          ${tabs.map((t) => `<div class="vsc-tab ${t.active ? 'active' : ''}" ${t.action ? `data-ide-tab="${t.action}"` : ''} ${t.go ? `data-go="${t.go}"` : ''}>${t.html || svg(t.icon || 'file')}<span>${esc(t.label)}</span><span class="tab-dirty" id="tab-dirty" style="${t.dirty ? '' : 'display:none'}">●</span>${t.close ? '<span class="x">×</span>' : ''}</div>`).join('')}
          <div class="vsc-tabs-actions">${actions}</div>
        </div>
        <div class="vsc-breadcrumbs">${crumbs.map((c, i) => `${i ? '<span class="sep">›</span>' : ''}<span>${esc(c)}</span>`).join('')}</div>
        <div class="vsc-content ${opts.flush ? 'flush' : ''}">${content}</div>
        ${panel ? `<div class="panel-resizer" data-resize="panel" title="Потяни, чтобы изменить высоту терминала"></div><div class="vsc-panel">${panel}</div>` : ''}
      </main>
    </div>
    <div class="vsc-statusbar">
      <span><span class="status-dot"></span> AI-помощник: ${state.user?.agent_mode === 'dsh' ? 'DSH' : 'демо'}</span>
      <span class="grow"></span>
      ${opts.editor ? `<span id="status-pos">Ln 1, Col 1</span><span>${esc(opts.editorLang || 'Plain Text')}</span><span>Spaces: 2</span><span>UTF-8</span><span>LF</span>` : ''}
      <span>${tokensShort(state.user?.token_balance || 0)} токенов</span>
    </div>
  </div>`;
}

/* ---------- dashboard ---------- */
function renderDashboard() {
  const done = state.lessons.filter((l) => l.done).length;
  const total = state.lessons.length || 6;
  const next = state.lessons.find((l) => !l.done) || state.lessons[state.lessons.length - 1];
  const projects = state.projects.slice(0, 6);
  const last = state.projects[0];
  const content = `
  <div class="welcome-hero workspace-hero">
    <div class="welcome-copy">
      <div class="eyebrow">Рабочая область</div>
      <h1>Открой папку и работай</h1>
      <div class="sub">Файлы, редактор и AI-помощник — в одном окне. Папка откроется как проект, без установки.</div>
      <div class="row">
        <button class="btn primary" data-action="open-folder" title="Chrome откроет окно: выбери папку и нажми «Выбор папки»">${svg('folder')}Открыть папку</button>
        <button class="btn ghost" data-go="#/templates">${svg('plus')}Собрать с нуля</button>
      </div>
      <div class="small dim" style="margin-top:8px">Chrome/Edge: выбери папку и нажми «Выбор папки». Доступ на запись спросится при первом сохранении.</div>
    </div>
    <div class="ws-resume">
      ${last ? `
        <div class="eyebrow">Продолжить</div>
        <div class="ws-resume-name">${esc(last.name)}</div>
        <div class="small muted">${filesWord(last.files_count)} · ${ago(last.updated_at)}</div>
        <button class="btn ghost sm" data-go="#/project/${last.id}">Открыть проект →</button>
      ` : `
        <div class="eyebrow">Старт</div>
        <div class="ws-resume-name">Пока нет проектов</div>
        <div class="small muted">Открой папку с диска или выбери шаблон.</div>
      `}
    </div>
  </div>
  <div class="grid g4">
    <div class="card stat"><div class="v">${state.projects.length}</div><div class="l">проектов</div><div class="s">в работе и готовых</div></div>
    <div class="card stat"><div class="v">${tokensShort(state.user.token_balance)}</div><div class="l">токенов</div><div class="s">потрачено ${tokensShort(state.user.tokens_spent)}</div></div>
    <div class="card stat"><div class="v">${done}/${total}</div><div class="l">уроков пройдено</div><div class="s">тест-драйв 48 часов</div></div>
    <div class="card stat"><div class="v">${state.user.stats?.deployments ?? 0}</div><div class="l">деплоев</div><div class="s">боты и мини-аппы</div></div>
  </div>

  <div style="display:grid;grid-template-columns:1.3fr .7fr;gap:16px;margin-top:16px">
    <div>
      <div class="between" style="margin-bottom:10px"><h2>Проекты</h2><a class="small dim" href="#/templates">+ добавить</a></div>
      ${projects.length ? `<div class="grid g2">${projects.map(projectCard).join('')}</div>` : `
        <div class="empty"><b>Пока пусто</b>Начни с шаблона «Бот-визитка с AI» — это 2 минуты.<br><br><button class="btn primary" data-go="#/templates">Выбрать шаблон</button></div>`}
    </div>
    <div class="stack">
      <div class="card">
        <div class="between"><h3>Уроки</h3><span class="badge gold">${done}/${total}</span></div>
        <div class="progress" style="margin:12px 0 8px"><i style="width:${Math.round(done / total * 100)}%"></i></div>
        ${next ? `<div class="small muted">Дальше: <b style="color:var(--vsc-text)">${esc(next.title)}</b> · ${next.minutes} мин</div>
        <button class="btn" style="width:100%;margin-top:12px" data-go="#/lesson/${next.id}">${svg('play')}Продолжить</button>` : ''}
      </div>
      <div class="card">
        <div class="row">${ic('spark','sm')}<div><b style="font-size:13px">Быстрый старт</b><div class="small dim">Бот-визитка, AI-ассистент или витрина</div></div></div>
        <button class="btn" style="width:100%;margin-top:12px" data-go="#/templates">Открыть шаблоны ${svg('arrow')}</button>
      </div>
    </div>
  </div>
  <div class="grid g3" style="margin-top:16px">
    <div class="card"><div class="eyebrow">01 · шаблон</div><h3 style="margin-top:6px;font-size:15px">Выбери продукт</h3><div class="small muted" style="margin-top:6px">Бот, агент или мини-апп. Файлы и превью появятся сразу.</div></div>
    <div class="card"><div class="eyebrow">02 · бриф</div><h3 style="margin-top:6px;font-size:15px">Ответь на 8 вопросов</h3><div class="small muted" style="margin-top:6px">Ниша, продукт, аудитория, тон. Без кода и терминала.</div></div>
    <div class="card"><div class="eyebrow">03 · деплой</div><h3 style="margin-top:6px;font-size:15px">Опубликуй</h3><div class="small muted" style="margin-top:6px">Вставь токен бота — платформа проверит и запишет деплой.</div></div>
  </div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();
}

function projectCard(p) {
  return `<div class="card project-card" data-go="#/project/${p.id}">
    <div class="top">${ic(p.template?.icon || 'bot')}<div style="min-width:0"><h3>${esc(p.name)}</h3><div class="meta">${esc(p.template?.name || p.template_id)}</div></div></div>
    <div class="row" style="gap:6px;flex-wrap:wrap">${directionBadge(p.template?.direction || 'bot')}${statusBadge(p.status)}</div>
    <div class="between small dim"><span>${filesWord(p.files_count)}</span><span>${ago(p.updated_at)}</span></div>
  </div>`;
}

/* ---------- templates ---------- */
function renderTemplates() {
  const list = state.templates.filter((t) => state.filter === 'all' || t.direction === state.filter);
  const content = `
  <div class="page-head">
    <div><div class="eyebrow">Каталог</div><h1>Шаблоны</h1><div class="sub">Выбери продукт — платформа развернёт файлы, превью и деплой. Тексты меняются в чате с агентом.</div></div>
  </div>
  <div class="filters">
    ${[['all','Все'],['bot','Чат-боты'],['agent','AI-агенты'],['miniapp','Мини-аппы']].map(([k,l]) => `<button class="${state.filter===k?'on':''}" data-filter="${k}">${l}</button>`).join('')}
  </div>
  <div class="grid g3">
    ${list.map((t) => `<div class="card template-card">
      <div class="between"><div class="row">${ic(t.icon)}<div><span class="badge ${t.direction==='bot'?'pink':t.direction==='agent'?'violet':'blue'}">${directionLabel(t.direction)}</span></div></div>${t.badge ? `<span class="badge gold">${t.badge}</span>` : ''}</div>
      <h3>${esc(t.name)}</h3>
      <div class="tagline">${esc(t.tagline)}</div>
      <div class="desc">${esc(t.description)}</div>
      <div class="stack-badges">${t.stack.map((s) => `<span>${esc(s)}</span>`).join('')}</div>
      <div class="foot"><b class="gold" style="font-size:15px">${esc(t.price)}</b><button class="btn primary sm" data-go="#/new/${t.id}">Развернуть ${svg('arrow')}</button></div>
    </div>`).join('')}
  </div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();
  $$('[data-filter]').forEach((b) => b.onclick = () => { state.filter = b.dataset.filter; renderTemplates(); });
}

/* ---------- brief ---------- */
function renderBrief(templateId) {
  const t = state.templates.find((x) => x.id === templateId);
  if (!t) { location.hash = '#/templates'; return; }
  const defaults = t.defaults || {};
  const field = (f) => {
    const value = defaults[f.key] ?? f.default ?? '';
    const full = ['textarea', 'color'].includes(f.type) || f.key === 'faq' ? ' full' : '';
    let input = '';
    if (f.type === 'textarea') input = `<textarea name="${f.key}" placeholder="${esc(f.placeholder || '')}">${esc(value)}</textarea>`;
    else if (f.type === 'select') input = `<select name="${f.key}">${(f.options || []).map((o) => `<option value="${esc(o.value)}" ${value === o.value ? 'selected' : ''}>${esc(o.label)}</option>`).join('')}</select>`;
    else if (f.type === 'color') input = `<div class="row"><input type="color" name="${f.key}" value="${esc(value || '#ff4f8b')}" style="width:54px;height:38px;padding:3px"><input value="${esc(value || '#ff4f8b')}" readonly style="flex:1;background:rgba(5,9,22,.55);border:1px solid var(--line2);border-radius:10px;padding:10px"></div>`;
    else input = `<input type="${f.type === 'email' ? 'email' : 'text'}" name="${f.key}" placeholder="${esc(f.placeholder || '')}" value="${esc(value)}">`;
    return `<div class="field${full}"><label>${esc(f.label)}${f.required ? ' *' : ''}</label>${input}${f.hint ? `<div class="hint">${esc(f.hint)}</div>` : ''}</div>`;
  };
  const content = `
  <div class="page-head">
    <div><a class="small dim" href="#/templates">← Все шаблоны</a><h1 style="margin-top:8px">${esc(t.name)}</h1><div class="sub">${esc(t.description)}</div></div>
    <span class="badge ${t.direction==='bot'?'pink':t.direction==='agent'?'violet':'blue'}">${directionLabel(t.direction)}</span>
  </div>
  <div class="brief-grid">
    <div class="card">
      <div class="between" style="margin-bottom:14px"><h3>Бриф</h3><span class="small dim">2 минуты · можно изменить позже</span></div>
      <form id="brief-form" class="brief-form">
        ${t.brief_fields.map(field).join('')}
        <div class="full" id="brief-error"></div>
        <div class="full row" style="justify-content:flex-end;margin-top:6px">
          <button type="button" class="btn ghost" data-go="#/templates">Отмена</button>
          <button class="btn primary" type="submit">${svg('rocket')}Развернуть проект</button>
        </div>
      </form>
    </div>
    <aside class="brief-aside stack">
      <div class="card hl">
        <div class="row">${ic(t.icon)}<div><b>${esc(t.name)}</b><div class="small dim">${directionLabel(t.direction)}</div></div></div>
        <div class="hr"></div>
        <div class="kv"><span>Что получишь</span><b>${t.direction === 'bot' ? 'Рабочий бот' : t.direction === 'agent' ? 'Агент по расписанию' : 'Мини-апп'}</b></div>
        <div class="kv"><span>Файлы</span><b>${t.direction === 'bot' ? 'бот + тексты' : t.direction === 'agent' ? 'агент + промпты' : 'экраны + стили'}</b></div>
        <div class="kv"><span>Чек клиенту</span><b class="gold">${esc(t.price)}</b></div>
        <div class="checklist">
          ${['Файлы проекта', 'Превью в браузере', 'Правки через агента', 'Деплой по токену'].map((x) => `<div>${svg('check')}${x}</div>`).join('')}
        </div>
      </div>
      <div class="card"><div class="small muted">После создания проекта открой чат и напиши, что поменять. Например: «добавь меню: Услуги, Записаться, Цены, Связаться».</div></div>
    </aside>
  </div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();

  $('#brief-form').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const brief = Object.fromEntries(fd.entries());
    const btn = e.target.querySelector('button[type=submit]');
    btn.disabled = true;
    $('#brief-error').innerHTML = '';
    try {
      const data = await api('/api/projects', { method: 'POST', body: { template_id: t.id, name: brief.business_name || t.name, brief } });
      await refreshBase();
      await refreshUser();
      location.hash = '#/project/' + data.id;
      toast('Проект развёрнут');
    } catch (err) {
      $('#brief-error').innerHTML = `<div class="form-error">${esc(err.message)}</div>`;
      btn.disabled = false;
    }
  };
}

/* ---------- project ---------- */
async function renderProject(projectId) {
  if (!state.project || state.project.id !== projectId) {
    $('#app').innerHTML = layout('<div class="loading"><div class="spinner"></div>Открываем проект…</div>', { title: 'Проект' });
    try {
      const data = await api('/api/projects/' + projectId);
      if (location.hash !== '#/project/' + projectId) return;
      state.project = data.project;
      track('project_open', { name: data.project.name }, projectId);
      state.activeFile = data.project.files.some((f) => f.path === 'content.json') ? 'content.json' : (data.project.files[0]?.path || '');
      state.activeTab = 'chat';
      state.auxTab = 'chat';
      state.dirty = false;
      state.collapsedDirs = new Set();
      state.preview = null;
    } catch (err) {
      toast(err.message, 'err');
      location.hash = '#/dashboard';
      return;
    }
  }
  const p = state.project;
  const file = p.files.find((f) => f.path === state.activeFile) || p.files[0];
  const tabs = file ? [{ label: file.path.split('/').pop(), icon: 'file', active: true, html: fileIcon(file.path), dirty: state.dirty }] : [{ label: 'Проект', icon: 'folder', active: true }];
  const content = `<div class="ide-main" style="--aux-w:${state.auxWidth}px">
    <section class="ide-editor">${file ? fileView(p) : '<div class="empty" style="margin:20px">Файлов нет</div>'}</section>
    <div class="ide-resizer" data-resize="aux" title="Потяни, чтобы изменить ширину AI-панели"></div>
    <aside class="ide-aux">
      <div class="aux-tabs">
        <button class="${state.auxTab === 'chat' ? 'on' : ''}" data-aux="chat">${svg('spark')}AI-помощник</button>
        <button class="${state.auxTab === 'preview' ? 'on' : ''}" data-aux="preview">${svg('play')}Превью</button>
        <button class="aux-expand" data-action="toggle-aux" title="Развернуть AI-панель">${svg('external')}</button>
      </div>
      <div class="aux-body">${state.auxTab === 'chat' ? chatView(p) : previewView(p)}</div>
    </aside>
    <div class="drop-overlay" id="drop-overlay">${svg('plus')}<b>Отпусти файлы</b><span>Добавлю их в проект</span></div>
  </div>`;
  const actions = `<button class="btn sm ghost" data-action="toggle-focus" title="${state.focusMode ? 'Вернуть панели' : 'Развернуть редактор'}">${svg('external')}</button><button class="btn sm" data-action="open-deploy">${svg('rocket')}Опубликовать</button>${p.is_shared ? '<span class="shared-badge">общий</span>' : `<button class="btn sm ghost" data-action="delete-project" title="Удалить">${svg('trash')}</button>`}`;
  $('#app').innerHTML = layout(content, {
    title: p.name,
    tabs,
    sidebar: projectSidebar(p),
    panel: projectPanel(p),
    flush: true,
    editor: true,
    editorLang: file ? fileLang(file.path) : 'Plain Text',
    breadcrumbs: ['Школа AI-агентов', p.template.name, p.name],
    actions,
  });
  bindCommon();
  bindResizers();
  bindDrop(p);
  bindTerminal(p);

  $$('[data-aux]').forEach((b) => b.onclick = () => { state.auxTab = b.dataset.aux; renderProject(p.id); });
  $$('[data-dir]').forEach((el) => el.onclick = () => {
    const key = el.dataset.dir;
    if (!key) return;
    if (state.collapsedDirs.has(key)) state.collapsedDirs.delete(key);
    else state.collapsedDirs.add(key);
    renderProject(p.id);
  });
  $$('[data-file]').forEach((el) => el.onclick = () => { state.activeFile = el.dataset.file; state.dirty = false; renderProject(p.id); });
  $$('[data-menu]').forEach((el) => el.onclick = (e) => { e.stopPropagation(); openTreeMenu(el); });
  const fileSearch = $('#file-search');
  if (fileSearch) fileSearch.oninput = () => {
    const value = fileSearch.value;
    state.fileFilter = value;
    renderProject(p.id);
    const next = $('#file-search');
    if (next) { next.focus(); next.setSelectionRange(value.length, value.length); }
  };
  $$('[data-tg-action]').forEach((b) => b.onclick = () => tgAction(b.dataset.tgAction));
  const chatForm = $('#chat-form');
  if (chatForm) { chatForm.onsubmit = sendChat; bindChatForm(chatForm); }
  const saveBtn = $('#save-file');
  if (saveBtn) saveBtn.onclick = saveFile;
  const deployForm = $('#deploy-form');
  if (deployForm) deployForm.onsubmit = doDeploy;
  const ta = $('#file-content');
  const gutter = $('#gutter');
  if (ta && gutter) {
    const layer = $('#code-layer');
    const codeEl = layer ? layer.querySelector('code') : null;
    const minimap = $('#minimap');
    const minimapLines = $('#minimap-lines');
    const minimapView = $('#minimap-view');
    const sync = () => {
      gutter.scrollTop = ta.scrollTop;
      if (layer) { layer.scrollTop = ta.scrollTop; layer.scrollLeft = ta.scrollLeft; }
      if (minimap && minimapView) {
        const ratio = ta.scrollHeight > ta.clientHeight ? ta.scrollTop / (ta.scrollHeight - ta.clientHeight) : 0;
        const viewH = Math.max(16, Math.min(minimap.clientHeight, (ta.clientHeight / Math.max(1, ta.scrollHeight)) * minimap.clientHeight));
        minimapView.style.height = viewH + 'px';
        minimapView.style.top = (6 + ratio * Math.max(0, minimap.clientHeight - viewH - 12)) + 'px';
      }
    };
    const redraw = () => {
      const count = Math.max(1, ta.value.split('\n').length);
      gutter.textContent = Array.from({ length: count }, (_, i) => i + 1).join('\n');
      if (codeEl) codeEl.innerHTML = highlightCode(ta.value, file.path);
      if (minimapLines) minimapLines.innerHTML = minimapHTML(ta.value);
    };
    const pos = () => {
      const before = ta.value.slice(0, ta.selectionStart);
      const line = before.split('\n').length;
      const col = before.length - before.lastIndexOf('\n');
      const el = $('#status-pos');
      if (el) el.textContent = `Ln ${line}, Col ${col}`;
    };
    ta.addEventListener('scroll', sync);
    ta.addEventListener('keyup', pos);
    ta.addEventListener('click', pos);
    ta.addEventListener('input', () => {
      state.dirty = true;
      const dot = $('#tab-dirty');
      if (dot) dot.style.display = 'inline';
      redraw();
      sync();
    });
    if (minimap) {
      minimap.onclick = (e) => {
        const r = minimap.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (e.clientY - r.top) / r.height));
        ta.scrollTop = ratio * Math.max(0, ta.scrollHeight - ta.clientHeight);
        sync();
      };
    }
    redraw();
    sync();
    pos();
  }
  scrollChat();
}

function buildFileTree(files, folders = []) {
  const root = { dirs: new Map(), files: [] };
  const ensure = (parts) => {
    let node = root;
    for (const dir of parts) {
      if (!node.dirs.has(dir)) node.dirs.set(dir, { dirs: new Map(), files: [] });
      node = node.dirs.get(dir);
    }
  };
  for (const folder of folders) ensure(String(folder).split('/').filter(Boolean));
  for (const file of files) {
    const parts = file.path.split('/');
    let node = root;
    for (let i = 0; i < parts.length - 1; i += 1) {
      const dir = parts[i];
      if (!node.dirs.has(dir)) node.dirs.set(dir, { dirs: new Map(), files: [] });
      node = node.dirs.get(dir);
    }
    node.files.push({ name: parts[parts.length - 1], path: file.path });
  }
  return root;
}

function renderTree(node, depth, prefix) {
  let html = '';
  const q = (state.fileFilter || '').toLowerCase();
  const dirs = [...node.dirs.entries()].sort((a, b) => a[0].localeCompare(b[0], 'ru'));
  for (const [name, child] of dirs) {
    const key = prefix ? `${prefix}/${name}` : name;
    const open = !state.collapsedDirs.has(key);
    html += `<div class="tree-row tree-folder" data-dir="${esc(key)}" style="padding-left:${8 + depth * 12}px" title="${esc(key)}">${chevron(open)}${folderIcon(open)}<span class="tree-name">${esc(name)}</span><button class="tree-more" data-menu="folder" data-path="${esc(key)}" title="Действия">⋯</button></div>`;
    if (open) html += renderTree(child, depth + 1, key);
  }
  const files = [...node.files].sort((a, b) => a.name.localeCompare(b.name, 'ru'));
  for (const file of files) {
    if (q && !file.path.toLowerCase().includes(q)) continue;
    html += `<div class="tree-row tree-file ${state.activeFile === file.path ? 'active' : ''}" data-file="${esc(file.path)}" title="${esc(file.path)}" style="padding-left:${22 + depth * 12}px">${fileIcon(file.path)}<span class="tree-name">${esc(file.name)}</span><button class="tree-more" data-menu="file" data-path="${esc(file.path)}" title="Действия">⋯</button></div>`;
  }
  return html;
}

async function refreshProjectView() {
  const p = state.project;
  if (!p) return;
  const data = await api('/api/projects/' + p.id);
  state.project = data.project;
  try { state.projects = (await api('/api/projects')).projects; } catch (_) {}
  if (!state.project.files.some((f) => f.path === state.activeFile)) state.activeFile = state.project.files[0]?.path || '';
  renderProject(p.id);
}

function closeTreeMenu() {
  document.querySelectorAll('.tree-menu').forEach((el) => el.remove());
}

async function createFileIn(folder) {
  const name = prompt(folder ? `Новый файл в «${folder}»` : 'Новый файл', 'new.txt');
  if (!name) return;
  const path = folder ? `${folder}/${name.replace(/^\/+/, '')}` : name.replace(/^\/+/, '');
  try {
    await api(`/api/projects/${state.project.id}/files`, { method: 'POST', body: { path, content: '' } });
    state.activeFile = path;
    state.dirty = false;
    await refreshProjectView();
    toast('Файл создан');
  } catch (err) { toast(err.message, 'err'); }
}

async function createFolderIn(folder) {
  const name = prompt(folder ? `Новая папка в «${folder}»` : 'Новая папка', 'new-folder');
  if (!name) return;
  const path = folder ? `${folder}/${name.replace(/^\/+/, '')}` : name.replace(/^\/+/, '');
  try {
    await api(`/api/projects/${state.project.id}/folders`, { method: 'POST', body: { path } });
    await refreshProjectView();
    toast('Папка создана');
  } catch (err) { toast(err.message, 'err'); }
}

async function renameEntry(path, isDir) {
  const next = prompt('Новый путь', path);
  if (!next || next === path) return;
  try {
    await api(`/api/projects/${state.project.id}/rename`, { method: 'POST', body: { path, new_path: next } });
    if (state.activeFile === path || state.activeFile.startsWith(path + '/')) {
      state.activeFile = next + state.activeFile.slice(path.length);
    }
    await refreshProjectView();
    toast('Переименовано');
  } catch (err) { toast(err.message, 'err'); }
}

async function deleteEntry(path, isDir) {
  if (!confirm(`Удалить «${path}»${isDir ? ' со всем содержимым' : ''}?`)) return;
  try {
    await api(`/api/projects/${state.project.id}/${isDir ? 'folders' : 'files'}?path=${encodeURIComponent(path)}`, { method: 'DELETE' });
    await refreshProjectView();
    toast('Удалено');
  } catch (err) { toast(err.message, 'err'); }
}

function downloadEntry(path) {
  const file = state.project.files.find((f) => f.path === path);
  if (!file) return;
  const blob = new Blob([file.content], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = path.split('/').pop();
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function openTreeMenu(btn) {
  closeTreeMenu();
  const path = btn.dataset.path;
  const isDir = btn.dataset.menu === 'folder';
  const parent = isDir ? path : path.split('/').slice(0, -1).join('/');
  const items = isDir
    ? [
      ['Новый файл', () => createFileIn(path)],
      ['Новая папка', () => createFolderIn(path)],
      ['Переименовать', () => renameEntry(path, true)],
      ['Удалить папку', () => deleteEntry(path, true), true],
    ]
    : [
      ['Открыть', () => { state.activeFile = path; renderProject(state.project.id); }],
      ['Переименовать', () => renameEntry(path, false)],
      ['Скачать', () => downloadEntry(path)],
      ['Удалить', () => deleteEntry(path, false), true],
    ];
  const menu = document.createElement('div');
  menu.className = 'tree-menu';
  items.forEach(([label, fn, danger]) => {
    const b = document.createElement('button');
    b.textContent = label;
    if (danger) b.className = 'danger';
    b.onclick = (e) => { e.stopPropagation(); closeTreeMenu(); fn(); };
    menu.appendChild(b);
  });
  document.body.appendChild(menu);
  const r = btn.getBoundingClientRect();
  const width = 180;
  menu.style.left = Math.max(8, Math.min(window.innerWidth - width - 8, r.right - width)) + 'px';
  menu.style.top = Math.min(window.innerHeight - menu.offsetHeight - 8, r.bottom + 4) + 'px';
  setTimeout(() => document.addEventListener('click', closeTreeMenu, { once: true }), 0);
}

function projectSidebar(p) {
  const others = state.projects.filter((x) => x.id !== p.id);
  return `<div class="vsc-side-head">Файлы проекта</div>
  <div class="vsc-side-actions">
    <button data-action="new-file" title="Новый файл">${svg('plus')} Файл</button>
    <button data-action="new-folder" title="Новая папка">${svg('folder')} Папка</button>
    <button data-action="open-deploy" title="Опубликовать">${svg('rocket')}</button>
  </div>
  <div class="tree-search"><input id="file-search" type="search" placeholder="Поиск по файлам…" value="${esc(state.fileFilter || '')}" autocomplete="off"></div>
  <div class="vsc-side-scroll">
    <div class="vsc-side-section">
      <div class="vsc-side-title">${esc(p.name)} ${p.is_shared ? '<span class="shared-badge">общий</span>' : ''}<span class="grow">${p.files.length}</span></div>
      <div class="tree-row tree-folder tree-root" data-dir="">${chevron(true)}${folderIcon(true)}<span class="tree-name">${esc(p.name)}</span></div>
      ${renderTree(buildFileTree(p.files, p.folders || []), 1, '')}
    </div>
    <div class="vsc-side-section">
      <div class="vsc-side-title">Проект</div>
      <div class="tree-row" data-action="add-files">${svg('plus')}Добавить файлы</div>
      <div class="tree-row" data-action="open-deploy">${svg('rocket')}Опубликовать</div>
      ${p.is_shared ? '' : `<div class="tree-row" data-action="delete-project">${svg('trash')}Удалить проект</div>`}
    </div>
    ${others.length ? `<div class="vsc-side-section"><div class="vsc-side-title">Другие проекты <span class="grow">${others.length}</span></div>${others.map((x) => `<a class="tree-row" data-go="#/project/${x.id}">${svg(x.template?.icon || 'bot')}<span class="tree-name">${esc(x.name)}</span></a>`).join('')}</div>` : ''}
  </div>`;
}

function stripAnsi(value) {
  return String(value || '')
    .replace(/\x1b\][^\x07]*(?:\x07|\x1b\\)/g, '')
    .replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, '')
    .replace(/\r/g, '');
}

function detectRunCommand(p) {
  const files = p.files || [];
  const has = (path) => files.some((f) => f.path === path);
  const pkg = files.find((f) => f.path === 'package.json');
  if (pkg) {
    try {
      const parsed = JSON.parse(pkg.content);
      const script = parsed?.scripts?.start || parsed?.scripts?.dev;
      if (script) return parsed?.scripts?.start ? 'npm start' : 'npm run dev';
    } catch (_) {}
  }
  if (has('src/calculator.js')) return 'node src/calculator.js';
  if (has('main.py')) return 'python3 main.py';
  if (has('bot.py')) return 'python3 bot.py';
  if (has('app.js')) return 'node app.js';
  if (has('index.js')) return 'node index.js';
  return '';
}

function bindTerminal(p) {
  if (state.termSocket) {
    try { state.termSocket.close(); } catch (_) {}
    state.termSocket = null;
  }
  const form = $('#term-form');
  const input = $('#term-input');
  const output = $('#term-output');
  const status = $('#term-status');
  const runBtn = $('#term-run');
  if (!form || !input || !output || !status) return;
  let socket = null;
  let pendingCommand = '';

  const sendCommand = (command) => {
    if (socket?.readyState === WebSocket.OPEN) {
      pendingCommand = '';
      socket.send(command + '\r');
      input.focus();
    } else {
      pendingCommand = command;
    }
  };

  const setStatus = (text, stateName) => {
    status.textContent = text;
    status.className = 'term-status ' + (stateName || '');
  };
  const append = (text) => {
    output.textContent += stripAnsi(text);
    output.scrollTop = output.scrollHeight;
  };

  const connect = () => {
    if (socket) { try { socket.close(); } catch (_) {} }
    const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
    socket = new WebSocket(proto + location.host + `/api/projects/${p.id}/terminal`);
    state.termSocket = socket;
    setStatus('подключаюсь…', 'connecting');
    input.disabled = true;
    socket.onopen = () => {
      if (state.termSocket !== socket) return;
      setStatus('на связи', 'online');
      input.disabled = false;
      input.focus();
      if (pendingCommand) {
        const command = pendingCommand;
        pendingCommand = '';
        socket.send(command + '\r');
      }
    };
    socket.onmessage = (e) => {
      if (state.termSocket !== socket) return;
      append(e.data);
    };
    socket.onerror = () => {
      if (state.termSocket !== socket) return;
      setStatus('ошибка', 'offline');
    };
    socket.onclose = () => {
      if (state.termSocket !== socket) return;
      setStatus('отключено · нажми, чтобы переподключиться', 'offline');
      input.disabled = true;
      append('\n[соединение закрыто]\n');
      status.onclick = connect;
    };
  };

  const runCommand = detectRunCommand(p);
  if (runBtn) {
    runBtn.disabled = !runCommand;
    runBtn.title = runCommand ? `Запустить: ${runCommand}` : 'Нет команды запуска';
    runBtn.onclick = () => {
      if (!runCommand) return;
      const panel = $('.vsc-panel');
      if (panel) {
        panel.classList.remove('collapsed');
        const toggle = panel.querySelector('[data-action="toggle-panel"]');
        if (toggle) toggle.textContent = '⌄';
      }
      pendingCommand = runCommand;
      if (!socket || socket.readyState !== WebSocket.OPEN) connect();
      else sendCommand(runCommand);
    };
  }

  form.onsubmit = (e) => {
    e.preventDefault();
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    const command = input.value;
    if (command.trim() === 'clear') {
      output.textContent = '';
      input.value = '';
      return;
    }
    socket.send(command + '\r');
    input.value = '';
  };
  input.onkeydown = (e) => {
    if (e.key === 'c' && e.ctrlKey) {
      e.preventDefault();
      if (socket?.readyState === WebSocket.OPEN) socket.send('\x03');
    }
  };
  output.onclick = () => input.focus();
  status.onclick = null;
  connect();
  // Терминал должен получить размер панели, чтобы переносы были нормальными.
  const sendSize = () => {
    if (socket?.readyState !== WebSocket.OPEN) return;
    const cols = Math.max(40, Math.floor(output.clientWidth / 7.2));
    const rows = Math.max(8, Math.floor(output.clientHeight / 16));
    socket.send(`__resize__:${rows}x${cols}`);
  };
  setTimeout(sendSize, 300);
}

function projectPanel(p) {
  const acts = p.messages.flatMap((m) => m.meta?.actions || []).slice(-6);
  const deploy = (p.deployment?.log || []).slice(-3);
  const lines = [];
  if (acts.length) {
    lines.push(`<div class="term-line"><span class="term-prompt">$</span> AI-помощник</div>`);
    acts.forEach((a) => lines.push(`<div class="term-line"><span class="term-time">${new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</span><span class="term-ok">✓</span> ${esc(a.summary || 'edit')} <span class="term-dim">${esc(a.path || '')}</span></div>`));
  }
  if (deploy.length) {
    deploy.forEach((x) => lines.push(`<div class="term-line"><span class="term-time">deploy</span><span class="${x.status === 'error' ? 'term-err' : x.status === 'warn' ? 'term-warn' : 'term-ok'}">${x.status === 'error' ? '✗' : x.status === 'warn' ? '!' : '✓'}</span> ${esc(x.message)}</div>`));
  }
  if (!lines.length) lines.push(`<div class="term-line"><span class="term-prompt">$</span> проект готов — открой файл или напиши AI-помощнику</div>`);
  return `<div class="vsc-panel-head"><span class="on">Терминал</span><span class="grow"></span><span class="term-status" id="term-status">подключаюсь…</span><button id="term-run" title="Запустить проект в терминале">▶</button><button data-action="toggle-panel" title="Свернуть">⌄</button></div>
  <div class="vsc-panel-body term-body">
    <div class="term-live">
      <pre class="term-output" id="term-output"></pre>
      <form class="term-form" id="term-form" autocomplete="off">
        <span class="term-prompt">$</span>
        <input id="term-input" type="text" placeholder="Введи команду, например node src/calculator.js" autocomplete="off" spellcheck="false" ${p ? '' : 'disabled'}>
        <button type="submit" title="Выполнить">↵</button>
      </form>
    </div>
    <details class="term-actions-log"><summary>Действия агента</summary>${lines.join('')}</details>
  </div>`;
}

function renderMarkdown(text) {
  const blocks = [];
  const raw = String(text || '').replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, body) => {
    const i = blocks.push({ lang, body }) - 1;
    return `\uE100${i}\uE101`;
  });
  let html = esc(raw);
  html = html.replace(/((?:^\|.*\|\s*$\n?)+)/gm, (block) => {
    const rows = block.trim().split('\n').map((line) => line.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim()));
    const sep = rows.findIndex((r) => r.every((c) => /^:?-{3,}:?$/.test(c)));
    if (sep < 1) return block;
    const head = rows[sep - 1];
    const body = rows.slice(sep + 1);
    return `<div class="msg-table-wrap"><table class="msg-table"><thead><tr>${head.map((c) => `<th>${c}</th>`).join('')}</tr></thead><tbody>${body.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  });
  html = html.replace(/^\s{0,3}###\s+(.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^\s{0,3}##\s+(.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^\s{0,3}#\s+(.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\n/g, '<br>');
  html = html.replace(/\uE100(\d+)\uE101/g, (_, i) => {
    const b = blocks[Number(i)];
    return `<pre class="msg-code"><code>${highlightCode(b.body, 'x.' + (b.lang || 'txt'))}</code></pre>`;
  });
  return html;
}

function chatView(p) {
  const isCode = p.template.direction === 'code';
  return `<div class="chat">
    <div class="chat-log" id="chat-log">
      ${p.messages.map((m, idx) => `<div class="msg ${m.role === 'user' ? 'user' : ''}">
        ${m.meta?.image ? `<img class="msg-shot" src="${esc(m.meta.image)}" alt="Скриншот">` : ''}
        ${m.meta?.ocr ? `<details class="msg-ocr"><summary>Текст со скриншота</summary><span>${esc(m.meta.ocr)}</span></details>` : ''}
        <div class="b">${m.role === 'user' ? esc(m.content) : renderMarkdown(m.content)}</div>
        ${m.meta?.steps?.length ? `<details class="agent-steps"><summary>${svg('spark')} Шаги агента · ${m.meta.steps.length}</summary><div class="step-list">${m.meta.steps.map((s) => `<div class="step-row ${s.kind}">${s.kind === 'thinking' ? svg('spark') : svg('terminal')}<div><b>${s.kind === 'thinking' ? 'Размышление' : esc(s.tool || 'Инструмент')}</b><span>${esc(s.text || '')}</span></div></div>`).join('')}</div></details>` : ''}
        ${m.meta?.actions?.length ? `<div class="acts">${m.meta.actions.map((a) => `<span>✓ ${esc(a.summary || a.path)}</span>`).join('')}</div>` : ''}
        <div class="meta">${m.role === 'user' ? 'Ты' : 'AI-помощник'} · ${ago(m.created_at)}${m.meta?.mode ? ' · ' + m.meta.mode : ''}${m.meta?.tokens ? ' · ' + tokensFull(m.meta.tokens) + ' токенов' : ''}</div>
      </div>`).join('')}
      ${p.messages.length <= 1 ? `<div class="chat-hints">
        <span class="small dim" style="width:100%">Попробуй:</span>
        ${isCode ? `
          <button data-quick="покажи структуру">Покажи структуру</button>
          <button data-quick="объясни main.py">Объясни main.py</button>
          <button data-quick="добавь README">Добавь README</button>
        ` : `
          <button data-quick="добавь меню: Услуги, Записаться, Цены, Связаться">Добавь меню</button>
          <button data-quick="цены: стрижка — 3500, маникюр — 2500">Обнови цены</button>
          <button data-quick="цвет #8b5cf6">Смени цвет</button>
          <button data-quick="включи оплату Stars">Включи оплату</button>
        `}
      </div>` : ''}
      ${state.sending ? `<div class="live-steps" id="live-steps"><div class="live-head"><span class="spinner"></span><b>Агент работает</b><span class="live-count" id="live-count">${state.liveSteps.length} шагов</span></div><div class="live-current" id="live-current">${state.liveSteps.length ? `<b>${esc(liveStepLabel(state.liveSteps[state.liveSteps.length - 1]))}</b><span>${esc(liveStepDetail(state.liveSteps[state.liveSteps.length - 1]))}</span>` : 'Агент читает проект…'}</div></div>` : ''}
    </div>
    <form class="chat-form" id="chat-form">
      ${state.chatImage ? `<div class="chat-attachment"><img src="${esc(state.chatImage)}" alt="Скриншот"><button type="button" id="remove-shot" title="Убрать">×</button></div>` : ''}
      <input type="file" id="shot-input" accept="image/png,image/jpeg,image/webp" hidden>
      <div class="chat-input-row">
        <button class="btn ghost shot" type="button" id="shot-btn" title="Прикрепить скриншот" aria-label="Прикрепить скриншот" ${state.sending ? 'disabled' : ''}>${svg('paperclip')}</button>
        <textarea name="message" rows="1" placeholder="${isCode ? 'Опиши задачу: создай файл, объясни код…' : 'Напиши задачу: «добавь меню: Услуги, Записаться, Цены, Связаться»'}" ${state.sending ? 'disabled' : ''}></textarea>
        <button class="btn ghost mic" type="button" id="voice-btn" title="Голосовой ввод" ${state.sending ? 'disabled' : ''}>${svg('mic')}</button>
        <button class="btn primary" type="submit" ${state.sending ? 'disabled' : ''}>${svg('send')}</button>
      </div>
      <div class="chat-hint">Enter — отправить · Shift+Enter — строка · микрофон — голосом · скрепка или Ctrl+V — скриншот</div>
    </form>
  </div>`;
}

function escCode(value) {
  return String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function highlightJSON(src) {
  let html = escCode(src);
  const keys = []; const strs = [];
  html = html.replace(/"(?:\\.|[^"\\])*"(?=\s*:)/g, (m) => `\uE000k${keys.push(m) - 1}\uE001`);
  html = html.replace(/"(?:\\.|[^"\\])*"/g, (m) => `\uE000s${strs.push(m) - 1}\uE001`);
  html = html.replace(/\b(true|false|null)\b/g, '<span class="tok-bool">$1</span>');
  html = html.replace(/\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b/g, '<span class="tok-num">$&</span>');
  html = html.replace(/([{}[\],:])/g, '<span class="tok-punc">$1</span>');
  html = html.replace(/\uE000k(\d+)\uE001/g, (_, i) => `<span class="tok-key">${keys[Number(i)]}</span>`);
  html = html.replace(/\uE000s(\d+)\uE001/g, (_, i) => `<span class="tok-str">${strs[Number(i)]}</span>`);
  return html;
}

function highlightPython(src) {
  let html = escCode(src);
  const strs = []; const comments = [];
  html = html.replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, (m) => `\uE000s${strs.push(m) - 1}\uE001`);
  html = html.replace(/#[^\n]*/g, (m) => `\uE002c${comments.push(m) - 1}\uE001`);
  html = html.replace(/\b(def|class|return|if|elif|else|for|while|in|not|and|or|import|from|as|with|try|except|finally|pass|break|continue|None|True|False|async|await|yield|lambda|global|nonlocal|raise|assert|del|is)\b/g, '<span class="tok-kw">$1</span>');
  html = html.replace(/\b\d+(?:\.\d+)?\b/g, '<span class="tok-num">$&</span>');
  html = html.replace(/\b([A-Za-z_]\w*)(?=\s*\()/g, '<span class="tok-fn">$1</span>');
  html = html.replace(/\uE002c(\d+)\uE001/g, (_, i) => `<span class="tok-com">${comments[Number(i)]}</span>`);
  html = html.replace(/\uE000s(\d+)\uE001/g, (_, i) => `<span class="tok-str">${strs[Number(i)]}</span>`);
  return html;
}

function highlightJS(src) {
  let html = escCode(src);
  const strs = []; const comments = [];
  html = html.replace(/("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)/g, (m) => `\uE000s${strs.push(m) - 1}\uE001`);
  html = html.replace(/\/\*[\s\S]*?\*\//g, (m) => `\uE002c${comments.push(m) - 1}\uE001`);
  html = html.replace(/\/\/[^\n]*/g, (m) => `\uE002c${comments.push(m) - 1}\uE001`);
  html = html.replace(/\b(const|let|var|function|return|if|else|for|while|new|class|extends|import|from|export|default|async|await|try|catch|finally|throw|typeof|instanceof|in|of|this|true|false|null|undefined)\b/g, '<span class="tok-kw">$1</span>');
  html = html.replace(/\b\d+(?:\.\d+)?\b/g, '<span class="tok-num">$&</span>');
  html = html.replace(/\b([A-Za-z_$]\w*)(?=\s*\()/g, '<span class="tok-fn">$1</span>');
  html = html.replace(/\uE002c(\d+)\uE001/g, (_, i) => `<span class="tok-com">${comments[Number(i)]}</span>`);
  html = html.replace(/\uE000s(\d+)\uE001/g, (_, i) => `<span class="tok-str">${strs[Number(i)]}</span>`);
  return html;
}

function highlightHTML(src) {
  let html = escCode(src);
  html = html.replace(/&lt;!--[\s\S]*?--&gt;/g, '<span class="tok-com">$&</span>');
  html = html.replace(/(&lt;\/?)([A-Za-z][\w-]*)/g, '$1<span class="tok-kw">$2</span>');
  html = html.replace(/([A-Za-z-]+)=("[^"]*")/g, '<span class="tok-key">$1</span>=<span class="tok-str">$2</span>');
  return html;
}

function highlightCSS(src) {
  let html = escCode(src);
  const strs = [];
  html = html.replace(/("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, (m) => `\uE000s${strs.push(m) - 1}\uE001`);
  html = html.replace(/\/\*[\s\S]*?\*\//g, '<span class="tok-com">$&</span>');
  html = html.replace(/([.#]?[A-Za-z][\w-]*)(?=\s*\{)/g, '<span class="tok-fn">$1</span>');
  html = html.replace(/([\w-]+)(?=\s*:)/g, '<span class="tok-key">$1</span>');
  html = html.replace(/\b\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw)?\b/g, '<span class="tok-num">$&</span>');
  html = html.replace(/\uE000s(\d+)\uE001/g, (_, i) => `<span class="tok-str">${strs[Number(i)]}</span>`);
  return html;
}

function highlightMarkdown(src) {
  let html = escCode(src);
  html = html.replace(/^(#{1,6})\s+(.+)$/gm, '<span class="tok-kw">$1</span> <span class="tok-key">$2</span>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<span class="tok-bool">**$1**</span>');
  html = html.replace(/`([^`]+)`/g, '<span class="tok-num">`$1`</span>');
  return html;
}

function highlightCode(text, path) {
  const ext = (path.split('.').pop() || '').toLowerCase();
  if (ext === 'json') return highlightJSON(text);
  if (ext === 'py') return highlightPython(text);
  if (['js', 'mjs', 'cjs', 'ts'].includes(ext)) return highlightJS(text);
  if (['html', 'htm'].includes(ext)) return highlightHTML(text);
  if (ext === 'css') return highlightCSS(text);
  if (['md', 'markdown'].includes(ext)) return highlightMarkdown(text);
  return escCode(text);
}

function fileLang(path) {
  const ext = (path.split('.').pop() || '').toLowerCase();
  return ({ json: 'JSON', py: 'Python', js: 'JavaScript', mjs: 'JavaScript', cjs: 'JavaScript', ts: 'TypeScript', html: 'HTML', htm: 'HTML', css: 'CSS', md: 'Markdown', txt: 'Plain Text', yml: 'YAML', yaml: 'YAML', sh: 'Shell', sql: 'SQL' }[ext]) || 'Plain Text';
}

function minimapHTML(text) {
  const lines = text.split('\n');
  const step = Math.max(1, Math.ceil(lines.length / 140));
  const bars = [];
  for (let i = 0; i < lines.length; i += step) {
    const line = lines[i];
    const t = line.trim();
    let width = Math.min(40, 3 + Math.min(t.length, 60) * 0.6);
    let color = 'rgba(140,140,140,.4)';
    if (/^[}\])]/.test(t)) color = 'rgba(255,92,122,.5)';
    else if (/["'`]/.test(t)) color = 'rgba(206,145,120,.6)';
    else if (/#|\/\//.test(t)) color = 'rgba(106,153,85,.6)';
    else if (/\b(def|class|function|const|let|var|import|from)\b/.test(t)) color = 'rgba(197,134,192,.6)';
    else if (/\b\d+(?:\.\d+)?\b/.test(t)) color = 'rgba(181,206,168,.55)';
    bars.push(`<i style="width:${width}px;background:${color}"></i>`);
  }
  return bars.join('');
}

function fileView(p) {
  const file = p.files.find((f) => f.path === state.activeFile) || p.files[0];
  if (!file) return '<div class="empty">Файлов нет</div>';
  const lineCount = Math.max(1, file.content.split('\n').length);
  const numbers = Array.from({ length: lineCount }, (_, i) => i + 1).join('\n');
  return `<div class="file-editor">
    <div class="bar"><span class="mono">${esc(file.path)}</span><span class="dim">${file.content.length} символов</span><button class="btn sm" id="save-file" style="margin-left:auto">${svg('save')}Сохранить</button></div>
    <div class="code-wrap">
      <div class="gutter" id="gutter">${numbers}</div>
      <div class="code-area">
        <pre class="code-layer" id="code-layer" aria-hidden="true" spellcheck="false"><code>${highlightCode(file.content, file.path)}</code></pre>
        <textarea id="file-content" spellcheck="false" wrap="off">${esc(file.content)}</textarea>
      </div>
      <div class="minimap" id="minimap" title="Миникарта: клик — перейти">
        <div class="minimap-lines" id="minimap-lines">${minimapHTML(file.content)}</div>
        <div class="minimap-view" id="minimap-view"></div>
      </div>
    </div>
  </div>`;
}

function previewView(p) {
  const t = p.template.direction;
  if (t === 'code') {
    const readme = p.files.find((f) => f.path.toLowerCase() === 'readme.md');
    const html = p.files.find((f) => f.path.toLowerCase() === 'index.html');
    return `<div class="agent-report">${esc(readme?.content || (html ? 'Это HTML-проект. Открой index.html слева и попроси AI-помощника запустить или поправить его.' : 'Папка загружена. Файлы слева, AI-помощник справа. Скажи, что сделать.'))}</div><div class="preview-note">Твой проект · ${filesWord(p.files.length)}</div>`;
  }
  if (t === 'miniapp') {
    return `<iframe class="miniapp-frame" src="/api/projects/${p.id}/preview?v=${Date.now()}" title="Мини-апп" sandbox="allow-scripts allow-same-origin"></iframe><div class="preview-note">Так приложение выглядит в Telegram</div>`;
  }
  if (t === 'agent') {
    const sample = p.files.find((f) => f.path === 'sample_output.md')?.content || 'Агент пока не прислал отчёт. Запусти его из чата.';
    return `<div class="agent-report">${esc(sample)}</div><div class="preview-note">Пример отчёта агента</div>`;
  }
  return telegramPreview(p);
}

function telegramPreview(p) {
  const contentFile = p.files.find((f) => f.path === 'content.json');
  let content = null;
  try { content = JSON.parse(contentFile?.content || '{}'); } catch (_) {}
  if (!content || !content.business) return '<div class="empty">Нет content.json</div>';
  if (!state.preview || state.preview.projectId !== p.id) {
    state.preview = {
      projectId: p.id,
      messages: [{ role: 'bot', text: content.greeting || 'Здравствуйте!' }],
    };
  }
  const msg = state.preview.messages.map((m) => `<div class="tg-b ${m.role === 'user' ? 'me' : ''}">${esc(m.text)}</div>`).join('');
  const buttons = (content.menu || []).map((b) => `<button data-tg-action="${esc(b.id)}">${esc(b.title)}</button>`).join('') + `<button data-tg-action="faq">Частые вопросы</button>`;
  return `<div class="phone" style="--acc:${esc(content.business.accent || '#ff4f8b')}">
    <div class="ph-top"><div class="ph-av">${esc((content.business.name || 'Б').slice(0,1))}</div><div><div class="ph-name">${esc(content.business.name)}</div><div class="ph-sub">бот · онлайн</div></div></div>
    <div class="ph-body" id="tg-body">${msg}<div class="tg-kb">${buttons}</div></div>
  </div><div class="preview-note">Эмулятор Telegram · нажимай кнопки</div>`;
}

function tgAction(action) {
  const p = state.project;
  const contentFile = p.files.find((f) => f.path === 'content.json');
  let content = {};
  try { content = JSON.parse(contentFile?.content || '{}'); } catch (_) {}
  if (!state.preview) state.preview = { projectId: p.id, messages: [] };
  const known = { 'услуги': 'services', 'записаться': 'book', 'запись': 'book', 'цены': 'prices', 'прайс': 'prices', 'связаться': 'contact', 'контакты': 'contact', 'вопросы': 'faq', 'частые вопросы': 'faq', 'программа': 'program', 'подарок': 'gift', 'уроки': 'lessons' };
  action = known[String(action).toLowerCase()] || action;
  const prices = (content.prices || []).map((x) => `${x.title} — ${x.price}`).join('\n');
  const faq = (content.faq || []).map((x) => `${x.q}\n${x.a}`).join('\n\n');
  const map = {
    services: prices || 'Услуги скоро появятся.',
    prices: prices || 'Цены скоро появятся.',
    program: prices || 'Программа скоро появится.',
    book: `Запись: ${content.contact || 'напишите администратору'}`,
    contact: `Связаться: ${content.contact || 'напишите администратору'}`,
    gift: 'Подарок уже ждёт: напишите «гайд» — пришлю.',
    lessons: 'Уроки открываются в личном кабинете. Ссылка — в закрепе.',
    faq: faq || 'Вопросы скоро появятся.',
    back: content.greeting || 'Здравствуйте!',
  };
  const label = (content.menu || []).find((x) => x.id === action)?.title || (action === 'faq' ? 'Частые вопросы' : action);
  state.preview.messages.push({ role: 'user', text: label });
  state.preview.messages.push({ role: 'bot', text: map[action] || content.greeting || 'Здравствуйте!' });
  renderProject(p.id);
}

function compressChatImage(file) {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) return reject(new Error('Это не изображение'));
    if (file.size > 10 * 1024 * 1024) return reject(new Error('Скриншот больше 10 МБ'));
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('Не удалось прочитать файл'));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error('Не удалось открыть изображение'));
      img.onload = () => {
        const max = 1600;
        const scale = Math.min(1, max / Math.max(img.width, img.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round(img.width * scale));
        canvas.height = Math.max(1, Math.round(img.height * scale));
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        let data = '';
        for (const q of [0.86, 0.72, 0.58]) {
          data = canvas.toDataURL('image/webp', q);
          if (data.length < 2_400_000) break;
        }
        resolve(data);
      };
      img.src = String(reader.result);
    };
    reader.readAsDataURL(file);
  });
}

async function attachChatImage(file) {
  const image = await compressChatImage(file);
  state.chatImage = image;
  const form = $('#chat-form');
  if (!form) return image;
  form.querySelector('.chat-attachment')?.remove();
  const box = document.createElement('div');
  box.className = 'chat-attachment';
  box.innerHTML = `<img src="${esc(image)}" alt="Скриншот"><button type="button" id="remove-shot" title="Убрать">×</button>`;
  box.querySelector('button').onclick = () => {
    state.chatImage = null;
    box.remove();
  };
  form.insertBefore(box, form.querySelector('.chat-input-row'));
  return image;
}

document.addEventListener('paste', async (e) => {
  const form = $('#chat-form');
  if (!form || form.contains(e.target)) return;
  if (e.target?.closest?.('.vsc-editor-area')) return;
  const items = Array.from(e.clipboardData?.items || []);
  const fromItem = items.find((x) => x.type.startsWith('image/'))?.getAsFile();
  const fromFiles = Array.from(e.clipboardData?.files || []).find((f) => f.type.startsWith('image/'));
  const file = fromItem || fromFiles;
  if (!file) return;
  e.preventDefault();
  try {
    await attachChatImage(file);
    form.querySelector('textarea')?.focus();
    toast('Скриншот из буфера прикреплён');
  } catch (err) {
    toast(err.message || 'Не удалось вставить скриншот', 'err');
  }
});

function bindChatForm(form) {
  if (!form) return;
  const ta = form.message;
  const shotInput = form.querySelector('#shot-input');
  const shotBtn = form.querySelector('#shot-btn');
  const removeShot = () => {
    state.chatImage = null;
    form.querySelector('.chat-attachment')?.remove();
  };
  form.querySelector('#remove-shot')?.addEventListener('click', removeShot);
  if (shotBtn && shotInput) {
    shotBtn.onclick = () => shotInput.click();
    shotInput.onchange = async () => {
      const file = shotInput.files?.[0];
      shotInput.value = '';
      if (!file) return;
      try {
        await attachChatImage(file);
        toast('Скриншот прикреплён');
      } catch (err) {
        toast(err.message || 'Не удалось прикрепить скриншот', 'err');
      }
    };
  }
  const grow = () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(170, Math.max(38, ta.scrollHeight)) + 'px';
  };
  ta.addEventListener('input', grow);
  ta.addEventListener('paste', async (e) => {
    const items = Array.from(e.clipboardData?.items || []);
    const fromItem = items.find((x) => x.type.startsWith('image/'))?.getAsFile();
    const fromFiles = Array.from(e.clipboardData?.files || []).find((f) => f.type.startsWith('image/'));
    const file = fromItem || fromFiles;
    if (!file) return;
    e.preventDefault();
    try {
      await attachChatImage(file);
      toast('Скриншот из буфера прикреплён');
    } catch (err) {
      toast(err.message || 'Не удалось вставить скриншот', 'err');
    }
  });
  grow();
  ta.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      form.requestSubmit();
    }
  });
  const mic = form.querySelector('#voice-btn');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!mic) return;
  if (!SR) {
    mic.onclick = () => toast('Голосовой ввод поддерживают Chrome и Edge', 'err');
    return;
  }
  let rec = null;
  let guard = null;
  let started = false;
  let base = '';
  const resetMic = () => {
    if (guard) clearTimeout(guard);
    guard = null;
    started = false;
    rec = null;
    mic.classList.remove('recording');
    mic.title = 'Голосовой ввод';
  };
  mic.onclick = () => {
    if (rec) {
      try { rec.stop(); } catch (_) {}
      return;
    }
    rec = new SR();
    rec.lang = 'ru-RU';
    rec.interimResults = true;
    rec.continuous = false;
    rec.maxAlternatives = 1;
    base = ta.value.trim();
    mic.classList.add('recording');
    mic.title = 'Слушаю… нажми, чтобы остановить';
    toast('Говори…');
    rec.onstart = () => {
      started = true;
      if (guard) clearTimeout(guard);
      guard = null;
    };
    rec.onresult = (e) => {
      let text = '';
      for (let i = e.resultIndex; i < e.results.length; i += 1) text += e.results[i][0].transcript;
      ta.value = (base ? base + ' ' : '') + text.trim();
      grow();
    };
    rec.onend = resetMic;
    rec.onerror = (e) => {
      const map = {
        'not-allowed': 'Разреши микрофон в адресной строке браузера',
        'service-not-allowed': 'Браузер заблокировал сервис распознавания',
        'audio-capture': 'Микрофон не найден',
        'no-speech': 'Ничего не услышал, попробуй ещё раз',
        network: 'Нет связи с сервисом распознавания речи',
      };
      toast(map[e.error] || 'Не удалось распознать голос', 'err');
      resetMic();
    };
    try {
      rec.start();
      guard = setTimeout(() => {
        if (!rec || started) return;
        toast('Браузер не дал доступ к микрофону. Разреши его в адресной строке.', 'err');
        try { rec.stop(); } catch (_) {}
        resetMic();
      }, 8000);
    } catch (err) {
      toast('Не удалось запустить микрофон: ' + (err?.message || err), 'err');
      resetMic();
    }
  };
}

function bindResizers() {
  const sr = document.querySelector('[data-resize="sidebar"]');
  if (sr) {
    sr.onpointerdown = (e) => {
      e.preventDefault();
      const wb = sr.closest('.vsc-workbench');
      const startX = e.clientX;
      const start = state.sideWidth;
      const move = (ev) => {
        state.sideWidth = Math.max(190, Math.min(420, start + (ev.clientX - startX)));
        wb.style.setProperty('--side-w', state.sideWidth + 'px');
      };
      const up = () => {
        localStorage.setItem('school-side-w', state.sideWidth);
        document.removeEventListener('pointermove', move);
        document.removeEventListener('pointerup', up);
        document.body.classList.remove('resizing');
      };
      document.body.classList.add('resizing');
      document.addEventListener('pointermove', move);
      document.addEventListener('pointerup', up);
    };
  }
  const aux = document.querySelector('[data-resize="aux"]');
  if (aux) {
    aux.onpointerdown = (e) => {
      e.preventDefault();
      const main = aux.closest('.ide-main');
      const startX = e.clientX;
      const start = state.auxWidth;
      const move = (ev) => {
        const max = Math.max(320, Math.min(760, window.innerWidth - 520));
        state.auxWidth = Math.max(300, Math.min(max, start + (startX - ev.clientX)));
        main.style.setProperty('--aux-w', state.auxWidth + 'px');
      };
      const up = () => {
        localStorage.setItem('school-aux-w', state.auxWidth);
        document.removeEventListener('pointermove', move);
        document.removeEventListener('pointerup', up);
        document.body.classList.remove('resizing');
      };
      document.body.classList.add('resizing');
      document.addEventListener('pointermove', move);
      document.addEventListener('pointerup', up);
    };
  }
  const pr = document.querySelector('[data-resize="panel"]');
  if (pr) {
    pr.onpointerdown = (e) => {
      e.preventDefault();
      const area = pr.closest('.vsc-editor-area');
      const startY = e.clientY;
      const start = state.panelHeight;
      const move = (ev) => {
        state.panelHeight = Math.max(90, Math.min(area.clientHeight * 0.62, start + (startY - ev.clientY)));
        area.style.setProperty('--panel-h', state.panelHeight + 'px');
      };
      const up = () => {
        localStorage.setItem('school-panel-h', state.panelHeight);
        document.removeEventListener('pointermove', move);
        document.removeEventListener('pointerup', up);
        document.body.classList.remove('resizing');
      };
      document.body.classList.add('resizing');
      document.addEventListener('pointermove', move);
      document.addEventListener('pointerup', up);
    };
  }
}

function liveStepLabel(s) {
  if (s.type === 'status') return 'Статус';
  if (s.type === 'thinking') return 'Думает';
  return s.tool || 'Инструмент';
}

function liveStepDetail(s) {
  if (s.type === 'thinking') return '';
  const text = String(s.text || '').replace(/\s+/g, ' ').trim();
  return text.length > 90 ? text.slice(0, 90) + '…' : text;
}

function appendLiveStep(ev) {
  const box = $('#live-steps');
  if (!box) return;
  const count = box.querySelector('#live-count');
  const current = box.querySelector('#live-current');
  if (count) count.textContent = `${state.liveSteps.length} шагов`;
  if (current) {
    current.innerHTML = `<b>${esc(liveStepLabel(ev))}</b><span>${esc(liveStepDetail(ev))}</span>`;
  }
  scrollChat();
}

async function sendChat(e) {
  e.preventDefault();
  const form = e.target;
  const message = form.message.value.trim() || (state.chatImage ? 'Посмотри скриншот' : '');
  if (!message || state.sending) return;
  state.sending = true;
  state.liveSteps = [];
  const image = state.chatImage;
  state.chatImage = null;
  const p = state.project;
  const beforeFiles = Object.fromEntries(p.files.map((f) => [f.path, f.content]));
  p.messages.push({ role: 'user', content: message, created_at: new Date().toISOString(), meta: image ? { image } : {} });
  renderProject(p.id);
  try {
    const res = await fetch(`/api/projects/${p.id}/chat/stream`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, image }),
    });
    if (!res.ok) {
      let detail = 'Агент не ответил';
      try { detail = (await res.json()).detail || detail; } catch (_) {}
      throw new Error(detail);
    }
    if (!res.body) throw new Error('Браузер не поддерживает потоковый ответ');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let payload = null;
    let streamError = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';
      for (const part of parts) {
        const line = part.split('\n').find((x) => x.startsWith('data: '));
        if (!line) continue;
        let msg = null;
        try { msg = JSON.parse(line.slice(6)); } catch (_) { continue; }
        if (msg.type === 'step') {
          state.liveSteps.push(msg.event);
          appendLiveStep(msg.event);
        } else if (msg.type === 'done') {
          payload = msg.payload;
        } else if (msg.type === 'error') {
          streamError = msg.message || 'Ошибка агента';
        }
      }
    }
    if (streamError) throw new Error(streamError);
    if (!payload) throw new Error('Агент не вернул результат');

    state.project = payload.project;
    if (hasLocalFolder(p.id)) {
      const changed = payload.project.files.filter((f) => beforeFiles[f.path] !== f.content);
      for (const f of changed) {
        try { await writeLocalPath(state.folderHandle, f.path, f.content); } catch (_) { /* доступ к папке мог быть отозван */ }
      }
    }
    state.sending = false;
    state.liveSteps = [];
    const me = await api('/api/me');
    state.user = me.user;
    renderProject(p.id);
    toast(`Готово · −${tokensFull(payload.tokens)} токенов`);
  } catch (err) {
    state.sending = false;
    state.liveSteps = [];
    state.chatImage = image;
    state.project.messages.pop();
    renderProject(p.id);
    toast(err.message, 'err');
  }
}

async function saveFile() {
  const p = state.project;
  const content = $('#file-content').value;
  try {
    await api(`/api/projects/${p.id}/files`, { method: 'PUT', body: { path: state.activeFile, content } });
    const file = p.files.find((f) => f.path === state.activeFile);
    if (file) file.content = content;
    state.dirty = false;
    let local = false;
    if (hasLocalFolder(p.id)) {
      try {
        await writeLocalPath(state.folderHandle, state.activeFile, content);
        local = true;
      } catch (_) {
        toast('В облаке сохранено, локальная папка недоступна', 'err');
      }
    }
    toast(local ? 'Сохранено в облако и в папку' : 'Файл сохранён');
    renderProject(p.id);
  } catch (err) { toast(err.message, 'err'); }
}

function scrollChat() {
  const log = $('#chat-log');
  if (log) log.scrollTop = log.scrollHeight;
}

/* ---------- deploy ---------- */
const BINARY_EXT = new Set(['png','jpg','jpeg','gif','webp','ico','pdf','zip','rar','7z','gz','tgz','mp3','mp4','mov','avi','wav','woff','woff2','ttf','otf','pyc','exe','dll','so','dylib','db','sqlite','bin']);

async function uploadFiles(fileList, p) {
  const files = [...fileList];
  const accepted = [];
  let skipped = 0;
  for (const f of files) {
    const ext = f.name.split('.').pop().toLowerCase();
    if (BINARY_EXT.has(ext) || f.name === '.env' || f.size > 1_000_000) { skipped += 1; continue; }
    try {
      const text = await f.text();
      if (text.includes('\u0000')) { skipped += 1; continue; }
      accepted.push({ path: (f.webkitRelativePath || f.name).replace(/\\/g, '/'), content: text });
    } catch (_) { skipped += 1; }
  }
  if (!accepted.length) {
    toast('Нет текстовых файлов для добавления', 'err');
    return;
  }
  try {
    for (const file of accepted) {
      await api(`/api/projects/${p.id}/files`, { method: 'PUT', body: file });
    }
    const fresh = await api('/api/projects/' + p.id);
    state.project = fresh.project;
    renderProject(p.id);
    toast(`Добавлено ${filesWord(accepted.length)}${skipped ? ` · ${filesWord(skipped)} пропущено` : ''}`);
  } catch (err) { toast(err.message, 'err'); }
}

function addFilesPicker(p) {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.onchange = () => uploadFiles(input.files, p);
  input.click();
}

function bindDrop(p) {
  const main = $('.ide-main');
  const overlay = $('#drop-overlay');
  if (!main || !overlay) return;
  let depth = 0;
  main.addEventListener('dragenter', (e) => {
    e.preventDefault();
    depth += 1;
    overlay.classList.add('on');
  });
  main.addEventListener('dragover', (e) => e.preventDefault());
  main.addEventListener('dragleave', (e) => {
    e.preventDefault();
    depth = Math.max(0, depth - 1);
    if (!depth) overlay.classList.remove('on');
  });
  main.addEventListener('drop', (e) => {
    e.preventDefault();
    depth = 0;
    overlay.classList.remove('on');
    const files = Array.from(e.dataTransfer?.files || []);
    if (!files.length) return;
    const images = files.filter((f) => f.type.startsWith('image/'));
    const rest = files.filter((f) => !f.type.startsWith('image/'));
    if (images.length) {
      attachChatImage(images[0])
        .then(() => toast('Скриншот прикреплён к сообщению'))
        .catch((err) => toast(err.message, 'err'));
    }
    if (rest.length) uploadFiles(rest, p);
  });
}

async function importFolder() {
  if (typeof window.showDirectoryPicker === 'function') {
    try {
      const handle = await window.showDirectoryPicker();
      await importDirectoryHandle(handle);
      return;
    } catch (err) {
      if (err?.name === 'AbortError') return;
      toast(err?.message || 'Не удалось открыть папку', 'err');
      return;
    }
  }
  toast('Браузер не умеет открывать папку — загружаю копию');
  openFolderFallback();
}

function openFolderFallback() {
  const input = document.createElement('input');
  input.type = 'file';
  input.webkitdirectory = true;
  input.multiple = true;
  input.onchange = async () => {
    const all = [...input.files];
    if (!all.length) return;
    const root = (all[0].webkitRelativePath || '').split('/')[0] || 'Мой проект';
    const files = [];
    let skipped = 0;
    for (const f of all) {
      const rel = (f.webkitRelativePath || f.name).split('/').slice(1).join('/') || f.name;
      const ext = f.name.split('.').pop().toLowerCase();
      if (!rel || rel.startsWith('.git/') || rel.includes('/node_modules/') || BINARY_EXT.has(ext) || f.name === '.env' || f.size > 1_000_000) {
        skipped += 1;
        continue;
      }
      try {
        const text = await f.text();
        if (text.includes('\u0000')) { skipped += 1; continue; }
        files.push({ path: rel, content: text });
      } catch (_) {
        skipped += 1;
      }
      if (files.length >= 1500) break;
    }
    await importProjectFiles(root, files, skipped, null);
  };
  input.click();
}

async function importDirectoryHandle(handle) {
  const files = [];
  let skipped = 0;
  const skipDirs = new Set(['.git', 'node_modules', '.dsh', '__pycache__', '.venv', 'venv', 'private']);
  const skipPaths = new Set(['data/db', 'data/competitors', 'docs/course/video', 'docs/research/media', 'platform/data']);
  const note = document.createElement('div');
  note.className = 'folder-progress';
  note.innerHTML = `<div class="spinner"></div><div><b>Читаю папку «${esc(handle.name)}»</b><span>0 файлов…</span></div>`;
  document.body.appendChild(note);
  const update = () => { const s = note.querySelector('span'); if (s) s.textContent = `${files.length} файлов · ${skipped} пропущено`; };
  async function walk(dir, prefix) {
    for await (const [name, entry] of dir.entries()) {
      if (files.length >= 1500) return;
      const rel = prefix ? `${prefix}/${name}` : name;
      if (entry.kind === 'directory') {
        if (skipDirs.has(name) || [...skipPaths].some((p) => rel === p || rel.startsWith(p + '/'))) { skipped += 1; continue; }
        await walk(entry, rel);
        continue;
      }
      const ext = name.split('.').pop().toLowerCase();
      if (!rel || BINARY_EXT.has(ext) || name === '.env') { skipped += 1; continue; }
      try {
        const file = await entry.getFile();
        if (file.size > 1_000_000) { skipped += 1; continue; }
        const text = await file.text();
        if (text.includes('\u0000')) { skipped += 1; continue; }
        files.push({ path: rel, content: text });
        update();
      } catch (_) {
        skipped += 1;
      }
    }
  }
  try {
    await walk(handle, '');
  } finally {
    note.remove();
  }
  await importProjectFiles(handle.name || 'Мой проект', files, skipped, handle);
}

async function importProjectFiles(root, files, skipped, handle) {
  if (!files.length) {
    toast('В папке нет текстовых файлов', 'err');
    return;
  }
  toast(`Читаю ${filesWord(files.length)}…`);
  try {
    const data = await api('/api/projects/import', { method: 'POST', body: { name: root, files } });
    state.folderHandle = handle || null;
    state.folderProjectId = handle ? data.id : null;
    await refreshBase();
    await refreshUser();
    location.hash = '#/project/' + data.id;
    toast(handle ? 'Папка открыта: изменения сохраняются локально' : (skipped ? `Проект открыт · ${filesWord(skipped)} пропущено` : 'Проект открыт'));
  } catch (err) {
    toast(err.message, 'err');
  }
}

async function ensureLocalWrite(handle) {
  try {
    if (!handle?.requestPermission) return false;
    return (await handle.requestPermission({ mode: 'readwrite' })) === 'granted';
  } catch (_) {
    return false;
  }
}

async function writeLocalPath(root, path, content) {
  if (!(await ensureLocalWrite(root))) throw new Error('Нет доступа на запись в локальную папку');
  const parts = path.split('/').filter(Boolean);
  let dir = root;
  for (let i = 0; i < parts.length - 1; i += 1) {
    dir = await dir.getDirectoryHandle(parts[i], { create: true });
  }
  const fileHandle = await dir.getFileHandle(parts[parts.length - 1], { create: true });
  const writable = await fileHandle.createWritable();
  await writable.write(content);
  await writable.close();
}

function hasLocalFolder(projectId) {
  return Boolean(state.folderHandle && state.folderProjectId === projectId);
}

function openDeploy() {
  const p = state.project;
  const existing = p.deployment;
  const modal = document.createElement('div');
  modal.className = 'modal-bg';
  modal.innerHTML = `<div class="modal">
    <div class="between"><h3>Опубликовать проект</h3><button class="btn sm ghost" id="deploy-close">✕</button></div>
    <div class="sub">Создай бота в @BotFather, скопируй токен и вставь сюда. Платформа проверит его через getMe.</div>
    ${existing?.bot_username ? `<div class="badge green" style="margin-bottom:10px">Уже опубликован: @${esc(existing.bot_username)}</div>` : ''}
    <form id="deploy-form">
      <div class="field"><label>Токен бота</label><input name="token" placeholder="123456789:AA..." autocomplete="off"></div>
      <div id="deploy-log"></div>
      <button class="btn primary" style="width:100%;margin-top:12px" type="submit">Проверить и опубликовать</button>
    </form>
    <div class="hint-row">MVP: токен проверяется, деплой записывается. 24/7-рантайм — следующий этап.</div>
  </div>`;
  document.body.appendChild(modal);
  $('#deploy-close').onclick = () => modal.remove();
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  $('#deploy-form').onsubmit = doDeploy;
}

async function doDeploy(e) {
  e.preventDefault();
  const form = e.target;
  const token = form.token.value.trim();
  const btn = form.querySelector('button[type=submit]');
  const log = $('#deploy-log') || form.querySelector('#deploy-log');
  btn.disabled = true;
  log.innerHTML = '<div class="log-row"><span class="dot"></span><span>Проверяем токен…</span></div>';
  try {
    const data = await api(`/api/projects/${state.project.id}/deploy`, { method: 'POST', body: { token } });
    log.innerHTML = data.log.map((x) => `<div class="log-row ${x.status}"><span class="dot"></span><span><b>${esc(x.step)}</b> · ${esc(x.message)}</span></div>`).join('');
    toast('Бот @' + data.username + ' опубликован');
    const fresh = await api('/api/projects/' + state.project.id);
    state.project = fresh.project;
    await refreshUser();
    setTimeout(() => { document.querySelector('.modal-bg')?.remove(); renderProject(state.project.id); }, 900);
  } catch (err) {
    log.innerHTML = `<div class="log-row error"><span class="dot"></span><span>${esc(err.message)}</span></div>`;
    btn.disabled = false;
  }
}

/* ---------- lessons ---------- */
function renderLessons() {
  const done = state.lessons.filter((l) => l.done).length;
  const total = state.lessons.length || 6;
  const pct = Math.round((done / total) * 100);
  const next = state.lessons.find((l) => !l.done) || state.lessons[state.lessons.length - 1];
  const content = `
  <section class="course-hero">
    <div class="course-copy">
      <div class="course-kicker">ТЕСТ-ДРАЙВ · 48 ЧАСОВ</div>
      <h1>Собери первого<br>AI-агента</h1>
      <p>Пять коротких шагов и финал. В каждом уроке — артефакт: бот, агент, мини-апп или оффер. Не просмотр, а запуск.</p>
      <div class="course-actions">
        <button class="btn primary" data-go="#/lesson/${next.id}">${done ? 'Продолжить' : 'Начать'} ${svg('arrow')}</button>
        <button class="btn ghost" data-go="#/templates">Собрать проект</button>
      </div>
      <div class="course-meta">
        <span>${svg('clock')} ~50 минут</span>
        <span>${svg('spark')} 5 артефактов</span>
        <span>${svg('shield')} без установки</span>
      </div>
    </div>
    <div class="course-progress">
      <div class="ring" style="--p:${pct}">
        <div class="ring-in"><b>${pct}%</b><span>пройдено</span></div>
      </div>
      <div class="course-progress-note">${done} из ${total} уроков</div>
    </div>
  </section>

  <div class="course-layout">
    <div class="course-main">
      <div class="course-section-head"><h2>Программа</h2><span>${total} шагов · артефакт в каждом</span></div>
      <div class="lesson-grid">
        ${state.lessons.map((l) => `
          <article class="lesson-card-v2 ${l.done ? 'done' : ''} ${!l.done && l.id === next.id ? 'current' : ''}" data-go="#/lesson/${l.id}" role="button" tabindex="0">
            <div class="lesson-num">${l.done ? '✓' : l.number}</div>
            <div class="lesson-body">
              <div class="lesson-title-row">
                <h3>${esc(l.title)}</h3>
                ${!l.done && l.id === next.id ? '<span class="lesson-pill">дальше</span>' : ''}
              </div>
              <p>${esc(l.subtitle)}</p>
              <div class="lesson-meta">
                <span>${svg('clock')} ${l.minutes} мин</span>
                ${l.done ? '<span class="lesson-done">пройден</span>' : `<span class="lesson-open">открыть ${svg('arrow')}</span>`}
              </div>
            </div>
          </article>`).join('')}
      </div>
    </div>

    <aside class="course-side">
      <div class="side-card next-card">
        <div class="eyebrow">Следующий шаг</div>
        <div class="next-num">${String(next.number).padStart(2, '0')}</div>
        <h3>${esc(next.title)}</h3>
        <p>${esc(next.subtitle)}</p>
        <button class="btn light" data-go="#/lesson/${next.id}">${next.done ? 'Повторить' : 'Продолжить'} ${svg('arrow')}</button>
      </div>
      <div class="side-card final-card">
        <div class="eyebrow">Финал</div>
        <h3>Покажи проект</h3>
        <p>Собери один продукт, покажи превью и получи персональный разбор.</p>
        <button class="btn ghost" data-go="#/templates">Собрать проект ${svg('arrow')}</button>
      </div>
    </aside>
  </div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();
}

function renderLesson(id) {
  const l = state.lessons.find((x) => x.id === id);
  if (!l) { location.hash = '#/lessons'; return; }
  const idx = state.lessons.findIndex((x) => x.id === id);
  const next = state.lessons[idx + 1];
  const content = `
  <div class="lesson-detail">
    <a class="small dim" href="#/lessons">← Все уроки</a>
    <div class="row" style="margin-top:12px;gap:8px"><span class="badge gold">Урок ${l.number}</span><span class="badge">${l.minutes} мин</span>${l.done ? '<span class="badge green">Пройден</span>' : ''}</div>
    <h1 style="margin-top:12px;font-size:34px">${esc(l.title)}</h1>
    <div class="sub" style="color:var(--muted);font-size:16px;margin-top:8px">${esc(l.subtitle)}</div>
    <div class="card" style="margin-top:20px">
      <h3>Что разбираем</h3>
      <ul class="lesson-list">${l.bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>
      <div class="task-box"><b>Задание.</b> ${esc(l.task)}</div>
      <div class="row" style="margin-top:16px">
        ${l.done ? `<span class="badge green">${svg('check')} Урок пройден</span>` : `<button class="btn primary" data-action="complete-lesson" data-id="${l.id}">${svg('check')}Отметить пройденным</button>`}
        ${next ? `<button class="btn" data-go="#/lesson/${next.id}">Следующий урок ${svg('arrow')}</button>` : `<button class="btn" data-go="#/templates">К шаблонам ${svg('arrow')}</button>`}
      </div>
    </div>
    <div class="card" style="margin-top:14px;background:rgba(255,209,102,.05);border-color:rgba(255,209,102,.25)">
      <div class="row">${ic('spark','sm')}<div><b style="font-size:13px">Не останавливайся на видео</b><div class="small muted">Дойди до артефакта: проект, превью, деплой. Именно это показывают клиенту.</div></div></div>
    </div>
  </div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();
}

async function completeLesson(id) {
  try {
    await api(`/api/lessons/${id}/complete`, { method: 'POST' });
    await refreshBase();
    await refreshUser();
    toast('Урок пройден');
    renderLesson(id);
  } catch (err) { toast(err.message, 'err'); }
}

/* ---------- billing ---------- */
async function renderBilling() {
  const target = location.hash;
  try {
    state.usage = (await api('/api/usage')).usage;
    state.packages = (await api('/api/billing/packages')).packages || [];
  } catch (_) {}
  if (location.hash !== target) return;
  const balance = Number(state.user.token_balance || 0);
  const spent = Number(state.user.tokens_spent || 0);
  const total = balance + spent;
  const pct = total > 0 ? Math.max(2, Math.round((spent / total) * 100)) : 0;
  const requestsLeft = Math.max(0, Math.floor(balance / 6000));
  const packages = state.packages.length ? state.packages : [];
  const content = `
  <div class="page-head"><div><div class="eyebrow">Баланс</div><h1>Токены и счётчик</h1><div class="sub">Сейчас демо: пакеты начисляются бесплатно. В проде токены начисляются только после оплаты.</div></div></div>
  <div class="grid g3">
    <div class="card hl">
      <div class="eyebrow">Доступно</div>
      <div style="font-family:Unbounded;font-size:38px;font-weight:800;margin-top:6px;line-height:1.05">${tokensFull(balance)} <span style="font-size:15px;font-weight:600;color:var(--muted)">токенов</span></div>
      <div class="progress" style="margin-top:12px"><i style="width:${100 - pct}%"></i></div>
      <div class="small muted" style="margin-top:8px">Потрачено ${tokensFull(spent)} · примерно ${tokensFull(requestsLeft)} ${plural(requestsLeft, 'запрос', 'запроса', 'запросов')}</div>
    </div>
    <div class="card">
      <div class="eyebrow">Как это работает</div>
      <div class="small muted" style="margin-top:8px;line-height:1.6">1 запрос ≈ 6 000 токенов. 1 млн токенов ≈ 160 запросов. Пакет 1 млн — 390 ₽.</div>
      <div class="token-rule"><b>Ты покупаешь токены оптом</b><span>Ученик покупает пакет, платформа списывает только фактические токены запроса. Остаток виден в счётчике.</span></div>
    </div>
    <div class="card">
      <div class="eyebrow">Демо-пополнение</div>
      <div class="pkg-grid" style="margin-top:10px">
        ${packages.map((p) => `<button class="pkg" data-action="topup" data-package="${esc(p.id)}"><span class="pkg-name">${esc(p.name)}</span><b>${tokensShort(p.tokens)}</b><span class="pkg-price">${rub(p.price_rub)}</span></button>`).join('')}
      </div>
      <div class="small dim" style="margin-top:8px">Это демо: до 5 млн токенов на аккаунт, без оплаты. В проде — Robokassa/Stars.</div>
    </div>
  </div>
  <div class="card" style="margin-top:16px">
    <div class="between" style="margin-bottom:10px"><h3>История токенов</h3><span class="small dim">последние 30 операций</span></div>
    <table class="table"><thead><tr><th>Когда</th><th>Тип</th><th>Проект</th><th class="r">Токены</th><th class="r">Сумма</th></tr></thead><tbody>
      ${state.usage.length ? state.usage.map((u) => {
        const n = Number(u.tokens || (Number(u.tokens_in || 0) + Number(u.tokens_out || 0)));
        const top = u.kind === 'topup';
        const demo = Boolean(u.demo);
        const type = top ? (demo ? '<span class="badge gold">демо</span>' : '<span class="badge green">пополнение</span>') : '<span class="badge">запрос</span>';
        const amount = top ? (demo ? '—' : rub(u.price_rub)) : money(u.price_rub);
        return `<tr><td>${ago(u.created_at)}</td><td>${type}</td><td>${esc(u.project_name || '—')}</td><td class="r mono ${top ? 'green' : ''}">${top ? '+' : '−'}${tokensFull(n)}</td><td class="r">${amount}</td></tr>`;
      }).join('') : '<tr><td colspan="5" class="dim">Пока пусто</td></tr>'}
    </tbody></table>
  </div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();
}

/* ---------- profile ---------- */
function openLocalTerminal(device) {
  document.querySelector('.local-term-modal')?.remove();
  const modal = document.createElement('div');
  modal.className = 'local-term-modal';
  modal.innerHTML = `<div class="local-term-box"><div class="local-term-head"><b>${esc(device.name)}</b><span class="term-status" id="local-term-status">подключаюсь…</span><span class="grow"></span><button type="button" id="local-term-close">×</button></div><pre class="local-term-output" id="local-term-output"></pre><form class="local-term-form" id="local-term-form"><span class="term-prompt">$</span><input id="local-term-input" placeholder="Команда на твоём компьютере…" autocomplete="off" spellcheck="false"><button type="submit">↵</button></form></div>`;
  document.body.appendChild(modal);
  const out = modal.querySelector('#local-term-output');
  const input = modal.querySelector('#local-term-input');
  const status = modal.querySelector('#local-term-status');
  const close = () => { try { ws.close(); } catch (_) {} modal.remove(); };
  modal.querySelector('#local-term-close').onclick = close;
  const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
  const ws = new WebSocket(proto + location.host + `/api/devices/${device.id}/terminal`);
  ws.onopen = () => { status.textContent = 'на связи'; status.className = 'term-status online'; input.focus(); };
  ws.onmessage = (e) => { out.textContent += stripAnsi(e.data); out.scrollTop = out.scrollHeight; };
  ws.onclose = () => { status.textContent = 'отключено'; status.className = 'term-status offline'; };
  ws.onerror = () => { status.textContent = 'ошибка'; status.className = 'term-status offline'; };
  modal.querySelector('#local-term-form').onsubmit = (e) => {
    e.preventDefault();
    if (ws.readyState !== WebSocket.OPEN) return;
    const command = input.value;
    ws.send(JSON.stringify({ type: 'input', data: command + '\r' }));
    input.value = '';
  };
  modal.querySelector('#local-term-input').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
}

async function bindDevices() {
  const btn = $('#pair-device');
  const list = $('#devices-list');
  if (!btn || !list) return;
  const render = (devices) => {
    list.innerHTML = devices.length ? devices.map((d) => `<div class="device-row"><div class="device-info"><b>${esc(d.name)}</b><span>${esc(d.root || 'папка не указана')}</span></div><i class="device-status ${d.online ? 'online' : ''}">${d.online ? 'online' : 'offline'}</i><button class="btn sm" data-device-term="${d.id}" ${d.online ? '' : 'disabled'}>Терминал</button><button class="tree-more" data-device-del="${d.id}" title="Удалить">×</button></div>`).join('') : '<div class="small dim" style="margin-top:10px">Пока нет подключённых компьютеров.</div>';
    list.querySelectorAll('[data-device-term]').forEach((b) => b.onclick = () => {
      const device = devices.find((d) => d.id === Number(b.dataset.deviceTerm));
      if (device) openLocalTerminal(device);
    });
    list.querySelectorAll('[data-device-del]').forEach((b) => b.onclick = async () => {
      if (!confirm('Отключить этот компьютер?')) return;
      try { await api('/api/devices/' + b.dataset.deviceDel, { method: 'DELETE' }); await load(); } catch (err) { toast(err.message, 'err'); }
    });
  };
  const load = async () => {
    try { render((await api('/api/devices')).devices || []); } catch (_) {}
  };
  btn.onclick = async () => {
    btn.disabled = true;
    try {
      const data = await api('/api/devices/pair', { method: 'POST', body: {} });
      const cmd = `node local-runner/runner.mjs --server ${location.origin} --code ${data.code} --dir "C:\\путь\\к\\твоей\\папке"`;
      $('#pair-result').innerHTML = `<div class="pair-box"><div class="eyebrow">Код сопряжения</div><b>${data.code}</b><p>Запусти в папке проекта:</p><pre>${esc(cmd)}</pre><button class="btn sm" id="pair-refresh">Проверить подключение</button></div>`;
      $('#pair-refresh').onclick = load;
      await load();
      const timer = setInterval(async () => { await load(); if (list.querySelector('.device-status.online')) clearInterval(timer); }, 3000);
    } catch (err) { toast(err.message, 'err'); }
    btn.disabled = false;
  };
  await load();
}

async function renderProfile() {
  const target = location.hash;
  let events = [];
  try { events = (await api('/api/me/events')).events || []; } catch (_) {}
  if (location.hash !== target) return;
  const u = state.user;
  const initials = String(u.name || u.email || 'U').split(/\s+/).map((x) => x[0]).slice(0, 2).join('').toUpperCase();
  const done = state.lessons.filter((l) => l.done).length;
  const labels = {
    register: 'Регистрация', login: 'Вход', page_view: 'Открыл экран', project_open: 'Открыл проект',
    project_create: 'Создал проект', project_import: 'Открыл папку', folder_open: 'Открыл папку',
    chat: 'Запрос AI-помощнику', file_save: 'Сохранил файл', deploy: 'Опубликовал бота',
    deploy_error: 'Ошибка деплоя', lesson_complete: 'Прошёл урок', profile_open: 'Открыл профиль',
  };
  const content = `
  <section class="profile-hero">
    <div class="avatar-lg">${esc(initials)}</div>
    <div>
      <div class="eyebrow">Аккаунт</div>
      <h1>${esc(u.name)}</h1>
      <div class="small muted">${esc(u.email)} · ${u.role === 'admin' ? 'админ' : 'ученик'} · с ${new Date(u.created_at).toLocaleDateString('ru-RU')}</div>
    </div>
    <div class="profile-balance">
      <div class="eyebrow">Токены</div>
      <b>${tokensShort(u.token_balance)}</b>
      <span>потрачено ${tokensShort(u.tokens_spent)}</span>
    </div>
  </section>
  <div class="grid g4">
    <div class="card stat"><div class="v">${state.projects.length}</div><div class="l">проектов</div></div>
    <div class="card stat"><div class="v">${done}/6</div><div class="l">уроков</div></div>
    <div class="card stat"><div class="v">${tokensShort(u.tokens_spent)}</div><div class="l">токенов сожжено</div></div>
    <div class="card stat"><div class="v">${u.last_seen_at ? ago(u.last_seen_at) : '—'}</div><div class="l">последняя активность</div></div>
  </div>
  <div class="grid g2" style="margin-top:16px">
    <div class="card">
      <h3>Настройки аккаунта</h3>
      <form id="profile-form" style="margin-top:12px">
        <div class="field"><label>Имя</label><input name="name" value="${esc(u.name)}" maxlength="80" required></div>
        <div class="field"><label>Email</label><input value="${esc(u.email)}" disabled></div>
        <button class="btn primary" type="submit">Сохранить имя</button>
      </form>
      <div class="profile-sep"></div>
      <h3>Сменить пароль</h3>
      <form id="password-form" style="margin-top:10px">
        <div class="field"><label>Текущий пароль</label><input name="current_password" type="password" required autocomplete="current-password"></div>
        <div class="field"><label>Новый пароль</label><input name="new_password" type="password" required minlength="10" placeholder="Минимум 10 символов" autocomplete="new-password"></div>
        <div class="field"><label>Повтори новый</label><input name="confirm_password" type="password" required minlength="10" autocomplete="new-password"></div>
        <button class="btn primary" type="submit">Сменить пароль</button>
      </form>
    </div>
    <div class="card">
      <div class="between"><h3>Мой компьютер</h3><span class="badge">local runner</span></div>
      <div class="small dim" style="margin:8px 0 10px">Подключи свой ПК, чтобы выполнять команды и работать с файлами локально. Пока это терминал; файлы и DSH — следующий шаг.</div>
      <button class="btn primary" id="pair-device">Подключить компьютер</button>
      <div id="pair-result"></div>
      <div id="devices-list" class="devices-list"></div>
    </div>
    <div class="card">
      <div class="between"><h3>Последние действия</h3><span class="small dim">${events.length}</span></div>
      <div class="activity-list">
        ${events.length ? events.slice(0, 14).map((e) => `<div class="activity-row"><span class="activity-dot"></span><div><b>${esc(labels[e.kind] || e.kind)}</b><span>${ago(e.created_at)}</span></div></div>`).join('') : '<div class="vsc-side-empty">Пока нет событий</div>'}
      </div>
    </div>
  </div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();
  const form = $('#profile-form');
  if (form) form.onsubmit = async (e) => {
    e.preventDefault();
    const name = new FormData(form).get('name');
    try {
      const data = await api('/api/me', { method: 'PATCH', body: { name } });
      state.user = data.user;
      toast('Имя сохранено');
      renderProfile();
    } catch (err) { toast(err.message, 'err'); }
  };
  const pwForm = $('#password-form');
  if (pwForm) pwForm.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(pwForm);
    const current = String(fd.get('current_password') || '');
    const next = String(fd.get('new_password') || '');
    const confirm = String(fd.get('confirm_password') || '');
    if (next !== confirm) { toast('Новые пароли не совпадают', 'err'); return; }
    try {
      await api('/api/me/password', { method: 'POST', body: { current_password: current, new_password: next } });
      state.user = null;
      location.hash = '#/login';
      renderAuth();
      toast('Пароль изменён — войди заново');
    } catch (err) { toast(err.message, 'err'); }
  };
  await bindDevices();
}

/* ---------- admin ---------- */
async function renderAdmin() {
  if (state.user?.role !== 'admin') { location.hash = '#/dashboard'; return; }
  const target = location.hash;
  try { state.admin = await api('/api/admin/stats'); } catch (err) { toast(err.message, 'err'); location.hash = '#/dashboard'; return; }
  if (location.hash !== target) return;
  const a = state.admin;
  const maxDay = Math.max(1, ...a.activity.map((d) => d.events));
  const eventLabels = {
    page_view: 'экраны', project_open: 'проекты', project_create: 'создание', project_import: 'импорт папки',
    chat: 'запросы', file_save: 'сохранения', deploy: 'деплой', login: 'входы', register: 'регистрации',
    lesson_complete: 'уроки', profile_open: 'профиль', folder_open: 'папки',
  };
  const content = `
  <div class="page-head"><div><div class="eyebrow">Админка</div><h1>Люди и активность</h1><div class="sub">Кто заходит, что делает, сколько проектов и токенов сжигает.</div></div></div>
  <div class="grid g4">
    <div class="card stat"><div class="v">${a.active_7d}</div><div class="l">активных за 7 дней</div><div class="s">DAU ${a.active_1d} · 30д ${a.active_30d}</div></div>
    <div class="card stat"><div class="v">${a.projects}</div><div class="l">проектов</div><div class="s">+${a.new_users_7d} новых за 7 дней</div></div>
    <div class="card stat"><div class="v">${tokensShort(a.tokens_used)}</div><div class="l">токенов сожжено</div><div class="s">~${tokensFull(a.avg_tokens)} на запрос</div></div>
    <div class="card stat"><div class="v">${rub(a.margin)}</div><div class="l">маржа</div><div class="s">выручка ${rub(a.revenue)}</div></div>
  </div>
  <div class="card" style="margin-top:16px">
    <div class="between"><h3>Активность за 7 дней</h3><span class="small dim">${a.events_7d} событий</span></div>
    <div class="activity-chart">
      ${a.activity.map((d) => `<div class="ac-col"><b>${d.events}</b><i style="height:${Math.max(4, Math.round(d.events / maxDay * 86))}px"></i><span>${d.day.slice(8, 10)}.${d.day.slice(5, 7)}</span></div>`).join('')}
    </div>
    <div class="event-pills">
      ${a.event_counts.slice(0, 8).map((e) => `<span>${esc(eventLabels[e.kind] || e.kind)} <b>${e.c}</b></span>`).join('')}
    </div>
  </div>
  <div class="grid g2" style="margin-top:16px">
    <div class="card"><div class="between"><h3>Пользователи</h3><span class="small dim">клик — детали</span></div><table class="table" style="margin-top:8px"><thead><tr><th>Email</th><th>Был</th><th class="r">Проекты</th><th class="r">События</th><th class="r">Токены</th><th class="r">Баланс</th></tr></thead><tbody>
      ${a.recent_users.map((u) => `<tr class="click-row" data-action="user-detail" data-user-id="${u.id}"><td>${esc(u.email)}</td><td class="dim">${u.last_seen_at ? ago(u.last_seen_at) : '—'}</td><td class="r">${u.projects}</td><td class="r">${u.events_count}</td><td class="r mono">${tokensShort(u.tokens_used)}</td><td class="r mono">${tokensShort(u.token_balance)}</td></tr>`).join('')}
    </tbody></table></div>
    <div class="card"><h3>Проекты</h3><table class="table" style="margin-top:8px"><thead><tr><th>Название</th><th>Шаблон</th><th>Статус</th><th>Автор</th></tr></thead><tbody>
      ${a.recent_projects.map((p) => `<tr><td>${esc(p.name)}</td><td class="mono">${esc(p.template_id)}</td><td>${statusBadge(p.status)}</td><td>${esc(p.email)}</td></tr>`).join('')}
    </tbody></table></div>
  </div>
  <div class="card" style="margin-top:16px"><h3>Последние действия</h3><table class="table" style="margin-top:8px"><thead><tr><th>Когда</th><th>Кто</th><th>Событие</th><th class="r">Проект</th></tr></thead><tbody>
    ${a.recent_events.map((e) => `<tr><td>${ago(e.created_at)}</td><td>${esc(e.email)}</td><td><span class="badge">${esc(eventLabels[e.kind] || e.kind)}</span></td><td class="r dim">${e.project_id ? '#' + e.project_id : '—'}</td></tr>`).join('')}
  </tbody></table></div>
  <div class="card" style="margin-top:16px"><h3>Движение токенов</h3><table class="table" style="margin-top:8px"><thead><tr><th>Когда</th><th>Кто</th><th>Тип</th><th class="r">Токены</th><th class="r">Цена</th><th class="r">Себестоимость</th></tr></thead><tbody>
    ${a.recent_usage.map((u) => {
      const n = Number(u.tokens || (Number(u.tokens_in || 0) + Number(u.tokens_out || 0)));
      const top = u.kind === 'topup';
      const demo = Boolean(u.demo);
      const type = top ? (demo ? '<span class="badge gold">демо</span>' : '<span class="badge green">покупка</span>') : '<span class="badge">запрос</span>';
      return `<tr><td>${ago(u.created_at)}</td><td>${esc(u.email)}</td><td>${type}</td><td class="r mono ${top ? 'green' : ''}">${top ? '+' : '−'}${tokensFull(n)}</td><td class="r">${demo ? '—' : money(u.price_rub)}</td><td class="r dim">${money(u.cost_rub)}</td></tr>`;
    }).join('')}
  </tbody></table></div>`;
  $('#app').innerHTML = layout(content, { panel: null });
  bindCommon();
}

async function openUserDetail(userId) {
  try {
    const data = await api('/api/admin/users/' + userId);
    const u = data.user;
    const modal = document.createElement('div');
    modal.className = 'modal-bg';
    modal.innerHTML = `<div class="modal" style="max-width:760px">
      <div class="between"><div><div class="eyebrow">Пользователь</div><h3>${esc(u.name)}</h3><div class="small muted">${esc(u.email)} · ${u.role} · создан ${new Date(u.created_at).toLocaleDateString('ru-RU')}</div></div><button class="btn sm ghost" id="user-close">✕</button></div>
      <div class="grid g4" style="margin:16px 0">
        <div class="card stat"><div class="v">${data.stats.projects}</div><div class="l">проектов</div></div>
        <div class="card stat"><div class="v">${data.stats.messages}</div><div class="l">сообщений</div></div>
        <div class="card stat"><div class="v">${tokensShort(u.tokens_spent)}</div><div class="l">токенов</div></div>
        <div class="card stat"><div class="v">${data.stats.lessons_done}/6</div><div class="l">уроков</div></div>
      </div>
      <div class="grid g2">
        <div><h3>Проекты</h3>${data.projects.length ? data.projects.map((p) => `<div class="log-row"><span class="dot"></span><span><b>${esc(p.name)}</b> · ${esc(p.template_id)} · ${statusBadge(p.status)}</span></div>`).join('') : '<div class="vsc-side-empty">Нет проектов</div>'}</div>
        <div><h3>Последние действия</h3>${data.events.length ? data.events.slice(0, 12).map((e) => `<div class="activity-row"><span class="activity-dot"></span><div><b>${esc(e.kind)}</b><span>${ago(e.created_at)}</span></div></div>`).join('') : '<div class="vsc-side-empty">Нет событий</div>'}</div>
      </div>
      <div class="small dim" style="margin-top:14px">Последняя активность: ${u.last_seen_at ? ago(u.last_seen_at) : '—'} · баланс ${tokensFull(u.token_balance)} токенов</div>
    </div>`;
    document.body.appendChild(modal);
    modal.querySelector('#user-close').onclick = () => modal.remove();
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  } catch (err) { toast(err.message, 'err'); }
}

/* ---------- common actions ---------- */
function openProjectMenu(btn) {
  closeTreeMenu();
  const id = Number(btn.dataset.projectMenu);
  const project = state.projects.find((p) => p.id === id);
  if (!project) return;
  const isOwner = project.user_id === state.user?.id;
  const toggleShare = ['Сделать ' + (project.is_shared ? 'личным' : 'общим'), async () => {
    try {
      await api('/api/projects/' + id, { method: 'PATCH', body: { is_shared: !project.is_shared } });
      await refreshBase();
      if (state.project?.id === id) { await refreshProjectView(); }
      else { render(); }
      toast(project.is_shared ? 'Проект снова личный' : 'Проект открыт для всех зарегистрированных');
    } catch (err) { toast(err.message, 'err'); }
  }];
  const items = [
    ['Открыть', () => { location.hash = '#/project/' + id; }],
    ...(isOwner ? [toggleShare] : []),
    ...(isOwner && !project.is_shared ? [
      ['Переименовать', async () => {
        const name = prompt('Название проекта', project.name);
        if (!name || name === project.name) return;
        try { await api('/api/projects/' + id, { method: 'PATCH', body: { name } }); await refreshBase(); render(); } catch (err) { toast(err.message, 'err'); }
      }],
      ['Удалить', async () => {
        if (!confirm(`Удалить проект «${project.name}»?`)) return;
        try {
          await api('/api/projects/' + id, { method: 'DELETE' });
          await refreshBase();
          if (location.hash === '#/project/' + id) { location.hash = '#/dashboard'; }
          else { render(); }
          toast('Проект удалён');
        } catch (err) { toast(err.message, 'err'); }
      }, true],
    ] : []),
  ];
  const menu = document.createElement('div');
  menu.className = 'tree-menu project-menu';
  items.forEach(([label, fn, danger]) => {
    const b = document.createElement('button');
    b.textContent = label;
    if (danger) b.className = 'danger';
    b.onclick = (e) => { e.stopPropagation(); closeTreeMenu(); fn(); };
    menu.appendChild(b);
  });
  document.body.appendChild(menu);
  const r = btn.getBoundingClientRect();
  menu.style.left = Math.max(8, Math.min(window.innerWidth - 188, r.right - 180)) + 'px';
  menu.style.top = Math.min(window.innerHeight - menu.offsetHeight - 8, r.bottom + 4) + 'px';
  setTimeout(() => document.addEventListener('click', closeTreeMenu, { once: true }), 0);
}

function bindCommon() {
  // delegated data-go handled globally
}

document.addEventListener('click', async (e) => {
  const quick = e.target.closest('[data-quick]');
  if (quick) {
    const ta = $('#chat-form textarea');
    if (ta) { ta.value = quick.dataset.quick; ta.focus(); }
    return;
  }
  const pm = e.target.closest('[data-project-menu]');
  if (pm) { e.preventDefault(); e.stopPropagation(); openProjectMenu(pm); return; }
  const go = e.target.closest('[data-go]');
  if (go) { e.preventDefault(); location.hash = go.dataset.go; return; }
  const action = e.target.closest('[data-action]');
  if (!action) return;
  const a = action.dataset.action;
  if (a === 'logout') {
    try { await api('/api/auth/logout', { method: 'POST' }); } catch (_) {}
    state.user = null; state.projects = []; state.project = null;
    location.hash = '#/login'; renderAuth();
  } else if (a === 'topup') {
    const packageId = action.dataset.package || 'start';
    try {
      const data = await api('/api/billing/topup', { method: 'POST', body: { package_id: packageId } });
      await refreshUser();
      toast(data.demo ? `Демо: +${tokensFull(data.added)} токенов` : `+${tokensFull(data.added)} токенов`);
      renderBilling();
    } catch (err) { toast(err.message, 'err'); }
  } else if (a === 'user-detail') {
    openUserDetail(action.dataset.userId);
  } else if (a === 'complete-lesson') {
    completeLesson(action.dataset.id);
  } else if (a === 'open-deploy') {
    openDeploy();
  } else if (a === 'open-folder') {
    importFolder();
  } else if (a === 'toggle-aux') {
    state.auxWidth = state.auxWidth > 500 ? 380 : Math.min(720, Math.round(window.innerWidth * 0.55));
    localStorage.setItem('school-aux-w', state.auxWidth);
    if (state.project) renderProject(state.project.id);
  } else if (a === 'add-files') {
    if (state.project) addFilesPicker(state.project);
  } else if (a === 'new-file') {
    if (state.project) createFileIn('');
  } else if (a === 'new-folder') {
    if (state.project) createFolderIn('');
  } else if (a === 'rename-project') {
    if (!state.project) return;
    const name = prompt('Название проекта', state.project.name);
    if (!name || name === state.project.name) return;
    try {
      await api('/api/projects/' + state.project.id, { method: 'PATCH', body: { name } });
      await refreshProjectView();
      toast('Проект переименован');
    } catch (err) { toast(err.message, 'err'); }
  } else if (a === 'toggle-focus') {
    state.focusMode = !state.focusMode;
    localStorage.setItem('school-focus', state.focusMode ? '1' : '0');
    if (state.project) renderProject(state.project.id);
  } else if (a === 'toggle-theme') {
    document.body.classList.toggle('theme-light');
    localStorage.setItem('school-theme', document.body.classList.contains('theme-light') ? 'light' : 'dark');
  } else if (a === 'delete-project') {
    if (!confirm('Удалить проект? Это действие нельзя отменить.')) return;
    try { await api('/api/projects/' + state.project.id, { method: 'DELETE' }); state.project = null; await refreshBase(); await refreshUser(); toast('Проект удалён'); location.hash = '#/dashboard'; } catch (err) { toast(err.message, 'err'); }
  } else if (a === 'toggle-panel') {
    action.closest('.vsc-panel')?.classList.toggle('collapsed');
    action.textContent = action.closest('.vsc-panel')?.classList.contains('collapsed') ? '⌃' : '⌄';
  }
});

/* ---------- router ---------- */
async function refreshBase() {
  const [cat, prj, les] = await Promise.all([api('/api/catalog'), api('/api/projects'), api('/api/lessons')]);
  state.templates = cat.templates;
  state.projects = prj.projects;
  state.lessons = les.lessons;
}

async function refreshUser() {
  const me = await api('/api/me');
  state.user = me.user;
}

async function render() {
  const hash = location.hash || '#/dashboard';
  if (!state.user) { renderAuth(); return; }
  document.body.classList.remove('auth-mode');
  track('page_view', { path: hash.split('?')[0] });
  if (hash.startsWith('#/project/')) {
    const id = Number(hash.split('/')[2]);
    await renderProject(id);
  } else if (hash.startsWith('#/new/')) {
    renderBrief(hash.split('/')[2]);
  } else if (hash.startsWith('#/lesson/')) {
    renderLesson(hash.split('/')[2]);
  } else if (hash.startsWith('#/templates')) {
    renderTemplates();
  } else if (hash.startsWith('#/lessons')) {
    renderLessons();
  } else if (hash.startsWith('#/billing')) {
    await renderBilling();
  } else if (hash.startsWith('#/profile')) {
    track('profile_open');
    await renderProfile();
  } else if (hash.startsWith('#/admin')) {
    await renderAdmin();
  } else {
    renderDashboard();
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && state.focusMode && state.project) {
    state.focusMode = false;
    localStorage.setItem('school-focus', '0');
    renderProject(state.project.id);
  }
});

async function boot() {
  const savedTheme = localStorage.getItem('school-theme');
  document.body.classList.toggle('theme-light', savedTheme === 'light');
  try {
    const me = await api('/api/me');
    state.user = me.user;
    await refreshBase();
  } catch (_) { state.user = null; }
  window.addEventListener('hashchange', render);
  if (!state.user) { state.authMode = 'login'; renderAuth(); return; }
  if (!location.hash) location.hash = '#/dashboard';
  render();
}

boot();



