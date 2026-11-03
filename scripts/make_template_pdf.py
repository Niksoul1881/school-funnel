"""Build a styled A4 PDF from docs/strategy/template-ideas-60.md."""
from __future__ import annotations

from pathlib import Path

import mistune
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "strategy" / "template-ideas-60.md"
HTML = ROOT / "docs" / "strategy" / ".template-ideas-60.html"
PDF = ROOT / "docs" / "strategy" / "template-ideas-60.pdf"


def main() -> None:
    source = MD.read_text(encoding="utf-8")
    # Remove the H1 and use a designed cover instead.
    if source.startswith("# "):
        source = source.split("\n", 1)[1].lstrip()
    # The cover already carries this line; avoid a duplicate heading on page 2.
    source = source.replace("## Боты · AI-агенты · Telegram Mini Apps\n\n", "", 1)

    body = mistune.create_markdown(plugins=["table", "strikethrough"])(source)

    html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 17mm 13mm 17mm;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Segoe UI", "Manrope", Arial, sans-serif;
    font-size: 9.4pt;
    line-height: 1.5;
    color: #1b1714;
    background: #fff;
  }}
  .cover {{
    height: 263mm;
    margin: -17mm -13mm 0;
    padding: 26mm 20mm;
    color: #f6efe4;
    background:
      radial-gradient(700px 420px at 10% 0%, rgba(255,107,94,.24), transparent 65%),
      radial-gradient(600px 420px at 90% 100%, rgba(232,179,106,.16), transparent 60%),
      #100e0c;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    page-break-after: always;
  }}
  .cover .mark {{
    width: 38px; height: 38px; border-radius: 11px;
    display: grid; place-items: center;
    background: #ff6b5e; color: #100e0c;
    font-weight: 800; font-size: 12px;
  }}
  .cover .brand {{ display: flex; align-items: center; gap: 11px; }}
  .cover .brand b {{ display:block; font-size: 13px; }}
  .cover .brand span {{ display:block; margin-top:3px; font-size: 8px; letter-spacing:.18em; text-transform:uppercase; color:#9b8f80; }}
  .cover .kicker {{ font-size: 9px; letter-spacing: .18em; text-transform: uppercase; color: #c7b9a7; margin-bottom: 14mm; }}
  .cover h1 {{
    margin: 0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 35pt;
    line-height: .98;
    letter-spacing: -.04em;
    color: #f6efe4;
  }}
  .cover h1 em {{ color:#ff6b5e; font-style:normal; }}
  .cover h1 i {{ color:#e8b36a; font-family: Georgia, serif; font-weight: 400; }}
  .cover .sub {{ margin: 6mm 0 0; max-width: 130mm; color:#bdb1a2; font-size: 11pt; line-height:1.6; }}
  .cover .bottom {{ display:flex; justify-content:space-between; align-items:flex-end; color:#8f8375; font-size:8.5px; }}
  .cover .bottom b {{ color:#f6efe4; font-size:10px; }}
  .cover .rule {{ height:1px; background:rgba(246,239,228,.15); margin-bottom:5mm; }}

  h1 {{
    font-size: 20pt;
    line-height: 1.06;
    letter-spacing: -.035em;
    margin: 0 0 6mm;
    padding-top: 2mm;
    color: #1b1714;
    page-break-before: always;
  }}
  h1:first-of-type {{ page-break-before: auto; }}
  h2 {{
    font-size: 13.5pt;
    letter-spacing: -.02em;
    margin: 8mm 0 3mm;
    color: #c74454;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 10.5pt;
    margin: 5mm 0 2mm;
    color: #1b1714;
    page-break-after: avoid;
  }}
  h4 {{ font-size: 9.5pt; margin: 4mm 0 1.5mm; }}
  p {{ margin: 0 0 2.4mm; }}
  ul, ol {{ margin: 1.5mm 0 3mm; padding-left: 5.5mm; }}
  li {{ margin: 1mm 0; }}
  strong {{ color: #1b1714; }}
  a {{ color: #b44451; text-decoration: none; }}
  blockquote {{
    margin: 4mm 0;
    padding: 3mm 4mm;
    border-left: 3px solid #ff6b5e;
    background: #fbf3ea;
    color: #5f5145;
    font-size: 8.8pt;
  }}
  hr {{ border: 0; border-top: 1px solid #e8ddd0; margin: 7mm 0; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 3mm 0 5mm;
    font-size: 7.15pt;
    line-height: 1.38;
    table-layout: fixed;
  }}
  th {{
    background: #1b1714;
    color: #f6efe4;
    font-weight: 700;
    text-align: left;
    padding: 2mm 1.5mm;
    border: 1px solid #1b1714;
    overflow-wrap: anywhere;
  }}
  td {{
    padding: 1.8mm 1.5mm;
    border: 1px solid #e4d8c9;
    vertical-align: top;
    overflow-wrap: anywhere;
  }}
  tbody tr:nth-child(even) td {{ background: #fbf7f0; }}
  tr {{ page-break-inside: avoid; }}
  table th:nth-child(1), table td:nth-child(1) {{ width: 8mm; text-align: center; }}
  table th:nth-child(2) {{ width: 28mm; }}
  table th:nth-child(6), table td:nth-child(6) {{ width: 11mm; text-align:center; }}
  /* Three- and five-column tables need natural widths, not the six-column grid. */
  table:not(:has(th:nth-child(6))) {{ table-layout: auto; }}
  table:not(:has(th:nth-child(6))) th:nth-child(1),
  table:not(:has(th:nth-child(6))) td:nth-child(1) {{ width: auto; text-align: left; }}
  .note {{ font-size: 8.5px; color:#77695b; }}
</style>
</head>
<body>
  <section class="cover">
    <div>
      <div class="brand"><div class="mark">AI</div><div><b>Школа AI-агентов</b><span>платформа запуска</span></div></div>
    </div>
    <div>
      <div class="kicker">Каталог шаблонов · 2026</div>
      <h1>60 идей<br><em>шаблонов</em><br><i>для запуска</i></h1>
      <p class="sub">Боты, AI-агенты и Telegram Mini Apps.<br>Аудит реальных проектов и пять приоритетов на запуск.</p>
    </div>
    <div class="bottom">
      <div><div class="rule"></div><b>60 идей · 3 блока · 12 шаблонов из практики</b><br>Внутренний документ для выбора первых пяти</div>
      <div>03.11.2026</div>
    </div>
  </section>
  {body}
</body>
</html>"""

    HTML.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(HTML.as_uri(), wait_until="load")
        page.pdf(
            path=str(PDF),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=(
                '<div style="width:100%;font-size:7px;color:#9b8f80;'
                'padding:0 13mm;display:flex;justify-content:space-between;font-family:Arial;">'
                "<span>Школа AI-агентов · шаблоны</span>"
                '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span>'
                "</div>"
            ),
            margin={"top": "17mm", "right": "13mm", "bottom": "17mm", "left": "13mm"},
        )
        browser.close()
    print(f"PDF: {PDF} ({PDF.stat().st_size / 1024:.0f} KB)")
    HTML.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
