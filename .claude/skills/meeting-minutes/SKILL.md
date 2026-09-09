---
name: meeting-minutes
description: >-
  Produce Dar Al-'Ulum Montréal staff meeting minutes (procès-verbal) in the
  school's standard bilingual EN/FR PDF format from a transcript, recording,
  notes, or a rough summary. Use this skill whenever the user asks for minutes,
  a procès-verbal, a compte rendu, a meeting summary, "write up the meeting",
  "create the minutes", or hands over a staff/teachers/admin meeting transcript
  (PDF, text, or pasted), even if they don't say the word "minutes". Also use it
  to regenerate or fix an existing set of minutes in this format. Every set of
  minutes is rendered with the bundled ReportLab script so the layout is
  identical from week to week; do not hand-build a PDF or a Markdown page instead.
---

# Meeting minutes, Dar Al-'Ulum Montréal standard

The standard is a bilingual (English left, French right) PDF: a titled cover
block, numbered topic sections written as short editorial prose, callout boxes
for decisions, individual cases and open questions, an action table with IDs
and due-date pills, and a closing "To confirm before circulating" list. The
reference document is `references/example-2026-09-02.json` (its rendered form
is what the principal approved as the standard). Read it before writing; it
shows the tone, the density and the French register better than any rule.

## Workflow

1. **Get the source text.** For a PDF transcript use pypdf:
   `python3 -c "import pypdf;print('\n'.join(p.extract_text() for p in pypdf.PdfReader('t.pdf').pages))"`.
   Transcripts from the school are usually mixed French and English, with
   unnamed speakers (Speaker 0 is almost always the principal). Read the whole
   thing before writing anything.
2. **Extract, don't transcribe.** List every topic, every decision, every rule
   restated, every date, every task with an owner, and every item that was
   raised but not settled. Group them into 4 to 8 topics. Drop small talk,
   repetition and half-sentences.
3. **Write the content JSON.** Follow `references/writing-guide.md` for voice
   and structure and `references/content-schema.md` for the fields. Write the
   English and French as two real texts, not a literal translation. When the
   user asks for English only (a one-on-one, an internal operations check-in,
   "just English"), set `"language": "en"` and fill only the `en` fields; the
   renderer switches to a single full-width column with English labels. Save it as
   `meeting-minutes/YYYY-MM-DD-<slug>.json` when working inside a repo that has
   that folder, otherwise next to the input file.
4. **Render.** `python3 <skill>/scripts/build_minutes.py content.json -o out.pdf`
   (needs `pip install reportlab`; fonts are bundled in `assets/fonts`).
5. **Check the pages.** Render to PNG with pymupdf
   (`pymupdf.open(pdf)[i].get_pixmap(dpi=80).save(...)`) and look at every page:
   no orphaned rule at the bottom of a page, no headline wrapping into four
   lines, callouts sitting under their section, pills readable, French
   accents intact. Fix the JSON, not the script, unless the layout itself is wrong.
6. **Deliver the PDF** (and keep the JSON beside it, it is the editable source).
   Tell the user what you could not resolve from the transcript; those items are
   already in the "To confirm" block, so the note can be one sentence.

## Rules that are easy to get wrong

- Never invent a name, a date, a number or a decision that the transcript does
  not carry. When the transcript is unclear (a name garbled, "Monday" with no
  date, two contradictory frequencies), write what was said and put the gap in
  `to_confirm`. That block exists precisely so the principal can settle it
  before the minutes go out.
- Speakers are not named in transcripts. Attribute to roles: the principal, a
  teacher, the teacher concerned, administration. Name a student only when the
  transcript names them clearly and the item is about that student.
- Commas, not dashes. The principal does not want em-dashes anywhere in his
  documents. Use a comma, a colon or a new sentence.
- Keep each topic to two or three paragraphs per language. Minutes are read on
  a phone between classes. Long transcript, tight minutes.
- Every action row needs an owner and a due value. If the meeting fixed neither,
  put "To be set / À déterminer" and add the item to `to_confirm`.
- The footer, the fonts, the colours and the section numbering are fixed by the
  script. Do not pass style through the JSON.

## Files

- `scripts/build_minutes.py`: JSON to PDF renderer. Run it, do not rewrite it.
- `references/writing-guide.md`: voice, section anatomy, French conventions.
- `references/content-schema.md`: every JSON field, with the allowed values.
- `references/example-2026-09-02.json`: the approved reference minutes, complete.
- `assets/fonts/`: Source Serif 4, Lato, IBM Plex Mono (OFL licensed).
