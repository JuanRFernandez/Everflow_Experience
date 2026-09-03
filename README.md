# EverFlow Experience — Website

Static website for [everflowexperience.com](https://everflowexperience.com) — a boutique alpine experience company in the Bavarian Alps.
Served with **GitHub Pages** from the `master` branch. No build step, no framework, no server: plain HTML, CSS and JavaScript.

`master` is the live site. Change it only through a pull request; the checks below run on every PR.

## Structure

```
├── index.html                 # home page (single page)
├── impressum.html             # Impressum / imprint (§ 5 DDG), linked in the footer of every page
├── datenschutz.html           # Datenschutzerklärung / privacy policy (GDPR), EN + DE, linked in footer + forms
├── CNAME                      # custom domain for GitHub Pages
├── .nojekyll                  # serve files as-is (skip Jekyll)
├── assets/
│   ├── css/
│   │   ├── site.css           # home page styles
│   │   ├── legal.css          # rules shared by Impressum + Datenschutz
│   │   ├── impressum.css      # Impressum-only rules (loaded after legal.css)
│   │   └── datenschutz.css    # Datenschutz-only rules (loaded after legal.css)
│   ├── js/main.js             # destinations gallery, booking modal, forms, Leaflet map (click-to-load)
│   ├── fonts/                 # self-hosted web fonts (woff2 + fonts.css, SIL OFL) — no Google Fonts request
│   ├── vendor/leaflet/        # self-hosted Leaflet 1.9.4 (BSD-2) — no CDN request
│   ├── img/
│   │   ├── brand/             # EverFlow mark (favicon + logo) and wordmark (hero title)
│   │   ├── badges/            # credentials shown on the site (Profi Ski)
│   │   ├── team/              # headshots, one file per person
│   │   ├── destinations/      # destination gallery images
│   │   ├── experiences/       # experience section images
│   │   └── ui/                # interface graphics (map placeholder)
│   ├── video/                 # hero background video (web-optimized mp4) + its poster frame
│   └── stays/                 # per-hotel material published with the hotel's written permission (see below)
├── scripts/check.py           # site checks (also run in CI)
└── .github/workflows/check.yml
```

## Rules the site follows

- **Zero third-party requests on page load.** Fonts and Leaflet are served from this repo; the only external request is the map tiles (CARTO / OpenStreetMap), and only after the visitor clicks "Show map". This keeps the site free of cookie banners and of the Google-Fonts/CDN privacy problem (LG München I, 3 O 17493/20). `scripts/check.py` fails if a `<link>` or `<script>` points to another host.
- **Legal pages stay linked and current.** When something changes — address, VAT ID, a new tool (analytics, newsletter, booking widget), a hosting or email provider, the map provider — update `impressum.html` and `datenschutz.html` **and** their "Last updated" date.
- **Hotel material only with written permission.** Photos of hotels we book for guests go under `assets/img/` with the hotel's exact credit line in the caption and an entry in the Impressum (Urheberrecht und Bildnachweise). Brochures go under `assets/stays/<hotel>/`, unmodified, only after the hotel has confirmed in writing that we may host them. Room overviews, rate sheets and other internal hotel documents never go into this repository (`assets/Hotels/` is git-ignored for that reason).
- **No prices, no booking or payment on the site.** Forms open the visitor's email or WhatsApp app with a pre-written message.

## Editing

- Texts, team bios, contact details → the HTML pages. Home-page styling → `assets/css/site.css`; legal pages → `assets/css/legal.css` plus the page's own file.
- Destinations list, booking form steps, WhatsApp numbers, map pins → `assets/js/main.js`.
- Team photos: 1000×1000 JPG in `assets/img/team/`, same crop and alpine background as the existing headshots.
- Line endings are LF everywhere (`.gitattributes`); editors pick up `.editorconfig`.

## Checks

```
python scripts/check.py
```

Verifies that every local link and asset resolves, that no page loads anything from a third-party host, that HTML tags are balanced, and lists unreferenced assets. The same script runs in GitHub Actions on every pull request and on every push to `master`.

Local preview: open `index.html` in a browser, or run `python -m http.server` in the repo folder.
