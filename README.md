# EverFlow Experience — Website

Static website for [everflowexperience.com](https://everflowexperience.com) — a boutique ski school in the Bavarian Alps.
Served for free with **GitHub Pages**. No build step, no framework, no server: plain HTML/CSS/JS.

Live at: https://juanrfernandez.github.io/Everflow_Experience/ (custom domain `everflowexperience.com` will be connected via Cloudflare DNS).

## Structure

```
├── index.html            # all content & markup (single page)
├── assets/
│   ├── css/styles.css    # all styling
│   ├── js/main.js        # menu, Book-Now modal, forms, Leaflet map
│   ├── img/              # images (headshots, logos, hero title, poster frame)
│   └── video/            # hero background video (web-optimized mp4)
└── README.md
```

External dependencies (CDN, no install needed): Google Fonts (Playfair Display, Public Sans, Poppins, Oswald, Montserrat) and [Leaflet 1.9.4](https://leafletjs.com) for the map.

## Editing

- Texts, team bios, contact details → edit `index.html` directly.
- Colors & typography → `assets/css/styles.css` (`:root` variables at the top; gold is `#bbac79 → #a89960`).
- Booking form steps / WhatsApp numbers → `assets/js/main.js`.
- Forms have **no backend**: they open the visitor's WhatsApp or email app with a pre-written message.

Local preview: open `index.html` in a browser, or `python -m http.server` in the repo folder.

## Deploying

Push to `master` → GitHub Pages redeploys automatically (Settings → Pages → Deploy from branch `master`, folder `/`).

## Assets

All media is local — zero dependencies on the old WordPress hosting. The hero video is a web-optimized mp4 (`assets/video/hero.mp4`, converted from the original 53 MB `.mov`; raw `.mov`/`.zip` files are gitignored). `assets/img/hero-poster.jpg` is the first video frame, shown while the video loads.

## Credits

Design ported 1:1 from the original WordPress/Elementor site. © Ever Flow.
