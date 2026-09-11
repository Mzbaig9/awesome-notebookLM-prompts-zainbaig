#!/usr/bin/env python3
"""Render the 11 September 2026 teacher feedback reports (one PDF per teacher)."""
import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle, KeepTogether)

FONT_DIR = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent

INK = colors.HexColor("#16231f"); MUTED = colors.HexColor("#5f706a")
GREEN = colors.HexColor("#1a5e4e"); RULE = colors.HexColor("#c9d3ce")
HAIR = colors.HexColor("#e0e6e2"); BOX = colors.HexColor("#eaf2ee")
PAGE_W, PAGE_H = letter; M = 54; W = PAGE_W - 2 * M

for n, f in {"Lato": "Lato-Regular.ttf", "Lato-Bold": "Lato-Bold.ttf",
             "Lato-Italic": "Lato-Italic.ttf", "Serif": "SourceSerif4-Regular.ttf",
             "Serif-Italic": "SourceSerif4-Italic.ttf", "Mono": "IBMPlexMono-Medium.ttf"}.items():
    pdfmetrics.registerFont(TTFont(n, str(FONT_DIR / f)))

def S(name, **kw):
    b = dict(fontName="Lato", fontSize=10.6, leading=16, textColor=INK, spaceAfter=9)
    b.update(kw); return ParagraphStyle(name, **b)

ST = {"school": S("school", fontName="Serif", fontSize=15, leading=18, spaceAfter=1),
      "school_fr": S("school_fr", fontName="Serif-Italic", fontSize=10.5, leading=13, textColor=MUTED, spaceAfter=0),
      "kicker": S("kicker", fontName="Mono", fontSize=7.5, leading=10, textColor=GREEN, spaceAfter=4),
      "title": S("title", fontName="Serif", fontSize=22, leading=26, spaceAfter=4),
      "sub": S("sub", fontName="Serif-Italic", fontSize=12, leading=15, textColor=MUTED, spaceAfter=14),
      "meta_k": S("meta_k", fontName="Lato-Bold", fontSize=9.2, leading=13, textColor=MUTED, spaceAfter=0),
      "meta_v": S("meta_v", fontSize=9.8, leading=13, spaceAfter=0),
      "h": S("h", fontName="Serif", fontSize=14.5, leading=18, spaceBefore=10, spaceAfter=6),
      "body": S("body"),
      "box": S("box", fontSize=10.2, leading=15, spaceAfter=0),
      "sig_name": S("sig_name", fontName="Lato-Bold", fontSize=10.6, leading=15, spaceAfter=0),
      "sig": S("sig", fontSize=9.8, leading=14, textColor=MUTED, spaceAfter=0)}

def on_page(c, doc):
    c.saveState()
    c.setStrokeColor(RULE); c.setLineWidth(0.6)
    c.line(M, 40, PAGE_W - M, 40)
    c.setFont("Mono", 7); c.setFillColor(MUTED)
    c.drawString(M, 28, "DAR AL-'ULUM MONTREAL  ·  INTERNAL, FOR THE TEACHER CONCERNED ONLY")
    c.drawRightString(PAGE_W - M, 28, f"PAGE {doc.page}")
    c.restoreState()

