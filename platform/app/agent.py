"""Агент проекта: mock по умолчанию и адаптер DeepSeek Harness.

Mock-режим нужен, чтобы демо работало без API-ключа и не тратило токены.
DSH-режим включается переменной AGENT_MODE=dsh и ключом DEEPSEEK_API_KEY.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import catalog, config


@dataclass
class AgentResult:
    text: str
    files: dict[str, str] = field(default_factory=dict)
    actions: list[dict] = field(default_factory=list)
    steps: list[dict] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    mode: str = "mock"


def _slug(text: str) -> str:
    value = re.sub(r"[^a-zа-я0-9]+", "-", text.lower()).strip("-")
    return value or "item"


def _menu_id(title: str) -> str:
    known = {
        "услуги": "services",
        "записаться": "book",
        "запись": "book",
        "цены": "prices",
        "прайс": "prices",
        "связаться": "contact",
        "контакты": "contact",
        "частые вопросы": "faq",
        "вопросы": "faq",
        "программа": "program",
        "подарок": "gift",
        "уроки": "lessons",
    }
    return known.get(title.strip().lower(), _slug(title))


def _split_list(raw: str) -> list[str]:
    return [x.strip(" .;") for x in re.split(r"[,;\n]", raw) if x.strip(" .;")]


def _json_load(files: dict[str, str], path: str, fallback: dict) -> dict:
    try:
        return json.loads(files.get(path, "")) or fallback
    except Exception:
        return fallback


def _set_miniapp_content(files: dict[str, str], content: dict) -> None:
    if "index.html" not in files:
        return
    encoded = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")
    files["index.html"] = re.sub(
        r"window\.__CONTENT__ = .*?;\s*</script>",
        lambda _m: f"window.__CONTENT__ = {encoded};</script>",
        files["index.html"],
        flags=re.S,
    )
    accent = content.get("business", {}).get("accent", "#ff4f8b")
    if "styles.css" in files:
        files["styles.css"] = re.sub(r"--accent:\s*#[0-9a-fA-F]{6}", f"--accent: {accent}", files["styles.css"])


def _apply(files: dict[str, str], content: dict, template_id: str) -> None:
    files["content.json"] = json.dumps(content, ensure_ascii=False, indent=2)
    if template_id.startswith("miniapp"):
        _set_miniapp_content(files, content)


def _reply_for_template(template_id: str) -> str:
    if template_id.startswith("miniapp"):
        return "Я собрал мини-апп. Могу поменять тексты, цены, акцентный цвет и экраны. Что поправить?"
    if template_id in ("content-agent", "price-agent"):
        return "Я собрал агента. Могу поменять расписание, источники и формат отчёта. Что поправить?"
    return "Я собрал бота. Могу поменять меню, тексты, цены и ответы на вопросы. Что поправить?"


class MockAgent:
    """Детерминированный агент: понимает ключевые слова и меняет файлы."""

    def _imported(self, project: dict, message: str, files: dict[str, str]) -> AgentResult:
        low = message.lower().strip()
        actions: list[dict] = []
        if "readme" in low:
            name = project.get("name", "Мой проект")
            paths = "\n".join(f"- `{p}`" for p in sorted(files))
            files["README.md"] = (
                f"# {name}\n\n"
                "Проект открыт в платформе «Школа AI-агентов».\n\n"
                "## Файлы\n\n" + paths + "\n\n"
                "## Что дальше\n\n"
                "1. Открой нужный файл в проводнике слева.\n"
                "2. Попроси AI-помощника объяснить или поправить код.\n"
            )
            actions.append({"type": "edit", "path": "README.md", "summary": "добавил README"})
            text = f"Добавил README.md с описанием проекта и списком файлов ({len(files)} шт.)."
        elif any(word in low for word in ("файл", "структур", "список", "что внутри")):
            lines = "\n".join(f"• {p} — {len(c.splitlines())} строк" for p, c in sorted(files.items()))
            text = f"Файлов в проекте: {len(files)}\n{lines}\n\nНапиши «объясни <файл>» — разберу."
        elif "объясни" in low or "что делает" in low:
            target = next((p for p in files if p.lower() in low or p.split("/")[-1].lower() in low), None)
            if target:
                preview = files[target][:1400]
                text = f"Файл `{target}`:\n\n{preview}\n\nЭто фрагмент. Могу разобрать конкретную функцию или добавить комментарии."
            else:
                text = "Уточни имя файла: например, «объясни main.py» или «объясни app.js»."
        else:
            text = (
                f"Вижу проект «{project.get('name', 'Мой проект')}». Файлов: {len(files)}. "
                "Могу показать структуру, объяснить файл или добавить README. "
                "Например: «покажи структуру», «объясни main.py», «добавь README»."
            )
        return AgentResult(text=text, files=files, actions=actions, tokens_in=max(1, len(message) // 4 + 450), tokens_out=max(1, len(text) // 4), mode="mock")

    def respond(self, project: dict, message: str) -> AgentResult:
        files = {f["path"]: f["content"] for f in project["files"]}
        if project.get("template_id") == "imported":
            return self._imported(project, message, files)
        content = _json_load(files, "content.json", catalog.build_content(project["template_id"], project.get("brief", {})))
        actions: list[dict] = []
        text = ""
        low = message.lower().strip()

        def act(path: str, summary: str) -> None:
            actions.append({"type": "edit", "path": path, "summary": summary})

        if any(word in low for word in ("меню", "кнопк")):
            raw = message.split(":", 1)[1] if ":" in message else ""
            items = _split_list(raw) or ["Услуги", "Записаться", "Цены", "Связаться"]
            content["menu"] = [{"id": _menu_id(item), "title": item[:40]} for item in items[:6]]
            act("content.json", "обновил меню")
            text = "Обновил меню: " + ", ".join(item["title"] for item in content["menu"]) + ". Проверь превью справа — кнопки уже там."
        elif any(word in low for word in ("цен", "прайс", "стоим")):
            raw = message.split(":", 1)[1] if ":" in message else ""
            if raw.strip():
                content["prices"] = catalog._parse_prices(raw)
                act("content.json", "обновил цены")
                text = "Обновил прайс: " + "; ".join(f"{p['title']} — {p['price']}" for p in content["prices"]) + "."
            else:
                text = "Цены сейчас такие: " + "; ".join(f"{p['title']} — {p['price']}" for p in content["prices"]) + ". Напиши новые в формате «стрижка — 3500, маникюр — 2500»."
        elif any(word in low for word in ("вопрос", "faq", "ответ")):
            lines = [line.strip() for line in message.splitlines() if "|" in line]
            if lines:
                content["faq"] = catalog._parse_faq("\n".join(lines))
                act("content.json", "обновил FAQ")
                text = f"Добавил {len(content['faq'])} вопроса в FAQ. Они появятся в боте и превью."
            else:
                text = "Пришли вопросы в формате: «Вопрос|Ответ», каждый с новой строки. Например: «Есть ли парковка?|Да, во дворе»."
        elif any(word in low for word in ("приветств", " greeting", "здравств")):
            raw = message.split(":", 1)[1].strip() if ":" in message else ""
            if raw:
                content["greeting"] = raw
                act("content.json", "обновил приветствие")
                text = "Обновил приветствие. Оно показывается в первом сообщении бота."
            else:
                text = "Напиши новое приветствие после двоеточия — я заменю текст."
        elif any(word in low for word in ("цвет", "акцент", "стил")):
            match = re.search(r"#[0-9a-fA-F]{6}", message)
            if match:
                content["business"]["accent"] = match.group(0)
                act("content.json", "обновил акцент")
                act("styles.css", "перекрасил мини-апп")
                text = f"Поставил акцент {match.group(0)}. В превью шапка и кнопки уже перекрашены."
            else:
                text = "Пришли цвет в формате #ff4f8b — я применю его к кнопкам и шапке."
        elif "запис" in low:
            if not any(item["id"] == "book" for item in content["menu"]):
                content["menu"].append({"id": "book", "title": "Записаться"})
            act("content.json", "добавил кнопку записи")
            text = f"Добавил кнопку «Записаться». Она ведёт на контакт: {content.get('contact', '')}."
        elif any(word in low for word in ("оплат", "платеж", "stars", "карт")):
            content["payment"] = "stars" if "stars" in low or "звезд" in low else "card"
            act("content.json", "включил оплату")
            text = "Включил оплату: " + ("Telegram Stars" if content["payment"] == "stars" else "карта / Robokassa") + ". В боте появится кнопка оплаты."
        elif any(word in low for word in ("расписан", "каждый день", "утр", "вечер")):
            time_match = re.search(r"(\d{1,2}:\d{2})", message)
            content["schedule"] = time_match.group(1) if time_match else "09:00"
            if "schedule.json" in files:
                files["schedule.json"] = json.dumps({"time": content["schedule"], "timezone": "Europe/Moscow", "days": "mon-sun"}, ensure_ascii=False, indent=2)
                act("schedule.json", "обновил расписание")
            text = f"Поставил запуск на {content['schedule']} каждый день. Отчёт будет приходить в Telegram."
        elif any(word in low for word in ("источник", "ссылк", "rss")):
            urls = re.findall(r"https?://\S+", message)
            if urls:
                content["sources"] = urls
                if "sources.json" in files:
                    files["sources.json"] = json.dumps({"sources": urls}, ensure_ascii=False, indent=2)
                    act("sources.json", "добавил источники")
                text = f"Добавил {len(urls)} источника. Агент будет брать их при следующем запуске."
            else:
                text = "Пришли ссылки на источники — по одной на строку."
        elif any(word in low for word in ("деплой", "запуск", "опублик", "бот token", "токен")):
            text = "Нажми «Опубликовать» вверху. Понадобится токен бота из @BotFather: создай бота, скопируй токен и вставь в окно. Платформа проверит токен через getMe и запишет деплой."
        elif any(word in low for word in ("файл", "код", "структур")):
            text = "В проекте такие файлы:\n" + "\n".join(f"• {path}" for path in sorted(files)) + "\nМеняй тексты в content.json — код подхватит."
        elif any(word in low for word in ("привет", "hi", "hello", "старт")):
            text = _reply_for_template(project["template_id"])
        else:
            text = (
                "Понял задачу. Могу сделать конкретно:\n"
                "• поменять меню — «добавь меню: Услуги, Записаться, Цены, Связаться»\n"
                "• обновить цены — «цены: стрижка — 3500, маникюр — 2500»\n"
                "• добавить вопросы — «Есть ли парковка?|Да, во дворе»\n"
                "• сменить цвет — «цвет #ff4f8b»\n"
                "• включить оплату — «включи оплату Stars»\n"
                "Напиши, что важнее, и я поправлю файлы."
            )

        _apply(files, content, project["template_id"])
        tokens_in = max(1, len(message) // 4 + 450)
        tokens_out = max(1, len(text) // 4)
        return AgentResult(text=text, files=files, actions=actions, tokens_in=tokens_in, tokens_out=tokens_out, mode="mock")


class DSHAgent:
    """Адаптер DeepSeek Harness: один ход агента в изолированной папке проекта."""

    def respond(self, project: dict, message: str, on_event=None) -> AgentResult:
        if not config.DEEPSEEK_API_KEY:
            return MockAgent().respond(project, message)
        workspace = config.DATA_DIR / "workspaces" / f"project-{project['id']}"
        workspace.mkdir(parents=True, exist_ok=True)
        original = {f["path"]: f["content"] for f in project["files"]}
        for path, content in original.items():
            target = workspace / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (workspace / "AGENTS.md").write_text(
            "Ты работаешь в проекте ученика школы AI-агентов. "
            "У тебя есть shell в этой папке: запускай команды сам, проверяй результат. "
            "У ученика в платформе внизу проекта есть живой интерактивный терминал: не отправляй его в VS Code, скажи открыть панель «Терминал» и ввести команду. "
            "Для интерактивных программ используй printf/echo с вводом. "
            "Меняй только файлы проекта. Тексты держи в content.json. "
            "После правок коротко объясни, что изменил, по-русски.",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["DEEPSEEK_API_KEY"] = config.DEEPSEEK_API_KEY
        history = []
        for m in project.get("messages", [])[-4:]:
            role = "Ученик" if m.get("role") == "user" else "Ассистент"
            history.append(f"{role}: {str(m.get('content', ''))[:400]}")
        context = "\n".join(history)
        task = (f"Контекст диалога:\n{context}\n\n" if context else "") + f"Задача: {message}"
        cmd = [config.DSH_BIN, "--profile", "headless", "--json", task]

        async def _run() -> tuple[bytes, bytes]:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            chunks: list[bytes] = []
            assert proc.stdout is not None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                chunks.append(line)
                if on_event:
                    try:
                        event = json.loads(line.decode("utf-8", "replace"))
                    except Exception:
                        continue
                    if event.get("type") in ("thinking", "tool_call"):
                        try:
                            on_event(event)
                        except Exception:
                            pass
            err = await proc.stderr.read() if proc.stderr else b""
            await proc.wait()
            return b"".join(chunks), err

        try:
            out_b, err_b = asyncio.run(asyncio.wait_for(_run(), timeout=180))
        except Exception as exc:  # dsh не установлен / нет прав / таймаут
            result = MockAgent().respond(project, message)
            result.text = f"DSH недоступен ({exc}). Включил mock-режим.\n\n" + result.text
            return result

        out = out_b.decode("utf-8", "replace")
        err = err_b.decode("utf-8", "replace")

        text_parts: list[str] = []
        steps: list[dict] = []
        usage_total = 0
        usage_out = 0
        for line in out.splitlines():
            try:
                event = json.loads(line)
            except Exception:
                continue
            if event.get("type") == "thinking" and event.get("text"):
                if len(steps) < 30:
                    steps.append({"kind": "thinking", "text": str(event["text"])[:700]})
            if event.get("type") == "tool_call":
                inp = event.get("input") if isinstance(event.get("input"), dict) else {}
                summary = inp.get("file_path") or inp.get("path") or inp.get("command") or inp.get("description") or inp.get("pattern") or ""
                if len(steps) < 30:
                    steps.append({"kind": "tool", "tool": str(event.get("tool") or "tool"), "text": str(summary)[:300]})
            if event.get("type") == "text" and event.get("text"):
                text_parts.append(event["text"])
            if event.get("type") == "final" and event.get("text"):
                text_parts.append(event["text"])
            if event.get("type") == "status" and isinstance(event.get("usage"), dict):
                u = event["usage"]
                total = int(u.get("totalTokens") or 0)
                if total > usage_total:
                    usage_total = total
                usage_out += int(u.get("outputTokens") or 0)
        text = "\n".join(dict.fromkeys(text_parts)).strip() or "Готово. Проверь файлы проекта."

        if usage_total:
            tokens_out = max(1, usage_out)
            tokens_in = max(1, usage_total - tokens_out)
        else:
            tokens_in = len(message) // 4 + 450
            tokens_out = len(text) // 4

        changed: dict[str, str] = {}
        for path in sorted(workspace.rglob("*")):
            if not path.is_file() or path.name == "AGENTS.md":
                continue
            rel = str(path.relative_to(workspace)).replace("\\", "/")
            if rel.startswith(".dsh"):
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if original.get(rel) != content:
                changed[rel] = content
        return AgentResult(
            text=text,
            files=changed,
            actions=[{"type": "edit", "path": p, "summary": "изменён агентом"} for p in changed],
            steps=steps,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            mode="dsh",
        )


def respond(project: dict, message: str, on_event=None) -> AgentResult:
    if config.AGENT_MODE == "dsh":
        return DSHAgent().respond(project, message, on_event=on_event)
    return MockAgent().respond(project, message)
