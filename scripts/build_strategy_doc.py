#!/usr/bin/env python3
"""Собирает читаемую HTML-версию стратегического документа из Markdown.

Использование:
    python scripts/build_strategy_doc.py
    python scripts/build_strategy_doc.py docs/strategy/koncepciya.md docs/strategy/koncepciya.html
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "docs" / "strategy" / "koncepciya.md"
DEFAULT_DST = ROOT / "docs" / "strategy" / "koncepciya.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Unbounded:wght@600;700;800&display=swap" rel="stylesheet">
<style>
:root{{--ink:#151a28;--muted:#5b647a;--line:#e3e6ef;--acc:#ff6b35;--acc2:#8b5cf6;--gold:#b77900;--soft:#f7f8fc}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:#eef0f6;color:var(--ink);font-family:Manrope,"Segoe UI",Arial,sans-serif;font-size:10.6pt;line-height:1.62}}
.page{{max-width:860px;margin:0 auto;background:#fff;padding:26mm 22mm 22mm;box-shadow:0 20px 60px rgba(20,24,40,.08)}}
.cover{{min-height:235mm;display:flex;flex-direction:column;justify-content:center;page-break-after:always}}
.kicker{{font-size:9pt;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:var(--acc)}}
h1{{font-family:Unbounded,Manrope,sans-serif;font-size:31pt;line-height:1.08;margin:14pt 0 10pt;letter-spacing:-.01em}}
.lead{{font-size:13pt;line-height:1.5;color:var(--muted);max-width:640px}}
.meta{{margin-top:26pt;padding-top:14pt;border-top:1px solid var(--line);display:flex;gap:26pt;font-size:9pt;color:var(--muted);letter-spacing:.04em;text-transform:uppercase;font-weight:700}}
.cover .box{{margin-top:30pt;padding:16pt 18pt;border-left:4px solid var(--acc);background:var(--soft);font-size:10.5pt;color:#333c52}}
.toc{{page-break-after:always;padding-top:6mm}}
.toc h2{{border-top:0;margin-top:0;padding-top:0;font-size:15pt}}
.toc ol{{columns:2;column-gap:26pt;padding-left:16pt;margin:10pt 0 0}}
.toc li{{break-inside:avoid;margin:0 0 6pt;font-size:9.6pt}}
.toc a{{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line)}}
h2{{font-family:Unbounded,Manrope,sans-serif;font-size:16.5pt;line-height:1.2;margin:24pt 0 9pt;padding-top:10pt;border-top:2px solid var(--acc);page-break-after:avoid}}
h3{{font-family:Unbounded,Manrope,sans-serif;font-size:11.6pt;line-height:1.3;margin:16pt 0 6pt;page-break-after:avoid}}
p{{margin:0 0 8pt}}
ul,ol{{margin:0 0 9pt;padding-left:17pt}}li{{margin:0 0 4pt}}
strong{{font-weight:800}}
a{{color:#3b45c8}}
blockquote{{margin:12pt 0;padding:11pt 15pt;background:var(--soft);border-left:4px solid var(--acc2);color:#333c52;font-size:9.9pt}}
blockquote p:last-child{{margin-bottom:0}}
code{{font-family:Consolas,"Cascadia Mono",monospace;font-size:9pt;background:#f1f3fa;padding:1.5pt 4pt;border-radius:4pt}}
pre{{margin:10pt 0;padding:12pt 14pt;background:#111827;color:#e5e9ff;border-radius:8pt;overflow:auto;page-break-inside:avoid}}
pre code{{background:none;color:inherit;padding:0;font-size:8.6pt;line-height:1.5}}
table{{width:100%;border-collapse:collapse;margin:10pt 0 13pt;font-size:8.9pt;line-height:1.42;page-break-inside:auto}}
thead{{display:table-header-group}}
th{{background:#f1f3fa;text-align:left;font-size:8pt;letter-spacing:.05em;text-transform:uppercase;color:#4b546b;padding:7pt 7pt;border-bottom:1.5px solid #cfd5e6}}
td{{padding:7pt 7pt;border-bottom:1px solid var(--line);vertical-align:top}}
tr:nth-child(even) td{{background:#fbfbfe}}
hr{{border:0;border-top:1px solid var(--line);margin:16pt 0}}
.small{{font-size:8.6pt;color:var(--muted)}}
.end{{margin-top:26pt;padding-top:12pt;border-top:1px solid var(--line);font-size:8.6pt;color:var(--muted)}}
@media print{{
  @page{{size:A4;margin:15mm 14mm}}
  html,body{{background:#fff}}
  .page{{box-shadow:none;max-width:none;padding:0;margin:0}}
  .cover{{min-height:250mm}}
  h2{{page-break-before:auto}}
  a{{color:inherit;text-decoration:none}}
  tr,blockquote,pre{{page-break-inside:avoid}}
}}
</style>
</head>
<body>
<div class="page">
<section class="cover">
  <div class="kicker">Концепция · для команды · 2 ноября 2026</div>
  <h1>{title}</h1>
  <div class="lead">{subtitle}</div>
  <div class="box">{abstract}</div>
  <div class="meta"><span>Версия 1.0</span><span>Внутренний документ</span><span>school-funnel / strategy</span></div>
</section>
<nav class="toc"><h2>Содержание</h2><ol>{toc}</ol></nav>
<main>{body}</main>
<div class="end">{footer}</div>
</div>
</body>
</html>
"""


