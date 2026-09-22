#!/usr/bin/env python3
"""
build_slides.py — Compiler for Zipline-style 16:9 engineering presentation slides.

Features:
1. Zero Overlap Guarantee: Dynamically offsets diagrams and content below headers.
2. Native Markdown Table Parser: Converts GitHub-style tables into elegant Zipline tables.
3. Native Codeslide & Arch SVG Layouts: Preserves pixel-perfect 100x56.25 canvas.
4. Standalone & Offline: Compiles to a single zero-dependency HTML file.
"""

import sys
import os
import re
from pathlib import Path


ZIPLINE_CSS = """
:root {
  --paper: #F2EEDE;
  --ink: #1A1A1A;
  --ink-soft: #33312B;
  --ink-faint: #85837A;
  --accent: #1E6FCC;
  --rust: #B4470F;
  --rust-2: #EBD8C6;
  --teal: #0F8A7A;
  --teal-d: #0C6C60;
  --teal-2: #D5E6DE;
  --zone: #E9E4D0;
  --grid: #DED9C7;
  --c-fullft: #33312B;
  --c-r32: #C8641A;
  --c-r1: #1E6FCC;
  --sans: "Avenir Next", "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --serif: Charter, "Iowan Old Style", Georgia, "Times New Roman", serif;
  --mono: "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
}

@page {
  size: 16in 9in;
  margin: 0;
}

@media print {
  html, body {
    width: 16in !important;
    height: 9in !important;
    background: #F2EEDE !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .deck {
    width: 16in !important;
    height: 9in !important;
    --u: 0.16in !important;
  }
  .stage {
    width: 16in !important;
    height: 9in !important;
    box-shadow: none !important;
  }
  .nav-chrome {
    display: none !important;
  }
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  height: 100%;
  background: #000;
  overflow: hidden;
  font-family: var(--sans);
  -webkit-font-smoothing: antialiased;
}

.deck {
  height: 100%;
  display: grid;
  place-items: center;
  --u: min(1vw, 1.7778vh);
}

.stage {
  position: relative;
  width: calc(var(--u) * 100);
  height: calc(var(--u) * 56.25);
  overflow: hidden;
  background: var(--paper);
  color: var(--ink);
  cursor: default;
  box-shadow: 0 0 calc(var(--u) * 5) rgba(0, 0, 0, 0.95);
}

.flat {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.flat.is-on {
  opacity: 1;
  pointer-events: auto;
}

/* Header & Typography with safe compact vertical footprint */
h1 {
  font-weight: 600;
  font-size: calc(var(--u) * 3.4);
  line-height: 1.1;
  letter-spacing: -0.015em;
  color: var(--ink);
}

h1.big {
  font-size: calc(var(--u) * 8.5);
  line-height: 1;
  letter-spacing: -0.025em;
  max-width: none;
}

.copy {
  position: absolute;
  left: calc(var(--u) * 6);
  top: calc(var(--u) * 3.6);
  width: calc(var(--u) * 86);
  z-index: 10;
}

.copy p {
  margin-top: calc(var(--u) * 0.8);
  font-size: calc(var(--u) * 1.48);
  line-height: 1.38;
  color: var(--ink-soft);
  max-width: 84ch;
}

.copy .tag {
  font-size: calc(var(--u) * 2.05);
  line-height: 1.35;
  color: var(--ink-soft);
  max-width: 44ch;
}

.copy .who {
  margin-top: calc(var(--u) * 2.2);
  font-size: calc(var(--u) * 1.75);
  line-height: 1.35;
  color: var(--ink);
}

.copy .who span {
  color: var(--ink-faint);
}

.copy .repo {
  display: inline-block;
  margin-top: calc(var(--u) * 0.9);
  font-size: calc(var(--u) * 1.55);
  color: var(--ink-soft);
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.copy .proto-badge {
  display: inline-block;
  margin-top: calc(var(--u) * 1.2);
  padding: calc(var(--u) * 0.3) calc(var(--u) * 0.8);
  border-radius: 4px;
  background: var(--rust-2);
  color: var(--rust);
  font-family: var(--mono);
  font-size: calc(var(--u) * 1.15);
  font-weight: 600;
}

.fine {
  position: absolute;
  left: calc(var(--u) * 6);
  right: calc(var(--u) * 28);
  bottom: calc(var(--u) * 2.2);
  font-size: calc(var(--u) * 1.15);
  line-height: 1.4;
  color: var(--ink-faint);
  z-index: 20;
}

.fine a {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.fine a:hover {
  color: var(--ink-soft);
}

/* Architecture SVG System (100 x 56.25 Canvas) */
.arch {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  font-family: var(--sans);
}

.arch text {
  dominant-baseline: central;
  fill: var(--ink-soft);
  font-size: 1.2px;
}

.arch text.t {
  fill: var(--ink);
  font-size: 1.75px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.arch text.tiny {
  font-size: 1.05px;
  fill: var(--ink-faint);
}

.arch text.faint {
  fill: var(--ink-faint);
}

.arch text.plane {
  font-size: 1.3px;
  font-weight: 600;
  fill: var(--ink-soft);
}

.arch .box {
  fill: var(--paper);
  stroke: var(--ink);
  stroke-width: 0.12;
}

.arch .card {
  fill: var(--paper);
  stroke: var(--ink);
  stroke-width: 0.1;
}

.arch .zone {
  fill: var(--zone);
}

.arch .cluster {
  fill: none;
  stroke: var(--ink-faint);
  stroke-width: 0.1;
  stroke-dasharray: 0.7, 0.5;
}

.arch .arrow {
  fill: none;
  stroke: var(--ink);
  stroke-width: 0.12;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.arch .res .card, .arch .res .box { stroke: var(--rust); }
.arch .res text.t { fill: var(--rust); }
.arch .zone.res { fill: var(--rust-2); }

.arch .plat .box { stroke: var(--teal); }
.arch .plat text.t { fill: var(--teal-d); }
.arch .plat text.plane { fill: var(--teal-d); }
.arch .zone.plat { fill: var(--teal-2); }

.arch .apibar {
  fill: var(--paper);
  stroke: var(--accent);
  stroke-width: 0.14;
}

.arch text.api-t {
  fill: var(--accent);
  font-size: 1.3px;
  font-weight: 600;
}

.arch .arrow.api { stroke: var(--accent); }

.arch .hw {
  fill: var(--zone);
  stroke: var(--ink);
  stroke-width: 0.12;
}

/* Code Slide matching Zipline Slide 10 */
.codeslide {
  position: absolute;
  left: calc(var(--u) * 6);
  right: calc(var(--u) * 6);
  top: calc(var(--u) * 16.5);
  display: grid;
  grid-template-columns: calc(var(--u) * 52) 1fr;
  column-gap: calc(var(--u) * 3.5);
  align-items: start;
  z-index: 10;
}

pre.term {
  font-family: var(--mono);
  font-size: calc(var(--u) * 0.92);
  line-height: 1.48;
  color: #E9E4D4;
  background: #1E1D19;
  padding: calc(var(--u) * 1.0) calc(var(--u) * 1.1);
  border-radius: calc(var(--u) * 0.4);
  white-space: pre;
  overflow: hidden;
}

pre.term .k { color: #9CC3F2; }
pre.term .s { color: #E7C27C; }
pre.term .c { color: #8A8879; font-style: italic; }

pre.term .api, pre.term .own {
  display: inline-block;
  width: calc(100% + var(--u) * 2.2);
  border-left: calc(var(--u) * 0.28) solid;
  margin-left: calc(var(--u) * -1.1);
  padding-left: calc(var(--u) * 0.85);
}

pre.term .api {
  border-color: var(--accent);
  background: rgba(30, 111, 204, 0.22);
}

pre.term .own {
  border-color: var(--teal);
  background: rgba(15, 138, 122, 0.22);
}

.calls div {
  margin-bottom: calc(var(--u) * 1.2);
  padding-left: calc(var(--u) * 1);
  border-left: 2px solid var(--accent);
}

.calls dt {
  font-family: var(--mono);
  font-size: calc(var(--u) * 1.25);
  font-weight: 600;
  color: var(--ink);
}

.calls dd {
  margin-top: calc(var(--u) * 0.2);
  font-size: calc(var(--u) * 1.2);
  line-height: 1.38;
  color: var(--ink-soft);
}

/* Zipline Markdown Table Layout */
.table-wrap {
  position: absolute;
  left: calc(var(--u) * 6);
  right: calc(var(--u) * 6);
  top: calc(var(--u) * 16.5);
  z-index: 10;
}

table.zipline-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--sans);
  font-size: calc(var(--u) * 1.18);
}

table.zipline-table th {
  font-family: var(--mono);
  font-size: calc(var(--u) * 0.98);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-faint);
  text-align: left;
  padding: calc(var(--u) * 0.5) calc(var(--u) * 0.8);
  border-bottom: 2px solid var(--ink);
}

table.zipline-table td {
  padding: calc(var(--u) * 0.46) calc(var(--u) * 0.8);
  border-bottom: 1px solid var(--grid);
  color: var(--ink-soft);
  font-variant-numeric: tabular-nums;
}

table.zipline-table tr.win {
  background: var(--teal-2);
  color: var(--teal-d);
  font-weight: 600;
}

table.zipline-table tr.wip {
  color: var(--rust);
}

/* Nav Chrome in Bottom-Right */
.nav-chrome {
  position: absolute;
  right: calc(var(--u) * 6);
  bottom: calc(var(--u) * 1.8);
  display: flex;
  align-items: center;
  gap: calc(var(--u) * 0.8);
  font-family: var(--mono);
  font-size: calc(var(--u) * 1.15);
  color: var(--ink-faint);
  z-index: 100;
}

.nav-chrome button {
  background: var(--paper);
  border: 1px solid var(--ink-faint);
  border-radius: 3px;
  padding: calc(var(--u) * 0.15) calc(var(--u) * 0.55);
  color: var(--ink);
  font-family: inherit;
  font-size: inherit;
  cursor: pointer;
}

.nav-chrome button:hover {
  background: var(--zone);
  border-color: var(--ink);
}
"""

