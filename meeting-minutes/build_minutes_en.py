#!/usr/bin/env python3
"""
English-only variant of the Dar Al-'Ulum meeting-minutes renderer.

Reads the same content JSON as the standard bilingual build_minutes.py (only
the "en" side of each field is used) and lays the minutes out in a single
column. Palette, fonts, styles and the footer come from the standard script.

Usage:
    python3 build_minutes_en.py content.json -o minutes-en.pdf [--skill-dir DIR]
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SKILL = ("/root/.claude/skills/synced/2647aceb-a845-4b12-90dc-91d8ab71d9a6_"
                 "7433ad11-26c2-4379-bdad-8cc91f648c3b/meeting-minutes")


def load_base(skill_dir):
    sys.path.insert(0, str(Path(skill_dir) / "scripts"))
    import build_minutes  # noqa: E402
    return build_minutes


def build(d, out, b):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak,
                                    PageTemplate, Spacer, Table, TableStyle)

    b.register_fonts()
    P, Mono, Rule, ST = b.P, b.Mono, b.Rule, b.ST
    CONTENT_W, MARGIN = b.CONTENT_W, b.MARGIN
    BODY_W = 430            # measure for prose; full width for tables
    en = lambda o: b.L(o, "en")

    body = b.S("body_en", rightIndent=CONTENT_W - BODY_W)
    headline = b.S("headline_en", fontName="Serif", fontSize=12.5, leading=15.7,
                   rightIndent=CONTENT_W - BODY_W)
    callout_st = b.S("callout_en", fontSize=10, leading=14.6)

    # ---- cover
    story = [Mono(f"{d.get('org', 'Dar Al-’Ulum Montréal')} · {en(d.get('kicker'))}", size=8.2, color=b.GREEN),
             Spacer(1, 12), P(en(d["title"]), ST["title"]), Spacer(1, 16)]
    cells = []
    for key, label in (("date", "Date"), ("meeting", "Meeting"), ("chair", "Chair"), ("present", "Present")):
        cells.append([Mono(label, size=7.5), Spacer(1, 5), P(en(d.get(key, {})), ST["meta_en"])])
    t = Table([cells], colWidths=[CONTENT_W / 4] * 4)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, b.HAIR), ("INNERGRID", (0, 0), (-1, -1), 0.75, b.HAIR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story += [t, Spacer(1, 14), Rule(b.INK, 1.6), Spacer(1, 14)]

    # ---- sections
    def callout(c):
        kind = c.get("type", "note")
        label = en(c.get("label")) or b.CALLOUT_LABELS.get(kind, b.CALLOUT_LABELS["note"])[0]
        lead = en(c.get("lead"))
        txt = (f"<b>{lead}</b> " if lead else "") + en(c.get("text"))
        inner = [Mono(label, font="Mono-Medium", color=b.GREEN), Spacer(1, 8), P(txt, callout_st)]
        tb = Table([[inner]], colWidths=[BODY_W], hAlign="LEFT")
        tb.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("BOX", (0, 0), (0, 0), 0.75, b.HAIR), ("LINEBEFORE", (0, 0), (0, 0), 2.2, b.GREEN)]))
        return tb

    for n, sec in enumerate(d.get("sections", []), 1):
        if n > 1:
            story.append(Spacer(1, 22))
        paras = [P(en(p), body) for p in sec.get("paragraphs", [])]
        head = b.section_header(n, en(sec.get("heading"))) + \
            [P(en(sec.get("headline")).replace("<br/>", " "), headline), Spacer(1, 9)]
        # header, headline and first paragraph never separate; the rest flows
        story.append(KeepTogether(head + paras[:1]))
        for p in paras[1:]:
            story += [Spacer(1, 9), p]
        for c in sec.get("callouts", []):
            story += [Spacer(1, 14), callout(c)]

    # ---- actions
    acts = d.get("actions", [])
    if acts:
        rows = [[Mono("ID"), Mono("Action"), Mono("Owner"), Mono("Due")]]
        for a in acts:
            color, bg = b.PILL[b.due_style(a)]
            due = a.get("due")
            due_txt = en(due) if isinstance(due, dict) else (due or "")
            cell = [Mono(due_txt, size=9, color=color, tracking=0, upper=False, bg=bg)]
            if a.get("note"):
                cell += [Spacer(1, 6), P(en(a["note"]), ST["note"])]
            rows.append([Mono(a.get("id", ""), size=9, color=b.GREEN, tracking=0, upper=False),
                         P(en(a.get("action")), ST["act_en"]),
                         P(en(a.get("owner")), ST["owner_en"]), cell])
        widths = [27.2, 250, 110, CONTENT_W - 27.2 - 250 - 110]
        at = Table(rows, colWidths=widths, repeatRows=1, splitByRow=1)
        at.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, b.RULE),
            ("TOPPADDING", (0, 1), (-1, -1), 10), ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
            ("LINEBELOW", (0, 1), (-1, -1), 0.8, b.HAIR)]))
        story += [PageBreak(), Rule(b.INK, 1.6), Spacer(1, 12), P("Action items", ST["h2"]),
                  Spacer(1, 18), at]

    # ---- to confirm
    items = d.get("to_confirm", [])
    if items:
        def item(it):
            txt = (f"<b>{it.get('title', '')}</b> " if it.get("title") else "") + en(it.get("text"))
            inner = Table([[P(txt, ST["confirm"])]], colWidths=[b.COL_W])
            inner.setStyle(TableStyle([
                ("LINEBEFORE", (0, 0), (0, 0), 2.2, b.AMBER),
                ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            return inner
        grid_rows = [[item(items[i]), "", item(items[i + 1]) if i + 1 < len(items) else ""]
                     for i in range(0, len(items), 2)]
        grid = Table(grid_rows, colWidths=[b.COL_W, b.GUTTER, b.COL_W])
        grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 18)]))
        story.append(KeepTogether([Spacer(1, 20), Rule(b.RULE, 0.8), Spacer(1, 18),
                                   P("To confirm before circulating", ST["h3"]), Spacer(1, 16), grid]))

    date_short = b.L(d.get("date"), "short") if isinstance(d.get("date"), dict) else ""
    b.FooterCanvas.footer_left = d.get("footer", f"{d.get('org', 'Dar Al-’Ulum Montréal')} · Staff Meeting Minutes")
    b.FooterCanvas.footer_right = date_short
    b.FooterCanvas.mode = d.get("footer_mode", "last")

    doc = BaseDocTemplate(str(out), pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=36, bottomMargin=72,
                          title=f"Staff Meeting Minutes — {date_short}", author=d.get("org", "Dar Al-'Ulum Montréal"))
    frame = Frame(MARGIN, 72, CONTENT_W, b.PAGE_H - 36 - 72, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    doc.build(story, canvasmaker=b.FooterCanvas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("content")
    ap.add_argument("-o", "--output")
    ap.add_argument("--skill-dir", default=DEFAULT_SKILL)
    a = ap.parse_args()
    src = Path(a.content)
    out = Path(a.output) if a.output else src.with_name(src.stem + "-en.pdf")
    build(json.loads(src.read_text(encoding="utf-8")), out, load_base(a.skill_dir))
    print(out)


if __name__ == "__main__":
    main()