def build(fname, teacher, subjects, title, paragraphs, expectations):
    doc = BaseDocTemplate(str(OUT / fname), pagesize=letter, leftMargin=M, rightMargin=M,
                          topMargin=48, bottomMargin=60, title=title, author="Mufti Mirza-Zain Baig")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(M, 60, W, PAGE_H - 108, id="f",
                                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                                        onPage=on_page)])
    s = []
    s.append(Paragraph("Dar Al-'Ulum Montreal", ST["school"]))
    s.append(Paragraph("Dar Al-'Ulum Montréal", ST["school_fr"]))
    s.append(Spacer(1, 6))
    s.append(Table([[""]], colWidths=[W], rowHeights=[1.2],
                   style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), GREEN)])))
    s.append(Spacer(1, 14))
    s.append(Paragraph("TEACHER FEEDBACK REPORT  ·  REVIEW OF STUDENT WORK", ST["kicker"]))
    s.append(Paragraph(title, ST["title"]))
    s.append(Paragraph("Findings from the principal's review of student manuals and workbooks", ST["sub"]))
    meta = [[Paragraph("To", ST["meta_k"]), Paragraph(teacher, ST["meta_v"])],
            [Paragraph("Subjects", ST["meta_k"]), Paragraph(subjects, ST["meta_v"])],
            [Paragraph("From", ST["meta_k"]), Paragraph("Mufti Mirza-Zain Baig, Principal", ST["meta_v"])],
            [Paragraph("Date", ST["meta_k"]), Paragraph("Thursday, 11 September 2026", ST["meta_v"])]]
    s.append(Table(meta, colWidths=[70, W - 70], style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, RULE)])))
    s.append(Spacer(1, 12))
    s.append(Paragraph("As Salam Alaykum Wa Rahmatullahi Wa Barakatuhu,", ST["body"]))
    for h, ps in paragraphs:
        s.append(Paragraph(h, ST["h"]))
        for p in ps:
            s.append(Paragraph(p, ST["body"]))
    box = Table([[Paragraph(e, ST["box"])] for e in expectations], colWidths=[W],
                style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), BOX),
                                  ("LINEBEFORE", (0, 0), (0, -1), 3, GREEN),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                                  ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    s.append(KeepTogether([Paragraph("What I expect moving forward", ST["h"]), box]))
    s.append(Spacer(1, 12))
    s.append(Paragraph("I know the load is heavy at the start of the year and I appreciate the work you are putting in. "
                       "Please go through your groups' manuals this week with the points above in mind and confirm with me "
                       "once it is done. May Allah reward you and put barakah in your efforts.", ST["body"]))
    s.append(KeepTogether([Spacer(1, 6), Paragraph("Jazakallah khayra,", ST["body"]),
                           Paragraph("(Mufti) Mirza-Zain Baig", ST["sig_name"]),
                           Paragraph("Principal, Dar Al-'Ulum Montreal", ST["sig"])]))
    doc.build(s)
    print("wrote", fname)

# ------------------------------------------------------------------ Br. Ibrahim, French
build("2026-09-11-Br-Ibrahim-French.pdf", "Br. Ibrahim", "French, all levels",
      "Br. Ibrahim, French",
      [("What I found", [
          "I went through the students' French manuals and workbooks this week and I am writing down what I noticed "
          "so that we are working from the same picture. The manual work is sporadic. A lot of questions are simply "
          "missing, some pages have a sentence written here and there and nothing else, and there is no sign that "
          "anyone verified whether the exercises were actually done. Where an activity was started it was not "
          "completed, and where work was completed there is no correction on it.",
          "Chapter one is in noticeably better shape than the rest, the work is largely completed there, but even "
          "in chapter one I do not see corrections. Beyond that the manual becomes patchy again. The pace of "
          "movement through the chapters is fine, that is not the issue. The issue is what is being left behind "
          "on each page.",
          "The writing is the part that concerns me most. It is not satisfactory. In the higher levels the students "
          "are not even attempting French, and what writing exists is completely broken. We are into the second "
          "week and I have not yet seen a written text from the students, and that is genuinely concerning at this "
          "point in the year."]),
       ("Why it matters", [
          "French is the subject where the ministry and the parents will judge us most harshly, and the higher-level "
          "students cannot afford another year of avoidance. A manual that is half done with no correction tells me "
          "nothing about who is struggling and who is coasting, and it tells the student that the work does not "
          "count. Correction is where the learning actually happens."])],
      ["Every exercise assigned in the manual needs to be verified as done, not assumed. Missing questions are "
       "to be completed, not skipped over.",
       "Every completed page needs to be corrected, with the correction visible on the page, chapter one included.",
       "Make sure the exercise numbers you assign are the ones the students actually do, and organize the class so "
       "that manual time is protected.",
       "Writing takes priority. I want regular written texts from every level starting now, and the higher levels "
       "need to be pushed to attempt French even when it is weak. Writing done in class has proven very helpful, "
       "keep it in class where you can see it.",
       "Textbooks one and two are to be completed with no gaps. Get the textbooks in the students' hands and "
       "keep them there.",
       "Where a student is clearly not doing the work versus clearly struggling, note it so we can separate the "
       "two and act accordingly."])

