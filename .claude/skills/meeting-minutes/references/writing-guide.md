# Writing guide

## Who reads this and why

Teachers and administration at Dar Al-'Ulum Montréal, many of them
French-first, some English-first, reading on a phone or a printout a day or two
after the meeting. They want to know what was decided, what they must do and by
when, and why the rule exists so they apply it correctly. The principal
circulates the PDF as the record of the meeting, so it is also what someone
consults a month later when a rule is questioned.

## Voice

Third person, present tense for standing rules ("Each teacher submits a weekly
summary every Friday"), past tense for what happened in the room ("It was
confirmed that his parents are already aware"). Calm, precise, slightly
editorial: the minutes explain the reason behind a rule in one clause ("Page
numbers are deliberately left out of that second part so that students do not
run ahead of the class"). No bullet lists inside sections, no exclamation, no
hedging, no filler like "it was discussed that". Commas instead of dashes.
Bold only the operative fact in a paragraph: the date, the deadline, the rule
("photographed and uploaded before it is corrected"), at most one bold run per
paragraph.

Do not narrate the conversation ("a teacher then asked whether..."). State the
outcome and, when it helps, the reasoning. If two people disagreed and the point
was settled, write the settled position and put the alternative in a Decision
callout ("Separate templates per grade were considered and rejected"). If it was
not settled, write both options neutrally and mark it Under consideration.

## Structure

**Cover block.** A kicker line (organisation and meeting type), a title in
English that names the two or three main subjects ("Student Monitoring, Weekly
Reports and the Portal"), its French subtitle, and four meta cells: date,
meeting type, chair, present. Chair is normally "Principal / Direction",
present "Teaching staff / Corps enseignant" unless the transcript says
otherwise.

**Sections, numbered 01, 02...** Each has:

- `heading`: a short noun phrase in English, upper-cased by the renderer
  ("STUDENT MONITORING", "THE ACADEMIC PORTAL"). Four words or fewer.
- `headline`: one line per language that states the outcome, not the topic.
  "Observe until 25 September, then tell the parents", not "Student
  monitoring". A `<br/>` can force a two-line break where the phrasing wants it.
- `paragraphs`: two or three per language, paired EN/FR. First paragraph gives
  the rule or decision, the second the reasoning or the mechanics, a third only
  if something separate but related belongs here.
- `callouts`: zero to two boxed items under the section. Types:
  - `decision`: what was settled, with the rejected alternative if there was one.
  - `case`: an individual student or staff matter (lead with the name and level).
  - `open`: raised, not settled; say what the options were and that it stays open.
  - `note` or `reminder`: a standing instruction worth pulling out of the prose.
  Each has an optional bold `lead` and a `text`, both in EN and FR.

Order sections by importance to the reader, not by the order they came up in
the meeting. Equipment complaints go last unless a rule came out of them.

**Action items.** One row per task that someone must do. `id` A1, A2... in
reading order. `action` is an imperative sentence in both languages. `owner`
is a role, EN bold with FR beneath ("All teachers / Tout le personnel
enseignant", "Administration / Direction", "Subject teachers / Enseignants
concernés", "Principal / Direction"). `due` is short: "Fri 25 Sep", "Fridays,
8:00 PM", "Monday", "Ongoing / En continu", "To be set / À déterminer". The
renderer colours it: amber pill when there is a real date or time, green pill
for a soft due ("Monday", "This week", "To be set"), plain grey text for
ongoing. Add a `note` only when the row needs a qualifier ("Then continuously",
"Past week in detail; next week in outline"). Seven to fifteen rows is normal.

**To confirm before circulating.** Two to five items the principal must settle
before sending: a date given as a weekday only, an owner not assigned, a name
the transcript garbled, two statements that contradict. Each has a bold English
title, one or two English sentences saying what is missing, and one short French
line in the imperative saying what to do ("Confirmer la date exacte du
lancement du portail."). If everything was clear, leave the list empty and the
block is omitted.

## French

Write Quebec school French, not a machine translation. Conventions:

- A space before `:` `;` `?` `!` (the renderer does not insert it).
- Levels: "secondaire 3", "5e année", "le secondaire 3, 4 et 5".
- Times: "20 h", "16 h 15", never "8:00 PM" in French.
- Dates in the meta block: "Mercredi 9 sept. 2026". In prose: "le 25 septembre".
- "Direction" for the principal as an office, "la direction" in prose.
- "gabarit" for template, "portail" for the portal, "manuel" for a textbook,
  "cahier" for a workbook, "corridor" not "couloir", "courriel" not "email",
  "laissez-passer de corridor" for hallway pass, "surveillance" for supervision,
  "suivi" for monitoring, "bulletin" for report card, "tutorat" for tutoring.
- French headline and paragraphs may be a little longer than the English; do not
  pad the English to match.

## What to leave out

Jokes, side conversations, the projector flickering unless a rule came out of
it, who said what, verbatim quotes, the order in which things came up, and any
remark about a named adult that is not a task or a decision.
