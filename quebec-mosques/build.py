"""Merge every source in raw/ into one deduplicated Quebec mosque list (CSV + XLSX).

Sources, in order of trust (earlier wins a field conflict, later only fills blanks):
  web-search region files, new_*.json gap searches, praysalat.json, osm.json.
Rows are merged when they share a street number and street word, a street number and
postal FSA, or a normalized name. raw/emails.json then fills missing emails.
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = Path(__file__).parent
SOURCES = ["mtl_central_west", "mtl_north_east", "laval_north", "south_shore", "rest_of_qc",
           "new_mtl", "new_suburbs", "new_regions", "mawaqit", "praysalat", "osm"]
FIELDS = ["region", "name", "type", "address", "city", "postal_code", "phone", "email",
          "alt_email", "website", "confidence", "sources", "email_source"]

# The three excluded mosques, matched by address or by a name that only they use.
EXCLUDE_ADDR = [("11900", "gouin"), ("2520", "laval"), ("12080", "laurentien")]
EXCLUDE_NAME = [r"makkah.?al.?mukk?arr?amah", r"\bmadani\b", r"academ\w+ an.?noor",
                r"^(islamic (centre|center) of quebec|centre islamique du quebec)\b"]
# Directory noise that is not a place of prayer.
JUNK = [r"persico", r"spot de chasse", r"grave site", r"makaburini", r"demeure de",
        r"terrasse fleury", r"mariage", r"quran school", r"^chemin portage", r"^ste agate",
        r"^mosque\s*$"]
# Same place listed under two addresses (moved, typo) or two names; checked by hand.
SAME_PLACE = [r"\b45(83|38) rue de verdun", r"vaudreuil soulanges|2400 st antoine|100 boul harwood",
              r"dhoun.?nourain", r"87[59]0 boulevard metropolitain|hidjra|al hijra",
              r"(40|60) rue de port royal|libanais|lebanese islamic",
              r"al.?madinah (center|mosque)|centre al madinah|12(60|48) mackay", r"khadijah",
              r"masjid terrebonne", r"shawinigan", r"msa mcgill|mcgill prayer", r"\bbilal\b",
              r"paix de chambly|mosque de la paix", r"al.?bayan islamic community",
              r"riviere du loup", r"ebrahim musallah|2405 boul lapiniere", r"lacordaire",
              r"al.?hidaya", r"\bisq\b|islamic services of quebec", r"attawassol|roussillon",
              r"valleyfield", r"al.?manara", r"9(09|11) m\w* gravel|masjid ammar", r"okba", r"thetford",
              r"^al aman |centre aman|mosque aman", r"no[ou]r.?(e|al).?madina|nour al medina",
              r"^centre communautaire islamique\s+23e avenue|4201 rue belanger", r"itissam",
              r"al.?jisr", r"jamieh", r"rimouski", r"rawdah", r"sorel"]
STREET_STOP = set("rue st street boulevard blvd bd boul av ave avenue chemin ch chem mnt montee "
                  "e o est ouest w n s nord sud de du des la le l d local suite unit".split())


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)


def keys(r):
    a, out = norm(r["address"]), []
    m = re.match(r"\s*(\d+)", a)
    if m:
        words = [w for w in re.findall(r"[a-z]{3,}", a) if w not in STREET_STOP]
        if words:
            out.append(("st", m.group(1), max(words, key=len)[:6]))
        if r["postal_code"]:
            out.append(("pc", m.group(1), norm(r["postal_code"]).replace(" ", "")[:3]))
    n = re.sub(r"\b(mosquee|mosque|masjid|centre|center|islamique|islamic|culturel|cultural|"
               r"communautaire|community|association|musulmane?|muslim|de|du|la|le|of|the|et|and)\b",
               "", norm(r["name"]))
    n = re.sub(r"\s+", "", n)
    if len(n) >= 5:
        out.append(("nm", n, norm(r["city"]).split(" ")[0] if r["city"] else ""))
    t = norm(f"{r['name']} {r['address']} {r['city']}")
    out += [("same", i) for i, p in enumerate(SAME_PLACE) if re.search(p, t)]
    return out


def bare_name(r):
    n = re.sub(r"\b(mosquee|mosque|masjid|centre|center|islamique|islamic|culturel|cultural|"
               r"communautaire|community|association|musulmane?|muslim|de|du|la|le|of|the|et|and)\b",
               "", norm(r["name"].split("(")[0]))
    return re.sub(r"\s+", "", n)


REGIONS = {
    "Montréal": "anjou dollard dorval lasalle lachine mont royal montreal pierrefonds verdun "
                "saint laurent saint leonard kirkland pointe claire westmount cote saint luc",
    "Laval": "laval",
    "Montérégie": "boucherville brossard chambly chateauguay delson granby longueuil saint constant "
                  "saint hubert saint hyacinthe saint jean sur richelieu salaberry de valleyfield "
                  "sorel tracy vaudreuil dorion la prairie candiac saint lambert beloeil",
    "Laurentides": "sainte marthe sur le lac saint jerome sainte therese blainville boisbriand mirabel saint eustache",
    "Lanaudière": "joliette mascouche repentigny terrebonne sainte julienne",
    "Capitale-Nationale": "quebec",
    "Chaudière-Appalaches": "sainte marie levis saint georges thetford mines",
    "Outaouais": "gatineau",
    "Estrie": "sherbrooke magog lac megantic",
    "Mauricie": "trois rivieres shawinigan",
    "Centre-du-Québec": "drummondville victoriaville",
    "Saguenay–Lac-Saint-Jean": "saguenay",
    "Bas-Saint-Laurent": "rimouski riviere du loup la pocatiere",
    "Abitibi-Témiscamingue": "rouyn noranda val d or ville marie",
    "Côte-Nord": "sept iles",
}


def region_of(r):
    c = re.sub(r"\s+", " ", norm(r["city"].split("(")[0])).strip()
    for region, cities in REGIONS.items():
        if any(c == x or c.startswith(x + " ") for x in _city_list(cities)):
            return region
    return "Autre"


def _city_list(cities):
    known = ["dollard des ormeaux", "mont royal", "saint laurent", "saint leonard", "pointe claire",
             "cote saint luc", "saint constant", "saint hubert", "saint hyacinthe",
             "saint jean sur richelieu", "salaberry de valleyfield", "sorel tracy", "vaudreuil dorion",
             "la prairie", "saint lambert", "saint jerome", "sainte therese", "saint eustache",
             "sainte julienne", "saint georges", "thetford mines", "lac megantic", "trois rivieres",
             "riviere du loup", "la pocatiere", "rouyn noranda", "val d or", "sept iles",
             "montreal nord", "sainte marthe sur le lac", "sainte marie", "ville marie"]
    out, rest = [], cities
    for k in sorted(known, key=len, reverse=True):
        if k in rest:
            out.append(k)
            rest = rest.replace(k, " ")
    return out + rest.split()


def main(raw):
    rows = []
    for rank, src in enumerate(SOURCES):
        p = Path(raw) / f"{src}.json"
        if not p.exists():
            continue
        for d in json.loads(p.read_text()):
            r = {f: str(d.get(f, "") or "").strip() for f in FIELDS}
            r["sources"] = str(d.get("source", "") or "").strip()
            r["postal_code"] = r["postal_code"].upper()
            r["_rank"] = rank
            rows.append(r)

    text = lambda r: f"{r['name']} {r['address']}"
    rows = [r for r in rows if r["name"] and not any(re.search(p, norm(text(r))) for p in JUNK)]
    excluded = [r for r in rows
                if any(re.search(p, norm(r["name"].split("(")[0]).strip()) for p in EXCLUDE_NAME)
                or any(re.match(rf"\s*{n}\b", norm(r["address"])) and w in norm(r["address"])
                       for n, w in EXCLUDE_ADDR)]
    rows = [r for r in rows if r not in excluded]

    # Union-find over shared keys.
    parent = list(range(len(rows)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for i, r in enumerate(rows):
        for k in keys(r):
            if k in seen:
                parent[find(i)] = find(seen[k])
            else:
                seen[k] = i
    by_name = {}
    for i, r in enumerate(rows):
        if r["address"] or r["city"]:
            by_name.setdefault(bare_name(r), set()).add(find(i))
    for i, r in enumerate(rows):
        if not r["address"] and not r["city"]:
            hits = {find(j) for j in by_name.get(bare_name(r), ())}
            hits |= {find(j) for n, js in by_name.items() for j in js
                     if len(bare_name(r)) >= 5 and (bare_name(r) in n or n in bare_name(r)) and len(n) >= 5}
            if len(hits) == 1:
                parent[find(i)] = hits.pop()
    groups = {}
    for i, r in enumerate(rows):
        groups.setdefault(find(i), []).append(r)

    out = []
    for g in groups.values():
        g.sort(key=lambda r: (r["_rank"], -sum(bool(r[f]) for f in FIELDS)))
        g.sort(key=lambda r: "not conf" in r["name"])
        m = dict(g[0])
        for r in g[1:]:
            for f in FIELDS:
                if not m[f] and r[f]:
                    m[f] = r[f]
            if not re.match(r"\s*\d", m["address"]) and re.match(r"\s*\d", r["address"]):
                m["address"], m["postal_code"] = r["address"], m["postal_code"] or r["postal_code"]
            if r["email"] and r["email"].lower() not in (m["email"].lower(), m["alt_email"].lower()) \
                    and not m["alt_email"]:
                m["alt_email"] = r["email"]
        m["sources"] = " ".join(dict.fromkeys(s for r in g for s in r["sources"].split() if s))
        if any(r["confidence"] == "high" for r in g):
            m["confidence"] = "high"
        out.append(m)

    email_rows = [e for f in ("emails.json", "emails_web.json") if (Path(raw) / f).exists()
                  for e in json.loads((Path(raw) / f).read_text())]
    if email_rows:
        by_key = {}
        for e in email_rows:
            for k in keys({"name": e["name"], "address": e["address"], "city": e.get("city", ""),
                           "postal_code": ""}):
                by_key[k] = e
        for m in out:
            e = next((by_key[k] for k in keys(m) if k in by_key), None)
            if e:
                for f in ("email", "alt_email", "email_source"):
                    m[f] = m[f] or e.get(f, "")

    for m in out:
        m["region"] = region_of(m)
    out.sort(key=lambda r: (r["region"], norm(r["city"]), norm(r["name"])))

    with open(HERE / "quebec_mosques.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)

    wb = Workbook()
    ws = wb.active
    ws.title = "Mosquées QC"
    ws.append(FIELDS)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E3D")
    for r in out:
        ws.append([r[f] for f in FIELDS])
    widths = {"region": 22, "name": 44, "type": 12, "address": 36, "city": 24, "postal_code": 10,
              "phone": 17, "email": 34, "alt_email": 30, "website": 34, "confidence": 10,
              "sources": 60, "email_source": 45}
    for i, f in enumerate(FIELDS, 1):
        ws.column_dimensions[get_column_letter(i)].width = widths[f]
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(HERE / "quebec_mosques.xlsx")

    print(f"{len(rows)} rows in, {len(excluded)} excluded, {len(out)} places, "
          f"{sum(bool(r['email']) for r in out)} with email")
    for n in sorted({r["name"] for r in excluded}):
        print("  excluded:", n)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "raw")
