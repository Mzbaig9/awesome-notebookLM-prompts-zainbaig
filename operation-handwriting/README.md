# Operation Handwriting

Two-week, one-hour-a-day handwriting intervention for Dar Al-Ulum Montreal, grouped by cycle (Cycle 1, 2 and 3 elementary).

| File | What it is |
|---|---|
| [01-program-plan.md](01-program-plan.md) | The plan: goal, success measure, the daily hour, the ten-day sequence per cycle, roles, print list, data and follow-up |
| [02-teachers-guide.md](02-teachers-guide.md) | The teacher's guide: non-negotiables, how to run the hour, verbal pathways for every print and cursive letter, common problems and fixes, left-handers, differentiation, scoring |
| [03-materials.md](03-materials.md) | Text source for all materials: test passages, rubric, word banks (English and French), sentences, warm-up card, poster text, staff launch message, parent note |
| [materials/pdf/](materials/pdf/) | Printable pack: lined paper per cycle, pre-test and post-test, every daily worksheet, teacher pack, student pack |
| [materials/pdf/docs/](materials/pdf/docs/) | The three documents above as PDFs for sharing with staff |

## Print list per group

Before Day 1, print for each cycle: `pretest-posttest.pdf` (the two pages for that cycle, one set per student), the cycle's lined paper (20 sheets per student), the cycle's worksheet file (one per student), `student-pack.pdf` (one per student), `teacher-pack.pdf` (one per teacher).

Cycle 1 worksheets: `c1-print-letters.pdf`, `c1-spacing-sentences.pdf`.
Cycle 2 worksheets: `c2-c3-size-spacing-slant.pdf` (pages 1 and 2), `c2-cursive-letters.pdf`.
Cycle 3 worksheets: `c2-c3-size-spacing-slant.pdf` (all pages), `c3-fluency.pdf`, plus `c2-cursive-letters.pdf` capitals pages for Day 6.

## Rebuilding the PDFs

```
pip install reportlab pymupdf markdown
python3 tools/build_pdfs.py
python3 tools/build_docs.py
```

Fonts are in `materials/fonts` (Andika by SIL for print, Cedarville Cursive for cursive, both under the SIL Open Font License, licence files included).
