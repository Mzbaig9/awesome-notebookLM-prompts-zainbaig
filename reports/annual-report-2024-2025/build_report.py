#!/usr/bin/env python3
"""Build the Dar Al-Ulum Montreal Annual Report 2024 and 2025 as a Letter PDF."""
import html
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# ---------------------------------------------------------------- data (from the statements)
REV24 = {"Cash & cheque donations": 52866.44, "Online donations": 159440.01,
         "Prep educational services": 5585.29, "Hifz part time": 8093.56,
         "Hifz and Aalimiyah full time and home services": 232888.45,
         "Aalimiyah part time": 18246.70, "Books": 3683.80}
DON24 = 52866.44 + 159440.01
EDU24 = 5585.29 + 8093.56 + 232888.45 + 18246.70 + 3683.80
TOT_REV24 = 480804.25

EXP24 = {"Salaries and wages": 331577.51, "Professional fees": 19914.57, "Credit card fees": 3228.47,
         "Insurance": 620.00, "Transaction and bank fees": 546.69, "Office supplies": 20488.43,
         "General supplies": 12378.37, "Rent": 85273.56, "Electricity": 1953.49,
         "Maintenance and repairs": 423.48, "Telephone and internet": 2529.88,
         "Meals, representation and travel": 3469.73, "Gas": 675.51, "Social activities": 1237.33}
PAY24 = 331577.51
OPS24 = 152739.51
TOT_EXP24 = 484317.02
NET24 = -3512.77

REV25 = {"Donations": 485435.50, "Evaluation revenue": 7500.00,
         "Educational and religious services": 344400.85}
DON25 = 485435.50
EDU25 = 7500.00 + 344400.85
TOT_REV25 = 837336.35

EXP25 = {"Payroll and fees": 532605.91, "Service contracts": 40269.45,
         "Professional and consulting fees": 34810.40, "Publicity and promotion": 617.07,
         "Permits and licences": 1000.00, "Insurance": 675.59, "Transaction and bank fees": 4306.55,
         "Office and educational supplies": 5814.03, "General supplies": 59541.34,
         "Subcontracting fees": 3936.00, "Computer and informatics": 174.70,
         "Evaluation fees": 10000.00, "Rent": 151317.62, "Electricity and heating": 6851.21,
         "Maintenance and repairs": 8520.96, "Telephone and internet": 5122.24,
         "Meals, representation and travel": 10626.50, "Gas": 1849.36,
         "Social activities": 2494.38, "Donations given": 965.42}
PAY25 = 532605.91
OPS25 = 348892.82
TOT_EXP25 = 881498.73
NET25 = -44162.38

BS24 = {"cash_chk": 5464.41, "cash_sav": 23.70, "cash": 5488.11, "ap": 5753.49, "loans": 0.0,
        "liab": 5753.49, "retained": 3247.39, "net": NET24, "equity": -265.38}
BS25 = {"cash_chk": 532.90, "cash_sav": 39.34, "cash": 572.24, "ap": 0.0, "loans": 45000.00,
        "liab": 45000.00, "retained": -265.38, "net": NET25, "equity": -44427.76}

PAYROLL_M24 = [("Jan", 26361.96), ("Feb", 23632.14), ("Mar", 24671.07), ("Apr", 27945.60),
               ("May", 26500.20), ("Jun", 22863.99), ("Jul", 15868.19), ("Aug", 16248.55),
               ("Sep", 47253.53), ("Oct", 37130.07), ("Nov", 29124.36), ("Dec", 33977.85)]

# sanity
assert abs(sum(REV24.values()) - TOT_REV24) < 0.01
assert abs(sum(EXP24.values()) - TOT_EXP24) < 0.01
assert abs(sum(REV25.values()) - TOT_REV25) < 0.01
assert abs(sum(EXP25.values()) - TOT_EXP25) < 0.01
assert abs(sum(v for _, v in PAYROLL_M24) - PAY24) < 0.01
assert abs(TOT_REV24 - TOT_EXP24 - NET24) < 0.01 and abs(TOT_REV25 - TOT_EXP25 - NET25) < 0.01

# ---------------------------------------------------------------- palette (validated)
TEAL = "#0A8FA6"   # 2025
GOLD = "#C48A0A"   # 2024
INK = "#14333B"
INK2 = "#4A5F66"
MUTED = "#8A9AA0"
GRID = "#E3E8EA"
SURF = "#FCFCFB"


def money(v, cents=False):
    if cents:
        s = f"{abs(v):,.2f}"
    else:
        s = f"{abs(round(v)):,}"
    return f"({s})" if v < 0 else s


def dollars(v):
    return "$" + money(v)


def pct(a, b):
    return f"{(a / b - 1) * 100:.0f}%"


def esc(s):
    return html.escape(s)


# ---------------------------------------------------------------- SVG charts
def _k(v):
    return f"${v/1e6:.1f}M" if v >= 1e6 else f"${v/1000:,.0f}k"


