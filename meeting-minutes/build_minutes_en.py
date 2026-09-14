#!/usr/bin/env python3
"""English-only variant of the Dar Al-'Ulum minutes renderer.

Reuses the fonts, palette, styles and page furniture of build_minutes.py and
lays the same content out in a single language: one full-width column per
section, one callout box, a four-column action table, English-only confirm
items. Text fields may be plain strings or {"en": ...} objects.

Usage: python3 build_minutes_en.py content.json -o minutes.pdf
"""
import argparse
import json
import sys
from pathlib import Path

SKILL = Path("/root/.claude/skills/synced/2647aceb-a845-4b12-90dc-91d8ab71d9a6_7433ad11-26c2-4379-bdad-8cc91f648c3b/meeting-minutes/scripts")
sys.path.insert(0, str(SKILL))
import build_minutes as B  # noqa: E402
from build_minutes import (AMBER, CONTENT_W, GREEN, HAIR, INK, MARGIN, PAGE_H, PILL, RULE,  # noqa: E402
                           ST, FooterCanvas, Mono, Rule, L, P, due_style, register_fonts,
                           section_header)
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, KeepTogether,  # noqa: E402
                                PageTemplate, Spacer, Table, TableStyle)

TEXT_W = 430          # reading measure for body prose
COL_W = (CONTENT_W - 32) / 2
GUTTER = 32


def E(obj):
    return L(obj, "en")


def header_block(d):
    kicker = f"{d.get('org', 'Dar Al-’Ulum Montréal')} · {E(d.get('kicker'))}"
    out = [Mono(kicker, size=8.2, color=GREEN), Spacer(1, 12),
           P(E(d["title"]), ST["title"]), Spacer(1, 6)]
    if d.get("subtitle"):
        out += [P(E(d["subtitle"]), ST["subtitle"]), Spacer(1, 6)]
    out.append(Spacer(1, 10))
    labels = d.get("meta_labels", {})
    cells = []
    for key, label in (("date", "Date"), ("meeting", "Meeting"), ("chair", "Chair"), ("present", "Present")):
        v = d.get(key, {})
        cells.append([Mono(labels.get(key, label), size=7.5), Spacer(1, 5), P(E(v), ST["meta_en"])])
    w = CONTENT_W / 4
    t = Table([cells], colWidths=[w] * 4)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, HAIR), ("INNERGRID", (0, 0), (-1, -1), 0.75, HAIR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    out += [t, Spacer(1, 14), Rule(INK, 1.6), Spacer(1, 14)]
    return out


HEADLINE = B.S("headline1", fontName="Serif", fontSize=13.5, leading=17, rightIndent=30)
BODY = B.S("body1", rightIndent=CONTENT_W - TEXT_W)


def body_items(sec):
    items = [P(E(sec.get("headline")), HEADLINE), Spacer(1, 9)]
    for i, para in enumerate(sec.get("paragraphs", [])):
        if i:
            items.append(Spacer(1, 9))
        items.append(P(E(para), BODY))
    return items


def split_table(n, sec):
    header = section_header(n, E(sec.get("heading")))[:-1]
    rows = [[header], [P(E(sec.get("headline")), HEADLINE)]]
    rows += [[P(E(p), BODY)] for p in sec.get("paragraphs", [])]
    t = Table(rows, colWidths=[CONTENT_W], splitByRow=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 14)]))
    return t


class Section(Flowable):
    MIN_SPLIT = 200

    def __init__(self, n, sec):
        super().__init__()
        self.n, self.sec = n, sec
        self.callouts = []
        for c in sec.get("callouts", []):
            self.callouts += [Spacer(1, 16), callout(c)]
        self.parts = section_header(n, E(sec.get("heading"))) + body_items(sec) + self.callouts

    def wrap(self, aw, ah):
        self.width = aw
        self._heights = [f.wrap(aw, ah)[1] for f in self.parts]
        self.height = sum(self._heights)
        return aw, self.height

    def split(self, aw, ah):
        frame_h = PAGE_H - 36 - 72
        if ah < self.MIN_SPLIT and self.height <= frame_h:
            return []
        t = split_table(self.n, self.sec)
        t.wrap(aw, ah)
        if sum(t._rowHeights[:3]) > ah:
            return []
        return [t] + self.callouts

    def draw(self):
        y = self.height
        for f, h in zip(self.parts, self._heights):
            y -= h
            f.drawOn(self.canv, 0, y)


