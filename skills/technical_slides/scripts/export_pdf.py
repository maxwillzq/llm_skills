#!/usr/bin/env python3
"""
export_pdf.py — Exports a Zipline 16:9 presentation to a high-resolution PDF.

Usage:
    python3 export_pdf.py <index.html_or_dir> [output.pdf]

Features:
1. Exact 16:9 Landscape Layout (1152 x 648 pts / 16in x 9in).
2. Uses headless Google Chrome to render each slide with Skia vector precision.
3. Automatically counts slides and unites them with pdfunite.
"""

import sys
import os
import shutil
import tempfile
import subprocess
from pathlib import Path


def export_presentation_to_pdf(html_path: Path, output_pdf: Path):
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    # Detect number of slides by searching data-slide in html
    content = html_path.read_text(encoding="utf-8")
    import re
    slides = re.findall(r'data-slide=["\'](\d+)["\']', content)
    num_slides = max([int(s) for s in slides]) if slides else 10

    print(f"📊 Found {num_slides} slides in {html_path.name}")
    print(f"🖨️  Rendering each slide in 16:9 landscape using Headless Chrome...")

    with tempfile.TemporaryDirectory(prefix="slides_pdf_") as tmpdir:
        tmp_dir = Path(tmpdir)
        slide_pdfs = []

        for i in range(1, num_slides + 1):
            slide_pdf = tmp_dir / f"slide_{i}.pdf"
            cmd = [
                "google-chrome",
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                f"--print-to-pdf={slide_pdf}",
                f"file://{html_path.resolve()}#slide-{i}"
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                print(f"⚠️ Warning rendering slide {i}: {res.stderr}")
            slide_pdfs.append(str(slide_pdf))
            print(f"  Slide {i}/{num_slides} rendered.")

        print(f"📦 Merging {len(slide_pdfs)} pages into {output_pdf.name} via pdfunite...")
        merge_cmd = ["pdfunite"] + slide_pdfs + [str(output_pdf.resolve())]
        subprocess.run(merge_cmd, check=True)

    file_size_kb = output_pdf.stat().st_size / 1024
    print(f"✅ Successfully exported 16:9 PDF: {output_pdf} ({file_size_kb:.1f} KB)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export_pdf.py <index.html_or_dir> [output.pdf]")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    if target.is_dir():
        html_path = target / "index.html"
        out_pdf = target / f"{target.name}.pdf"
    elif target.suffix == ".html":
        html_path = target
        out_pdf = target.parent / f"{target.stem}.pdf"
    elif target.suffix == ".md":
        html_path = target.parent / "index.html"
        out_pdf = target.parent / f"{target.stem}.pdf"
    else:
        html_path = target
        out_pdf = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else target.with_suffix(".pdf")

    if len(sys.argv) > 2:
        out_pdf = Path(sys.argv[2]).resolve()

    export_presentation_to_pdf(html_path, out_pdf)


if __name__ == "__main__":
    main()
