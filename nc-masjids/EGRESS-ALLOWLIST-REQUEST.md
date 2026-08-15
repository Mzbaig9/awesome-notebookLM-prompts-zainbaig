# Egress allowlist needed to finish the email collection

The masjid roster in `nc-masjids-roster.csv` is complete enough to work from.
The **email column could not be filled** because every outbound HTTPS request
to a non-GitHub host was refused by the organization egress proxy with a
`403` on `CONNECT`.

This file lists exactly which hosts need to be reachable to finish the job.

## What failed

Confirmed `connect_rejected` / `EGRESS_BLOCKED` responses were recorded for,
among others:

- `iccharlotte.org`
- `greenvillencmasjid.org`
- `greenvillemasjid.com`
- `ashevillemasjid.com`
- `en.wikipedia.org`

Seven independent research agents each attempted fetches across the full
domain set below and **none succeeded**. Only `github.com` was reachable.

## Tier 1 — directory sites (highest yield per fetch)

These are aggregate listings. Unblocking just these would close most of the
remaining roster gaps as well as surface many emails.

```
salatomatic.com
islamicfinder.org
prayersconnect.com
zabihah.com
masjidsinusa.com
mosquesmasjids.com
mosques.cmac.ws
islamicvalley.com
halaltrip.com
muslimguide.com
masjid.us
masjidbox.com
muslimlistings.org
en.wikipedia.org
facebook.com
m.facebook.com
```

## Tier 2 — masjid-maintained regional directories

Curated by the masjids themselves; higher data quality than the commercial
aggregators.

```
icgmasjid.org          (/nearby-islamic-centers/ — 7 exact Triad addresses)
raleighmasjid.org      (/nearby-islamic-centers/ — 8 Triangle centers)
apexmosque.org         (/mosques-in-research-triangle-park-rtp/)
masraleigh.org         (MAS-RDU affiliated-center list)
muslimlife.wfu.edu     (/community-resources/mosques/ — Forsyth County)
```

## Tier 3 — nonprofit registries (officer contacts via Form 990)

Several masjids have no website but do have IRS filings that list a
principal officer contact.

```
causeiq.com
guidestar.org
charitynavigator.org
projects.propublica.org
```

## Tier 4 — individual masjid domains

```
iccharlotte.org             isgcharlotte.org           masjidashshaheed.org
pillarsmosque.org           charlottemcc.org           umcc-charlotte.org
masjidqiblatain.com         azicc.org                  noicharlotte.com
meccharlotte.org            izbnc.org                  ciacademy.us
isgmc.com                   ilmcenter.org              statesvillemasjid.org
iclnmooresville.org         islamiccenterofshelby.com
raleighmasjid.org           alimanschool.org           masjidkingkhalid.org
assalaamic.org              mqyc.org                   riinc.org
mycc-rdu.org                carymasjid.org             apexmosque.org
icmnc.org                   alnooric.org               ibadarrahman.org
arrazzaqislamiccenter.org   ndmnc.org                  dukemsa.com
chapelhillmasjid.org        uncmsa.org                 smithfieldmasjid.org
alsalammosque.net           islamiccenterofsanford.org islamiccenterdunn.org
alrahma.cc                  masjidhenderson.com
icgmasjid.org               islamiccenterofthetriad.com masjidnoornc.org
alummil-ummat.org           prosunnah.org              wdmic.org
dawatulhaqq.com             icohp.org                  triadmuslims.org
masjidalmuminun336.org      communitymosque.com        clemmonsislamiccenter.org
burlingtonmasjid.com        meislam.org                islamicsocietyofthecarolinas.webador.com
fayettevillemasjidnc.com    masjidomaribnsayyid.org    masjidr.wordpress.com
icwh.org                    goldsboromasjid.org        macnc.org
islamiccenteroflumberton.org
greenvillencmasjid.org      wilsonicdc.com             icrrnc.org
islamiccenterwilson.wixsite.com
ashevillemasjid.com         morgantonmosque.org        boonemasjid.com
```

## How to change it

The network policy is set **on the environment**, not inside the session —
there is no local override, and the proxy README explicitly says not to route
around a 403. See:

https://code.claude.com/docs/en/claude-code-on-the-web

A new session is needed after the policy changes for it to take effect.

## Also worth raising

The `WebSearch` budget hit its 200-call session cap partway through the sweep.
Discovery stopped short of full statewide coverage — `masjidsinusa.com` claims
96 NC centers across 47 cities, against the ~107 organizations rostered here
(a figure that includes schools, campus MSAs and unverified leads). Raising
`CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` alongside the allowlist would let a
follow-up run close the remaining city gaps listed in `README.md`.