def callout(c):
    kind = c.get("type", "note")
    label = E(c.get("label")) or B.CALLOUT_LABELS.get(kind, B.CALLOUT_LABELS["note"])[0]
    lead = E(c.get("lead"))
    txt = (f"<b>{lead}</b> " if lead else "") + E(c.get("text"))
    cell = [Mono(label, font="Mono-Medium", color=GREEN), Spacer(1, 8), P(txt, ST["callout"])]
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (0, 0), 0.75, HAIR), ("LINEBEFORE", (0, 0), (0, 0), 2.2, GREEN)]))
    return t


def action_table(actions):
    widths = [27.2, 262, 118, CONTENT_W - 27.2 - 262 - 118]
    rows = [[Mono("ID"), Mono("Action"), Mono("Owner"), Mono("Due")]]
    for a in actions:
        color, bg = PILL[due_style(a)]
        pill = Mono(E(a.get("due")), size=9, color=color, tracking=0, upper=False, bg=bg)
        due_cell = [pill]
        if a.get("note"):
            due_cell += [Spacer(1, 6), P(E(a["note"]), ST["note"])]
        rows.append([Mono(a.get("id", ""), size=9, color=GREEN, tracking=0, upper=False),
                     P(E(a.get("action")), ST["act_en"]),
                     P(E(a.get("owner")), ST["owner_en"]), due_cell])
    t = Table(rows, colWidths=widths, repeatRows=1, splitByRow=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, RULE),
        ("TOPPADDING", (0, 1), (-1, -1), 10), ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
        ("LINEBELOW", (0, 1), (-1, -1), 0.8, HAIR)]))
    return t


def actions_block(d):
    acts = d.get("actions", [])
    if not acts:
        return []
    return [Spacer(1, 26), CondPageBreak(300), Rule(INK, 1.6), Spacer(1, 12), P("Action items", ST["h2"]),
            Spacer(1, 18), action_table(acts)]


def confirm_block(d):
    items = d.get("to_confirm", [])
    if not items:
        return []

    def item(it):
        body = f"<b>{it.get('title', '')}</b> {E(it.get('text'))}" if it.get("title") else E(it.get("text"))
        inner = Table([[P(body, ST["confirm"])]], colWidths=[COL_W])
        inner.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, 0), 2.2, AMBER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return inner

    rows = []
    for i in range(0, len(items), 2):
        rows.append([item(items[i]), "", item(items[i + 1]) if i + 1 < len(items) else ""])
    grid = Table(rows, colWidths=[COL_W, GUTTER, COL_W])
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 18)]))
    return [KeepTogether([Spacer(1, 20), Rule(RULE, 0.8), Spacer(1, 18),
                          P("To confirm before circulating", ST["h3"]), Spacer(1, 16), grid])]


def build(d, out):
    register_fonts()
    story = header_block(d)
    for i, sec in enumerate(d.get("sections", []), 1):
        if i > 1:
            story.append(Spacer(1, 18))
        story.append(Section(i, sec))
    story += actions_block(d)
    story += confirm_block(d)
    date_short = L(d.get("date"), "short") if isinstance(d.get("date"), dict) else ""
    FooterCanvas.footer_left = d.get("footer", f"{d.get('org', 'Dar Al-’Ulum Montréal')} · Meeting Minutes")
    FooterCanvas.footer_right = date_short
    FooterCanvas.mode = d.get("footer_mode", "last")
    doc = BaseDocTemplate(str(out), pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=36, bottomMargin=72,
                          title=f"Meeting Minutes — {date_short}", author=d.get("org", ""))
    frame = Frame(MARGIN, 72, CONTENT_W, PAGE_H - 36 - 72, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    doc.build(story, canvasmaker=FooterCanvas)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("content")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = Path(args.content)
    d = json.loads(src.read_text(encoding="utf-8"))
    out = Path(args.output) if args.output else src.with_suffix(".pdf")
    build(d, out)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
