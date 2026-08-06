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
│   ├── img/              # images (see TODO below)
│   └── video/            # hero background video (see TODO below)
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

Push to `main` → GitHub Pages redeploys automatically (Settings → Pages → Deploy from branch `main`).

## TODO — localize assets

Media files still load from the old WordPress site. Before that hosting is cancelled, download these and place them here, then swap the URLs in `index.html`:

| WordPress file | Target path |
|---|---|
| `/wp-content/uploads/2025/11/a-drone-shooting-over-zugspitze...utc.mov` | `assets/video/zugspitze-drone.mp4` (convert `.mov` → `.mp4`) |
| `/wp-content/uploads/2025/11/02-2048x2048.png` (EVER FLOW title) | `assets/img/everflow-title.png` |
| `/wp-content/uploads/2025/05/cropped-FAVICON-03.png` (nav logo) | `assets/img/logo.png` |
| `/wp-content/uploads/2025/05/cropped-FAVICON-02-270x270.png` (favicon) | `assets/img/favicon.png` |
| `/wp-content/uploads/2026/07/juan_headshot-1.jpg` | `assets/img/juan.jpg` |
| `/wp-content/uploads/2026/07/gregorio_headshot.jpg` | `assets/img/gregorio.jpg` |
| `/wp-content/uploads/2026/07/jeremy_headshot.jpg` | `assets/img/jeremy.jpg` |
| `/wp-content/uploads/2026/07/paolo_headshot.jpg` | `assets/img/paolo.jpg` |
| `/wp-content/uploads/2026/07/felipe_headshot.jpg` | `assets/img/felipe.jpg` |
| `/wp-content/uploads/2025/12/Profi_Ski_weiss_blau...1024x589.jpg` | `assets/img/profi-ski.jpg` |

## Credits

Design ported 1:1 from the original WordPress/Elementor site. © Ever Flow.
