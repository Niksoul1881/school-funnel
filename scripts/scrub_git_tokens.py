"""Rewrite accidental Telegram bot tokens in Git history files."""
from __future__ import annotations

import re
from pathlib import Path

PATTERN = re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b")
root = Path(".").resolve()
for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue
    updated = PATTERN.sub("REDACTED_TELEGRAM_TOKEN", text)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
