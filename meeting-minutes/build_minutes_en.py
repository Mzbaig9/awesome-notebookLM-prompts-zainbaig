#!/usr/bin/env python3
"""English-only variant of the Dar Al-'Ulum minutes renderer.

Imports the skill's build_minutes.py and replaces the bilingual builders with
single-column English ones. Usage:
    python3 build_minutes_en.py content.json -o out.pdf
"""
import argparse, json, sys
from pathlib import Path

SKILL = Path("/root/.claude/skills/synced/2647aceb-a845-4b12-90dc-91d8ab71d9a6_7433ad11-26c2-4379-bdad-8cc91f648c3b/meeting-minutes/scripts")
sys.path.insert(0, str(SKILL))
import build_minutes as b
from reportlab.platypus import Table, TableStyle, Spacer, PageBreak, KeepTogether

ST, P, L, Mono, Rule = b.ST, b.P, b.L, b.Mono, b.Rule
W = b.CONTENT_W


def header_block(d):
    kicker = f"{d.get('org', 'Dar Al-’Ulum Montréal')} · {L(d.get('kicker'), 'en')}"
    out = [Mono(kicker, size=8.2, color=b.GREEN), Spacer(1, 12),
           P(L(d["title"], "en"), ST["title"]), Spacer(1, 16)]
    cells = []
    for key, label in (("date", "Date"), ("meeting", "Meeting"), ("chair", "Chair"), ("present", "Present")):
        cells.append([Mono(label, size=7.5), Spacer(1, 5), P(L(d.get(key, {}), "en"), ST["meta_en"])])
    t = Table([cells], colWidths=[W / 4] * 4)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, b.HAIR), ("INNERGRID", (0, 0), (-1, -1), 0.75, b.HAIR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return out + [t, Spacer(1, 14), Rule(b.INK, 1.6), Spacer(1, 14)]


def _headline(sec):
    return [P(L(sec.get("headline"), "en").replace("<br/>", " "), ST["headline"])]


def atomic_columns(sec):
    items = _headline(sec) + [Spacer(1, 9)]
    for i, para in enumerate(sec.get("paragraphs", [])):
        if i:
            items.append(Spacer(1, 9))
        items.append(P(L(para, "en"), ST["body"]))
    t = Table([[items]], colWidths=[W])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t


def split_table(n, sec):
    header = b.section_header(n, L(sec.get("heading"), "en"))[:-1]
    rows = [[header], [_headline(sec)]]
    rows += [[P(L(p, "en"), ST["body"])] for p in sec.get("paragraphs", [])]
    t = Table(rows, colWidths=[W], splitByRow=1)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                           ("BOTTOMPADDING", (0, 0), (-1, 0), 14)]))
    return t


def callout_pair(c):
    kind = c.get("type", "note")
    label = L(c.get("label") or {}, "en") or b.CALLOUT_LABELS.get(kind, b.CALLOUT_LABELS["note"])[0]
    lead, body = L(c.get("lead"), "en"), L(c.get("text"), "en")
    txt = (f"<b>{lead}</b> " if lead else "") + body
    t = Table([[[Mono(label, font="Mono-Medium", color=b.GREEN), Spacer(1, 8), P(txt, ST["callout"])]]],
              colWidths=[W])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                           ("BOX", (0, 0), (0, 0), 0.75, b.HAIR), ("LINEBEFORE", (0, 0), (0, 0), 2.2, b.GREEN)]))
    return t


def action_table(actions):
    widths = [27.2, 250, 120, W - 27.2 - 250 - 120]
    rows = [[Mono("ID"), Mono("Action"), Mono("Owner"), Mono("Due")]]
    for a in actions:
        color, bg = b.PILL[b.due_style(a)]
        due = a.get("due")
        due_txt = L(due, "en") if isinstance(due, dict) else (due or "")
        due_cell = [Mono(due_txt, size=9, color=color, tracking=0, upper=False, bg=bg)]
        note = L(a.get("note"), "en")
        if note:
            due_cell += [Spacer(1, 6), P(note, ST["note"])]
        rows.append([Mono(a.get("id", ""), size=9, color=b.GREEN, tracking=0, upper=False),
                     P(L(a.get("action"), "en"), ST["act_en"]),
                     P(L(a.get("owner"), "en"), ST["owner_en"]), due_cell])
    t = Table(rows, colWidths=widths, repeatRows=1, splitByRow=1)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                           ("LINEBELOW", (0, 0), (-1, 0), 0.8, b.RULE),
                           ("TOPPADDING", (0, 1), (-1, -1), 10), ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
                           ("LINEBELOW", (0, 1), (-1, -1), 0.8, b.HAIR)]))
    return t


def actions_block(d):
    acts = d.get("actions", [])
    if not acts:
        return []
    return [PageBreak(), Rule(b.INK, 1.6), Spacer(1, 12), P("Action items", ST["h2"]),
            Spacer(1, 18), action_table(acts)]


def confirm_block(d):
    items = d.get("to_confirm", [])
    if not items:
        return []

    def item(it):
        body = f"<b>{it.get('title', '')}</b> {L(it.get('text'), 'en')}" if it.get("title") else L(it.get("text"), "en")
        inner = Table([[P(body, ST["confirm"])]], colWidths=[b.COL_W])
        inner.setStyle(TableStyle([("LINEBEFORE", (0, 0), (0, 0), 2.2, b.AMBER),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                                   ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return inner

    rows = [[item(items[i]), "", item(items[i + 1]) if i + 1 < len(items) else ""] for i in range(0, len(items), 2)]
    grid = Table(rows, colWidths=[b.COL_W, b.GUTTER, b.COL_W])
    grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 18)]))
    return [KeepTogether([Spacer(1, 20), Rule(b.RULE, 0.8), Spacer(1, 18),
                          P("To confirm before circulating", ST["h3"]), Spacer(1, 16), grid])]


for name in ("header_block", "atomic_columns", "split_table", "callout_pair",
             "action_table", "actions_block", "confirm_block"):
    setattr(b, name, globals()[name])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = Path(args.content)
    d = json.loads(src.read_text(encoding="utf-8"))
    d.setdefault("footer", f"{d.get('org', 'Dar Al-’Ulum Montréal')} · Staff Meeting Minutes")
    out = Path(args.output) if args.output else src.with_suffix(".pdf")
    b.build(d, out)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
