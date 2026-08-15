# Masjids in North Carolina — roster and contact research

Compiled by seven parallel research agents covering the state by region, plus
one working top-down through aggregate Islamic directories.

## Status

| Deliverable | State |
|---|---|
| Roster (name, city, county, address, website, phone) | **Done** — ~107 organizations |
| Email addresses | **Blocked** — see below |

## The roster is usable. The emails are not.

`nc-masjids-roster.csv` is the deliverable. It carries name, city, county,
region, street address, website, phone, and per-row flags.

`DO-NOT-MAIL-unverified-email-candidates.csv` is **not** a deliverable. It is a
verification worklist and its filename says what to do with it.

### Why there is no email column

Every outbound HTTPS request to a non-GitHub host was refused by the
organization egress proxy with a `403` on `CONNECT`. All seven agents hit it
independently; not one page was ever fetched. The plan had been to open each
masjid's `/contact` page and copy the address shown there — that step was
impossible from start to finish.

What remained was `WebSearch`, which returns a summarizer's *description* of a
page rather than the page. That distinction is the whole problem. When a
summary says a masjid's email is `info@<their-domain>`, there is no way from
here to tell whether it read that string off the page or pattern-completed a
plausible one. Roughly half the candidates gathered have exactly that
guessable shape.

Rather than hand over a mailing list that is somewhere between mostly-right
and quietly-wrong, the candidates are quarantined with a per-row risk grade:

- `PATTERN-RISK` — matches `info@`/`contact@` + domain. Trivially guessable,
  highest chance of being fabricated.
- `DISTINCTIVE` — a shape that could not be derived from the domain
  (`icgncinfo@gmail.com`, `office@islam1.org`). Far more likely genuine.
- `STALE-RISK` — real-looking but from a dated directory (`@iname.com`,
  `@earthlink.net`).
- `HIGH-RISK` — could not be attributed to any page at all.

To finish this properly, see `EGRESS-ALLOWLIST-REQUEST.md`.

## What the roster covers

| Region | Organizations |
|---|---|
| Charlotte Metro | 25 |
| Triangle | 34 |
| Triad | 18 |
| Southeastern | 17 |
| Eastern | 7 |
| Western | 6 |

Counts include Islamic schools with prayer facilities, campus MSAs, one
umbrella organization (MAS-RDU), and rows flagged `UNVERIFIED`. The count of
distinct operating community masjids is lower — roughly 90.

### Notable entries

- **Ar-Razzaq Islamic Center**, Durham — the oldest masjid in North Carolina,
  founded 1956 as Muhammad's Mosque #34. NC historical marker G-148. It
  directly seeded masjids in Raleigh, Fayetteville, Greenville and Kinston.
- **Masjid Al-Muminun**, Winston-Salem — oldest Islamic organization in the
  Triad, community roots to 1955.
- **Masjid Omar Ibn Sayyid**, Fayetteville — named for the enslaved West
  African Muslim scholar; historical marker placed 2010.
- **Islamic Center of Boone** (2022), **Islamic Center of Youngsville** and
  **ILM Center** (both Dec 2025) — the newest in the state.

### Flags used in the roster

`SHIA`, `AHMADIYYA`, `NATION-OF-ISLAM` mark congregations outside the Sunni
mainstream — include or exclude by purpose. `AFRICAN-AMERICAN` and
`REFUGEE-COMMUNITY` mark congregations that are easy to miss because they are
under-represented in commercial mosque directories; they were sought
deliberately. `SCHOOL`, `CAMPUS`, `MILITARY`, `UMBRELLA` mark rows that are
not standalone community masjids. `UNVERIFIED`, `POSSIBLY-CLOSED`,
`POSSIBLY-DEFUNCT`, `POSSIBLE-DUPLICATE`, `ADDRESS-CONFLICT` and
`STATE-AMBIGUOUS` mark data-quality problems to resolve.

## Known gaps

Discovery stopped short — the `WebSearch` session budget capped out at 200
calls mid-sweep.

- **Union County (Monroe, Indian Trail)** — the most likely genuine omission.
  A `monroemosque.com` surfaced but was attributed on follow-up to Monroe,
  *Washington*. Re-check this first.
- **Hickory / Catawba County** — an "Islamic Community Center" at 1960 US Hwy
  70 SE appeared in one summary, conflated with the Morganton center. Hickory
  is the largest unsearched population center in the west and has significant
  Hmong and African refugee communities.
- **Never searched for lack of budget**: Northampton, Hertford, Bertie,
  Martin, Camden, Currituck, Dare, Chowan, Perquimans, Gates, Tyrrell,
  Washington, Hyde, Greene, Pamlico counties; and most far-western counties
  (Haywood, Jackson, Macon, Swain, Cherokee, Clay, Graham, Transylvania,
  Polk, Rutherford, McDowell, Mitchell, Yancey, Avery, Ashe, Alleghany,
  Wilkes, Alexander, Madison).
- **Never swept**: ICNA / ISNA / CAIR-NC chapter directories, the Ihsan Bagby
  US Mosque Survey, and Nation of Islam / Moorish Science / W.D. Mohammed
  bodies in small towns, which rarely appear in mainstream directories.

`masjidsinusa.com` claims 96 NC centers across 47 cities. Treat this roster as
substantial but not exhaustive.

## False positives excluded (they recur in every search)

- `greenvillemasjid.com` / "Islamic Society of Greenville" — Greenville,
  **South Carolina**.
- "JIAR Fayetteville St. Masjid" — on Fayetteville *Street* in **Durham**, not
  in Fayetteville.
- Henderson (Vance County, eastern NC) vs. Hendersonville (Henderson County,
  western NC) — two different places.
- `shelbymasjid.org` — Shelby Township, **Michigan**.
- `icburlington.org` — not Burlington, NC.
- `masjidbilalky.org` — Lexington, **Kentucky**.
- "Islamic Center of Union County" (`icucnj.com`) — **New Jersey**.
- Iqra Islamic Society of Greater Concord — IRS record says Concord,
  **New Hampshire**. Flagged in the roster, not excluded, pending confirmation.
