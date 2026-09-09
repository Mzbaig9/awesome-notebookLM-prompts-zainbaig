#!/usr/bin/env python3
"""
Render Dar Al-'Ulum Montréal staff meeting minutes (bilingual EN/FR) to PDF.

Usage:
    python3 build_minutes.py content.json -o minutes.pdf

The JSON schema is documented in ../references/content-schema.md and
illustrated by ../references/example-2026-09-02.json. Fonts are bundled in
../assets/fonts. Requires reportlab (pip install reportlab).
"""
import argparse
import json
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

# ---------------------------------------------------------------- palette
INK = colors.HexColor("#16231f")      # primary text
MUTED = colors.HexColor("#5f706a")    # secondary text, labels
GREEN = colors.HexColor("#1a5e4e")    # accent: kickers, callout bars, ids
AMBER = colors.HexColor("#8a4f08")    # dated pills, to-confirm bars
RULE = colors.HexColor("#c9d3ce")     # section rules
HAIR = colors.HexColor("#e0e6e2")     # box borders, dividers
PILL_AMBER = colors.HexColor("#f7efe4")
PILL_GREEN = colors.HexColor("#eaf2ee")

PAGE_W, PAGE_H = letter
MARGIN = 42.8
CONTENT_W = PAGE_W - 2 * MARGIN          # 526.4
COL_W = 247.2                            # each bilingual column
GUTTER = CONTENT_W - 2 * COL_W           # 32
HALF = CONTENT_W / 2                     # 263.2, column incl. half gutter

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def register_fonts():
    faces = {
        "Lato": "Lato-Regular.ttf",
        "Lato-Bold": "Lato-Bold.ttf",
        "Lato-Italic": "Lato-Italic.ttf",
        "Serif": "SourceSerif4-Regular.ttf",
        "Serif-Italic": "SourceSerif4-Italic.ttf",
        "Mono": "IBMPlexMono-Regular.ttf",
        "Mono-Medium": "IBMPlexMono-Medium.ttf",
    }
    for name, fn in faces.items():
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / fn)))
    pdfmetrics.registerFontFamily("Lato", normal="Lato", bold="Lato-Bold",
                                  italic="Lato-Italic", boldItalic="Lato-Bold")
    pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif",
                                  italic="Serif-Italic", boldItalic="Serif-Italic")


# ---------------------------------------------------------------- styles
def S(name, **kw):
    base = dict(fontName="Lato", fontSize=10.2, leading=15, textColor=INK,
                alignment=TA_LEFT, spaceBefore=0, spaceAfter=0)
    base.update(kw)
    return ParagraphStyle(name, **base)


ST = {
    "title": S("title", fontName="Serif", fontSize=26, leading=28, rightIndent=CONTENT_W - 390),
    "subtitle": S("subtitle", fontName="Serif-Italic", fontSize=14, leading=18, textColor=MUTED),
    "meta_en": S("meta_en", fontName="Lato-Bold", fontSize=10.5, leading=15),
    "meta_fr": S("meta_fr", fontSize=9.8, leading=14, textColor=MUTED),
    "headline": S("headline", fontName="Serif", fontSize=12.5, leading=15.7),
    "body": S("body"),
    "callout": S("callout", fontSize=10, leading=14.6),
    "act_en": S("act_en", fontSize=9, leading=13),
    "act_fr": S("act_fr", fontSize=9, leading=13, textColor=MUTED),
    "owner_en": S("owner_en", fontName="Lato-Bold", fontSize=9, leading=13),
    "note": S("note", fontSize=9, leading=13, textColor=MUTED),
    "h2": S("h2", fontName="Serif", fontSize=20, leading=24),
    "h2_fr": S("h2_fr", fontName="Serif-Italic", fontSize=12.5, leading=16, textColor=MUTED),
    "h3": S("h3", fontName="Serif", fontSize=16.5, leading=20),
    "h3_fr": S("h3_fr", fontName="Serif-Italic", fontSize=11.5, leading=15, textColor=MUTED),
    "confirm": S("confirm", fontSize=10, leading=14.6),
    "confirm_fr": S("confirm_fr", fontName="Serif-Italic", fontSize=10, leading=14, textColor=MUTED),
}

