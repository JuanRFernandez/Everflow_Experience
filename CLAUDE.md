# CLAUDE.md — rules for every Claude session in this repo

The website of EverFlow Experience: plain HTML, CSS and JavaScript, served by GitHub Pages
from `master`. `README.md` explains the structure; this file holds the rules.

Answer Juan in the language he writes (usually Argentine Spanish). Everything on the site and
in this repository is English, with German for the legal pages.

## Rules

1. **`master` is the live site.** Change it only through a pull request. Never push to it.
2. **This repository is public.** Nothing internal goes in: no contact persons or e-mail
   addresses of partners, no commission or rate, no agreement, no name of a hotel that has
   not agreed to be shown, no Drive path, no local path. `scripts/check.py` fails when a
   page shows a price, when a file of the hotel library is in the repository, and when a
   text file holds a Drive path, a local path or an e-mail address other than the site's own.
3. **Hotel material only with written permission**, with the hotel's exact credit line.
   The permission register decides; `docs/HOTEL_MATERIAL.md` lists what is published.
4. **Zero third-party requests on page load.** Fonts and Leaflet are served from this repo.
5. **No prices, no booking, no payment on the site.**
6. **Legal pages stay current.** A change of address, tax status, tool or provider goes into
   `impressum.html` and `datenschutz.html` together with a new "Stand" / "Last updated" date.
7. Run `python scripts/check.py` before every commit. It must end with `0 failures`.

## The hotels

Questions about a hotel, a new hotel card, an offer for a guest: the skill
`.claude/skills/hotels/SKILL.md` has the steps. In short:

```bash
uv run --with pypdf python scripts/library.py status         # is the library current?
uv run --with pypdf python scripts/library.py build --apply  # rebuild it from the material
python scripts/library.py search toboggan --in berchtesgaden
python scripts/library.py permissions                        # what may go on the site
python scripts/library.py verify <hotel>.facts.json          # every fact stands on its page
```

`library.local.json` (git-ignored) holds the four local paths: the material, the folders that
may be read, the library and the permission register. All four lie outside this repository.
A file is never read when its name, or the name of its folder, says agreement, form, rate,
payment or identity paper; a folder of archived material is skipped. The name is all the tool
looks at: a document with a neutral name is read, so name what you save for what it is.

## Where things are

- The material as the hotels sent it, the library and the permission register: Drive.
- Terms, contacts and the state of every hotel deal: the partner Sheet, through the repo
  `Everflow-Research` (same parent folder).
- Draft pull requests wait for something from a hotel; the pull request says what.
