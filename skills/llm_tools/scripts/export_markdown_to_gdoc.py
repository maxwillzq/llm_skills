#!/usr/bin/env python3
"""
export_markdown_to_gdoc.py

Utility script to prepare a Markdown file for Google Docs export:
1. Detects all Mermaid code blocks (```mermaid ... ```).
2. Renders each diagram to a high-resolution PNG using Kroki (https://kroki.io/mermaid/png).
3. Saves images into an images/ directory adjacent to the markdown file (or custom output dir).
4. Replaces Mermaid blocks with prominent visual placeholders for easy drag-and-drop in Google Docs.
5. Emits a *_for_gdocs.md file ready for codemind:create_document or manual paste.
"""

import argparse
import os
import re
import sys
import urllib.request


def extract_diagram_title(code: str, index: int) -> str:
    """Try to infer a concise title from the first few lines of mermaid code."""
    lines = [line.strip() for line in code.split("\n") if line.strip()]
    for line in lines:
        if line.startswith("title "):
            return line[6:].strip()
        if line.startswith("%%") and "title:" in line.lower():
            return line.split(":", 1)[1].strip()
    diag_type = lines[0].split()[0] if lines else "Diagram"
    return f"架构图 {index}: {diag_type}"


def render_mermaid_to_png(mermaid_code: str, output_path: str, timeout: int = 15) -> bool:
    """Render mermaid code to PNG using Kroki POST endpoint."""
    url = "https://kroki.io/mermaid/png"
    req = urllib.request.Request(
        url,
        data=mermaid_code.encode("utf-8"),
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Linux; export_markdown_to_gdoc.py)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Error rendering diagram to {output_path}: {e}", file=sys.stderr)
        return False


def process_markdown_file(markdown_path: str, img_dir: str = None, output_md: str = None) -> tuple[str, list[str]]:
    """Process markdown file and generate gdocs-ready markdown."""
    markdown_path = os.path.abspath(markdown_path)
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    doc_dir = os.path.dirname(markdown_path)
    base_name = os.path.splitext(os.path.basename(markdown_path))[0]

    if img_dir is None:
        img_dir = os.path.join(doc_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    if output_md is None:
        output_md = os.path.join(doc_dir, f"{base_name}_for_gdocs.md")

    with open(markdown_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
    matches = list(pattern.finditer(content))

    if not matches:
        print(f"No mermaid blocks found in {markdown_path}. No changes needed.")
        return markdown_path, []

    print(f"Found {len(matches)} Mermaid diagram(s). Rendering to PNG...")
    saved_images = []
    replacements = []

    for i, m in enumerate(matches, 1):
        code = m.group(1).strip()
        img_filename = f"mermaid_{i}.png"
        img_path = os.path.join(img_dir, img_filename)
        rel_img_path = os.path.relpath(img_path, doc_dir)

        title = extract_diagram_title(code, i)
        print(f"[{i}/{len(matches)}] Rendering '{title}' -> {img_path} ...", end=" ")
        if render_mermaid_to_png(code, img_path):
            size_kb = os.path.getsize(img_path) / 1024.0
            print(f"Done ({size_kb:.1f} KB)")
            saved_images.append(img_path)
        else:
            print("Failed")

        placeholder = (
            f"\n\n---\n"
            f"> 🖼️ **【此处插入 {title}】**\n"
            f"> *(对应高清图: {rel_img_path} ，在 Google Doc 中直接拖入或粘贴)*\n"
            f"---\n\n"
        )
        replacements.append((m.span(), placeholder))

    new_content = ""
    last_idx = 0
    for span, repl in replacements:
        new_content += content[last_idx:span[0]]
        new_content += repl
        last_idx = span[1]
    new_content += content[last_idx:]

    with open(output_md, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\n[Success] Generated Google-Docs-ready Markdown: {output_md}")
    print(f"Rendered {len(saved_images)} images in: {img_dir}")
    return output_md, saved_images


def main():
    parser = argparse.ArgumentParser(
        description="Extract Mermaid diagrams to PNG and prepare Markdown for Google Docs import."
    )
    parser.add_argument("markdown_file", help="Path to the source markdown file.")
    parser.add_argument("--img-dir", help="Directory to save rendered PNG images (default: ./images).")
    parser.add_argument("--output-md", help="Path for the generated output markdown file.")
    args = parser.parse_args()

    try:
        output_md, saved_images = process_markdown_file(
            args.markdown_file, img_dir=args.img_dir, output_md=args.output_md
        )
        print("\nNext Steps:")
        print("1. Call `codemind:create_document(title=..., markdown_text=...)` with the contents of the generated file.")
        print("2. Open the returned Google Doc URL.")
        print("3. Drag-and-drop the rendered images from the images directory into each placeholder location.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
