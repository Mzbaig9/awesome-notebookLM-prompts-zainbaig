# Content JSON schema

All text fields that appear in both languages are objects `{"en": "...", "fr": "..."}`.
Markup allowed inside text: `<b>`, `<i>`, `<br/>`. Everything else is escaped.

```
{
  "org": "Dar Al-'Ulum Montréal",                 // optional, default shown
  "kicker": {"en": "Weekly staff meeting", "fr": "Réunion hebdomadaire du personnel"},
  "title": {"en": "...", "fr": "..."},           // EN serif title, FR italic subtitle
  "date": {"en": "Wednesday 2 Sep 2026", "fr": "Mercredi 2 sept. 2026", "short": "2 Sep 2026"},
  "meeting": {"en": "Staff meeting", "fr": "Réunion du personnel"},
  "chair": {"en": "Principal", "fr": "Direction"},
  "present": {"en": "Teaching staff", "fr": "Corps enseignant"},

  "sections": [
    {
      "heading": "Student monitoring",           // plain string, EN, rendered "01 · STUDENT MONITORING"
      "headline": {"en": "...", "fr": "..."},
      "paragraphs": [ {"en": "...", "fr": "..."}, ... ],   // paired, 1 to 3 normally
      "callouts": [                              // optional
        {
          "type": "decision" | "case" | "open" | "note" | "reminder",
          "label": {"en": "...", "fr": "..."},   // optional, overrides the type's default label
          "lead": {"en": "Bold lead.", "fr": "..."},        // optional
          "text": {"en": "...", "fr": "..."}
        }
      ]
    }
  ],

  "actions": [
    {
      "id": "A1",
      "action": {"en": "Imperative sentence.", "fr": "Phrase à l'impératif."},
      "owner": {"en": "All teachers", "fr": "Tout le personnel enseignant"},
      "due": {"en": "Fri 25 Sep", "fr": "..."},  // fr optional; shown as "en / fr" when different
      "due_style": "fixed" | "soft" | "ongoing", // optional; inferred from the text if absent
      "note": {"en": "...", "fr": "..."}         // optional qualifier under the pill
    }
  ],

  "to_confirm": [                                // optional; block omitted when empty
    {
      "title": "Portal start date.",             // bold EN lead, include the full stop
      "text": {"en": "What is missing.", "fr": "Quoi faire, à l'impératif."}
    }
  ],

  "footer": "Dar Al-'Ulum Montréal · Staff Meeting Minutes / Procès-verbal",  // optional
  "footer_mode": "last" | "all"                  // optional, default "last" (footer on final page only)
}
```

Due style inference when `due_style` is absent: text containing a digit is
`fixed` (amber pill), text containing "ongoing" or "continu" is `ongoing`
(plain grey), anything else is `soft` (green pill).

Long sections: if a section has more than six paragraph pairs or roughly more
than 3200 characters, the renderer switches that section to a row-per-paragraph
table so it can split across pages. Prefer splitting the topic into two sections
instead.
