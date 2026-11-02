"""Настоящий терминал проекта: PTY + bash внутри workspace."""
from __future__ import annotations

import asyncio
import os
import signal
import struct
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
    import pty
    import termios
except ImportError:  # Windows dev: терминал доступен только в Linux-контейнере
    fcntl = None
    pty = None
    termios = None

from . import config, store
from .db import fetch_one
from .security import token_hash


def workspace_for(project_id: int) -> Path:
    path = config.DATA_DIR / "workspaces" / f"project-{project_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sync_workspace(project: dict) -> Path:
    workspace = workspace_for(project["id"])
    for item in project["files"]:
        target = workspace / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")
    (workspace / "AGENTS.md").write_text(
        "Ты работаешь в проекте ученика школы AI-агентов. "
        "У тебя есть shell в этой папке: запускай команды сам, проверяй результат. "
        "У ученика в платформе внизу проекта есть живой интерактивный терминал: не отправляй его в VS Code, скажи открыть панель «Терминал» и ввести команду. "
        "Для интерактивных программ используй printf/echo с вводом. "
        "Тексты держи в content.json. После правок коротко объясни, что изменил, по-русски.",
        encoding="utf-8",
    )
    return workspace


def import_workspace(project_id: int) -> None:
    """Подхватываем изменения, сделанные руками в терминале, обратно в проект."""
    workspace = workspace_for(project_id)
    skip_dirs = {".git", "node_modules", ".dsh", "__pycache__", ".venv", "venv"}
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace).as_posix()
        if rel == "AGENTS.md" or rel == ".env" or any(part in skip_dirs for part in path.parts):
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "\u0000" in content:
            continue
        store.write_file(project_id, rel, content)


def user_from_websocket(websocket) -> dict | None:
    token = websocket.cookies.get(config.COOKIE_NAME)
    if not token:
        return None
    row = fetch_one(
        """
        SELECT u.*, s.expires_at AS session_expires
        FROM sessions s JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ?
        """,
        (token_hash(token),),
    )
    if not row or row["session_expires"] < datetime.now(timezone.utc).isoformat(timespec="seconds"):
        return None
    return dict(row)


async def run_shell(websocket, project: dict) -> None:
    if pty is None or fcntl is None or termios is None:
        await websocket.send_text("Терминал доступен в Linux-контейнере платформы.\r\n")
        return
    workspace = sync_workspace(project)
    master, slave = pty.openpty()
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["PS1"] = "\\w $ "
    env["PYTHONUNBUFFERED"] = "1"
    env["DATA_DIR"] = str(config.DATA_DIR)
    proc = subprocess.Popen(
        ["/bin/bash", "--noprofile", "--norc"],
        cwd=str(workspace),
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
        preexec_fn=os.setsid,
        close_fds=True,
    )
    os.close(slave)
    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 120, 0, 0))

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    def on_readable() -> None:
        try:
            data = os.read(master, 65536)
        except OSError:
            data = b""
        if data:
            queue.put_nowait(data)
        else:
            try:
                loop.remove_reader(master)
            except Exception:
                pass
            queue.put_nowait(b"")

    loop.add_reader(master, on_readable)

    async def pump() -> None:
        while True:
            data = await queue.get()
            if not data:
                break
            try:
                await websocket.send_text(data.decode("utf-8", "replace"))
            except Exception:
                break

    pump_task = asyncio.create_task(pump())
    try:
        while True:
            message = await websocket.receive_text()
            if message.startswith("__resize__:"):
                try:
                    _, rest = message.split(":", 1)
                    rows, cols = [int(x) for x in rest.split("x", 1)]
                    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
                except Exception:
                    pass
                continue
            os.write(master, message.encode("utf-8", "replace"))
    except Exception:
        pass
    finally:
        try:
            loop.remove_reader(master)
        except Exception:
            pass
        pump_task.cancel()
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            os.close(master)
        except Exception:
            pass
        try:
            import_workspace(project["id"])
        except Exception:
            pass
