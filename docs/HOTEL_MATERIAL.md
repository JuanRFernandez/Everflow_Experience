# Partner material on the site

Which hotels and chalets are shown on everflowexperience.com, with which material, on which
basis and with which credit line. One row per partner, added in the pull request that shows it.

**This repository is public.** Contact persons, e-mail addresses, commercial terms, Drive paths
and partners that are not shown do not belong here. The permission register and the working
inventory (what each partner sent, who said what, what is missing) are kept in Drive, next to
the material.

## Shown

| Partner | Page | Basis | Credit line (shown as "© …" under every photo) | Files |
|---|---|---|---|---|
| Hotel Vier Jahreszeiten Kempinski München | `/stay/kempinski-muenchen/`: five photos and the official brochure "The Munich Eras" | In writing from the hotel, 01.09., 04.09. and 15.09.2026: photos for our use with the photo credit, offers presented as the hotel's own, brochure downloadable | `Hotel Vier Jahreszeiten Kempinski München` | `assets/img/stays/kempinski-muenchen/` · `assets/stays/kempinski-muenchen/` |
| Kempinski Hotel Berchtesgaden | `/stay/kempinski-berchtesgaden/`: three photos | In writing from the hotel, 04.09.2026 (offers presented as the hotel's own) and 01.10.2026 (photos and their copyright, in answer to our request for the website) | `Kempinski Hotel Berchtesgaden` | `assets/img/stays/kempinski-berchtesgaden/` |
| Rote Wand Gourmet Hotel | `/stay/rote-wand/`: eight photos | In writing from the hotel, 25.09. and 29.09.2026 (photos and marketing material, with the correct copyright); credit line given 30.09.2026 | `Rote Wand Gourmet Hotel / Robert Rieger` | `assets/img/stays/rote-wand/` |

## Adding a partner

The steps are in `.claude/skills/hotels/SKILL.md`. What decides:

1. The partner's line in the permission register says `site: yes`, and `photos: yes` for
   photos. The register records the basis: the partner's words in writing, or Juan's decision
   with its date. `scripts/photos.py` refuses a photo the register does not allow.
2. Every fact on the page stands in a document of the partner
   (`python scripts/library.py verify`), or on its official website, linked from the page.
   The words are ours; the partner's own programme is named as the partner's.
3. Every photo carries the partner's **exact credit line**, never EverFlow's. If photos come
   from several photographers, ask whether one line covers all of them. Photos go through
   `scripts/photos.py` (WebP, sRGB, no metadata, under 250 KB). The originals stay in Drive.
4. Brochures only when the partner allowed the download: `assets/stays/<partner>/`, byte for
   byte as the partner sent them.
5. Never in this repository: room overviews, rate sheets, agreements, presentations made for
   the trade (`assets/Hotels/` is git-ignored for that reason).
6. The Impressum lists every credit line automatically (from `content/partners.json`); change
   the "Stand" date in `content/site.json` when the list changes.
7. `python scripts/build.py`, `python scripts/check.py`, then a pull request. `master` is the
   live site.