_ALLOWED = re.compile(r"&lt;(/?)(b|i|br)\s*/?&gt;")


def P(text, style):
    """Paragraph with plain text where only <b>, <i> and <br/> markup survive."""
    if text is None:
        text = ""
    esc = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    esc = _ALLOWED.sub(lambda m: f"<{m.group(1)}{m.group(2)}{'/' if m.group(2) == 'br' else ''}>", esc)
    return Paragraph(esc, style)


def L(obj, lang):
    """Pick a language from a {en, fr} dict, tolerating plain strings."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    return obj.get(lang, "") or ""


# ---------------------------------------------------------------- flowables
class Mono(Flowable):
    """Small tracked monospace label (kickers, column labels, pills)."""

    def __init__(self, text, size=7.5, color=MUTED, tracking=0.75, font="Mono",
                 upper=True, bg=None, pad_x=6, pad_y=2.5, width=None):
        super().__init__()
        self.text = text.upper() if upper else text
        self.size, self.color, self.tracking, self.font = size, color, tracking, font
        self.bg, self.pad_x, self.pad_y = bg, pad_x, pad_y
        self._w = width

    def text_width(self):
        w = pdfmetrics.stringWidth(self.text, self.font, self.size)
        return w + self.tracking * max(len(self.text) - 1, 0)

    def wrap(self, aw, ah):
        h = self.size * 1.2 + (2 * self.pad_y if self.bg else 0)
        self.width = self._w or aw
        self.height = h
        return self.width, h

    def draw(self):
        c = self.canv
        tw = self.text_width()
        x = 0
        if self.bg:
            c.setFillColor(self.bg)
            c.rect(0, 0, tw + 2 * self.pad_x, self.height, stroke=0, fill=1)
            x = self.pad_x
        t = c.beginText()
        t.setFont(self.font, self.size)
        t.setFillColor(self.color)
        t.setCharSpace(self.tracking)
        t.setTextOrigin(x, (self.height - self.size * 1.2) / 2 + self.size * 0.3)
        t.textOut(self.text)
        c.drawText(t)


class Rule(Flowable):
    def __init__(self, color=RULE, thickness=0.8, space_before=0, space_after=0):
        super().__init__()
        self.color, self.t = color, thickness
        self.sb, self.sa = space_before, space_after

    def wrap(self, aw, ah):
        self.width = aw
        self.height = self.t + self.sb + self.sa
        return aw, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.rect(0, self.sa, self.width, self.t, stroke=0, fill=1)


# ---------------------------------------------------------------- builders
def header_block(d):
    kicker = f"{d.get('org', 'Dar Al-’Ulum Montréal')} · {L(d.get('kicker'), 'en')} / {L(d.get('kicker'), 'fr')}"
    out = [Mono(kicker, size=8.2, color=GREEN), Spacer(1, 12),
           P(L(d["title"], "en"), ST["title"]), Spacer(1, 6),
           P(L(d["title"], "fr"), ST["subtitle"]), Spacer(1, 16)]

    cells = []
    for key, label in (("date", "Date"), ("meeting", "Meeting / Réunion"),
                       ("chair", "Chair / Présidence"), ("present", "Present / Présents")):
        v = d.get(key, {})
        cells.append([Mono(label, size=7.5), Spacer(1, 5),
                      P(L(v, "en"), ST["meta_en"]), P(L(v, "fr"), ST["meta_fr"])])
    w = CONTENT_W / 4
    t = Table([cells], colWidths=[w] * 4)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, HAIR),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, HAIR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    out += [t, Spacer(1, 14), Rule(INK, 1.6), Spacer(1, 14)]
    return out


def section_header(n, heading):
    return [Mono(f"{n:02d} · {heading}", size=8.2, color=GREEN), Spacer(1, 7),
            Rule(RULE, 0.8), Spacer(1, 14)]


COL_STYLE = [
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEAFTER", (0, 0), (0, -1), 0.8, HAIR),
    ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), GUTTER / 2),
    ("LEFTPADDING", (1, 0), (1, -1), GUTTER / 2), ("RIGHTPADDING", (1, 0), (1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
]


def _label_and_headline(sec, lang):
    return [Mono("English" if lang == "en" else "Français"), Spacer(1, 10),
            P(L(sec.get("headline"), lang), ST["headline"])]


def atomic_columns(sec):
    """One row, two independent cells: paragraph spacing is per column."""
    def col(lang):
        items = _label_and_headline(sec, lang) + [Spacer(1, 9)]
        for i, para in enumerate(sec.get("paragraphs", [])):
            if i:
                items.append(Spacer(1, 9))
            items.append(P(L(para, lang), ST["body"]))
        return items
    t = Table([[col("en"), col("fr")]], colWidths=[HALF, HALF])
    t.setStyle(TableStyle(COL_STYLE + [("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t


def split_table(n, sec):
    """Whole section as one table platypus can break between rows.

    Row 0 spans both columns and carries the numbered header; row 1 the
    language labels and headlines; one row per paragraph pair after that.
    """
    paras = sec.get("paragraphs", [])
    header = section_header(n, L(sec.get("heading"), "en"))[:-1]   # drop trailing spacer
    rows = [[header, ""],
            [_label_and_headline(sec, "en"), _label_and_headline(sec, "fr")]]
    rows += [[P(L(p, "en"), ST["body"]), P(L(p, "fr"), ST["body"])] for p in paras]
    t = Table(rows, colWidths=[HALF, HALF], splitByRow=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (0, 0), (1, 0)),
        ("LINEAFTER", (0, 1), (0, -1), 0.8, HAIR),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 1), (0, -1), GUTTER / 2),
        ("LEFTPADDING", (1, 1), (1, -1), GUTTER / 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 14),
    ]))
    return t


class Section(Flowable):
    """A numbered topic: header, bilingual body, callouts.

    Drawn as one block when it fits. When it does not, the section moves to
    the next page if the space left is small (under MIN_SPLIT), otherwise it
    falls back to a paragraph-by-paragraph table that platypus splits.
    """
    MIN_SPLIT = 200

    def __init__(self, n, sec):
        super().__init__()
        self.n, self.sec = n, sec
        self.header = section_header(n, L(sec.get("heading"), "en"))
        self.callouts = []
        for c in sec.get("callouts", []):
            self.callouts += [Spacer(1, 16), callout_pair(c)]
        self.parts = self.header + [atomic_columns(sec)] + self.callouts

    def wrap(self, aw, ah):
        self.width = aw
        self._heights = [f.wrap(aw, ah)[1] for f in self.parts]
        self.height = sum(self._heights)
        return aw, self.height

    def split(self, aw, ah):
        frame_h = PAGE_H - 36 - 72
        if ah < self.MIN_SPLIT and self.height <= frame_h:
            return []                        # push the whole section to the next page
        t = split_table(self.n, self.sec)
        t.wrap(aw, ah)
        # never leave the header or the headline alone at the foot of a page
        if sum(t._rowHeights[:3]) > ah:
            return []
        return [t] + self.callouts

    def draw(self):
        y = self.height
        for f, h in zip(self.parts, self._heights):
            y -= h
            f.drawOn(self.canv, 0, y)


def section(n, sec):
    return [Section(n, sec)]


CALLOUT_LABELS = {
    "decision": ("Decision", "Décision"),
    "case": ("Individual case", "Cas individuel"),
    "open": ("Under consideration", "À l'étude"),
    "note": ("Note", "Note"),
    "reminder": ("Reminder", "Rappel"),
}


def callout_pair(c):
    kind = c.get("type", "note")
    lab = c.get("label") or {}
    en_label = L(lab, "en") or CALLOUT_LABELS.get(kind, CALLOUT_LABELS["note"])[0]
    fr_label = L(lab, "fr") or CALLOUT_LABELS.get(kind, CALLOUT_LABELS["note"])[1]

    def cell(lang, label):
        lead = L(c.get("lead"), lang)
        body = L(c.get("text"), lang)
        txt = (f"<b>{lead}</b> " if lead else "") + body
        return [Mono(label, font="Mono-Medium", color=GREEN), Spacer(1, 8), P(txt, ST["callout"])]

    t = Table([[cell("en", en_label), "", cell("fr", fr_label)]],
              colWidths=[COL_W, GUTTER, COL_W])
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
          ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]
    for col in (0, 2):
        st += [("BOX", (col, 0), (col, 0), 0.75, HAIR),
               ("LINEBEFORE", (col, 0), (col, 0), 2.2, GREEN)]
    t.setStyle(TableStyle(st))
    return t


PILL = {
    "fixed": (AMBER, PILL_AMBER),   # a real date or deadline
    "soft": (GREEN, PILL_GREEN),    # a day without a date, or "to be set"
    "ongoing": (MUTED, None),       # continuous, no pill background
}


def due_style(a):
    s = a.get("due_style")
    if s in PILL:
        return s
    txt = L(a.get("due"), "en").lower()
    if "ongoing" in txt or "continu" in txt:
        return "ongoing"
    if re.search(r"\d", txt):
        return "fixed"
    return "soft"


def action_table(actions):
    head = [Mono("ID"), Mono("Action"), Mono("Action (FR)"),
            Mono("Owner / Responsable"), Mono("Due / Échéance")]
    rows = [head]
    for a in actions:
        color, bg = PILL[due_style(a)]
        due = a.get("due")
        due_txt = L(due, "en") if isinstance(due, dict) else (due or "")
        if isinstance(due, dict) and due.get("fr") and due["fr"] != due["en"]:
            due_txt = f"{due['en']} / {due['fr']}"
        due_w = CONTENT_W - 27.2 - 113 - 117 - 111.7 - 10
        pill = Mono(due_txt, size=9, color=color, tracking=0, upper=False, bg=bg)
        extra_note = ""
        if pill.text_width() + 12 > due_w and isinstance(due, dict) and due.get("fr"):
            # too wide for the column: EN alone in the pill, FR moves to the note line
            pill = Mono(due["en"], size=9, color=color, tracking=0, upper=False, bg=bg)
            extra_note = due["fr"]
        due_cell = [pill]
        note = a.get("note")
        n_txt = ""
        if note:
            n_en, n_fr = L(note, "en"), L(note, "fr")
            n_txt = n_en + (f" / {n_fr}" if n_fr and n_fr != n_en else "")
        if extra_note:
            n_txt = extra_note + (f". {n_txt}" if n_txt else "")
        if n_txt:
            due_cell += [Spacer(1, 6), P(n_txt, ST["note"])]
        rows.append([
            Mono(a.get("id", ""), size=9, color=GREEN, tracking=0, upper=False),
            P(L(a.get("action"), "en"), ST["act_en"]),
            P(L(a.get("action"), "fr"), ST["act_fr"]),
            [P(L(a.get("owner"), "en"), ST["owner_en"]), P(L(a.get("owner"), "fr"), ST["act_fr"])],
            due_cell,
        ])
    widths = [27.2, 113, 117, 111.7, CONTENT_W - 27.2 - 113 - 117 - 111.7]
    t = Table(rows, colWidths=widths, repeatRows=1, splitByRow=1)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
          ("TOPPADDING", (0, 0), (-1, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
          ("LINEBELOW", (0, 0), (-1, 0), 0.8, RULE),
          ("TOPPADDING", (0, 1), (-1, -1), 10), ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
          ("LINEBELOW", (0, 1), (-1, -1), 0.8, HAIR)]
    t.setStyle(TableStyle(st))
    return t


def actions_block(d):
    acts = d.get("actions", [])
    if not acts:
        return []
    return [PageBreak(), Rule(INK, 1.6), Spacer(1, 12),
            P("Action items", ST["h2"]), P("Suivis et responsabilités", ST["h2_fr"]),
            Spacer(1, 18), action_table(acts)]


def confirm_block(d):
    items = d.get("to_confirm", [])
    if not items:
        return []

    def item(it):
        body = f"<b>{it.get('title', '')}</b> {L(it.get('text'), 'en')}" if it.get("title") else L(it.get("text"), "en")
        inner = Table([[[P(body, ST["confirm"]), Spacer(1, 6),
                          P(L(it.get("text"), "fr") or it.get("fr", ""), ST["confirm_fr"])]]],
                      colWidths=[COL_W])
        inner.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, 0), 2.2, AMBER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return inner

    rows = []
    for i in range(0, len(items), 2):
        left = item(items[i])
        right = item(items[i + 1]) if i + 1 < len(items) else ""
        rows.append([left, "", right])
    grid = Table(rows, colWidths=[COL_W, GUTTER, COL_W])
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 18)]))
    return [KeepTogether([Spacer(1, 20), Rule(RULE, 0.8), Spacer(1, 18),
                          P("To confirm before circulating", ST["h3"]),
                          P("À confirmer avant diffusion", ST["h3_fr"]),
                          Spacer(1, 16), grid])]


# ---------------------------------------------------------------- document
class FooterCanvas(rl_canvas.Canvas):
    """Draws the footer on the last page (or every page when footer == 'all')."""
    footer_left = ""
    footer_right = ""
    mode = "last"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for i, state in enumerate(self._saved):
            self.__dict__.update(state)
            if self.mode == "all" or i == n - 1:
                self._footer()
            super().showPage()
        super().save()

    def _footer(self):
        y = 62.4
        self.setFillColor(HAIR)
        self.rect(MARGIN, y, CONTENT_W, 0.8, stroke=0, fill=1)
        for text, x, right in ((self.footer_left, MARGIN, False),
                               (self.footer_right, PAGE_W - MARGIN, True)):
            t = self.beginText()
            t.setFont("Mono", 8.2)
            t.setFillColor(MUTED)
            t.setCharSpace(0.85)
            w = pdfmetrics.stringWidth(text, "Mono", 8.2) + 0.85 * (len(text) - 1)
            t.setTextOrigin(x - w if right else x, y - 14)
            t.textOut(text)
            self.drawText(t)


def build(d, out):
    register_fonts()
    story = header_block(d)
    for i, sec in enumerate(d.get("sections", []), 1):
        if i > 1:
            story.append(Spacer(1, 18))
        story += section(i, sec)
    story += actions_block(d)
    story += confirm_block(d)

    date_short = L(d.get("date"), "short") if isinstance(d.get("date"), dict) else ""
    FooterCanvas.footer_left = d.get("footer", f"{d.get('org', 'Dar Al-’Ulum Montréal')} · Staff Meeting Minutes / Procès-verbal")
    FooterCanvas.footer_right = date_short
    FooterCanvas.mode = d.get("footer_mode", "last")

    doc = BaseDocTemplate(str(out), pagesize=letter,
                          leftMargin=MARGIN, rightMargin=MARGIN, topMargin=36, bottomMargin=72,
                          title=f"Staff Meeting Minutes / Procès-verbal — {date_short}",
                          author=d.get("org", "Dar Al-'Ulum Montréal"))
    frame = Frame(MARGIN, 72, CONTENT_W, PAGE_H - 36 - 72, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    doc.build(story, canvasmaker=FooterCanvas)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("content", help="JSON content file")
    ap.add_argument("-o", "--output", help="output PDF path (default: next to the JSON)")
    args = ap.parse_args()
    src = Path(args.content)
    d = json.loads(src.read_text(encoding="utf-8"))
    out = Path(args.output) if args.output else src.with_suffix(".pdf")
    build(d, out)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
