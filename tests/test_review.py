"""Browser checks for the review fixes: phone menu, full-screen view focus, enquiry errors and fallback, WhatsApp links,
map texts, no-script notes, titles. python -X utf8 test_review.py <repo root>"""
import functools
import http.server
import os
import sys
import threading
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import sync_playwright

ROOT = sys.argv[1]
fails = []


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


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL', 'chrome') or None, headless=True)
    errors = []

    # ---- phone menu: hidden by default, opens and closes, scrolls in landscape
    phone = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
    pg = phone.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(BASE + '/')
    check(not pg.is_visible('.site-nav'), 'phone: the menu is hidden at first')
    pg.click('.menu-toggle')
    check(pg.is_visible('.site-nav a[href="/destinations/"]'), 'phone: the menu opens')
    pg.click('.menu-toggle')
    check(not pg.is_visible('.site-nav'), 'phone: the menu closes')
    phone.close()
    land = browser.new_context(viewport={'width': 844, 'height': 390}, device_scale_factor=2)
    pl = land.new_page()
    pl.goto(BASE + '/')
    pl.click('.menu-toggle')
    box = pl.evaluate('(() => { const n = document.querySelector(".site-nav"); const r = n.getBoundingClientRect(); return [r.bottom, n.scrollHeight, n.clientHeight, window.innerHeight]; })()')
    check(box[0] <= box[3] + 1 and box[1] > box[2], f'landscape: the open menu fits the screen and scrolls ({box})')
    land.close()

    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))

    # ---- full-screen view: the focus stays when a button reaches the end; the arrows keep working
    pg.goto(BASE + '/stay/rote-wand/')
    pg.click('.gallery .photo-open >> nth=0')
    n = pg.evaluate('document.querySelectorAll(".lightbox-figure") ? parseInt(document.querySelector(".lightbox-count").textContent.split("/")[1]) : 0')
    pg.focus('.lightbox-next')
    for _ in range(n + 1):
        pg.keyboard.press('Enter')
    inside = pg.evaluate('document.activeElement && document.activeElement.closest(".lightbox") !== null')
    last = pg.evaluate('document.querySelector(".lightbox-count").textContent.trim()')
    check(inside, f'full screen: after reaching the last photo the focus stays in the view ({last})')
    check(pg.get_attribute('.lightbox-next', 'aria-disabled') == 'true', 'full screen: "Next" is marked aria-disabled at the end')
    pg.keyboard.press('ArrowLeft')
    before = pg.evaluate('document.querySelector(".lightbox-count").textContent.trim()')
    check(before != last, f'full screen: ArrowLeft still works at the end ({last} -> {before})')
    pg.keyboard.press('Escape')
    check(not pg.is_visible('.lightbox'), 'full screen: Escape closes')

    # ---- gallery buttons on the page
    pg.goto(BASE + '/stay/chalets-megeve/')
    check(pg.get_attribute('#chalet-141 [data-prev]', 'aria-disabled') == 'true', 'gallery: "Previous" starts aria-disabled, not disabled')
    pg.click('#chalet-141 [data-next]')
    pg.wait_for_timeout(900)
    check(pg.get_attribute('#chalet-141 [data-prev]', 'aria-disabled') == 'false', 'gallery: after "Next", "Previous" is live')

    # ---- enquiry: inline errors, focus, fallback and the page line
    pg.goto(BASE + '/es/enquire/?destination=lech')
    pg.click('#enquiry button[type=submit]')
    check(pg.get_attribute('#f-name', 'aria-invalid') == 'true' and pg.inner_text('#f-name-error').strip() == 'Por favor, ingresa tu nombre.',
          'enquiry: an empty name shows its error, in Spanish')
    check(pg.evaluate('document.activeElement.id') == 'f-name', 'enquiry: the focus goes to the first empty field')
    pg.fill('#f-name', 'Prueba')
    pg.fill('#f-email', 'no-es-un-mail')
    pg.click('#enquiry button[type=submit]')
    check(pg.get_attribute('#f-email', 'aria-invalid') == 'true' and 'válida' in pg.inner_text('#f-email-error'), 'enquiry: a bad e-mail shows its error')
    check(pg.get_attribute('#f-name', 'aria-invalid') == 'false', 'enquiry: the name is no longer flagged')
    pg.fill('#f-email', 'prueba@example.org')
    pg.evaluate('window.__opened = []; window.open = function (u) { window.__opened.push(u); return null; }')
    pg.click('#send-whatsapp')
    url = pg.evaluate('window.__opened.filter(Boolean)[0] || ""')
    text = unquote(parse_qs(urlparse(url).query).get('text', [''])[0])
    check('Página: /es/enquire/ (es)' in text, 'enquiry: the WhatsApp message says which page it comes from')
    check(pg.is_visible('.form-legend') and pg.locator('.req').count() == 2, 'enquiry: the two required fields are marked, with the legend')
    check(pg.locator('.optional').count() == 0, 'enquiry: no "(optional)" markers are left')
    # the e-mail fallback appears after the submit (the mailto: navigation is swallowed by the browser)
    pg.click('#enquiry button[type=submit]')
    pg.wait_for_timeout(500)
    check(pg.is_visible('#mail-fallback') and 'Prueba' in pg.input_value('#f-copy'), 'enquiry: the copy-and-paste fallback shows the message')
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE)
    pg.click('#copy-message')
    pg.wait_for_timeout(300)
    check(pg.inner_text('#copy-message').strip() == 'Mensaje copiado', 'enquiry: "Copy message" confirms')

    # ---- WhatsApp links of the band and the footer carry the page
    pg.goto(BASE + '/destinations/lech/')
    hrefs = pg.eval_on_selector_all('a[href^="https://wa.me/"]', 'els => els.map(e => e.href)')
    check(hrefs and all('text=' in h for h in hrefs) and all('%2Fdestinations%2Flech%2F' in h for h in hrefs), f'WhatsApp links name the page ({len(hrefs)} links)')

    # ---- the Spanish menu marks the pages that exist in English only
    pg.goto(BASE + '/es/')
    marks = pg.eval_on_selector_all('.site-nav a .lang-mark', 'els => els.map(e => e.closest("a").getAttribute("href"))')
    check(sorted(marks) == ['/about/', '/experiences/', '/stay/'], f'ES menu: EN marks on the English-only pages ({marks})')
    check(pg.locator('.site-nav a[href="/es/destinations/"] .lang-mark').count() == 0, 'ES menu: no mark on a translated page')

    # ---- map: texts in Spanish, focus on the map after loading
    outside = []
    pg.on('request', lambda r: outside.append(r.url) if not r.url.startswith((BASE, 'data:', 'blob:')) else None)
    pg.goto(BASE + '/es/destinations/')
    check(not outside, 'map: no request outside the site before the click')
    pg.click('#map-load')
    try:
        pg.wait_for_selector('.leaflet-control-zoom-in', timeout=8000)
    except Exception:
        pass
    titles = pg.evaluate('[".leaflet-control-zoom-in", ".leaflet-control-zoom-out"].map(s => (document.querySelector(s) || {}).title)')
    check(titles == ['Acercar', 'Alejar'], f'map: the zoom buttons are named in Spanish ({titles})')
    check(pg.evaluate('document.activeElement && document.activeElement.id') == 'map', 'map: the focus moves to the map')

    # ---- titles with intent, the Munich exception, robots
    pg.goto(BASE + '/destinations/lech/')
    check(pg.title() == 'Ski trips to Lech am Arlberg — EverFlow Experience', f'title: {pg.title()}')
    pg.goto(BASE + '/pt/destinations/munich/')
    check(pg.title() == 'Munique antes ou depois dos Alpes — EverFlow Experience', f'title Munich PT: {pg.title()}')
    h2s = pg.eval_on_selector_all('.qa-item h2', 'els => els.map(e => e.textContent)')
    check(h2s == ['Para quem é Munique', 'Quando visitar Munique', 'Como chegar a Munique'], f'PT headings name the place ({h2s})')
    r = pg.request.get(BASE + '/robots.txt')
    check('Disallow: /content/' in r.text() and 'Sitemap:' in r.text(), 'robots.txt keeps the source files out')
    check(not errors, f'no script errors ({errors[:2]})')

    # ---- without the script: the notes show, the buttons that need it are hidden, the menu is open
    nojs = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
    p2 = nojs.new_page()
    p2.goto(BASE + '/enquire/')
    check(p2.is_visible('form noscript, form noscript p') or 'needs JavaScript' in p2.inner_text('form'), 'no script: the form says it needs JavaScript')
    check(not p2.is_visible('#send-whatsapp'), 'no script: the send buttons are hidden')
    p2.goto(BASE + '/destinations/')
    check('needs JavaScript' in p2.inner_text('main') and not p2.is_visible('#map-load'), 'no script: the map note shows and the button is hidden')
    nojs.close()

    # ---- widths
    for w in (320, 360, 390, 768, 1024, 1280, 1440):
        c = browser.new_context(viewport={'width': w, 'height': 900})
        p3 = c.new_page()
        for path in ['/', '/es/', '/pt/', '/enquire/', '/es/enquire/', '/destinations/', '/destinations/lech/', '/stay/', '/stay/chalets-megeve/']:
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