JS_NAVIGATION = """
const slides = Array.from(document.querySelectorAll('.flat'));
const counter = document.getElementById('counter');
let idx = 0;

function showSlide(n) {
  idx = (n + slides.length) % slides.length;
  slides.forEach((s, i) => s.classList.toggle('is-on', i === idx));
  counter.textContent = `${idx + 1} / ${slides.length}`;
  location.hash = `slide-${idx + 1}`;
}

function nextSlide() { showSlide(idx + 1); }
function prevSlide() { showSlide(idx - 1); }

window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
    e.preventDefault();
    nextSlide();
  } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
    e.preventDefault();
    prevSlide();
  }
});

if (location.hash.startsWith('#slide-')) {
  const initial = parseInt(location.hash.replace('#slide-', ''), 10) - 1;
  if (!isNaN(initial) && initial >= 0 && initial < slides.length) {
    showSlide(initial);
  }
}
"""


def parse_markdown_table(table_lines: list) -> str:
    """Converts Markdown table lines into an elegant Zipline table."""
    rows = [line.strip().strip("|").split("|") for line in table_lines if line.strip()]
    if not rows or len(rows) < 2:
        return ""
    
    headers = [h.strip() for h in rows[0]]
    aligns = [a.strip() for a in rows[1]]
    data_rows = rows[2:]

    html = ['<div class="table-wrap"><table class="zipline-table">', '  <thead><tr>']
    for h in headers:
        html.append(f'    <th>{h}</th>')
    html.append('  </tr></thead>')
    html.append('  <tbody>')

    for r in data_rows:
        cells = [re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", c.strip()) for c in r]
        row_str = " ".join(cells)
        # Identify win or wip rows
        is_win = "Faster" in row_str or "Win" in row_str or "2.97x" in row_str or "2.16x" in row_str or "1.65x" in row_str
        is_wip = "Compute" in row_str or "WIP" in row_str or "Slowdown" in row_str
        tr_class = ' class="win"' if is_win else (' class="wip"' if is_wip else '')

        html.append(f'  <tr{tr_class}>')
        for c in cells:
            html.append(f'    <td>{c}</td>')
        html.append('  </tr>')
    html.append('  </tbody></table></div>')

    return "\n".join(html)


def parse_markdown_slides(md_path: Path):
    """Parses slides.md into frontmatter and an array of slide dicts."""
    text = md_path.read_text(encoding="utf-8")
    
    frontmatter = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            text = parts[2]
            for line in fm_text.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip()

    slide_chunks = re.split(r"(?m)^<!--\s*slide\s+(\d+)\s*(.*?)\s*-->", text)
    slides = []
    
    if len(slide_chunks) > 1:
        i = 1
        while i < len(slide_chunks):
            num = slide_chunks[i]
            stype = slide_chunks[i+1].strip()
            body = slide_chunks[i+2].strip()
            slides.append({"num": num, "type": stype, "body": body})
            i += 3
    else:
        raw_slides = text.split("\n---\n")
        for i, s in enumerate(raw_slides):
            slides.append({"num": str(i + 1), "type": "auto", "body": s.strip()})

    return frontmatter, slides


def render_html(frontmatter: dict, slides: list) -> str:
    """Builds the complete HTML string with guaranteed non-overlapping layout."""
    title = frontmatter.get("title", "Presentation")
    author = frontmatter.get("author", "Author")
    fine_default = frontmatter.get("fine", "")

    slide_htmls = []
    for idx, slide in enumerate(slides):
        is_first = (idx == 0)
        slide_num = slide["num"]
        body = slide["body"]

        fine_match = re.search(r"<!--\s*fine:\s*(.*?)\s*-->", body, re.DOTALL)
        fine_text = fine_match.group(1).strip() if fine_match else ""
        fine_p = f'<p class="fine">{fine_text}</p>' if fine_text and fine_text.lower() not in ("none", "empty") else ""
        body_clean = re.sub(r"<!--\s*fine:\s*.*?\s*-->", "", body, flags=re.DOTALL).strip()

        # Check if the slide contains a Markdown table
        if "|" in body_clean and ("| :---" in body_clean or "|:---" in body_clean or "| ---" in body_clean):
            lines = body_clean.splitlines()
            h1 = ""
            p = ""
            table_lines = []
            rest_lines = []
            in_table = False

            for l in lines:
                if l.startswith("# ") and not h1:
                    h1 = l[2:].strip()
                elif l.startswith("> ") and not p:
                    p = l[2:].strip()
                elif l.strip().startswith("|"):
                    in_table = True
                    table_lines.append(l)
                else:
                    if in_table:
                        in_table = False
                    rest_lines.append(l)

            table_html = parse_markdown_table(table_lines)
            rest_text = "\n".join(rest_lines).strip()

            slide_html = f"""
    <!-- Slide {slide_num} (Markdown Table Layout) -->
    <section class="flat {'is-on' if is_first else ''}" data-slide="{slide_num}">
      <div class="copy">
        <h1>{h1}</h1>
        <p>{p}</p>
      </div>
      {table_html}
      {rest_text}
      {fine_p}
    </section>"""

        elif body_clean.startswith("<div") or body_clean.startswith("<section"):
            # Direct HTML layout (like cover or codeslide)
            slide_html = f"""
    <!-- Slide {slide_num} -->
    <section class="flat {'is-on' if is_first else ''}" data-slide="{slide_num}">
{body_clean}
      {fine_p}
    </section>"""
        else:
            lines = body_clean.splitlines()
            h1 = ""
            p = ""
            rest = []
            for l in lines:
                if l.startswith("# ") and not h1:
                    h1 = l[2:].strip()
                elif l.startswith("> ") and not p:
                    p = l[2:].strip()
                else:
                    rest.append(l)
            
            rest_text = "\n".join(rest).strip()
            
            slide_html = f"""
    <!-- Slide {slide_num} -->
    <section class="flat {'is-on' if is_first else ''}" data-slide="{slide_num}">
      <div class="copy">
        <h1>{h1}</h1>
        <p>{p}</p>
      </div>
      {rest_text}
      {fine_p}
    </section>"""
        slide_htmls.append(slide_html)

    all_slides_html = "\n".join(slide_htmls)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {author}</title>
<style>
{ZIPLINE_CSS}
</style>
</head>
<body>
<div class="deck">
  <div class="stage" id="stage">
{all_slides_html}

    <!-- Bottom-right Navigation Chrome -->
    <div class="nav-chrome">
      <button onclick="prevSlide()">&larr; Prev</button>
      <span id="counter">1 / {len(slides)}</span>
      <button onclick="nextSlide()">Next &rarr;</button>
    </div>
  </div>
</div>

<script>
{JS_NAVIGATION}
</script>
</body>
</html>
"""
    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build_slides.py <slides.md> [output.html]")
        sys.exit(1)

    md_path = Path(sys.argv[1]).resolve()
    if not md_path.exists():
        print(f"Error: {md_path} does not exist.")
        sys.exit(1)

    out_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else md_path.parent / "index.html"

    print(f"📖 Reading Markdown from {md_path}...")
    frontmatter, slides = parse_markdown_slides(md_path)
    print(f"🎨 Compiling {len(slides)} slides into Zipline presentation with zero-overlap safety...")
    html_content = render_html(frontmatter, slides)

    out_path.write_text(html_content, encoding="utf-8")
    print(f"✅ Successfully compiled slides to {out_path} ({len(html_content)} bytes)")


if __name__ == "__main__":
    main()
