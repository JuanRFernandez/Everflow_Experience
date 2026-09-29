# Hotel material on the site

What hotel material is published on everflowexperience.com, under which permission and with
which credit line. One row per hotel, added in the same pull request that publishes the material.

**This repository is public.** Hotels we are still talking to, contact persons, e-mail
addresses, commercial terms and Drive links do not belong here. The working inventory
(what each hotel sent, who gave which permission, what is still missing) is kept in the
team's Drive, next to the material itself: `05_PARTNERS_AGENCIES_B2B ▸ 1_Stay ▸
EFE_Hotel_Material_Inventory`.

## Published

| Hotel | On the site | Permission | Credit line | Files |
|---|---|---|---|---|
| Hotel Vier Jahreszeiten Kempinski München | Card in "Where our guests stay": three photos and the official brochure "The Munich Eras" | In writing from the hotel, 15.09.2026: photos may be shown, the brochure may be offered for download | `Hotel Vier Jahreszeiten Kempinski München` (one line for all photos) | `assets/img/stays/kempinski-muenchen/` · `assets/stays/kempinski-muenchen/` |

## Adding a hotel

1. The hotel's permission is **in writing** and names what it covers (photos, brochure, logo).
   A download link sent without a word about publishing is not a permission.
2. The hotel has given the **exact credit line**. If the photos come from several
   photographers, ask whether one line covers all of them.
3. Photos: pick two or three, save them at web size (longest side about 1000 px, JPEG, under
   250 KB) in `assets/img/stays/<hotel>/`. The originals stay in Drive.
4. Brochures: `assets/stays/<hotel>/`, byte for byte as the hotel sent them.
5. Never in this repository: room overviews, rate sheets, agreements, presentations made for
   the trade (`assets/Hotels/` is git-ignored for that reason).
6. On the page: the credit line in the caption, the hotel's offer presented as the hotel's own,
   no prices. In `impressum.html`: the hotel in "Urheberrecht und Bildnachweise" and a new
   "Stand" date.
7. `python scripts/check.py`, then a pull request. `master` is the live site.
8. Add the row to the table above.
