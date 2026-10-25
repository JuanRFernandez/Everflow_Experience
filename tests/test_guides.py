"""Browser checks for the guides-es-pt branch: the guides in Spanish and Portuguese, the new guide, hreflang, sitemap,
links, the guide sections on the translated home and destination pages. python -X utf8 test_guides.py <repo root>"""
import functools
import http.server
import os
import re
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = sys.argv[1]
fails = []
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import build  # noqa: E402

NOT_SAID = re.compile(r'\breserv\w*|\b(?:pre|pré-?)?p[aá]g(?!in|od|an[aoi]|es?\b)\w*|\bcomisi(?:ón|ones)\b|\bcomiss(?:ão|ões)\b', re.I)
SLUGS = [g['slug'] for g in build.GUIDES]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass


httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=os.path.join(ROOT, '_site')))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{httpd.server_address[1]}'


def check(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond:
        fails.append(what)


# ---- files: every guide in three languages, in the sitemap, with hreflang; no forbidden words on the ES/PT pages
SITE = os.path.join(ROOT, '_site')
sitemap = open(os.path.join(SITE, 'sitemap.xml'), encoding='utf-8').read()
for slug in SLUGS + ['']:
    for prefix in ('', 'es/', 'pt/'):
        rel = f'{prefix}guides/{slug}/index.html' if slug else f'{prefix}guides/index.html'
        url = '/' + rel[:-len('index.html')]
        exists = os.path.isfile(os.path.join(SITE, rel))
        check(exists, f'{rel} exists')
        if not exists:
            continue
        text = open(os.path.join(SITE, rel), encoding='utf-8').read()
        check(f'<loc>https://everflowexperience.com{url}</loc>' in sitemap, f'{url} is in the sitemap')
        alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="https://everflowexperience\.com([^"]+)"', text)
        want = {('en', url.replace(f'/{prefix}', '/', 1) if prefix else url)}
        check(len(alts) == 4 and {h for h, _ in alts} == {'en', 'es', 'pt-BR', 'x-default'}, f'{rel}: hreflang for en, es, pt-BR and x-default ({[h for h, _ in alts]})')
        if prefix:
            check(not NOT_SAID.search(text.split('<main')[1]), f'{rel}: no reserva, pago or comisión')
            check(f'<html lang="{"es" if prefix == "es/" else "pt-BR"}">' in text, f'{rel}: the page language')
            check('/guides/' in text and f'href="/{prefix}guides/"' in text, f'{rel}: links to the guides in its language')
check(len(SLUGS) == 4 and 'first-week-from-south-america' in SLUGS, f'four guides, the new one among them ({SLUGS})')