def slugify(index: int) -> str:
    return f"sec-{index}"


def extract_title(md: str) -> tuple[str, str, str, str]:
    """Возвращает title, subtitle, abstract, body без заголовка и подзаголовка."""
    lines = md.splitlines()
    title = "Концепция"
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            lines = lines[:i] + lines[i + 1:]
            break
    subtitle = ""
    abstract = ""
    # первый выделенный абзац после заголовка
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s == "---":
            continue
        if s.startswith("**") and s.endswith("**"):
            subtitle = s.strip("*").strip()
            lines = lines[:i] + lines[i + 1:]
        break
    # первый обычный абзац после подзаголовка — врезка на обложке
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s == "---" or s.startswith("#"):
            continue
        if not s.startswith("**") and len(s) > 80:
            abstract = s
            lines = lines[:i] + lines[i + 1:]
        break
    return title, subtitle, abstract, "\n".join(lines)


def build(src: Path, dst: Path) -> None:
    md_text = src.read_text(encoding="utf-8")
    title, subtitle, abstract, body_md = extract_title(md_text)
    body_html = mistune.create_markdown(plugins=["table", "strikethrough"])(body_md)

    # ids для h2 + оглавление
    heads = [h.strip() for h in re.findall(r"^##\s+(.+)$", body_md, flags=re.M)]
    toc_items = []
    counter = 0

    def add_id(match: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        return f'<h2 id="{slugify(counter)}">'

    body_html = re.sub(r"<h2>", add_id, body_html)
    for i, h in enumerate(heads, 1):
        toc_items.append(f'<li><a href="#{slugify(i)}">{html.escape(h)}</a></li>')

    out = TEMPLATE.format(
        title=html.escape(title),
        subtitle=html.escape(subtitle or "Учим делать ботов, агентов и мини-аппы — и даём среду, где они работают."),
        abstract=html.escape(abstract or "Рабочая гипотеза для команды: продукт, воронка, архитектура, экономика и роудмап."),
        toc="".join(toc_items),
        body=body_html,
        footer="Документ — рабочая гипотеза. Цифры, конверсии и цены проверить на первом потоке; юридические и платёжные вопросы — с юристом и бухгалтером.",
    )
    dst.write_text(out, encoding="utf-8")
    print(f"OK: {dst} ({len(out) / 1024:.1f} KB, {len(heads)} sections)")


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DST
    build(src, dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
