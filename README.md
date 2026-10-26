# EverFlow Experience — Website

Static website for [everflowexperience.com](https://everflowexperience.com): tailor-made ski and
mountain trips, hosted across the Alps.
No framework, no server: plain HTML, CSS and JavaScript, generated from the content files by one
small Python script and served by **GitHub Pages**.

`master` is the live site. Change it only through a pull request: on every pull request GitHub
Actions lints, builds, checks and tests the site, and every push to `master` that passes is built
and deployed (`.github/workflows/site.yml`). Nothing generated is committed: the repository holds
the sources, `_site/` is the build.

## Structure

```
├── content/                   # EVERYTHING the site says: edit here
│   ├── site.json              # name, brand line, contact, legal dates, extra photo credits, the Search Console tag
│   ├── pages.json             # texts of home, about, enquiry, how it works, FAQ, the guests' words
│   ├── destinations.json      # countries and places (facts, who / when / how)
│   ├── partners.json          # hotels, chalets, apartments: texts, key facts, photos, credit line, place
│   ├── experiences.json       # the eight experiences
│   ├── guides.json            # the guides: sections, places and hotels they name
│   ├── team.json              # the team
│   ├── i18n/es.json, pt.json, de.json  # Spanish, Portuguese, German: each English text → its translation
│   └── legal/                 # Impressum and Datenschutz texts (German / English)
├── assets/
│   ├── css/everflow.css       # the one stylesheet (tokens in :root)
│   ├── js/everflow.js         # menu, galleries (a photo opens large), stay filters, enquiry form, click-to-load map, home video
│   ├── fonts/                 # Playfair Display + Public Sans, self-hosted (SIL OFL)
│   ├── vendor/leaflet/        # Leaflet 1.9.4 (BSD-2), loaded only after "Open the interactive map"
│   ├── img/                   # WebP files written by scripts/photos.py
│   │   ├── brand/             # the wordmark (SVG, ink and white) and the icons
│   │   └── stays/<partner>/   # partner photos, each shown with the partner's credit line
│   ├── stays/<partner>/       # partner brochures, unmodified, only with written permission
│   └── video/hero-1080.mp4    # home video, original quality (tablets and larger screens only)
├── brand/                     # source files of the logo: the wordmark as PNG and, traced from it, as SVG (scripts/photos.py brand)
├── scripts/
│   ├── build.py               # content/ → _site/ (standard library only)
│   ├── check.py               # site checks on _site/ and on the repository (also run in CI)
│   ├── photos.py              # original photo → WebP files for the site (needs Pillow)
│   ├── map.py                 # Natural Earth data → assets/img/map/alps.svg, the drawn map of the destinations
│   ├── library.py             # the hotel library (local tool, see CLAUDE.md)
│   └── library.example.json   # the shape of library.local.json (the local paths of the hotel library)
├── tests/                     # browser tests (Playwright): python tests/run.py
├── docs/HOTEL_MATERIAL.md     # which partners are shown, on which basis, with which credit
├── .github/workflows/site.yml # lint, build, check, test on every pull request; build and deploy on master
├── requirements-dev.txt       # the tools: Playwright, ruff, Pillow, pypdf
├── pyproject.toml             # the lint settings
├── CLAUDE.md                  # rules for Claude sessions in this repo
├── .claude/skills/hotels/     # the steps for a hotel question, a partner page, an offer
└── _site/                     # THE BUILT SITE (git-ignored): pages, sitemap.xml, robots.txt, CNAME, a copy of assets/
```

## Working on the site

1. Once: `pip install -r requirements-dev.txt` and `python -m playwright install chromium`
   (only for the browser tests; the build needs nothing but Python 3.12).
2. Change the text in `content/*.json` (or the layout in `scripts/build.py`, the look in
   `assets/css/everflow.css`).
3. `python scripts/build.py` writes the site into `_site/`.
4. `python scripts/check.py` must end with `0 failures`; `ruff check scripts tests` must be clean.
5. Preview: `python -m http.server --directory _site`, then open http://localhost:8000.
   (Links start with `/`, so opening the files directly does not work.)
6. For a change a visitor can see: `python tests/run.py` (Chrome; with `BROWSER_CHANNEL` set to
   nothing it uses the bundled Chromium, as in CI). `tests/test_enquiry.py` covers the enquiry form,
   `test_guides.py` the guides in three languages, `test_stay.py` "Where to stay", `test_review.py`
   menu, galleries, map and the form's messages, `test_lenas.py` Las Leñas; every suite ends with a
   sideways-scroll check at 320 to 1440 px.
7. A pull request to `master`. The site is deployed from the merge within a few minutes.

A new photo: `uv run --with pillow python scripts/photos.py site <original> assets/img/<folder>/<name>`.
It writes up to three sizes (800, 1600, 2400 px, never larger than the original); the browser picks
the one the screen needs, so phones stay fast and large screens get a sharp photo. Every photo is
logged with its original in the library folder (outside the repo): `photos.py rebuild` redoes them
all, for instance after a change of quality.
A partner's photo: `uv run --with pillow python scripts/photos.py stay <partner> <name> <original>`;
it refuses when the permission register does not allow photos of that partner.
The wordmark: `uv run --with pillow python scripts/photos.py brand` colours `brand/everflow-wordmark.svg`
for the header and the footer and cuts the icons from the PNG.

A stay (`content/partners.json`) has a `type`: `hotel`, `chalet` or `apartment`, or a list when it
is more than one, the main one first. A house of a collection (`residences`) also has its key facts
(`guests`, `bedrooms`, `bathrooms`, `size_m2`: a number, a range such as `12–16`, or `about 800`),
`ski_access`, up to four `highlights`, a one-sentence `card` and a two- or three-sentence `about`;
a hotel has `ski_access` and `highlights`, three at most together: the labels its card shows, chosen
to add to the card's sentence, not to repeat it. Every value stands in the partner's material
(`library.py verify`); a value that cannot be checked stays out. "Where to stay" lists every stay
in the order of the file, with filters by type and destination that keep their state in the
address (`/stay/?type=chalet&place=megeve`); every stay has a button that opens the enquiry with
the stay filled in (`/enquire/?destination=…&stay=…&house=…&type=…`). On the enquiry page the four
fields are linked: a destination narrows the stays and the types, a stay sets its destination (and,
for a hotel, shows its type), a type chosen by the visitor narrows stays and houses, a collection
lists its houses; without the script every option shows.

A guest's words go into `content/pages.json` under `testimonials` (the quote verbatim, first name,
country, trip and season), only with the guest's written consent, which stays in Drive; the home
page and the enquiry page show them once the list has entries. A team member in `content/team.json`
may have no `photo` yet: the page then shows the name and role alone.