def grouped_bars(cats, s24, s25, width=640, height=260, fmt=_k):
    """Vertical grouped bars, 2024 gold and 2025 teal, direct labels, legend."""
    left, right, top, bottom = 56, 12, 34, 40
    pw, ph = width - left - right, height - top - bottom
    vmax = max(max(s24), max(s25))
    step = 200000 if vmax > 500000 else 100000
    ymax = (int(vmax // step) + 1) * step
    n = len(cats)
    slot = pw / n
    bw = min(46, slot * 0.28)
    gap = 2
    out = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="Liberation Sans, DejaVu Sans, sans-serif">']
    # legend
    out.append(f'<g font-size="11" fill="{INK2}">'
               f'<rect x="{left}" y="8" width="10" height="10" rx="2" fill="{GOLD}"/><text x="{left+14}" y="17">2024</text>'
               f'<rect x="{left+56}" y="8" width="10" height="10" rx="2" fill="{TEAL}"/><text x="{left+70}" y="17">2025</text></g>')
    # grid
    for g in range(0, ymax + 1, step):
        y = top + ph - g / ymax * ph
        out.append(f'<line x1="{left}" x2="{left+pw}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{fmt(g) if g else "0"}</text>')
    for i, c in enumerate(cats):
        cx = left + slot * i + slot / 2
        for j, (v, col) in enumerate(((s24[i], GOLD), (s25[i], TEAL))):
            x = cx - bw - gap / 2 if j == 0 else cx + gap / 2
            h = v / ymax * ph
            y = top + ph - h
            r = 4 if h > 6 else 0
            out.append(f'<path d="M{x:.1f},{top+ph} v{-(h-r):.1f} a{r},{r} 0 0 1 {r},{-r} h{bw-2*r} a{r},{r} 0 0 1 {r},{r} v{h-r:.1f} z" fill="{col}"/>')
            out.append(f'<text x="{x+bw/2:.1f}" y="{y-5:.1f}" text-anchor="middle" font-size="10.5" fill="{INK}">{fmt(v)}</text>')
        out.append(f'<text x="{cx:.1f}" y="{top+ph+18}" text-anchor="middle" font-size="11" fill="{INK2}">{esc(c)}</text>')
    out.append(f'<line x1="{left}" x2="{left+pw}" y1="{top+ph}" y2="{top+ph}" stroke="{MUTED}" stroke-width="1"/>')
    out.append("</svg>")
    return "".join(out)


def hbars_pair(rows, width=640, row_h=34, fmt=lambda v: f"${v/1000:,.0f}k"):
    """Horizontal grouped bars per category: 2024 gold above 2025 teal."""
    left, right, top = 200, 70, 30
    n = len(rows)
    height = top + n * row_h + 8
    pw = width - left - right
    vmax = max(max(a, b) for _, a, b in rows)
    bh = 11
    out = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="Liberation Sans, DejaVu Sans, sans-serif">']
    out.append(f'<g font-size="11" fill="{INK2}">'
               f'<rect x="{left}" y="6" width="10" height="10" rx="2" fill="{GOLD}"/><text x="{left+14}" y="15">2024</text>'
               f'<rect x="{left+56}" y="6" width="10" height="10" rx="2" fill="{TEAL}"/><text x="{left+70}" y="15">2025</text></g>')
    for i, (label, a, b) in enumerate(rows):
        y0 = top + i * row_h
        out.append(f'<text x="{left-10}" y="{y0+bh+4}" text-anchor="end" font-size="11" fill="{INK}">{esc(label)}</text>')
        for j, (v, col) in enumerate(((a, GOLD), (b, TEAL))):
            y = y0 + j * (bh + 2)
            w = max(v / vmax * pw, 0)
            r = 4 if w > 6 else 0
            out.append(f'<path d="M{left},{y} h{max(w-r,0):.1f} a{r},{r} 0 0 1 {r},{r} v{bh-2*r} a{r},{r} 0 0 1 {-r},{r} h{-max(w-r,0):.1f} z" fill="{col}"/>')
            out.append(f'<text x="{left+w+6:.1f}" y="{y+bh-2}" font-size="10" fill="{INK2}">{fmt(v)}</text>')
    out.append("</svg>")
    return "".join(out)


def monthly_bars(data, width=640, height=220):
    left, right, top, bottom = 50, 12, 20, 34
    pw, ph = width - left - right, height - top - bottom
    ymax = 50000
    n = len(data)
    slot = pw / n
    bw = slot * 0.62
    out = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="Liberation Sans, DejaVu Sans, sans-serif">']
    for g in range(0, ymax + 1, 10000):
        y = top + ph - g / ymax * ph
        out.append(f'<line x1="{left}" x2="{left+pw}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{"$"+str(g//1000)+"k" if g else "0"}</text>')
    peak = max(v for _, v in data)
    for i, (m, v) in enumerate(data):
        x = left + slot * i + (slot - bw) / 2
        h = v / ymax * ph
        y = top + ph - h
        r = 4
        out.append(f'<path d="M{x:.1f},{top+ph} v{-(h-r):.1f} a{r},{r} 0 0 1 {r},{-r} h{bw-2*r:.1f} a{r},{r} 0 0 1 {r},{r} v{h-r:.1f} z" fill="{GOLD}"/>')
        if v == peak or i in (0, 6, 11):
            out.append(f'<text x="{x+bw/2:.1f}" y="{y-5:.1f}" text-anchor="middle" font-size="10" fill="{INK}">${v/1000:,.1f}k</text>')
        out.append(f'<text x="{x+bw/2:.1f}" y="{top+ph+16}" text-anchor="middle" font-size="10.5" fill="{INK2}">{m}</text>')
    out.append(f'<line x1="{left}" x2="{left+pw}" y1="{top+ph}" y2="{top+ph}" stroke="{MUTED}"/>')
    out.append("</svg>")
    return "".join(out)


def mix_bar(label, parts, width=640):
    """100% stacked horizontal bar: parts = [(name, value, color)]."""
    left, h = 60, 22
    total = sum(v for _, v, _ in parts)
    pw = width - left - 8
    out = [f'<svg viewBox="0 0 {width} 58" width="{width}" height="58" font-family="Liberation Sans, DejaVu Sans, sans-serif">']
    out.append(f'<text x="0" y="{h/2+5+6}" font-size="12" font-weight="bold" fill="{INK}">{esc(label)}</text>')
    x = left
    for i, (name, v, col) in enumerate(parts):
        w = v / total * pw - (2 if i < len(parts) - 1 else 0)
        out.append(f'<rect x="{x:.1f}" y="6" width="{w:.1f}" height="{h}" rx="3" fill="{col}"/>')
        out.append(f'<text x="{x+w/2:.1f}" y="{6+h+16}" text-anchor="middle" font-size="10.5" fill="{INK2}">{esc(name)} {v/total*100:.0f}%</text>')
        x += w + 2
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- tables
def stmt_rows(d, cents=True):
    return "".join(f'<tr><td>{esc(k)}</td><td class="num">{money(v, cents)}</td></tr>' for k, v in d.items())


def compare_table(rows, cents=False):
    """rows: (label, v24, v25, bold?)"""
    out = ['<table class="cmp"><thead><tr><th></th><th class="num">2024</th><th class="num">2025</th><th class="num">Change</th></tr></thead><tbody>']
    for label, a, b, bold in rows:
        cls = ' class="tot"' if bold else ""
        ch = "" if a == 0 else pct(b, a) if (a > 0 and b > 0) else ""
        out.append(f'<tr{cls}><td>{esc(label)}</td><td class="num">{money(a, cents)}</td><td class="num">{money(b, cents)}</td><td class="num">{ch}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


# ---------------------------------------------------------------- derived figures
rev_growth = pct(TOT_REV25, TOT_REV24)
don_growth = pct(DON25, DON24)
edu_growth = pct(EDU25, EDU24)
exp_growth = pct(TOT_EXP25, TOT_EXP24)
pay_growth = pct(PAY25, PAY24)
rent_growth = pct(EXP25["Rent"], EXP24["Rent"])
fee_cov24 = EDU24 / TOT_EXP24 * 100
fee_cov25 = EDU25 / TOT_EXP25 * 100
pay_share25 = PAY25 / TOT_EXP25 * 100
rent_share25 = EXP25["Rent"] / TOT_EXP25 * 100
supplies25 = EXP25["General supplies"] + EXP25["Office and educational supplies"]
supplies24 = EXP24["General supplies"] + EXP24["Office supplies"]
prof25 = EXP25["Professional and consulting fees"] + EXP25["Service contracts"] + EXP25["Subcontracting fees"]
prof24 = EXP24["Professional fees"]
util25 = EXP25["Electricity and heating"] + EXP25["Gas"] + EXP25["Telephone and internet"] + EXP25["Maintenance and repairs"]
util24 = EXP24["Electricity"] + EXP24["Gas"] + EXP24["Telephone and internet"] + EXP24["Maintenance and repairs"]
other25 = TOT_EXP25 - PAY25 - EXP25["Rent"] - supplies25 - prof25 - util25
other24 = TOT_EXP24 - PAY24 - EXP24["Rent"] - supplies24 - prof24 - util24
gap25 = TOT_EXP25 - EDU25
gap24 = TOT_EXP24 - EDU24

# ---------------------------------------------------------------- pages
pages = []
TOTAL_PAGES = 12


def page(body, n, cls=""):
    footer = "" if n == 1 else f'<div class="foot"><span>Dar Al-Ulum Montreal</span><span>Annual Report 2024 and 2025</span><span>{n}</span></div>'
    pages.append(f'<section class="page {cls}">{body}{footer}</section>')


# 1 cover
page(f'''
<div class="cover">
  <div class="cover-band"></div>
  <div class="cover-inner">
    <div class="eyebrow">Dar Al-Ulum Montreal</div>
    <h1>Annual Report</h1>
    <div class="years"><span>2024</span><span class="amp">and</span><span>2025</span></div>
    <p class="cover-sub">Two years of growth in Islamic education for the Muslim children of Montreal, reported with gratitude to the donors, families and teachers who made it possible.</p>
  </div>
  <div class="cover-foot">
    <div>Henri-Bourassa and Saint-Laurent, Montreal, Quebec</div>
    <div>Fiscal years ended December 31, 2024 and December 31, 2025</div>
  </div>
</div>''', 1, "cover-page")

# 2 contents + at a glance
page(f'''
<h2 class="section">Contents</h2>
<table class="toc">
<tr><td>Message from the Founder</td><td>3</td></tr>
<tr><td>Who we are</td><td>4</td></tr>
<tr><td>Two years at a glance</td><td>5</td></tr>
<tr><td>Where the support came from</td><td>6</td></tr>
<tr><td>Where the money went</td><td>7</td></tr>
<tr><td>The year 2024</td><td>8</td></tr>
<tr><td>The year 2025</td><td>9</td></tr>
<tr><td>Financial position and the road ahead</td><td>10</td></tr>
<tr><td>Statement of operations, 2024 and 2025</td><td>11</td></tr>
<tr><td>Statement of financial position and notes</td><td>12</td></tr>
</table>
<div class="glance">
  <div class="tile"><div class="tile-n">{dollars(TOT_REV25)}</div><div class="tile-l">Total revenue in 2025</div><div class="tile-s">up {rev_growth} from {dollars(TOT_REV24)} in 2024</div></div>
  <div class="tile"><div class="tile-n">{dollars(DON25)}</div><div class="tile-l">Donations received in 2025</div><div class="tile-s">up {don_growth} from {dollars(DON24)} in 2024</div></div>
  <div class="tile"><div class="tile-n">{dollars(PAY25)}</div><div class="tile-l">Invested in teachers and staff in 2025</div><div class="tile-s">up {pay_growth} from {dollars(PAY24)} in 2024</div></div>
  <div class="tile"><div class="tile-n">{fee_cov25:.0f}%</div><div class="tile-l">Share of 2025 costs covered by tuition and service fees</div><div class="tile-s">the rest is carried by donors</div></div>
</div>
<p class="fine">All amounts in this report are in Canadian dollars and are drawn from the organization's year-end accounting records for the calendar years 2024 and 2025. The figures are unaudited.</p>
''', 2)

# 3 founder message
page(f'''
<h2 class="section">Message from the Founder</h2>
<div class="letter">
<p>As Salam Alaykum wa Rahmatullahi wa Barakatuh.</p>
<p>Alhamdulilah, the two years covered in this report are the years in which Dar Al-Ulum Montreal stopped being a small project and became an institution. In June 2021 we opened with five students under the direct mashwarah of my teacher, Hazrat Mufti Ebrahim Desai, may Allah elevate his rank. By the end of 2025 the same idea was serving well over a hundred families across two sites, with a full Hifdh program, a full time and part time Aalimiyah program, an academic preparatory stream, and a homeschool support service recognized for ministry evaluations. None of that belongs to me. It belongs to the teachers who carry the classrooms every day, to the parents who trusted us with their children, and to the donors who decided that this city needed a place like this and paid for it to exist.</p>
<p>I owe you honesty as much as gratitude, because your money is an Amanah. In 2024 we closed the year almost exactly at break even, with a deficit of {dollars(-NET24)} on revenue of {dollars(TOT_REV24)}. In 2025 revenue grew by {rev_growth} to {dollars(TOT_REV25)}, and donations more than doubled, yet expenses grew faster. We hired more teachers, we took on more space, and we absorbed the real cost of educating a much larger student body. The year ended with a deficit of {dollars(-NET25)} and a loan of {dollars(BS25["loans"])} that bridged the gap. Tuition now covers roughly forty cents of every dollar it costs to teach a child here. The remaining sixty cents comes from you.</p>
<p>We have never turned a student away for financial hardship and, InshaAllah, we never will. That policy is only possible because of the people reading this report. In a province where the space for Muslim children to learn their deen keeps narrowing, every classroom we keep open is a form of resistance and, I pray, a Sadaqah Jariyah for everyone who had a share in it.</p>
<p>The pages that follow set out exactly what came in, exactly what went out, and where we stand. Read them, question them, and then help us carry this into 2026.</p>
<p>Jazakallah Khayra.</p>
<div class="sig">
<div class="sig-name">(Mufti) Mirza-Zain Baig, CSAA</div>
<div class="sig-role">Founder and Principal, Dar Al-Ulum Montreal</div>
</div>
</div>
''', 3)

# 4 who we are
page(f'''
<h2 class="section">Who we are</h2>
<p class="lead">Dar Al-Ulum Montreal is an Islamic educational institution founded in June 2021 to give Muslim children in Quebec a rigorous religious and academic education without leaving their city or their families.</p>
<div class="two-col">
<div>
<h3>Our story</h3>
<p>The school began with five students and a conviction that a student of knowledge should not have to choose between a seminary abroad and no seminary at all. It was established under the guidance of the late Hazrat Mufti Ebrahim Desai and has grown in four years to serve more than 145 students across two Montreal sites, at Henri-Bourassa and Saint-Laurent, supported by a team of roughly thirty teachers and staff.</p>
<h3>How we are organized</h3>
<p>Dar Al-Ulum Montreal operates as a registered charity in Canada and is recognized as a 501(c)(3) organization in the United States, so gifts from donors on both sides of the border are receipted. The institution is governed by a board and its accounts are kept on a calendar year basis.</p>
<h3>Our commitment</h3>
<p>No child has ever been refused a place at Dar Al-Ulum for financial reasons. Tuition is set well below the true cost of a seat, and the difference is met by the community. That gap is the single most important number in this report and it appears on page 10.</p>
</div>
<div>
<h3>What we offer</h3>
<div class="prog"><div class="prog-t">Hifdh al-Quran</div><div>Full time and part time memorization of the Quran with daily revision and tajweed.</div></div>
<div class="prog"><div class="prog-t">Aalimiyah</div><div>A full time and part time program of classical Islamic sciences, including Arabic, fiqh, hadith and tafsir, taught in the Hanafi tradition.</div></div>
<div class="prog"><div class="prog-t">Preparatory and academic stream</div><div>Academic instruction that runs alongside religious studies so that graduates leave ready for university and for leadership.</div></div>
<div class="prog"><div class="prog-t">Homeschool support and evaluations</div><div>Curriculum support and ministry evaluation reports for families who homeschool, recognized for the purposes of Quebec reporting.</div></div>
<div class="prog"><div class="prog-t">Community and social activities</div><div>Summer programs, student outings and community events that keep the students connected to one another and to the wider Muslim community.</div></div>
</div>
</div>
''', 4)

# 5 at a glance
cmp_rows = [
    ("Donations and fundraising", DON24, DON25, False),
    ("Tuition and educational services", EDU24, EDU25, False),
    ("Total revenue", TOT_REV24, TOT_REV25, True),
    ("Teachers, staff and payroll", PAY24, PAY25, False),
    ("General operating expenses", OPS24, OPS25, False),
    ("Total expenses", TOT_EXP24, TOT_EXP25, True),
    ("Net result for the year", NET24, NET25, True),
]
page(f'''
<h2 class="section">Two years at a glance</h2>
<p class="lead">Revenue grew by {rev_growth} between 2024 and 2025. Expenses grew by {exp_growth} over the same period, because the school hired, expanded and served far more students than the year before.</p>
<figure>
{grouped_bars(["Donations", "Tuition and services", "Total revenue", "Total expenses"], [DON24, EDU24, TOT_REV24, TOT_EXP24], [DON25, EDU25, TOT_REV25, TOT_EXP25])}
<figcaption>Revenue and expenses, 2024 and 2025, in Canadian dollars.</figcaption>
</figure>
{compare_table(cmp_rows)}
<p class="note">The 2024 accounts record payroll under salaries and wages and the 2025 accounts record it under payroll and fees. Both are shown here as teachers, staff and payroll. Change is shown where both years have a positive balance.</p>
''', 5)

# 6 where the support came from
page(f'''
<h2 class="section">Where the support came from</h2>
<p class="lead">Two streams fund the school: tuition and service fees paid by families, and donations given by the community. In 2024 the two were nearly equal. In 2025 donations became the larger stream for the first time.</p>
<figure>
{mix_bar("2024", [("Donations", DON24, GOLD), ("Tuition and services", EDU24, "#E2C57A")])}
{mix_bar("2025", [("Donations", DON25, TEAL), ("Tuition and services", EDU25, "#8CCAD5")])}
<figcaption>Share of total revenue by source.</figcaption>
</figure>
<div class="two-col">
<div>
<h3>Donations</h3>
<p>Donations rose from {dollars(DON24)} in 2024 to {dollars(DON25)} in 2025, an increase of {don_growth}. In 2024 the accounts separated cash and cheque gifts of {dollars(REV24["Cash & cheque donations"])} from online gifts of {dollars(REV24["Online donations"])}, so three quarters of giving already arrived through the online channel. In 2025 all giving was recorded under a single donations account.</p>
<p>This growth is the reason the school could expand in 2025 without collapsing under the cost. It is also the clearest measure of how much the community has come to rely on Dar Al-Ulum and how much it trusts it.</p>
</div>
<div>
<h3>Tuition and educational services</h3>
<p>Fee revenue rose from {dollars(EDU24)} to {dollars(EDU25)}, an increase of {edu_growth}. In 2024 the largest single line was the full time Hifdh and Aalimiyah program together with home services at {dollars(REV24["Hifz and Aalimiyah full time and home services"])}, followed by part time Aalimiyah at {dollars(REV24["Aalimiyah part time"])}, part time Hifdh at {dollars(REV24["Hifz part time"])}, preparatory services at {dollars(REV24["Prep educational services"])} and book sales at {dollars(REV24["Books"])}.</p>
<p>In 2025 educational and religious services brought in {dollars(REV25["Educational and religious services"])} and homeschool evaluation services added {dollars(REV25["Evaluation revenue"])}, a new line reflecting the growth of the evaluation program.</p>
</div>
</div>
''', 6)

# 7 where the money went
exp_rows = [("Teachers, staff and payroll", PAY24, PAY25), ("Rent", EXP24["Rent"], EXP25["Rent"]),
            ("Supplies, office and educational", supplies24, supplies25),
            ("Professional, service and contract fees", prof24, prof25),
            ("Utilities, telecom and maintenance", util24, util25),
            ("All other operating costs", other24, other25)]
page(f'''
<h2 class="section">Where the money went</h2>
<p class="lead">Every dollar the school spends goes to one of a small number of things: the people who teach, the rooms they teach in, the materials the students use, and the services that keep a growing institution compliant and running.</p>
<figure>
{hbars_pair(exp_rows)}
<figcaption>Expenses by category, 2024 and 2025. Categories group the line items in the statement of operations on page 11.</figcaption>
</figure>
<div class="two-col">
<div>
<h3>People first</h3>
<p>Payroll is the largest cost in both years and it is where the growth went. Salaries and wages of {dollars(PAY24)} in 2024 became payroll and fees of {dollars(PAY25)} in 2025, an increase of {pay_growth}. Payroll was {pay_share25:.0f} cents of every dollar spent in 2025. A school is its teachers, and the community's donations paid for more of them.</p>
<h3>Space</h3>
<p>Rent rose from {dollars(EXP24["Rent"])} to {dollars(EXP25["Rent"])}, an increase of {rent_growth}, as the school grew into more space across its two sites. Rent was {rent_share25:.0f} cents of every dollar spent in 2025.</p>
</div>
<div>
<h3>Supplies and services</h3>
<p>General and office supplies together rose from {dollars(supplies24)} to {dollars(supplies25)} as classrooms were equipped for more students. Professional, consulting, service contract and subcontracting fees rose from {dollars(prof24)} to {dollars(prof25)}, and 2025 also carried {dollars(EXP25["Evaluation fees"])} in evaluation fees tied to the homeschool evaluation program, {dollars(EXP25["Permits and licences"])} in permits and licences and {dollars(EXP25["Publicity and promotion"])} in publicity.</p>
<h3>Everything else</h3>
<p>Utilities, telephone and internet, maintenance, insurance, bank and card fees, student meals, outings and social activities made up the balance, {dollars(util25 + other25)} in 2025 against {dollars(util24 + other24)} in 2024.</p>
</div>
</div>
''', 7)

# 8 year 2024
page(f'''
<h2 class="section">The year 2024</h2>
<p class="lead">2024 was a year of consolidation. The school ran on {dollars(TOT_REV24)} of revenue against {dollars(TOT_EXP24)} of expenses and closed within {dollars(-NET24)} of break even.</p>
<div class="two-col">
<div>
<h3>Revenue</h3>
<p>Families paid {dollars(EDU24)} in tuition and service fees, which covered {fee_cov24:.0f}% of the year's costs. Donors gave {dollars(DON24)}, with {dollars(REV24["Online donations"])} arriving online and {dollars(REV24["Cash & cheque donations"])} by cash and cheque.</p>
<h3>Expenses</h3>
<p>Payroll of {dollars(PAY24)} and rent of {dollars(EXP24["Rent"])} together accounted for {(PAY24 + EXP24["Rent"]) / TOT_EXP24 * 100:.0f}% of spending. Office supplies of {dollars(EXP24["Office supplies"])}, general supplies of {dollars(EXP24["General supplies"])} and professional fees of {dollars(EXP24["Professional fees"])} were the next largest items.</p>
<h3>Year end</h3>
<p>The school ended 2024 with {dollars(BS24["cash"])} in the bank and {dollars(BS24["ap"])} owing to suppliers. Accumulated funds moved from {dollars(BS24["retained"])} at the start of the year to a small negative balance of {dollars(-BS24["equity"])} at the close.</p>
</div>
<div>
<h3>Payroll through the year</h3>
<p>Monthly payroll shows the rhythm of a school year. It ran near {dollars(25000)} a month through the winter and spring, eased over the summer, and then stepped up sharply in September when the new academic year opened with more teachers and more students. The fall months set the base from which 2025 grew.</p>
<h3>Looking back</h3>
<p>Break even on a budget of nearly half a million dollars, with no reserve and no borrowing, was an achievement for a school in its third full year. It was also a warning. The September step up in payroll shows that the institution was already committing to a larger 2025 before the funding for it existed.</p>
</div>
</div>
<figure>
{monthly_bars(PAYROLL_M24, width=640, height=210)}
<figcaption>Payroll paid by month in 2024, in Canadian dollars. Total {dollars(PAY24)}.</figcaption>
</figure>
''', 8)

# 9 year 2025
page(f'''
<h2 class="section">The year 2025</h2>
<p class="lead">2025 was a year of expansion. Revenue reached {dollars(TOT_REV25)}, expenses reached {dollars(TOT_EXP25)}, and the year closed with a deficit of {dollars(-NET25)} that was bridged by a loan.</p>
<div class="two-col">
<div>
<h3>Revenue</h3>
<p>Donations of {dollars(DON25)} became the school's largest source of funds, at {DON25 / TOT_REV25 * 100:.0f}% of revenue. Tuition and educational services contributed {dollars(REV25["Educational and religious services"])}, and the homeschool evaluation program added {dollars(REV25["Evaluation revenue"])} in its own right.</p>
<h3>Expenses</h3>
<p>The school invested {dollars(PAY25)} in teachers and staff, {dollars(EXP25["Rent"])} in space, and {dollars(EXP25["General supplies"])} in general supplies as classrooms were fitted out for a much larger student body. Service contracts of {dollars(EXP25["Service contracts"])} and professional and consulting fees of {dollars(EXP25["Professional and consulting fees"])} reflect the administrative, legal and accounting work that a larger institution requires. Maintenance rose to {dollars(EXP25["Maintenance and repairs"])} and heating and electricity to {dollars(EXP25["Electricity and heating"])} with the additional space.</p>
</div>
<div>
<h3>What the deficit means</h3>
<p>Fee revenue covered {fee_cov25:.0f}% of the cost of running the school in 2025, down from {fee_cov24:.0f}% in 2024. That is not a sign of weakness in the fee base, which grew by {edu_growth}. It is the arithmetic of a policy: the school grew faster than it raised tuition, and it kept its door open to every family regardless of means.</p>
<p>The gap between what families paid and what the education cost was {dollars(gap25)}. Donors closed {dollars(DON25)} of it. The remaining {dollars(-NET25)} was carried forward as a deficit and financed by a {dollars(BS25["loans"])} loan.</p>
<h3>Year end</h3>
<p>The school closed 2025 with {dollars(BS25["cash"])} in the bank, no supplier balances outstanding, and a loan of {dollars(BS25["loans"])}. Accumulated funds stood at a negative {dollars(-BS25["equity"])}.</p>
</div>
</div>
<figure>
{mix_bar("Cost", [("Paid by families", EDU25, "#8CCAD5"), ("Paid by donors", DON25, TEAL), ("Deficit", -NET25, GOLD)])}
<figcaption>How the {dollars(TOT_EXP25)} cost of running the school in 2025 was met.</figcaption>
</figure>
''', 9)

# 10 financial position and road ahead
page(f'''
<h2 class="section">Financial position and the road ahead</h2>
<div class="two-col">
<div>
<h3>Where we stand</h3>
<table class="cmp small">
<thead><tr><th>At December 31</th><th class="num">2024</th><th class="num">2025</th></tr></thead>
<tbody>
<tr><td>Cash in bank</td><td class="num">{money(BS24["cash"])}</td><td class="num">{money(BS25["cash"])}</td></tr>
<tr><td>Owed to suppliers</td><td class="num">{money(BS24["ap"])}</td><td class="num">{money(BS25["ap"])}</td></tr>
<tr><td>Loans</td><td class="num">{money(BS24["loans"])}</td><td class="num">{money(BS25["loans"])}</td></tr>
<tr class="tot"><td>Accumulated funds</td><td class="num">{money(BS24["equity"])}</td><td class="num">{money(BS25["equity"])}</td></tr>
</tbody></table>
<p>The school holds no buildings, vehicles or investments on its books. Everything it receives is spent on education in the same year. That is by design, and it is also why the institution has no cushion. Two consecutive deficits have left accumulated funds at a negative {dollars(-BS25["equity"])} and the loan must be repaid.</p>
<h3>The number that matters</h3>
<p>With more than 145 students, the cost of a year of education at Dar Al-Ulum in 2025 was approximately {dollars(TOT_EXP25 / 145)} per student, while fee revenue came to approximately {dollars(EDU25 / 145)} per student. Every student at the school is therefore sponsored by the community to the extent of roughly {dollars((TOT_EXP25 - EDU25) / 145)} a year, whether the family knows it or not.</p>
</div>
<div>
<h3>Priorities for 2026</h3>
<p>The first priority is to repay the {dollars(BS25["loans"])} loan and to rebuild a reserve so that payroll never again depends on the timing of the next campaign. The second is to lift recurring monthly giving, because a school that grew its costs by {exp_growth} in a year cannot be run on year-end appeals alone. The third is to keep the institution's commitment that no child is refused for lack of means, which is only sustainable if the sponsorship gap on the left is funded deliberately rather than by accident.</p>
<h3>How you can help</h3>
<p>A monthly gift is the most valuable thing a supporter can give, because it turns an unpredictable deficit into a planned budget. Sponsoring a student for a year, or a portion of a year, directly closes the gap described on this page. Zakat and Sadaqah are accepted and applied in accordance with the Shariah, and the school issues official receipts in both Canada and the United States.</p>
<p>To give, or to discuss sponsoring a student, a classroom or a program, please contact the administration of Dar Al-Ulum Montreal at either site. Every contribution, of any size, is received as an Amanah and reported back to you in the next edition of this report.</p>
</div>
</div>
''', 10)

# 11 statement of operations
page(f'''
<h2 class="section">Statement of operations</h2>
<p class="fine">For the years ended December 31, 2024 and December 31, 2025. Unaudited. Canadian dollars. Line items follow the organization's chart of accounts for each year.</p>
<div class="two-col stmt">
<div>
<h3>Year ended December 31, 2024</h3>
<table class="stmt">
<tr class="grp"><td>Revenue</td><td></td></tr>
{stmt_rows(REV24)}
<tr class="tot"><td>Total revenue</td><td class="num">{money(TOT_REV24, True)}</td></tr>
<tr class="grp"><td>Expenses</td><td></td></tr>
{stmt_rows(EXP24)}
<tr class="tot"><td>Total expenses</td><td class="num">{money(TOT_EXP24, True)}</td></tr>
<tr class="net"><td>Deficiency of revenue over expenses</td><td class="num">{money(NET24, True)}</td></tr>
</table>
</div>
<div>
<h3>Year ended December 31, 2025</h3>
<table class="stmt">
<tr class="grp"><td>Revenue</td><td></td></tr>
{stmt_rows(REV25)}
<tr class="tot"><td>Total revenue</td><td class="num">{money(TOT_REV25, True)}</td></tr>
<tr class="grp"><td>Expenses</td><td></td></tr>
{stmt_rows(EXP25)}
<tr class="tot"><td>Total expenses</td><td class="num">{money(TOT_EXP25, True)}</td></tr>
<tr class="net"><td>Deficiency of revenue over expenses</td><td class="num">{money(NET25, True)}</td></tr>
</table>
</div>
</div>
''', 11)

# 12 financial position + notes
page(f'''
<h2 class="section">Statement of financial position</h2>
<p class="fine">As at December 31, 2024 and December 31, 2025. Unaudited. Canadian dollars.</p>
<table class="stmt wide">
<thead><tr><th></th><th class="num">2024</th><th class="num">2025</th></tr></thead>
<tr class="grp"><td>Assets</td><td></td><td></td></tr>
<tr><td>Cash, chequing account</td><td class="num">{money(BS24["cash_chk"], True)}</td><td class="num">{money(BS25["cash_chk"], True)}</td></tr>
<tr><td>Cash, savings account</td><td class="num">{money(BS24["cash_sav"], True)}</td><td class="num">{money(BS25["cash_sav"], True)}</td></tr>
<tr class="tot"><td>Total assets</td><td class="num">{money(BS24["cash"], True)}</td><td class="num">{money(BS25["cash"], True)}</td></tr>
<tr class="grp"><td>Liabilities</td><td></td><td></td></tr>
<tr><td>Accounts payable</td><td class="num">{money(BS24["ap"], True)}</td><td class="num">{money(BS25["ap"], True)}</td></tr>
<tr><td>Loans</td><td class="num">{money(BS24["loans"], True)}</td><td class="num">{money(BS25["loans"], True)}</td></tr>
<tr class="tot"><td>Total liabilities</td><td class="num">{money(BS24["liab"], True)}</td><td class="num">{money(BS25["liab"], True)}</td></tr>
<tr class="grp"><td>Accumulated funds</td><td></td><td></td></tr>
<tr><td>Balance, beginning of year</td><td class="num">{money(BS24["retained"], True)}</td><td class="num">{money(BS25["retained"], True)}</td></tr>
<tr><td>Deficiency of revenue over expenses for the year</td><td class="num">{money(BS24["net"], True)}</td><td class="num">{money(BS25["net"], True)}</td></tr>
<tr class="tot"><td>Balance, end of year</td><td class="num">{money(BS24["equity"], True)}</td><td class="num">{money(BS25["equity"], True)}</td></tr>
<tr class="net"><td>Total liabilities and accumulated funds</td><td class="num">{money(BS24["liab"] + BS24["equity"], True)}</td><td class="num">{money(BS25["liab"] + BS25["equity"], True)}</td></tr>
</table>
<h3>Notes to the financial information</h3>
<div class="notes">
<p><b>Basis of preparation.</b> The figures in this report are taken from the organization's year-end income statements, balance sheets and trial balances for the calendar years 2024 and 2025 as maintained in its accounting system. They have not been audited or reviewed by an independent accountant. Amounts in the narrative sections are rounded to the nearest dollar and percentages are computed from the unrounded figures.</p>
<p><b>Revenue classification.</b> In 2024 donations were recorded in two accounts, cash and cheque donations and online donations, and educational revenue was recorded across five program accounts. In 2025 the chart of accounts was simplified to a single donations account and two educational accounts, educational and religious services and evaluation revenue. Comparisons in this report group the accounts of each year into donations and tuition and educational services.</p>
<p><b>Payroll.</b> Payroll is recorded as salaries and wages in 2024 and as payroll and fees in 2025. Monthly figures on page 8 are the payroll disbursements recorded in the 2024 general ledger and reconcile to the annual total.</p>
<p><b>Loans.</b> The 2025 balance sheet carries a loan of {dollars(BS25["loans"])} classified as a current liability. No loans were outstanding at December 31, 2024.</p>
<p><b>Capital assets.</b> No capital assets are recorded on the balance sheet in either year. Premises are rented.</p>
</div>
''', 12)

# ---------------------------------------------------------------- html
CSS = f"""
@page {{ size: Letter; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: {SURF}; color: {INK}; font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif; font-size: 10.6pt; line-height: 1.45; }}
.page {{ width: 8.5in; height: 11in; padding: 0.7in 0.75in 0.8in; position: relative; overflow: hidden; page-break-after: always; break-after: page; }}
.page:last-child {{ page-break-after: auto; break-after: auto; }}
.foot {{ position: absolute; left: 0.75in; right: 0.75in; bottom: 0.42in; display: flex; justify-content: space-between; font-size: 8.5pt; color: {MUTED}; border-top: 1px solid {GRID}; padding-top: 6px; letter-spacing: 0.02em; }}
h1, h2, h3, .tile-n, .years, .cover .eyebrow {{ font-family: "Bitstream Charter", "Liberation Serif", Georgia, serif; }}
h2.section {{ font-size: 22pt; font-weight: normal; margin: 0 0 14px; color: {INK}; padding-bottom: 8px; border-bottom: 2px solid {GOLD}; }}
h3 {{ font-size: 12.5pt; font-weight: bold; margin: 14px 0 4px; color: #0F4F5B; }}
h3:first-child {{ margin-top: 0; }}
p {{ margin: 0 0 8px; }}
p.lead {{ font-size: 11.8pt; color: {INK2}; margin-bottom: 12px; }}
p.fine, p.note {{ font-size: 8.8pt; color: {MUTED}; }}
p.note {{ margin-top: 8px; }}
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 26px; }}
figure {{ margin: 6px 0 12px; }}
figure.tight {{ margin: 4px 0 0; }}
figure svg {{ display: block; width: 100%; height: auto; }}
figcaption {{ font-size: 8.8pt; color: {MUTED}; margin-top: 4px; }}
table {{ border-collapse: collapse; width: 100%; }}
table.cmp td, table.cmp th {{ padding: 5px 6px; border-bottom: 1px solid {GRID}; font-size: 10pt; }}
table.cmp th {{ text-align: left; color: {MUTED}; font-weight: normal; font-size: 9pt; text-transform: uppercase; letter-spacing: 0.06em; }}
table.cmp tr.tot td {{ font-weight: bold; border-top: 1px solid {MUTED}; }}
table.cmp.small td, table.cmp.small th {{ padding: 4px 6px; font-size: 9.6pt; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
table.stmt td, table.stmt th {{ padding: 2.6px 5px; font-size: 8.9pt; border-bottom: 1px solid #EEF1F2; }}
table.stmt th {{ text-align: left; color: {MUTED}; font-weight: normal; font-size: 8.5pt; text-transform: uppercase; letter-spacing: 0.06em; }}
table.stmt tr.grp td {{ font-weight: bold; color: #0F4F5B; padding-top: 8px; border-bottom: 1px solid {MUTED}; text-transform: uppercase; font-size: 8.2pt; letter-spacing: 0.06em; }}
table.stmt tr.tot td {{ font-weight: bold; border-top: 1px solid {MUTED}; }}
table.stmt tr.net td {{ font-weight: bold; border-top: 2px solid {INK}; border-bottom: none; padding-top: 5px; }}
table.stmt.wide td, table.stmt.wide th {{ font-size: 9.6pt; padding: 4px 6px; }}
.stmt h3 {{ font-size: 11pt; }}
.toc td {{ padding: 4px 0; border-bottom: 1px dotted {GRID}; font-size: 10.5pt; }}
.toc td:last-child {{ text-align: right; color: {MUTED}; }}
.glance {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 26px 0 16px; }}
.tile {{ border: 1px solid {GRID}; border-top: 3px solid {TEAL}; border-radius: 6px; padding: 14px 16px 12px; background: #fff; }}
.tile-n {{ font-size: 26pt; line-height: 1.1; color: {INK}; }}
.tile-l {{ font-size: 10pt; color: {INK2}; margin-top: 4px; }}
.tile-s {{ font-size: 8.8pt; color: {MUTED}; margin-top: 2px; }}
.letter {{ font-size: 11pt; line-height: 1.6; }}
.letter p {{ margin-bottom: 11px; }}
.sig {{ margin-top: 22px; }}
.sig-name {{ font-weight: bold; }}
.sig-role {{ color: {INK2}; font-size: 10pt; }}
.prog {{ margin-bottom: 9px; padding-left: 10px; border-left: 3px solid {GOLD}; font-size: 10pt; }}
.prog-t {{ font-weight: bold; color: #0F4F5B; }}
.notes p {{ font-size: 9.3pt; color: {INK2}; }}
/* cover */
.cover-page {{ padding: 0; background: #0F3D47; color: #fff; }}
.cover {{ height: 100%; position: relative; }}
.cover-band {{ position: absolute; left: 0; top: 0; bottom: 0; width: 0.55in; background: {GOLD}; }}
.cover-inner {{ position: absolute; left: 1.3in; right: 0.9in; top: 2.4in; }}
.cover .eyebrow {{ font-size: 14pt; letter-spacing: 0.12em; text-transform: uppercase; color: #E2C57A; margin-bottom: 18px; }}
.cover h1 {{ font-size: 52pt; font-weight: normal; margin: 0; line-height: 1; }}
.years {{ font-size: 40pt; margin-top: 10px; color: #8CCAD5; }}
.years .amp {{ font-size: 18pt; margin: 0 14px; color: #B9D9DF; font-style: italic; }}
.cover-sub {{ margin-top: 30px; font-size: 12.5pt; line-height: 1.55; color: #D6E4E7; max-width: 5.6in; }}
.cover-foot {{ position: absolute; left: 1.3in; bottom: 0.9in; font-size: 9.5pt; color: #B9D9DF; line-height: 1.7; }}
"""

doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Dar Al-Ulum Montreal Annual Report 2024 and 2025</title><style>{CSS}</style></head><body>{''.join(pages)}</body></html>"""
assert "—" not in doc and "–" not in doc, "no dashes"
html_path = OUT / "annual_report.html"
html_path.write_text(doc, encoding="utf-8")

pdf_path = OUT / "Dar_Al-Ulum_Montreal_Annual_Report_2024_2025.pdf"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page()
    pg.goto(html_path.as_uri())
    pg.emulate_media(media="print")
    pg.pdf(path=str(pdf_path), format="Letter", print_background=True, prefer_css_page_size=True,
           margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    b.close()
print("wrote", pdf_path)
