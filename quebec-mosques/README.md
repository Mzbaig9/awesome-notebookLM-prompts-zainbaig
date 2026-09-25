# Mosquées du Québec

`quebec_mosques.csv` and `quebec_mosques.xlsx` list 112 mosques, musallas and Islamic centres across Quebec, Montreal included, compiled in September 2026. Masjid Makkah Al-Mukarramah (Jean-Talon), the Islamic Centre of Quebec (ICQ, Saint-Laurent) and Masjid Madani (Parc-Extension) are excluded on purpose. Same-name places elsewhere (the Pierrefonds Makkah on Gouin O, the Madani in Laval) are kept.

The list was built from web search result snippets because direct access to directory sites and maps was blocked in the environment that produced it. It is not exhaustive. Each row carries a `confidence` (high: address confirmed by a snippet, medium: partial or conflicting, low: name only) and the `source` URL. Areas with thin or no coverage include the West Island (Pointe-Claire, Dorval, Kirkland), Anjou, Montréal-Est, Mercier, the Plateau, Côte-Saint-Luc, Blainville, Boisbriand, Mirabel, Saint-Eustache, Saint-Lambert and La Prairie.

The `email` column is filled for 66 of 112 rows, only where a search result showed that address for that mosque; nothing is guessed. A few are an umbrella body's address (Salahouddine uses AICP's, Attawassol uses the Roussillon centre's) and Al Amal Châteauguay's is its donations inbox. `alt_email` holds a second address when one was found and `email_source` the page it most likely came from.

`raw/` holds the per-region results and `build.py` merges them, deduplicates by street address and applies the exclusions, then joins `raw/emails.json`: `python3 build.py`.