# the FAQ link to the family guide is localized now
for prefix, want in (('', '/guides/ski-week-with-kids/'), ('es/', '/es/guides/ski-week-with-kids/'), ('pt/', '/pt/guides/ski-week-with-kids/')):
    home = open(os.path.join(SITE, prefix + 'index.html'), encoding='utf-8').read()
    check(f'href="{want}"' in home, f'/{prefix}: the FAQ links the family guide at {want}')
    check('id="guides"' in home, f'/{prefix}: the home shows the guides section')

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL', 'chrome') or None, headless=True)
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    errors, outside = [], []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('request', lambda r: outside.append(r.url) if not r.url.startswith((BASE, 'data:', 'blob:')) else None)

    # ---- the new guide in English
    pg.goto(BASE + '/guides/first-week-from-south-america/')
    check(pg.inner_text('h1').strip() == 'A first ski week in the Alps.', 'EN: the new guide\'s heading')
    check(pg.title() == 'Ski week in the Alps from Argentina and Brazil — EverFlow Experience', f'EN title: {pg.title()}')
    body = pg.inner_text('main')
    for s in ('non-stop flights from São Paulo to Zurich, Frankfurt and Munich', 'Buenos Aires to Frankfurt, Madrid and Rome', 'without a visa for stays of up to 90 days', 'ETIAS',
              'Travel insurance with winter-sports cover', 'only four hours, five from late March', 'outside the Easter weeks', 'we recommend it to every guest'):
        check(s in body, f'EN: says "{s}"')
    check(pg.locator('.card').count() >= 5 + 3, 'EN: five place cards and the other three guides')
    check(pg.locator('.breadcrumb a[href="/guides/"]').count() == 1, 'EN: breadcrumb to /guides/')
    h2s = pg.eval_on_selector_all('main h2', 'els => els.map(e => e.textContent)')
    check(h2s[:6] == ['When to come.', 'Getting there.', 'The papers.', 'What to bring.', 'Your first days.', 'Where we would go.'], f'EN headings ({h2s[:6]})')
    cta = pg.get_attribute('.cta .button', 'href')
    check(cta == '/enquire/?interest=ski-coaching', f'EN: the band leads to the enquiry with coaching ({cta})')

    # ---- Spanish and Portuguese
    for lang, h1, title, words, crumb, more in (
            ('es', 'Una primera semana de esquí en los Alpes.', 'Semana de esquí en los Alpes desde Argentina y Brasil — EverFlow Experience',
             ['vuelos directos desde São Paulo a Zúrich, Fráncfort y Múnich', 'sin visa', 'invierno austral', 'Los documentos.', 'Qué llevar.', 'Adónde iríamos.', 'salgas del espacio Schengen'], 'Guías', 'Más guías'),
            ('pt', 'Uma primeira semana de esqui nos Alpes.', 'Semana de esqui nos Alpes da Argentina e do Brasil — EverFlow Experience',
             ['voos diretos de São Paulo para Zurique, Frankfurt e Munique', 'sem visto', 'inverno do hemisfério sul', 'Os documentos.', 'O que levar.', 'Para onde iríamos.', 'contam com um guia', 'o instrutor certo'], 'Guias', 'Mais guias')):
        pg.goto(f'{BASE}/{lang}/guides/first-week-from-south-america/')
        check(pg.inner_text('h1').strip() == h1, f'/{lang}/: the heading "{h1}"')
        check(pg.title() == title, f'/{lang}/ title: {pg.title()}')
        body = pg.inner_text('main')
        for s in words:
            check(s in body, f'/{lang}/: says "{s}"')
        check(pg.inner_text('.breadcrumb li:first-child').strip() == crumb and pg.get_attribute('.breadcrumb a', 'href') == f'/{lang}/guides/', f'/{lang}/: breadcrumb "{crumb}" to /{lang}/guides/')
        check(more in pg.locator('#guides').evaluate('e => e.textContent'), f'/{lang}/: "{more}" section')
        links = pg.eval_on_selector_all('#guides a.card-link', 'els => els.map(e => e.getAttribute("href"))')
        check(links and all(x.startswith(f'/{lang}/guides/') for x in links), f'/{lang}/: the guide cards link to /{lang}/guides/ ({links})')
        place_links = pg.eval_on_selector_all('main .card a.card-link[href*="/destinations/"]', 'els => els.map(e => e.getAttribute("href"))')
        check(place_links and all(x.startswith(f'/{lang}/destinations/') for x in place_links), f'/{lang}/: the place cards link to /{lang}/destinations/')
        check(pg.get_attribute('.cta .button', 'href') == f'/{lang}/enquire/?interest=ski-coaching', f'/{lang}/: the band leads to the enquiry in {lang}')
        switch = pg.eval_on_selector_all('.lang-switch a', 'els => els.map(e => e.getAttribute("href"))')
        check(switch == ['/guides/first-week-from-south-america/', '/es/guides/first-week-from-south-america/', '/pt/guides/first-week-from-south-america/'], f'/{lang}/: the language switch keeps the guide ({switch})')
        pg.goto(f'{BASE}/{lang}/guides/')
        check(pg.locator('.card').count() == 4, f'/{lang}/guides/: four guide cards')
        check(pg.locator('h1').inner_text().strip() in ('Antes de planear.', 'Antes de planejar.'), f'/{lang}/guides/: the heading ({pg.locator("h1").inner_text()})')
        pg.goto(f'{BASE}/{lang}/guides/chalet-or-hotel/')
        body = pg.inner_text('main')
        check('5.400 m²' in body and '4.700 m²' in body and '3.000 m²' in body, f'/{lang}/guides/chalet-or-hotel/: the spa figures with a point')
        check(pg.locator('main .card').count() >= 6, f'/{lang}/guides/chalet-or-hotel/: the stay cards')
        pg.goto(f'{BASE}/{lang}/destinations/lech/')
        check(pg.locator('#guides .card').count() >= 2 and all(x.startswith(f'/{lang}/guides/') for x in pg.eval_on_selector_all('#guides a.card-link', 'els => els.map(e => e.getAttribute("href"))')),
              f'/{lang}/destinations/lech/: the guides section in {lang}')
        pg.goto(f'{BASE}/{lang}/')
        check(pg.locator('#guides .card').count() == 4, f'/{lang}/: four guide cards on the home')
        marks = pg.eval_on_selector_all('.site-nav a .lang-mark', 'els => els.map(e => e.closest("a").getAttribute("href"))')
        check(sorted(marks) == ['/about/', '/experiences/', '/stay/'], f'/{lang}/: EN marks unchanged ({marks})')
    pg.goto(BASE + '/guides/ski-week-with-kids/')
    check(pg.get_attribute('.breadcrumb a', 'href') == '/guides/' and pg.locator('.lang-switch a[href="/es/guides/ski-week-with-kids/"]').count() == 1, 'EN guide: breadcrumb and switch')
    check(not errors, f'no script errors ({errors[:2]})')
    check(not outside, f'no request outside the site ({outside[:3]})')

    # ---- widths
    for w in (320, 360, 390, 768, 1024, 1280, 1440):
        c = browser.new_context(viewport={'width': w, 'height': 900})
        p3 = c.new_page()
        for path in ['/guides/', '/es/guides/', '/pt/guides/', '/guides/first-week-from-south-america/', '/es/guides/first-week-from-south-america/',
                     '/pt/guides/first-week-from-south-america/', '/es/guides/chalet-or-hotel/', '/pt/guides/lech-or-st-moritz/', '/es/', '/pt/destinations/lech/']:
            p3.goto(BASE + path)
            over = p3.evaluate('document.documentElement.scrollWidth - window.innerWidth')
            if over > 0:
                check(False, f'{path} at {w}px scrolls sideways by {over}px')
        c.close()
    print('widths checked')
    browser.close()

httpd.shutdown()
print(f'{len(fails)} failures')
sys.exit(1 if fails else 0)
