#!/usr/bin/env python3
"""Converts the three Markdown documents to PDF (materials/pdf/docs) using python-markdown and pymupdf.

Run from the operation-handwriting folder:  python3 tools/build_docs.py
Requires: pip install markdown pymupdf
"""
import os
import markdown
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "materials", "pdf", "docs")
os.makedirs(OUT, exist_ok=True)

CSS = """
body { font-family: sans-serif; font-size: 10pt; line-height: 1.35; }
h1 { font-size: 19pt; margin-bottom: 2pt; }
h2 { font-size: 13.5pt; margin-top: 14pt; border-bottom: 1px solid #999; }
h3 { font-size: 11.5pt; margin-top: 10pt; }
p { margin: 4pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 6pt 0; }
th, td { border: 1px solid #888; padding: 3pt 4pt; vertical-align: top; }
th { background-color: #eeeeee; }
hr { border: 0; border-top: 1px solid #999; margin: 8pt 0; }
"""

PAGE = pymupdf.paper_rect("letter")
MARGIN = 46  # points
FOOTER = "Operation Handwriting, Dar Al-Ulum Montreal"

for name in ("01-program-plan.md", "02-teachers-guide.md", "03-materials.md"):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        body = markdown.markdown(f.read(), extensions=["tables"])
    story = pymupdf.Story(html=body, user_css=CSS)
    out_path = os.path.join(OUT, name.replace(".md", ".pdf"))
    writer = pymupdf.DocumentWriter(out_path)
    where = pymupdf.Rect(MARGIN, MARGIN, PAGE.width - MARGIN, PAGE.height - MARGIN - 14)
    more = True
    while more:
        dev = writer.begin_page(PAGE)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    # page numbers and footer
    doc = pymupdf.open(out_path)
    for i, page in enumerate(doc, 1):
        page.insert_text((MARGIN, PAGE.height - 24), FOOTER, fontsize=7, color=(0.4, 0.4, 0.4))
        page.insert_text((PAGE.width - MARGIN - 30, PAGE.height - 24), f"{i} / {doc.page_count}", fontsize=7,
                         color=(0.4, 0.4, 0.4))
    doc.save(out_path, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    doc.close()
    print(name, "->", os.path.relpath(out_path, ROOT))