# ------------------------------------------------------------------ Br. Abdessamad, Math
build("2026-09-11-Br-Abdessamad-Math.pdf", "Br. Abdessamad", "Mathematics, all levels except Grade 4",
      "Br. Abdessamad, Mathematics",
      [("What I found in Secondary 2", [
          "I reviewed the Secondary 2 math workbooks. The work that exists is on page six, the students have been "
          "writing directly in the books at question four, and there is no correction. The correction is not "
          "supposed to be inside the book. Page one is finished, page three has nothing done in the manual, and "
          "the correction that was done sits on one page while the next page is untouched. In honesty, looking at "
          "it I could not tell what the purpose of the book is right now, it is a few pages done and the rest empty."]),
       ("What I found in the other levels", [
          "The other groups show the same pattern as Secondary 2. The work that was assigned is not being done "
          "properly and the progression is not being tracked, so it is impossible to tell from the books who is "
          "behind and why.",
          "In Grade 5 and Grade 6 the correction is not done properly, and the word problems are being skipped in "
          "large numbers. The word problems cannot be skipped. They need to be completed with much more rigour "
          "than they are getting now, and the challenge questions should also be done wherever possible, the "
          "students need the exposure. Word problems are part of the Grade 6 exam, so this is not optional."]),
       ("Tracking", [
          "Keep a sample of the work for tracking purposes. Work with each of the exercises you told them to do, "
          "and assign specific parts, for example only part two, so that you can separate the students who are "
          "lazy from the students who are genuinely not able to do the work. Set a page target for each group and "
          "write down where they are, so that when you give them more time they move on to the next target. "
          "When a target is not met, write that down too, because it means the work was not done properly."])],
      ["Correction is done properly on every page, outside the book where the book is not meant for it, and "
       "nothing is left half corrected.",
       "Word problems are completed in full and with rigour at every level, and no word problem is skipped. Print "
       "extra word problems for Grade 6 since they are on the exam.",
       "Challenge questions are done wherever possible for exposure.",
       "Anything that is extra or not needed is circled in blue rather than having a name written on it, so that "
       "it is known at a glance.",
       "A page target and a written progression record per group, updated as they advance, so we can distinguish "
       "the lazy from the struggling and act on each.",
       "Where things are going well, correction can be more positive, the students should see that too."])

# ------------------------------------------------------------------ Br. Anas, English and Math
build("2026-09-11-Br-Anas-English-Math.pdf", "Br. Anas", "English, English as a second language, and Mathematics",
      "Br. Anas, English and Mathematics",
      [("What I found in English", [
          "I went through the students' English manuals and workbooks this week and I am writing down what I "
          "noticed. The manual work is sporadic. I am missing a lot of questions, the writing is patchy and not "
          "really complete, and there is no sign that the exercises were verified as done. Where an activity was "
          "started it was not completed.",
          "Chapter one is much better, the work there is completed, but I do not see any correction on it. After "
          "chapter one the manual becomes somewhat complete but still very sporadic. The speed at which the groups "
          "are moving through the chapters is fine, that is not the concern. The concern is what is left undone "
          "on each page behind them.",
          "The writing is not satisfactory. We are into the second week and I have not yet seen a written text "
          "from the students, and that is concerning at this stage. The writing that has been done in class has "
          "been very helpful, so that part is working and should continue."]),
       ("What I found in Math", [
          "The math picture is the same across the levels. Correction is not being done properly and word problems "
          "are being skipped. Word problems cannot be skipped, they need to be completed in full and with rigour. "
          "Anything extra or not needed is to be circled in blue rather than named, so it is known at a glance."])],
      ["Every exercise assigned in the English manual is verified as done. Missing questions are completed, not "
       "left behind.",
       "Every completed page is corrected, with the correction visible, chapter one included.",
       "Make sure the exercise numbers you assign are the ones the students actually do, and organize the class so "
       "that manual time and writing time are both protected.",
       "More writing. I want regular written texts from every group starting now. Keep the in-class writing, it "
       "is the part that is working.",
       "Textbooks one and two are to be completed with no gaps. Get the textbooks in the students' hands.",
       "In math, all word problems are done properly, correction is done properly, and extras are circled in "
       "blue."])
