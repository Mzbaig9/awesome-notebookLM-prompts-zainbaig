#!/usr/bin/env python3
"""Builds every printable PDF for Operation Handwriting into materials/pdf.

Run from the operation-handwriting folder:  python3 tools/build_pdfs.py
Requires: reportlab (pip install reportlab). Fonts are in materials/fonts.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "materials", "fonts")
OUT = os.path.join(ROOT, "materials", "pdf")
os.makedirs(OUT, exist_ok=True)

pdfmetrics.registerFont(TTFont("Print", os.path.join(FONTS, "Andika-Regular.ttf")))
pdfmetrics.registerFont(TTFont("PrintBold", os.path.join(FONTS, "Andika-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Cursive", os.path.join(FONTS, "CedarvilleCursive-Regular.ttf")))
pdfmetrics.registerFont(TTFont("UI", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("UIBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

W, H = letter
M = 16 * mm  # page margin
GREY_TRACE = 0.72
GREY_LINE = 0.55
BRAND = "Operation Handwriting, Dar Al-Ulum Montreal"

# Font geometry (fraction of em): x-height and ascender height, measured from the TTFs.
FONT_GEO = {
    "Print": {"x": 0.498, "asc": 0.781, "mid": 0.62, "gap": 0.45},
    "Cursive": {"x": 0.415, "asc": 0.69, "mid": 0.55, "gap": 0.72},
}


# ---------------------------------------------------------------- helpers
class Page:
    def __init__(self, c):
        self.c = c

    def header(self, title, subtitle=None, name_line=True, day=None):
        c = self.c
        c.setFillGray(0)
        c.setFont("UIBold", 14)
        tlines = simpleSplit(title, "UIBold", 14, W - 2 * M - 50)
        ty = H - M - 4
        for tl in tlines:
            c.drawString(M, ty, tl)
            ty -= 17
        if day:
            c.setFont("UI", 10)
            c.drawRightString(W - M, H - M - 4, day)
        y = ty - 3
        if subtitle:
            c.setFont("UI", 9.5)
            for line in simpleSplit(subtitle, "UI", 9.5, W - 2 * M):
                c.drawString(M, y, line)
                y -= 12
        if name_line:
            y -= 4
            c.setFont("UI", 10)
            c.drawString(M, y, "Name: ______________________________      Date: _______________")
            y -= 6
        c.setStrokeGray(0.3)
        c.setLineWidth(0.6)
        c.line(M, y - 4, W - M, y - 4)
        self.footer()
        return y - 16

    def footer(self):
        c = self.c
        c.setFont("UI", 7)
        c.setFillGray(0.45)
        c.drawString(M, 9 * mm, BRAND)
        c.setFillGray(0)

    def text(self, x, y, s, font="UI", size=10, grey=0.0, width=None, leading=None):
        """Draw wrapped text, returns y after the block."""
        c = self.c
        c.setFont(font, size)
        c.setFillGray(grey)
        width = width or (W - M - x)
        leading = leading or size * 1.3
        for line in simpleSplit(s, font, size, width):
            c.drawString(x, y, line)
            y -= leading
        c.setFillGray(0)
        return y

    # three-line handwriting row: returns baseline y and the font size that fits
    def hw_row(self, y_top, row_h, font="Print", x0=M, x1=W - M, top=True, mid=True):
        c = self.c
        geo = FONT_GEO[font]
        base = y_top - row_h
        midline = base + row_h * geo["mid"]
        c.setLineWidth(0.7)
        if top:
            c.setStrokeGray(0.6)
            c.line(x0, y_top, x1, y_top)
        if mid:
            c.setStrokeGray(0.6)
            c.setDash(4, 3)
            c.line(x0, midline, x1, midline)
            c.setDash()
        c.setStrokeGray(0.15)
        c.setLineWidth(0.9)
        c.line(x0, base, x1, base)
        size = (row_h * geo["mid"]) / geo["x"]
        return base, size

    def hw_block_height(self, row_h, font="Print"):
        return row_h * (1 + FONT_GEO[font]["gap"])

    def single_row(self, y, x0=M, x1=W - M):
        c = self.c
        c.setStrokeGray(0.35)
        c.setLineWidth(0.7)
        c.line(x0, y, x1, y)

    def trace_row(self, y_top, row_h, font, model, traces=4, words=None, model_black=True,
                  spacing_factor=1.15):
        """A row with a black model, grey copies to trace, then empty space."""
        c = self.c
        base, size = self.hw_row(y_top, row_h, font)
        x = M + 3
        c.setFont(font, size)
        if model_black and model:
            c.setFillGray(0)
            c.drawString(x, base, model)
            x += pdfmetrics.stringWidth(model, font, size) * spacing_factor + size * 0.35
        if model:
            for _ in range(traces):
                c.setFillGray(GREY_TRACE)
                c.drawString(x, base, model)
                x += pdfmetrics.stringWidth(model, font, size) * spacing_factor + size * 0.25
        if words:
            c.setFillGray(GREY_TRACE)
            avail = W - M - x
            need = sum(pdfmetrics.stringWidth(w, font, size) for w in words) + size * 0.9 * (len(words) - 1)
            if need > avail:
                size = size * avail / need
                c.setFont(font, size)
            for w in words:
                c.drawString(x, base, w)
                x += pdfmetrics.stringWidth(w, font, size) + size * 0.9
        c.setFillGray(0)
        return base

    def box(self, x, y, w, h, label=None, grey=0.2):
        c = self.c
        c.setStrokeGray(grey)
        c.setLineWidth(0.8)
        c.rect(x, y, w, h)
        if label:
            c.setFont("UIBold", 9)
            c.setFillGray(0)
            c.drawString(x + 4, y + h - 12, label)

    def checkbox(self, x, y, s, size=10):
        c = self.c
        c.setStrokeGray(0.2)
        c.rect(x, y - 1, 9, 9)
        c.setFont("UI", size)
        c.setFillGray(0)
        c.drawString(x + 14, y, s)


def new_pdf(name):
    c = canvas.Canvas(os.path.join(OUT, name), pagesize=letter)
    c.setTitle(name.replace(".pdf", "").replace("-", " ").title() + " | " + BRAND)
    c.setAuthor("Dar Al-Ulum Montreal")
    return c


# ---------------------------------------------------------------- content
TEST_EN = ("The quick brown fox jumps over the lazy dog. I write with care and I sit up tall. "
           "Every letter sits on the line and every word has its space.")
TEST_FR = ("Le petit chat gris joue avec la balle jaune dans le jardin. J'écris avec soin et je me "
           "tiens bien droit. Chaque lettre est sur la ligne et chaque mot a sa place.")

PRINT_FAMILIES = [
    ("Sheet A, straight line family", "Day 2", [("l", "leaf", "lune"), ("i", "ink", "île"), ("t", "top", "tasse")]),
    ("Sheet B, round family (start at two o'clock, go anticlockwise)", "Day 3",
     [("c", "cat", "carte"), ("o", "open", "orage"), ("a", "apple", "arbre"), ("d", "door", "dent"),
      ("g", "goat", "gare"), ("q", "queen", "quatre")]),
    ("Sheet C, bump family (down, back up, over)", "Day 4",
     [("r", "rain", "rue"), ("n", "nest", "nuit"), ("m", "moon", "main"), ("h", "hat", "haut"),
      ("b", "book", "bleu"), ("p", "pen", "porte")]),
    ("Sheet D, tricky family", "Day 5",
     [("e", "egg", "école"), ("s", "sun", "sac"), ("f", "fish", "fleur"), ("k", "kite", "kiwi"),
      ("u", "up", "usine"), ("v", "van", "vent")]),
    ("Sheet E, tricky family", "Day 5",
     [("w", "water", "wagon"), ("x", "box", "taxi"), ("y", "yes", "yeux"), ("z", "zip", "zéro"),
      ("j", "jam", "jour")]),
]

CURSIVE_FAMILIES = [
    ("Cursive sheet A, undercurve family (entry stroke, exit stroke)", "Day 3",
     [("i", "it", "ici"), ("u", "up", "une"), ("w", "we", "wapiti"), ("t", "to", "tu")]),
    ("Cursive sheet B, loop family", "Day 4",
     [("e", "eat", "elle"), ("l", "lit", "lit"), ("h", "hut", "huit"), ("k", "kit", "kaki"),
      ("b", "bet", "bal"), ("f", "fit", "fil")]),
    ("Cursive sheet C, round family", "Day 5",
     [("a", "at", "ami"), ("d", "did", "dur"), ("g", "get", "gel"), ("q", "quit", "qui"),
      ("c", "cat", "cou"), ("o", "on", "os")]),
    ("Cursive sheet D, overcurve family", "Day 6",
     [("n", "net", "nez"), ("m", "mat", "mur"), ("v", "vet", "vie"), ("x", "ax", "axe"),
      ("y", "yet", "yoga"), ("z", "zig", "zone")]),
    ("Cursive sheet E, remaining letters", "Day 7",
     [("r", "rat", "riz"), ("s", "sit", "sel"), ("p", "pit", "pas"), ("j", "jet", "joli")]),
]

C1_SENTENCES = [("I sit up tall.", "Je suis assis bien droit."),
                ("My pencil is sharp.", "Mon crayon est pointu."),
                ("We help our friends.", "Nous aidons nos amis."),
                ("The sun is hot today.", "Il fait chaud aujourd'hui."),
                ("I love my school.", "J'aime mon école."),
                ("Honesty is the best.", "L'honnêteté est la meilleure.")]

C2_PARA_EN = ("Good handwriting is a gift to the reader. When my letters are clear, my ideas are clear too. "
              "I take my time, I sit up straight, and I make every letter sit on the line.")
C2_PARA_FR = ("Une belle écriture est un cadeau pour le lecteur. Quand mes lettres sont claires, mes idées "
              "le sont aussi. Je prends mon temps, je me tiens droit, et chaque lettre est sur la ligne.")

C3_SPEED_EN = ("The best writers are not the fastest. They are the ones whose words can be read by anyone, "
               "at any time, without asking what a letter was meant to be. Speed comes on its own once the hand "
               "knows every letter by heart. Until then, we write clearly, we keep the same slant, and we leave "
               "a space the size of a letter between words. A page that can be read is a page that respects the "
               "person reading it.")
C3_SPEED_FR = ("Les meilleurs scripteurs ne sont pas les plus rapides. Ce sont ceux dont les mots peuvent être "
               "lus par n'importe qui, à tout moment, sans demander ce qu'une lettre voulait dire. La vitesse "
               "vient d'elle-même quand la main connaît chaque lettre par cœur. D'ici là, nous écrivons "
               "clairement, nous gardons la même inclinaison, et nous laissons un espace de la taille d'une "
               "lettre entre les mots. Une page lisible est une page qui respecte la personne qui la lit.")

RUBRIC = [
    ("Letter formation", "Many letters malformed or reversed, drawn in pieces", "Several letters malformed, some reversals",
     "Most letters correct, a few inconsistencies", "All letters formed correctly and the same way each time"),
    ("Size and proportion", "No difference between tall, small and tail letters", "Sizes inconsistent, some distinction",
     "Sizes mostly correct, occasional slips", "Tall, small and tail letters clearly and consistently sized"),
    ("Baseline", "Letters float or sink throughout", "Frequent floating or sinking", "Mostly on the line",
     "Every letter sits on the line"),
    ("Spacing", "Words run together or gaps are random", "Spacing uneven, some words touch",
     "Mostly even, a few tight or wide gaps", "Even letter spacing, clear word spaces"),
    ("Slant and consistency", "Slant changes letter by letter", "Slant varies within words", "Mostly consistent",
     "One consistent slant throughout"),
    ("Legibility", "A stranger cannot read most of it", "Readable with effort", "Readable with occasional hesitation",
     "Readable at first glance"),
]

LINE_SPEC = {  # row height (baseline to top line) per cycle, in mm
    1: {"row": 19, "font": "Print"},
    2: {"row": 13, "font": "Print"},
    3: {"row": 9, "font": None},   # single lines
}


# ---------------------------------------------------------------- lined paper
def lined_paper(cycle):
    c = new_pdf(f"lined-paper-cycle{cycle}.pdf")
    p = Page(c)
    spec = LINE_SPEC[cycle]
    for _ in range(2):  # two identical pages so double-sided printing is easy
        y = p.header(f"Lined paper, Cycle {cycle}", None, name_line=True)
        if spec["font"]:
            row = spec["row"] * mm
            block = p.hw_block_height(row, spec["font"])
            while y - block > 14 * mm:
                p.hw_row(y, row, spec["font"])
                y -= block
        else:
            row = spec["row"] * mm
            c.setStrokeGray(0.75)
            c.setLineWidth(0.5)
            c.line(M + 14 * mm, y + 4, M + 14 * mm, 14 * mm)  # margin
            while y > 14 * mm:
                p.single_row(y)
                y -= row
        c.showPage()
    c.save()


# ---------------------------------------------------------------- pre/post test
def test_sheet():
    c = new_pdf("pretest-posttest.pdf")
    p = Page(c)
    for cycle in (1, 2, 3):
        for lang, passage, prompt in (("English", TEST_EN, "Copy the text below in your best handwriting."),
                                      ("Français", TEST_FR, "Copie le texte ci-dessous de ta plus belle écriture.")):
            y = p.header(f"Handwriting test, Cycle {cycle} ({lang})", None, name_line=True)
            p.checkbox(M, y, "Pre-test, Day 1")
            p.checkbox(M + 120, y, "Post-test, Day 10")
            c.setFont("UI", 9)
            limit = "10 minutes" if cycle == 1 else "8 minutes"
            c.drawRightString(W - M, y, f"Time: {limit}")
            y -= 18
            y = p.text(M, y, prompt, "UI", 10)
            y -= 2
            y = p.text(M, y, passage, "Print", 15 if cycle == 1 else 13, leading=(21 if cycle == 1 else 18))
            y -= 6
            # writing area
            spec = LINE_SPEC[cycle]
            score_top = 62 * mm
            if spec["font"]:
                row = spec["row"] * mm
                block = p.hw_block_height(row, spec["font"])
                while y - block > score_top:
                    p.hw_row(y, row, spec["font"])
                    y -= block
            else:
                row = spec["row"] * mm
                while y > score_top + 4:
                    p.single_row(y)
                    y -= row
            # scoring box, teacher only
            bx, by, bw, bh = M, 14 * mm, W - 2 * M, 44 * mm
            p.box(bx, by, bw, bh, "Teacher scoring (1 to 4 each)")
            c.setFont("UI", 7.5)
            cols = [r[0] for r in RUBRIC] + ["Total / 24"]
            cw = (bw - 8) / 7
            for i, name in enumerate(cols):
                x = bx + 4 + i * cw
                yy = by + bh - 26
                for ln in simpleSplit(name, "UI", 7.5, cw - 8):
                    c.drawString(x + 2, yy, ln)
                    yy -= 9
                c.rect(x + 2, by + 8, cw - 8, 20)
            c.showPage()
    c.save()


# ---------------------------------------------------------------- letter sheets
def letter_sheets(fname, families, font, row_mm, title_prefix, intro):
    c = new_pdf(fname)
    p = Page(c)
    row = row_mm * mm
    block = p.hw_block_height(row, font)
    per_page = 4 if font == "Cursive" else 5
    for title, day, letters in families:
        chunks = [letters[i:i + per_page] for i in range(0, len(letters), per_page)]
        for ci, chunk in enumerate(chunks):
            t = title if len(chunks) == 1 else f"{title} ({ci + 1} of {len(chunks)})"
            y = p.header(f"{title_prefix}: {t}", intro, day=day)
            for (L, en, fr) in chunk:
                if y - 2 * block < 12 * mm:
                    break
                p.trace_row(y, row, font, L, traces=4)
                y -= block
                p.trace_row(y, row, font, None, traces=0, words=[en, fr])
                y -= block
            c.showPage()
    c.save()


def print_extras():
    """Pattern sheet, capitals, numbers, size sort for Cycle 1 (appended to c1-print-letters)."""
    c = new_pdf("c1-print-extras.pdf")
    p = Page(c)
    # pattern sheet
    y = p.header("Pattern strokes", "Trace the grey patterns, then continue on your own to the end of the line. Keep the pencil light.", day="Day 1")
    row = 16 * mm
    block = row * 1.35
    patterns = ["lines", "circles", "bumps", "cups", "zigzag", "waves", "loops"]
    for pat in patterns:
        if y - block < 16 * mm:
            break
        base, _ = p.hw_row(y, row, "Print")
        c.setStrokeGray(GREY_TRACE)
        c.setLineWidth(1.6)
        x = M + 6
        unit = row * 0.7
        pth = c.beginPath()
        for i in range(6):
            if pat == "lines":
                pth.moveTo(x, y); pth.lineTo(x, base)
                x += unit * 0.8
            elif pat == "circles":
                r = row * 0.31
                pth.moveTo(x + 2 * r, base + r)
                pth.arcTo(x, base, x + 2 * r, base + 2 * r, startAng=0, extent=360)
                x += 2 * r + unit * 0.4
            elif pat == "bumps":
                r = row * 0.31
                pth.moveTo(x, base)
                pth.arcTo(x, base - r, x + 2 * r, base + r, startAng=180, extent=-180)
                x += 2 * r
            elif pat == "cups":
                r = row * 0.31
                pth.moveTo(x, base + 2 * r)
                pth.arcTo(x, base, x + 2 * r, base + 2 * r, startAng=180, extent=180)
                x += 2 * r
            elif pat == "zigzag":
                pth.moveTo(x, base); pth.lineTo(x + unit * 0.5, y); pth.lineTo(x + unit, base)
                x += unit
            elif pat == "waves":
                r = row * 0.25
                pth.moveTo(x, base + r)
                pth.arcTo(x, base, x + 2 * r, base + 2 * r, startAng=180, extent=-180)
                pth.arcTo(x + 2 * r, base, x + 4 * r, base + 2 * r, startAng=180, extent=180)
                x += 4 * r
            elif pat == "loops":
                r = row * 0.28
                pth.moveTo(x, base)
                pth.curveTo(x + r * 2.2, y + r * 0.3, x - r * 0.8, y + r * 0.3, x + r * 1.4, base)
                x += r * 1.8
        c.drawPath(pth, stroke=1, fill=0)
        y -= block
    c.showPage()

    # capitals, 5 per page
    caps = [("L", "Lion", "Lundi"), ("I", "Ice", "Ici"), ("T", "Top", "Table"), ("H", "Hat", "Hiver"), ("E", "Egg", "École"),
            ("F", "Fish", "Fleur"), ("C", "Cat", "Carte"), ("O", "Open", "Orage"), ("Q", "Queen", "Quatre"), ("G", "Goat", "Gare"),
            ("B", "Book", "Bleu"), ("D", "Door", "Dent"), ("P", "Pen", "Porte"), ("R", "Rain", "Rue"), ("J", "Jam", "Jour"),
            ("U", "Up", "Usine"), ("A", "Apple", "Arbre"), ("V", "Van", "Vent"), ("W", "Water", "Wagon"), ("X", "Box", "Xylo"),
            ("Y", "Yes", "Yeux"), ("Z", "Zip", "Zéro"), ("K", "Kite", "Kiwi"), ("M", "Moon", "Main"), ("N", "Nest", "Nuit"),
            ("S", "Sun", "Sac")]
    row = 15 * mm
    block = p.hw_block_height(row, "Print")
    for i in range(0, len(caps), 5):
        y = p.header(f"Capital letters ({i // 5 + 1} of 6)", "Every capital starts at the top and touches the top line. Trace the grey letters, then write four more on your own.", day="Day 6")
        for (L, en, fr) in caps[i:i + 5]:
            p.trace_row(y, row, "Print", L, traces=4)
            y -= block
            p.trace_row(y, row, "Print", None, words=[en, fr])
            y -= block
        c.showPage()

    # numbers
    y = p.header("Numbers 0 to 9", "Numbers are tall, they start at the top and touch the top line. Trace, then continue.", day="Day 8")
    row = 15 * mm
    block = p.hw_block_height(row, "Print")
    for n in "0123456789":
        if y - block < 16 * mm:
            break
        p.trace_row(y, row, "Print", n, traces=5)
        y -= block
    c.showPage()

    # size sort
    y = p.header("Tall, small or tail?", "Write each letter of the alphabet in its group. Tall letters touch the top line, small letters stay under the dashed line, tail letters go under the baseline.", day="Day 6")
    c.setFont("Print", 22)
    c.drawString(M, y - 14, "a b c d e f g h i j k l m n o p q r s t u v w x y z")
    y -= 40
    row = 15 * mm
    block = p.hw_block_height(row, "Print")
    for label in ("Tall letters", "Small letters", "Tail letters"):
        c.setFont("UIBold", 10)
        c.drawString(M, y - 2, label)
        y -= 14
        for _ in range(2):
            p.hw_row(y, row, "Print")
            y -= block
        y -= 6
    c.showPage()
    c.save()


def c1_spacing_sentences():
    c = new_pdf("c1-spacing-sentences.pdf")
    p = Page(c)
    row = 12 * mm
    block = p.hw_block_height(row, "Print")
    # spacing sheet
    y = p.header("Spacing and the line", "Letters in a word sit close together. Between words, put one finger. Every letter sits on the baseline. Trace the sentence, then write it again underneath.", day="Day 7")
    for en, fr in [("I sit up tall.", "Je suis assis bien droit."), ("We help our friends.", "Nous aidons nos amis.")]:
        for s in (en, fr):
            p.trace_row(y, row, "Print", None, words=[s])
            y -= block
            p.hw_row(y, row, "Print")
            y -= block
    c.setFont("UIBold", 10)
    c.drawString(M, y, "These words are squashed. Write them again with a finger space between each word.")
    y -= 16
    for s in ("Ilovemyschool.", "Lesoleilestchaud."):
        c.setFont("Print", 16)
        c.drawString(M, y - 4, s)
        y -= 20
        p.hw_row(y, row, "Print")
        y -= block
    c.showPage()
    # sentence sheets EN then FR
    for lang, idx in (("English", 0), ("Français", 1)):
        y = p.header(f"Sentence sheet 1 ({lang})", "Trace the sentence, then copy it on the empty line. Tall, small or tail? Finger space between words. Every letter on the line.", day="Day 8")
        for pair in C1_SENTENCES:
            if y - 2 * block < 16 * mm:
                break
            p.trace_row(y, row, "Print", None, words=[pair[idx]])
            y -= block
            p.hw_row(y, row, "Print")
            y -= block
        c.showPage()
    # dictation record
    y = p.header("Dictation", "Your teacher reads each sentence twice. Listen, then write. One sentence per line.", day="Day 9")
    for i in range(1, 7):
        c.setFont("UIBold", 10)
        c.drawString(M, y - 10, str(i))
        p.hw_row(y, row, "Print", x0=M + 14)
        y -= block
    c.showPage()
    c.save()


def cursive_extras():
    c = new_pdf("c2-cursive-extras.pdf")
    p = Page(c)
    row = 13 * mm
    block = p.hw_block_height(row, "Cursive")
    # joins sheet
    y = p.header("Joins", "A join is correct when the pencil never lifts inside the word. Baseline joins first, then top joins (after b, o, v, w). Trace, then write the pair or word three more times.", day="Day 7")
    groups = [["ll", "ee", "nn"], ["in", "at", "up", "an", "it"], ["ov", "wi", "bo", "wa", "ve"], ["br", "os", "ws"],
              ["little", "bottle", "window"], ["brown", "always", "house"], ["petite", "bouteille", "fenêtre"],
              ["brun", "toujours", "maison"]]
    for g in groups:
        if y - block < 16 * mm:
            break
        p.trace_row(y, row, "Cursive", None, words=g)
        y -= block
    c.showPage()
    # capitals
    caps = list("ABCDEFGHIJKLMNOPRSTW")
    rowc = 15 * mm
    blockc = p.hw_block_height(rowc, "Cursive")
    for i in range(0, len(caps), 5):
        y = p.header(f"Cursive capitals ({i // 5 + 1} of 4)", "Capitals are tall. Trace the grey letters, then write four more. A capital is not joined to the next letter unless it feels natural.", day="Day 8")
        for L in caps[i:i + 5]:
            p.trace_row(y, rowc, "Cursive", L, traces=4)
            y -= blockc
        c.showPage()
    # paragraph + dictation
    for lang, para in (("English", C2_PARA_EN), ("Français", C2_PARA_FR)):
        y = p.header(f"Sentence sheet 2 ({lang})", "Copy the paragraph in cursive on the lines. Then your teacher dictates four sentences, one per numbered line.", day="Day 9")
        y = p.text(M, y, para, "Print", 12.5, leading=17)
        y -= 6
        for _ in range(5):
            p.hw_row(y, row, "Cursive")
            y -= block
        c.setFont("UIBold", 10)
        c.drawString(M, y, "Dictation")
        y -= 14
        for i in range(1, 5):
            if y - block < 16 * mm:
                break
            c.setFont("UIBold", 10)
            c.drawString(M, y - 10, str(i))
            p.hw_row(y, row, "Cursive", x0=M + 14)
            y -= block
        c.showPage()
    c.save()


# ---------------------------------------------------------------- Cycle 2 Day 2 and Cycle 3 Days 2 to 4
def size_spacing_slant():
    c = new_pdf("c2-c3-size-spacing-slant.pdf")
    p = Page(c)
    # self-check sheet
    y = p.header("Self-check", "Look at your Day 1 test. Be honest. Tick what is true for you, then choose three targets.", day="Day 1")
    items = ["My letters are not always the same shape.", "My tall letters and small letters are the same height.",
             "Some letters float above the line or sink below it.", "My words run into each other.",
             "My letters lean in different directions.", "I press so hard the page has grooves.",
             "My line is faint and shaky.", "I hold my pencil in a fist or with my thumb wrapped over.",
             "I rush and then I cannot read my own work.", "My cursive letters are not joined."]
    for it in items:
        p.checkbox(M, y, it)
        y -= 17
    y -= 6
    c.setFont("UIBold", 11)
    c.drawString(M, y, "My three targets for the next two weeks")
    y -= 18
    for i in range(1, 4):
        c.setFont("UI", 10)
        c.drawString(M, y, f"{i}.")
        p.single_row(y - 3, x0=M + 16)
        y -= 22
    y -= 6
    c.setFont("UIBold", 11)
    c.drawString(M, y, "Score your own Day 1 test with the rubric (1 to 4 each)")
    y -= 18
    for name in [r[0] for r in RUBRIC] + ["Total / 24"]:
        c.setFont("UI", 10)
        c.drawString(M, y, name)
        c.rect(M + 150, y - 4, 40, 14)
        y -= 20
    c.showPage()

    # size and spacing sheet (C2 Day 2, C3 Day 2), print rows
    row = 12 * mm
    block = p.hw_block_height(row, "Print")
    y = p.header("Size and spacing", "Tall letters touch the top line, small letters stay under the dashed line, tail letters hang below. One letter width between words. Trace, copy, then rewrite your Day 1 test on the last lines.", day="Day 2")
    for s in ("tall small tail", "the quick brown fox", "grand petit queue", "le petit chat gris"):
        p.trace_row(y, row, "Print", None, words=[s])
        y -= block
        p.hw_row(y, row, "Print")
        y -= block
    c.setFont("UIBold", 10)
    c.drawString(M, y, "Rewrite your Day 1 test here")
    y -= 14
    while y - block > 16 * mm:
        p.hw_row(y, row, "Print")
        y -= block
    c.showPage()

    # slant sheet (C3 Day 3): single lines with light slant guides
    y = p.header("Slant", "Pick one slant and keep it. The faint diagonal lines are your guide. Copy the sentence three times, then write two lines of your own.", day="Day 3")
    c.setFont("Print", 13)
    c.drawString(M, y, "Every letter leans the same way, from the first word to the last.")
    y -= 22
    top = y
    bottom = 16 * mm
    c.saveState()
    clip = c.beginPath()
    clip.rect(M, bottom, W - 2 * M, top - bottom)
    c.clipPath(clip, stroke=0, fill=0)
    c.setStrokeGray(0.82)
    c.setLineWidth(0.5)
    dx = (top - bottom) * 0.30  # about 17 degrees from vertical, forward slant
    x = M - dx
    while x < W - M:
        c.line(x, bottom, x + dx, top)
        x += 9 * mm
    c.restoreState()
    rowh = 9 * mm
    while y > bottom:
        p.single_row(y)
        y -= rowh
    c.showPage()

    # spacing sheet (C3 Day 4)
    y = p.header("Spacing", "Even spaces between letters, one letter width between words, a margin on the left. Copy each line, then rewrite the squashed line with proper spacing.", day="Day 4")
    rowh = 9 * mm
    for s in ("Even spacing makes a page easy to read.", "Un espacement régulier rend la page facile à lire.",
              "Onelettersbetweenwordsnotmoreandnotless.", "Unelettreentrelesmotspasplusetpasmoins."):
        c.setFont("Print", 12.5)
        c.drawString(M, y, s)
        y -= 16
        for _ in range(2):
            p.single_row(y)
            y -= rowh
        y -= 6
    while y > 16 * mm:
        p.single_row(y)
        y -= rowh
    c.showPage()
    c.save()


# ---------------------------------------------------------------- Cycle 3 fluency
def c3_fluency():
    c = new_pdf("c3-fluency.pdf")
    p = Page(c)
    row = 11 * mm
    block = p.hw_block_height(row, "Cursive")
    # joins repair
    y = p.header("Join repair", "The joins that break most: after o, v, w, b, and r or s in the middle of a word. Trace each group, then write it three times without lifting the pencil.", day="Day 5")
    groups = [["ov", "ow", "oa", "on"], ["ve", "vi", "wa", "wi"], ["br", "bo", "be", "bu"], ["ar", "er", "or", "ur"],
              ["as", "es", "is", "us"], ["brown", "over", "always"], ["house", "person", "window"],
              ["toujours", "personne", "fenêtre"]]
    for g in groups:
        if y - block < 16 * mm:
            break
        p.trace_row(y, row, "Cursive", None, words=g)
        y -= block
    c.showPage()

    # speed sheet
    for lang, passage in (("English", C3_SPEED_EN), ("Français", C3_SPEED_FR)):
        y = p.header(f"Speed with legibility ({lang})", "Copy the passage. Stop when your teacher says. Count the words you wrote and the words a partner can read at first glance. Legible words per minute is the score.", day="Day 7")
        y = p.text(M, y, passage, "Print", 11.5, leading=15.5)
        y -= 4
        # table
        bx, bw = M, W - 2 * M
        cols = ["Trial", "Time", "Words written", "Legible words", "Legible words per minute"]
        cw = [40, 50, 100, 100, bw - 290]
        c.setFont("UIBold", 9)
        x = bx
        for name, w in zip(cols, cw):
            c.rect(x, y - 16, w, 16)
            c.drawString(x + 3, y - 11, name)
            x += w
        y -= 16
        c.setFont("UI", 9)
        for trial, t in (("1", "1 min"), ("2", "3 min"), ("3", "5 min")):
            x = bx
            for i, w in enumerate(cw):
                c.rect(x, y - 16, w, 16)
                if i == 0:
                    c.drawString(x + 3, y - 11, trial)
                if i == 1:
                    c.drawString(x + 3, y - 11, t)
                x += w
            y -= 16
        y -= 10
        rowh = 9 * mm
        while y > 16 * mm:
            p.single_row(y)
            y -= rowh
        c.showPage()

    # dictation sheet
    y = p.header("Dictation and clean copy", "Your teacher reads the passage at speaking pace. Write it on the top half without stopping. Then rewrite it cleanly on the bottom half.", day="Day 8")
    rowh = 9 * mm
    c.setFont("UIBold", 10)
    c.drawString(M, y, "First pass (speed)")
    y -= 14
    half = (y - 16 * mm) / 2
    stop = y - half + 10
    while y > stop:
        p.single_row(y)
        y -= rowh
    y -= 4
    c.setFont("UIBold", 10)
    c.drawString(M, y, "Clean copy")
    y -= 14
    while y > 16 * mm:
        p.single_row(y)
        y -= rowh
    c.showPage()

    # presentation sheets: rough and final
    for kind in ("Rough draft", "Final copy"):
        y = p.header(f"Presentation, {kind}", "Title on the first line, date on the right, margin on the left, indent the first line of the paragraph, no crossing out on the final copy.", day="Day 9")
        c.setStrokeGray(0.7)
        c.setLineWidth(0.5)
        c.line(M + 16 * mm, y + 4, M + 16 * mm, 16 * mm)
        c.setFont("UI", 8)
        c.setFillGray(0.5)
        c.drawString(M, y - 6, "Title")
        c.drawRightString(W - M, y - 6, "Date")
        c.setFillGray(0)
        rowh = 9 * mm
        while y > 16 * mm:
            p.single_row(y)
            y -= rowh
        c.showPage()
    c.save()


# ---------------------------------------------------------------- teacher pack
def teacher_pack():
    c = new_pdf("teacher-pack.pdf")
    p = Page(c)
    # rubric
    y = p.header("Scoring rubric", "Six criteria, 1 to 4 each, 24 points. Bands: 6 to 11 needs intervention, 12 to 17 developing, 18 to 21 secure, 22 to 24 excellent.", name_line=False)
    colw = [108, 103, 103, 103, 103]
    x0 = M
    heads = ["Criterion", "1", "2", "3", "4"]
    c.setFont("UIBold", 9)
    x = x0
    for h_, w in zip(heads, colw):
        c.rect(x, y - 16, w, 16)
        c.drawString(x + 3, y - 11, h_)
        x += w
    y -= 16
    for r in RUBRIC:
        cells = [simpleSplit(t, "UI", 8, w - 6) for t, w in zip(r, colw)]
        hgt = max(len(cl) for cl in cells) * 10 + 8
        x = x0
        for cl, w in zip(cells, colw):
            c.rect(x, y - hgt, w, hgt)
            c.setFont("UIBold" if x == x0 else "UI", 8)
            yy = y - 11
            for line in cl:
                c.drawString(x + 3, yy, line)
                yy -= 10
            x += w
        y -= hgt
    y -= 18
    y = p.text(M, y, "Score the pre-test the same day, before you have seen the student write anything else. Same passage, same time limit on Day 10. Show each student the two samples side by side on Day 10.", "UI", 10)
    c.showPage()

    # class tracking sheet
    y = p.header("Class tracking sheet", "One line per student. Hand (L or R). Pre score Day 1. Day 5 note: moving or not. Post score Day 10. Gain. Follow-up if post score is under 12 or a motor concern.", name_line=False)
    c.setFont("UI", 10)
    c.drawString(M, y, "Cycle: ______    Lead teacher: ______________________    Dates: ______________________")
    y -= 18
    cols = ["#", "Student", "Hand", "Pre /24", "Day 5 note", "Post /24", "Gain", "Follow-up"]
    cw = [22, 150, 36, 46, 110, 46, 40, W - 2 * M - 450]
    c.setFont("UIBold", 8.5)
    x = M
    for name, w in zip(cols, cw):
        c.rect(x, y - 15, w, 15)
        c.drawString(x + 3, y - 11, name)
        x += w
    y -= 15
    rh = 17
    n = 1
    while y - rh > 34 * mm:
        x = M
        for i, w in enumerate(cw):
            c.rect(x, y - rh, w, rh)
            if i == 0:
                c.setFont("UI", 8)
                c.drawString(x + 3, y - 12, str(n))
            x += w
        y -= rh
        n += 1
    y -= 12
    c.setFont("UI", 9.5)
    c.drawString(M, y, "Average pre-test: ______     Average post-test: ______     Average gain: ______     Students under 12 on post-test: ______")
    c.showPage()

    # daily checklist card + warm-up card
    y = p.header("Daily checklist and warm-up card", None, name_line=False)
    y = p.text(M, y, "The hour", "UIBold", 12)
    steps = ["0 to 5, set-up and warm-up. Posture call: feet, back, arms, paper, helper hand. Grip check. Warm-up below.",
             "5 to 15, direct teaching. Model on the board three times, say the pathway out loud. Air writing, desk writing, one on paper.",
             "15 to 35, guided practice. Worksheet of the day. Circulate in a loop: posture, grip, then formation. One correction per student per pass.",
             "35 to 50, applied writing. Sentence, paragraph or dictation on lined paper using today's target.",
             "50 to 57, self-check and feedback. Student circles the best letter or word. One star, one wish per student, in pencil or green.",
             "57 to 60, tracker and clean-up. Progress chart box coloured, sheets into the folder."]
    for s in steps:
        y = p.text(M + 8, y, s, "UI", 10)
        y -= 3
    y -= 8
    y = p.text(M, y, "Warm-up (5 minutes, read to the group)", "UIBold", 12)
    warm = ["Shoulders: roll back five times, forward five times.",
            "Wrists: circle ten times each way, then shake the hands out.",
            "Fingers: squeeze a fist tight, open wide, ten times. Touch each finger to the thumb, forward and back, three rounds.",
            "Pencil walk: hold the pencil at the tip, walk the fingers to the top and back without the other hand.",
            "Air letters: three letters from yesterday, straight arm, big and slow, saying the pathway.",
            "Posture call: feet, back, arms, paper, helper hand. Wait until everyone is set."]
    for s in warm:
        y = p.text(M + 8, y, s, "UI", 10)
        y -= 3
    y -= 8
    y = p.text(M, y, "Fix one thing at a time, in this order", "UIBold", 12)
    y = p.text(M + 8, y, "Posture, then grip, then pressure, then letter formation, then size, then baseline, then spacing. Keep the same wish until it is fixed.", "UI", 10)
    c.showPage()

    # posture and grip poster
    c.setFont("UIBold", 26)
    c.drawCentredString(W / 2, H - M - 24, "Ready to write")
    lines = ["Feet flat on the floor.", "Back against the chair.", "Both arms on the desk.",
             "Paper tilted. Top to the right if you write with your right hand, top to the left if you write with your left hand.",
             "Helper hand holds the paper still.",
             "Pencil rests on the middle finger, held by the thumb and the index finger, two fingers from the tip.",
             "Fingers bent and relaxed. No white knuckles.", "Light grey line. No grooves on the back of the page.",
             "Tall, small or tail? Every letter sits on the line. One finger between words."]
    y = H - M - 70
    for i, s in enumerate(lines, 1):
        c.setFont("UIBold", 18)
        c.drawString(M, y, f"{i}.")
        y = p.text(M + 28, y, s, "UI", 17, leading=22)
        y -= 14
    p.footer()
    c.showPage()
    c.save()


# ---------------------------------------------------------------- student pack
def student_pack():
    c = new_pdf("student-pack.pdf")
    p = Page(c)
    # progress chart
    y = p.header("My handwriting progress", "Colour one box at the end of every hour. Your teacher writes tomorrow's wish under the box.", name_line=True)
    bw = (W - 2 * M - 4 * 8) / 5
    bh = 78
    for r in range(2):
        x = M
        for i in range(5):
            d = r * 5 + i + 1
            c.setStrokeGray(0.2)
            c.rect(x, y - bh, bw, bh)
            c.setFont("UIBold", 12)
            c.drawString(x + 6, y - 16, f"Day {d}")
            c.setFont("UI", 7.5)
            c.setFillGray(0.4)
            c.drawString(x + 6, y - bh + 6, "Wish for tomorrow:")
            c.setFillGray(0)
            c.rect(x, y - bh - 34, bw, 34)
            x += bw + 8
        y -= bh + 34 + 18
    y -= 10
    c.setFont("UIBold", 12)
    c.drawString(M, y, "My best letter this week:")
    p.single_row(y - 3, x0=M + 160, x1=M + 260)
    y -= 26
    c.drawString(M, y, "My best word this week:")
    p.single_row(y - 3, x0=M + 160, x1=M + 300)
    y -= 36
    c.setFont("UIBold", 12)
    c.drawString(M, y, "Pre-test score: ____ / 24        Post-test score: ____ / 24        Gain: ____")
    y -= 36
    c.setFont("UI", 11)
    y = p.text(M, y, "Three things I do every time I write: I sit up tall, I hold my pencil the right way, I make every letter sit on the line.", "UI", 11)
    c.showPage()

    # folder cover
    c.setFont("UIBold", 30)
    c.drawCentredString(W / 2, H - 110, "Operation Handwriting")
    c.setFont("UI", 14)
    c.drawCentredString(W / 2, H - 135, "Dar Al-Ulum Montreal")
    c.setFont("UI", 16)
    c.drawString(M + 30, H - 230, "Name: ________________________________")
    c.drawString(M + 30, H - 270, "Cycle: ______      Group: ______________")
    c.drawString(M + 30, H - 310, "Teacher: _____________________________")
    c.setFont("Print", 20)
    c.setFillGray(0.5)
    c.drawCentredString(W / 2, H - 420, "I write so that anyone can read me.")
    c.drawCentredString(W / 2, H - 450, "J'écris pour que tout le monde puisse me lire.")
    c.setFillGray(0)
    c.setStrokeGray(0.3)
    c.setLineWidth(1.2)
    c.rect(M, M, W - 2 * M, H - 2 * M)
    p.footer()
    c.showPage()

    # certificate
    c.setStrokeGray(0.2)
    c.setLineWidth(2)
    c.rect(M, M, W - 2 * M, H - 2 * M)
    c.setLineWidth(0.6)
    c.rect(M + 6, M + 6, W - 2 * M - 12, H - 2 * M - 12)
    c.setFont("UIBold", 30)
    c.drawCentredString(W / 2, H - 130, "Certificate of Achievement")
    c.setFont("UI", 14)
    c.drawCentredString(W / 2, H - 160, "Operation Handwriting, Dar Al-Ulum Montreal")
    c.setFont("UI", 15)
    c.drawCentredString(W / 2, H - 230, "This certificate is presented to")
    c.setLineWidth(0.8)
    c.line(W / 2 - 170, H - 285, W / 2 + 170, H - 285)
    c.setFont("UI", 13)
    y = H - 330
    for line in simpleSplit("for two weeks of daily effort, for writing that can now be read at first glance, and for the gain between the first day and the last.", "UI", 13, W - 2 * M - 80):
        c.drawCentredString(W / 2, y, line)
        y -= 19
    c.setFont("UI", 12)
    c.drawCentredString(W / 2, H - 420, "Pre-test ______ / 24          Post-test ______ / 24          Gain ______")
    c.setFont("UI", 12)
    c.drawString(M + 50, 130, "Teacher: ______________________")
    c.drawRightString(W - M - 50, 130, "Principal: ______________________")
    c.drawCentredString(W / 2, 95, "Date: __________________")
    c.showPage()
    c.save()


def merge(name, parts):
    """Concatenate part PDFs into one. Uses pymupdf, falls back to pypdf, else leaves the parts."""
    out = os.path.join(OUT, name)
    try:
        import pymupdf
        doc = pymupdf.open()
        for part in parts:
            doc.insert_pdf(pymupdf.open(os.path.join(OUT, part)))
        doc.save(out)
        doc.close()
    except ImportError:
        try:
            from pypdf import PdfWriter
        except ImportError:
            print("no PDF merger installed, leaving", parts, "unmerged")
            return
        w = PdfWriter()
        for part in parts:
            w.append(os.path.join(OUT, part))
        with open(out, "wb") as f:
            w.write(f)
    for part in parts:
        os.remove(os.path.join(OUT, part))


if __name__ == "__main__":
    for cyc in (1, 2, 3):
        lined_paper(cyc)
    test_sheet()
    letter_sheets("c1-print-lower.pdf", PRINT_FAMILIES, "Print", 15,
                  "Print letters", "Say the pathway out loud. Trace the grey letters, then write four more on your own. Second row: trace the words, then write them again.")
    print_extras()
    merge("c1-print-letters.pdf", ["c1-print-lower.pdf", "c1-print-extras.pdf"])
    c1_spacing_sentences()
    letter_sheets("c2-cursive-lower.pdf", CURSIVE_FAMILIES, "Cursive", 14,
                  "Cursive letters", "Every letter starts with an entry stroke from the line and ends with an exit flick. Say the pathway. Trace the grey letters, then write four more. Second row: trace the words, then write them again.")
    cursive_extras()
    merge("c2-cursive-letters.pdf", ["c2-cursive-lower.pdf", "c2-cursive-extras.pdf"])
    size_spacing_slant()
    c3_fluency()
    teacher_pack()
    student_pack()
    print("done:", sorted(os.listdir(OUT)))
