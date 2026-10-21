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
| Alpin Resort Sacher Seefeld | `/stay/sacher-seefeld/`: six photos | In writing from the hotel, 08.10.2026: a selection of the pictures on our website, with the credit line it gave | `Alpin Resort Sacher Seefeld` | `assets/img/stays/sacher-seefeld/` |
| Interalpen-Hotel Tyrol | `/stay/interalpen-tyrol/`: six photos (750 px, the largest the hotel's website serves) | In writing from the hotel, 06.10.2026: brochures and pictures sent in answer to our request for the website. Credit line asked; the hotel's name until then | `Interalpen-Hotel Tyrol` | `assets/img/stays/interalpen-tyrol/` |
| Kempinski Palace Engelberg | `/stay/kempinski-engelberg/`: text only | In writing from the hotel, 30.09.2026: photos and logos may be used on our website. Photos and credit line not received yet | — | — |
| Hotel & Chalet Aurelio | `/stay/aurelio-lech/`: eleven photos (hotel and Club Chalet) from the press material of its collection | Spoken permission; shown on Juan's decision of 19.10.2026. The credits confirmed in writing by pepper-collection, whose collection the hotel belongs to, 19.10.2026; the hotel's own reply outstanding | `Hotel & Chalet Aurelio`, and `Hotel & Chalet Aurelio / Patrick Schwienbacher` where the file names the photographer | `assets/img/stays/aurelio-lech/` |
| pepper-collection | `/stay/pepper-collection/`: eight houses, ten photos each (ULA Signature: eight renderings, marked as renderings), from its media page and the photo package the partner shared on 20.10.2026 | In writing from the partner: the credits on 19.10.2026, the listings and the package on 20.10.2026 | `pepper-collection / Patrick Schwienbacher`, `pepper-collection / Stefano Scata`, `pepper-collection / Andreas Pollok` (the photographer each file names); `KITZMÜLLER Architektur` for the renderings of ULA Signature (the partner's wording, 21.10.2026); `pepper-collection` for ULA Easy Stay | `assets/img/stays/pepper-collection/` |
| Schlosshotel Kitzbühel | `/stay/schlosshotel-kitzbuehel/`: text only, facts from the hotel's website | Shown on Juan's decision of 19.10.2026 | — | — |
| Chalets in Megève | `/stay/chalets-megeve/`: 22 houses with ten photos each (every photo of the house saved in Drive) | In writing from the partner, 29.09.2026 (its properties on our website), and Juan's decision of 19.10.2026: shown as EverFlow's chalets, without the partner's name | `Photos courtesy of the owner` | `assets/img/stays/chalets-megeve/` |

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
   `scripts/photos.py` (WebP, sRGB, no metadata, in up to three sizes from 800 to 2400 px, so
   phones load the small one and large screens a sharp one). The originals stay in Drive; the
   script logs each source in the library folder, and `photos.py rebuild` redoes them all.
4. Brochures only when the partner allowed the download: `assets/stays/<partner>/`, byte for
   byte as the partner sent them.
5. Never in this repository: room overviews, rate sheets, agreements, presentations made for
   the trade (`assets/Hotels/` is git-ignored for that reason).
6. The Impressum lists every credit line automatically (from `content/partners.json`); change
   the "Stand" date in `content/site.json` when the list changes.
7. `python scripts/build.py`, `python scripts/check.py`, then a pull request. `master` is the
   live site.
