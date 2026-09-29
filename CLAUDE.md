# CLAUDE.md — rules for every Claude session in this repo

The website of EverFlow Experience: plain HTML, CSS and JavaScript, served by GitHub Pages
from `master`. `README.md` explains the structure; this file holds the rules.

Answer Juan in the language he writes (usually Argentine Spanish). Everything on the site and
in this repository is English, with German for the legal pages.

## Rules

1. **`master` is the live site.** Change it only through a pull request. Never push to it.
2. **This repository is public.** Nothing internal goes in: no contact persons or e-mail
   addresses of partners, no commission or rate, no agreement, no name of a hotel that has
   not agreed to be shown, no Drive link.
3. **Hotel material only with written permission**, with the hotel's exact credit line.
   The steps are in `docs/HOTEL_MATERIAL.md`; the table there lists what is published.
4. **Zero third-party requests on page load.** Fonts and Leaflet are served from this repo.
5. **No prices, no booking, no payment on the site.**
6. **Legal pages stay current.** A change of address, tax status, tool or provider goes into
   `impressum.html` and `datenschutz.html` together with a new "Stand" / "Last updated" date.
7. Run `python scripts/check.py` before every commit. It must end with `0 failures`.

## Where things are

- Partner database and the state of every hotel deal: the repo `Everflow-Research`
  (same parent folder), which reads the master Google Sheet.
- Hotel photos, brochures and press kits as received: Drive, `05_PARTNERS_AGENCIES_B2B ▸
  1_Stay ▸ <hotel>`. The working inventory is the Doc `EFE_Hotel_Material_Inventory` there.
- Draft pull requests wait for something from a hotel; the pull request says what.
