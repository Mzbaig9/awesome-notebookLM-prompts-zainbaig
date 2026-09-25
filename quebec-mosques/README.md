# Mosquées du Québec

`quebec_mosques.xlsx` and `quebec_mosques.csv` list 186 mosques, musallas, prayer rooms and Islamic centres across Quebec, Montreal included, compiled in September 2026, 133 of them with a contact email. Masjid Makkah Al-Mukarramah (11900 boul. Gouin O, Pierrefonds), the Islamic Centre of Quebec (ICQ, 2520 ch. Laval, Saint-Laurent) and Masjid Madani (12080 boul. Laurentien, Cartierville) are excluded on purpose.

Places come from OpenStreetMap, PraySalat, Mawaqit, targeted web searches and each mosque's own website, merged by street address and name. `region` is the Quebec administrative region, `type` separates mosques and centres from musallas, campus or airport prayer rooms, Shia centres, Ahmadiyya and Ismaili jamatkhanas so they can be filtered, and `sources` lists every page a row was built from.

Emails were only recorded where a page showed that address for that place (the mosque's own site, its Mawaqit listing, or a directory whose address or phone matched); nothing is guessed. `email_note` flags the ones that belong to an umbrella body rather than the site itself, and `email_source` says where each was seen. The 53 without an email are mostly small musallas whose only contact is a phone number or a login-walled Facebook page.

`raw/` holds each source as fetched and `build.py` merges them, applies the exclusions and joins the emails in `raw/emails.json` (search and manual lookups) and `raw/emails_web.json` (website scrape): `python3 build.py`.