A guide (`content/guides.json`) is running text plus cards of the places and the hotels and
chalets it names; the destination pages it lists under `related` link to it. A guide states what
the destination and partner pages already state, or plain general knowledge: a new fact about a
hotel goes on its partner page first, checked against the hotel's material. Every guide needs
`name`, `eyebrow`, `h1`, `lead`, `description` and `card` (and may have a shorter `seo_title`), and
exists in Spanish and Portuguese like the home page (its texts in `content/i18n/`).

## Languages

The home page, the destinations, the guides and the enquiry form also exist in Spanish (`/es/`,
Latin American Spanish) and Portuguese (`/pt/`, Brazilian), for the guests and agencies who write
from Argentina and Brazil, and in German (`/de/`). The other pages (where to stay, experiences,
about, the partner pages) are English only, and the legal pages German and English. The language
menu in the header (a globe: English, Español, Português, Deutsch) leads to the same page in each
language, or to that language's home page where the page exists in English only.

The home page has a section for guests from Brazil and Argentina (coaching in Portuguese and
Spanish, the flights, Las Leñas, the guide written for them); on the Spanish and Portuguese home
pages it comes right after the hero. `_site/llms.txt` sums the site up for AI assistants, built
from the content like the pages.

`content/i18n/es.json`, `pt.json` and `de.json` map each English text of those pages to its translation.
A new or changed English text has no translation until it is added: the page shows it in English
meanwhile, and `scripts/check.py` warns. To add the missing ones:

1. `python scripts/build.py --missing missing.json` lists them (`missing.json` is a scratch file;
   do not commit it).
2. Translate them with DeepL (target `ES-419`, `PT-BR` and `DE`; German addresses the reader with
   "Sie"), then check the output against the rule
   for place names: a city, region, range or lake with a living exonym takes it (Múnich / Munique,
   Zúrich / Zurique, Ginebra / Genebra, Baviera, el Tirol, Saboya / Saboia, Engadina, los Dolomitas /
   as Dolomitas, los Andes); a resort, village, lift, ski area or brand keeps its local name (Lech am
   Arlberg, Zermatt, Megève, Kitzbühel, Garmisch-Partenkirchen, Cortina d'Ampezzo, Ski Arlberg,
   Les 3 Vallées). St. Moritz and Las Leñas stay as they are in every language.
   German takes München, Zürich, Genf, Mailand, Venedig, Tirol, Savoyen, Engadin, die Dolomiten.
   `{name}`-style placeholders, `[links](/…)` and numbers stay unchanged; Spanish, Portuguese and
   German write thousands with a point (1.300 m) and decimals with a comma (1,5 horas).
3. Add them to the files, then `python scripts/build.py` and `python scripts/check.py`.

A translation that no page uses any more is a warning too: remove it. The Spanish, Portuguese and
German pages follow the same wording rules as the English ones: `scripts/check.py` fails on
reserva/reservar, pago/pagamento and comisión/comissão there, and on buchen/Buchung (also in
compounds and related forms such as Buchungsanfrage, ausgebucht, buchbar or umbuchen), reservieren,
bezahlen/Zahlung, Kaution, Stornierung and Provision on the German pages.

## Rules the site follows

- **Zero third-party requests on page load.** Fonts, scripts, photos and the video are served
  from this repo; a Content-Security-Policy on every page enforces it in the browser. The only
  external request is the map tiles (OpenStreetMap), and only after the visitor clicks "Open the
  interactive map"; the map shown first is drawn from Natural Earth data and served from this repo. No cookies, no tracking, no cookie banner.
- **Partner photos carry their owner's credit.** Every photo of a hotel or chalet sits in a
  figure with its credit line under it ("© <owner>", or a courtesy line such as "Photo courtesy
  of the owner"), and every credit line is listed in the Impressum. `scripts/check.py` fails
  otherwise.
- **No prices, no booking or payment on the site.** The enquiry form opens the visitor's own
  e-mail or WhatsApp with the message ready; nothing is stored. `scripts/check.py` fails on a
  price, or on booking, reservation or payment wording (in the text, in labels and alt texts,
  and in the script's texts).
- **Legal pages stay current.** A change of address, tax status, tool or provider goes into
  `content/legal/` together with a new date in `content/site.json`.
- **The repository is public, the hotel library is not.** The material the partners sent, its
  searchable text and the permission register live outside the repository; `scripts/check.py`
  fails if one of those files is in it, or if a text file holds a Drive path, a local path or
  an e-mail address other than the site's own (the tests' made-up guests use `example.org`).

## Checks and deployment

`python scripts/check.py` (also in GitHub Actions on every pull request and push to `master`):
`_site/` is what the content gives (and carries `CNAME` and `.nojekyll`), every link, image and
anchor resolves, nothing loads from another host, every page has one `<h1>` and labelled form
fields, images are under 950 KB without metadata, partner photos are credited, the sitemap is
complete, every language version a page names exists, no text file holds a control character,
and nothing internal is in the repository. It warns about texts without a translation and
translations nothing uses.

`.github/workflows/site.yml` runs, on every pull request and every push to `master`: `ruff`,
`scripts/build.py`, `scripts/check.py` and `tests/run.py` (Chromium). A push to `master` that
passes is deployed to GitHub Pages from the built `_site/` (Pages source: GitHub Actions). The
domain comes from `content/site.json`; the build writes it into `_site/CNAME`.
