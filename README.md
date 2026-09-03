# EverFlow Experience — Website

Static website for [everflowexperience.com](https://everflowexperience.com) — a boutique alpine experience company in the Bavarian Alps.
Served for free with **GitHub Pages**. No build step, no framework, no server: plain HTML/CSS/JS.

## Structure

```
├── index.html            # all content, markup & styling (single page, inline CSS)
├── impressum.html        # Impressum / imprint (§ 5 DDG) — legally required, linked in the footer
├── datenschutz.html      # Datenschutzerklärung / privacy policy (GDPR) — EN + DE, linked in footer + forms
├── CNAME                 # custom domain for GitHub Pages
├── .nojekyll             # serve files as-is (skip Jekyll)
├── assets/
│   ├── js/main.js        # destinations gallery, booking modal, forms, Leaflet map (click-to-load)
│   ├── fonts/            # self-hosted web fonts (woff2 + fonts.css, SIL OFL) — no Google Fonts request
│   ├── vendor/leaflet/   # self-hosted Leaflet 1.9.4 (BSD-2) — no CDN request
│   ├── dest-*.jpg        # destination gallery images
│   ├── exp-*.jpg         # experience section images
│   ├── img/              # headshots, logos, hero title, poster frame, favicon
│   └── video/            # hero background video (web-optimized mp4)
└── README.md
```

No CDN dependencies: fonts (Playfair Display, Public Sans, Poppins, Oswald, Montserrat) and [Leaflet 1.9.4](https://leafletjs.com) are served from this repo. The only third-party request is the map tiles (CARTO / OpenStreetMap), and only after the visitor clicks "Show map" — this keeps the site free of cookie banners and of the Google-Fonts/CDN privacy problem (LG München, 3 O 17493/20).

## Legal pages

`impressum.html` and `datenschutz.html` are required by German law (§ 5 DDG, GDPR). Keep them linked from the footer of every page and from the forms. When something changes — address, VAT ID, a new tool (analytics, newsletter, booking widget), a new hosting or email provider, the map provider — update both pages **and** the "Last updated" date. Partner-hotel photos need a photo credit where they appear (see Impressum → Urheberrecht und Bildnachweise).

## Editing

- Texts, team bios, contact details, styling → edit `index.html` directly (CSS is in the `<style>` block at the top).
- Destinations list / booking form steps / WhatsApp numbers → `assets/js/main.js`.
- Team photos: 1000×1000 JPG in `assets/img/`, same crop and alpine background as the existing headshots.
- Forms have **no backend**: they open the visitor's WhatsApp or email app with a pre-written message.

Local preview: open `index.html` in a browser, or `python -m http.server` in the repo folder.
