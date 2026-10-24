# CLAUDE.md — rules for every Claude session in this repo

The website of EverFlow Experience: plain HTML, CSS and JavaScript, served by GitHub Pages
from `master`, generated from `content/*.json` by `scripts/build.py`. `README.md` explains the
structure; this file holds the rules.

Answer Juan in the language he writes (usually Argentine Spanish). Everything in this
repository is English. The site is English, with German for the legal pages, and the home
page, the destinations, the guides and the enquiry form also exist in Spanish (`/es/`) and
Brazilian Portuguese (`/pt/`), from `content/i18n/` (README → Languages).

## Rules

1. **`master` is the live site.** Change it only through a pull request. Never push to it.
2. **This repository is public.** Nothing internal goes in: no contact persons or e-mail
   addresses of partners, no commission or rate, no agreement, no name of a partner that
   the permission register does not clear for the site, no Drive path, no local path. A
   partner the register shows without its name is never named here either. `scripts/check.py`
   fails when a page shows a price, when a file of the hotel library is in the repository,
   and when a text file holds a Drive path, a local path or an e-mail address other than the
   site's own.
3. **Partner material only when the permission register allows it**, with the partner's
   exact credit line under every photo ("© …", or a courtesy line such as "Photo courtesy of
   the owner"), never EverFlow's. The register records the
   basis: the partner's words in writing, or Juan's decision with its date.
   `docs/HOTEL_MATERIAL.md` lists what is published.
4. **Zero third-party requests on page load.** Fonts and Leaflet are served from this repo.
5. **No prices, no booking, no payment on the site.**
6. **Legal pages stay current.** A change of address, tax status, tool or provider goes into
   `content/legal/` together with a new "Stand" / "Last updated" date in `content/site.json`.
7. **Never edit a generated page** (`index.html`, `destinations/`, `stay/`, `guides/`, `es/`, `pt/`,
   `impressum.html` …). Change `content/` or `scripts/build.py`, then run `python scripts/build.py`.
8. **Spanish and Portuguese follow the English.** A new or changed English text on a page that
   exists in all three languages gets its translation in `content/i18n/es.json` and `pt.json` in
   the same pull request, made with DeepL (ES-419, PT-BR). `scripts/check.py` warns until it has one.
9. Run `python scripts/check.py` before every commit. It must end with `0 failures`.

## The hotels

Questions about a hotel, a new partner page, an offer for a guest: the skill
`.claude/skills/hotels/SKILL.md` has the steps. In short:

```bash
uv run --with pypdf python scripts/library.py status         # is the library current?
uv run --with pypdf python scripts/library.py build --apply  # rebuild it from the material
python scripts/library.py search toboggan --in berchtesgaden
python scripts/library.py permissions                        # what may go on the site
python scripts/library.py verify <hotel>.facts.json          # every fact stands on its page
uv run --with pillow python scripts/photos.py stay <partner> <name> <original>  # a photo for the site
```

`library.local.json` (git-ignored) holds the four local paths: the material, the folders that
may be read, the library and the permission register. All four lie outside this repository.
A file is never read when its name, or the name of its folder, says agreement or contract (in
English, German, French, Spanish or Portuguese), form, rate, payment or identity paper, with or
without accents and also when written as one word; a folder of archived material is skipped.
The name is all the tool looks at: a document with a neutral name is read, so name what you save
for what it is.
Besides the PDFs it reads only our own notes on a partner's website or offer
(`…_EFE_<Partner>-Website-Facts_vNN.md`, `-Offer-Text_`, `-Owner-Facts_`), one page per `##`
section; no other Markdown file.

## Where things are

- The material as the hotels sent it, the library and the permission register: Drive.
- Terms, contacts and the state of every hotel deal: the partner Sheet, through the repo
  `Everflow-Research` (same parent folder).
- Draft pull requests wait for something from a hotel; the pull request says what.
