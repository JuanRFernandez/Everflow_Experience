# EverFlow Experience — Website

Static website for [everflowexperience.com](https://everflowexperience.com) — a boutique alpine experience company in the Bavarian Alps.
Served for free with **GitHub Pages**. No build step, no framework, no server: plain HTML/CSS/JS.

## Structure

```
├── index.html            # all content, markup & styling (single page, inline CSS)
├── CNAME                 # custom domain for GitHub Pages
├── .nojekyll             # serve files as-is (skip Jekyll)
├── assets/
│   ├── js/main.js        # destinations gallery, booking modal, forms, Leaflet map
│   ├── dest-*.jpg        # destination gallery images
│   ├── exp-*.jpg         # experience section images
│   ├── img/              # headshots, logos, hero title, poster frame, favicon
│   └── video/            # hero background video (web-optimized mp4)
└── README.md
```

External dependencies (CDN, no install needed): Google Fonts (Playfair Display, Public Sans, Poppins, Oswald, Montserrat) and [Leaflet 1.9.4](https://leafletjs.com) for the map. Everything else — content, images, styling, behavior — is served from this repo, so the page renders even if a CDN is blocked.

## Editing

- Texts, team bios, contact details, styling → edit `index.html` directly (CSS is in the `<style>` block at the top).
- Destinations list / booking form steps / WhatsApp numbers → `assets/js/main.js`.
- Forms have **no backend**: they open the visitor's WhatsApp or email app with a pre-written message.

Local preview: open `index.html` in a browser, or `python -m http.server` in the repo folder.
