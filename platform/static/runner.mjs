#!/usr/bin/env node
/**
 * School Platform local runner — MVP.
 *
 * Запуск:
 *   node local-runner/runner.mjs --server https://school.91-184-242-178.sslip.io:8443 \
 *     --code 123456 --dir "C:\Users\NikSouk\Desktop\Proj\school-funnel"
 *
 * После первого pairing токен сохраняется в local-runner/.device.json.
 * Дальше можно запускать без --code.
 */
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import readline from 'node:readline/promises';

const here = dirname(fileURLToPath(import.meta.url));
const configPath = join(here, '.device.json');
const argv = process.argv.slice(2);
const arg = (name) => {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 ? argv[i + 1] : '';
};

let server = (arg('server') || process.env.SCHOOL_SERVER || 'https://school.91-184-242-178.sslip.io:8443').replace(/\/+$/, '');
let code = arg('code');
let root = arg('dir');
let name = arg('name') || 'Мой компьютер';
const forcePair = argv.includes('--force-pair');

if (code && !forcePair && existsSync(configPath)) {
  try {
    const saved = JSON.parse(readFileSync(configPath, 'utf8'));
    if (saved.token) {
      console.log('[runner] Использую сохранённый токен; для новой пары добавь --force-pair');
      code = '';
      server = saved.server || server;
      root = root || saved.root;
    }
  } catch {}
}

if (!code && existsSync(configPath)) {
  try {
    const saved = JSON.parse(readFileSync(configPath, 'utf8'));
    server = saved.server || server;
    root = root || saved.root;
    if (saved.token) {
      console.log(`[runner] Подключаюсь как ${saved.name || name} к ${server}`);
    }
  } catch {}
}

if (!root) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  root = (await rl.question('Папка для работы: ')).trim();
  rl.close();
}
if (!existsSync(root) || !statSync(root).isDirectory()) {
  console.error(`[runner] Папка не найдена: ${root}`);
  process.exit(1);
}

async function pair() {
  const res = await fetch(`${server}/api/devices/claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, name, root }),
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
  return res.json();
}

async function getToken() {
  if (code) {
    const data = await pair();
    writeFileSync(configPath, JSON.stringify({ server, token: data.token, device_id: data.device_id, root, name }, null, 2), { mode: 0o600 });
    console.log(`[runner] Pairing OK, device #${data.device_id}`);
    return data.token;
  }
  if (existsSync(configPath)) {
    const saved = JSON.parse(readFileSync(configPath, 'utf8'));
    if (saved.token) return saved.token;
  }
  throw new Error('Нет токена. Запусти с --code из профиля платформы.');
}

const token = await getToken();
const wsUrl = server.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:') + '/api/devices/ws';

const sessions = new Map();

function openSession(id) {
  if (sessions.has(id)) return;
  const isWin = process.platform === 'win32';
  const shell = isWin ? 'powershell.exe' : '/bin/bash';
  const shellArgs = isWin ? ['-NoLogo', '-NoProfile', '-Command', '-'] : ['--noprofile', '--norc'];
  let child;
  try {
    child = spawn(shell, shellArgs, { cwd: root, env: { ...process.env, TERM: 'xterm-256color' }, windowsHide: true });
  } catch (err) {
    send({ type: 'output', session: id, data: `\r\n[runner] Не удалось запустить ${shell}: ${err.message}\r\n` });
    send({ type: 'exit', session: id });
    return;
  }
  sessions.set(id, child);
  const out = (data) => send({ type: 'output', session: id, data: data.toString('utf8') });
  child.stdout.on('data', out);
  child.stderr.on('data', out);
  child.on('error', (err) => out(`\r\n[runner error] ${err.message}\r\n`));
  child.on('exit', (code) => {
    sessions.delete(id);
    send({ type: 'exit', session: id, code });
  });
  try {
    if (isWin) child.stdin.write('[Console]::OutputEncoding = [Text.Encoding]::UTF8\r\n');
  } catch {}
}

let socket = null;
let closedByUser = false;

function send(message) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(message));
}

function connect() {
  socket = new WebSocket(wsUrl);
  socket.addEventListener('open', () => {
    socket.send(JSON.stringify({ type: 'auth', token }));
    console.log('[runner] Онлайн. Жду команды из платформы.');
  });
  socket.addEventListener('message', (event) => {
    let message;
    try { message = JSON.parse(event.data); } catch { return; }
    const session = String(message.session || '');
    if (message.type === 'open') openSession(session);
    if (message.type === 'input') {
      const child = sessions.get(session);
      try {
        if (child?.stdin?.writable) child.stdin.write(String(message.data || ''));
      } catch (err) {
        send({ type: 'output', session, data: `\r\n[runner] stdin: ${err.message}\r\n` });
      }
    }
    if (message.type === 'close') {
      const child = sessions.get(session);
      if (child) { try { child.kill(); } catch {} }
      sessions.delete(session);
    }
  });
  socket.addEventListener('close', (event) => {
    console.log('[runner] Соединение закрыто. Переподключаюсь через 5 секунд…');
    for (const child of sessions.values()) { try { child.kill(); } catch {} }
    sessions.clear();
    if (event.code === 1008) {
      console.error('[runner] Токен отклонён. Удали .device.json и запусти pairing заново.');
      process.exit(1);
    }
    if (!closedByUser) setTimeout(connect, 5000);
  });
  socket.addEventListener('error', () => {});
}

process.on('SIGINT', () => {
  closedByUser = true;
  for (const child of sessions.values()) { try { child.kill(); } catch {} }
  try { socket?.close(); } catch {}
  process.exit(0);
});

connect();
