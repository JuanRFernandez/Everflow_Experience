# Hotel material on the site

Which hotels are shown on everflowexperience.com, with which material, under which permission
and with which credit line. One row per hotel, added in the pull request that shows it.

**This repository is public.** Hotels we are still talking to, contact persons, e-mail
addresses, commercial terms and Drive paths do not belong here. The permission register and
the working inventory (what each hotel sent, who gave which permission, what is missing) are
kept in Drive, next to the material.

## Shown

| Hotel | On the site | Permission | Credit line | Files |
|---|---|---|---|---|
| Hotel Vier Jahreszeiten Kempinski München | Card with three photos and the official brochure "The Munich Eras" | In writing from the hotel, 15.09.2026: photos may be shown, the brochure may be offered for download | `Hotel Vier Jahreszeiten Kempinski München` (one line for all photos) | `assets/img/stays/kempinski-muenchen/` · `assets/stays/kempinski-muenchen/` |
| Kempinski Hotel Berchtesgaden | Card in our own words, no hotel material | In writing from the hotel, 04.09.2026: we may present the hotel's offers as the hotel's own | none: no photos are shown | none |
| Rote Wand Gourmet Hotel | Card in our own words, no hotel material | In writing from the hotel, 25.09. and 29.09.2026: photos and marketing material, with the correct copyright | none yet: photos are shown once the hotel has sent them with its credit line | none |

## Adding a hotel

The steps are in `.claude/skills/hotels/SKILL.md`. What decides:

1. The hotel's line in the permission register says yes. The permission is **in writing**
   and names what it covers (photos, brochure). A download link sent without a word about
   publishing is not a permission.
2. We have visited the hotel: the section is "addresses we have visited ourselves".
3. Every fact on the card stands in a document of the hotel
   (`python scripts/library.py verify`). The words are ours.
4. Photos need the **exact credit line**. If they come from several photographers, ask
   whether one line covers all of them. Two or three photos, about 1000 px, under 250 KB,
   without metadata, in `assets/img/stays/<hotel>/`. The originals stay in Drive.
5. Brochures only when the hotel allowed the download: `assets/stays/<hotel>/`, byte for byte
   as the hotel sent them.
6. Never in this repository: room overviews, rate sheets, agreements, presentations made for
   the trade (`assets/Hotels/` is git-ignored for that reason).
7. In `impressum.html`: the hotel in "Urheberrecht und Bildnachweise" and a new "Stand" date,
   as soon as its photos are shown.
8. `python scripts/check.py`, then a pull request. `master` is the live site.
