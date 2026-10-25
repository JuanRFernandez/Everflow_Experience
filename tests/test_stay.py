"""Browser tests for "Where to stay": filters, enquiry links, lightbox button, widths. python tests/test_stay.py <repo root>"""
import functools
import http.server
import os
import sys
import threading
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import sync_playwright

ROOT = sys.argv[1]


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
fails = []


def check(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond:
        fails.append(what)


def visible_cards(pg):
    return pg.eval_on_selector_all('#stay-grid > .card', 'els => els.filter(e => !e.hidden).length')


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL', 'chrome') or None, headless=True)
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))

    # ---- filters
    pg.goto(BASE + '/stay/')
    total = pg.eval_on_selector_all('#stay-grid > .card', 'els => els.length')
    check(pg.is_visible('[data-stay-filters]'), 'filters are shown with the script')
    check(visible_cards(pg) == total, f'all {total} stays show at first')
    check(pg.inner_text('[data-filter-count]') == f'{total} stays', 'the count says every stay')
    check(pg.get_attribute('[data-filter-type=""]', 'aria-pressed') == 'true', '"All" is pressed')
    check(not pg.is_visible('[data-filter-clear]'), '"Clear filters" is hidden without a filter')
    check(pg.evaluate('document.querySelector("[data-filter-place]").selectedIndex') == 0, 'the select shows "All destinations"')

    pg.click('[data-filter-type="chalet"]')
    chalets = pg.eval_on_selector_all('#stay-grid > .card', 'els => els.filter(e => !e.hidden && e.dataset.type.split(" ").includes("chalet")).length')
    check(visible_cards(pg) == chalets and chalets > 0, f'"Chalets" shows only chalets ({chalets})')
    check('type=chalet' in pg.url, 'the address keeps the type')
    check(pg.get_attribute('[data-filter-type="chalet"]', 'aria-pressed') == 'true', '"Chalets" is pressed')
    check(pg.is_visible('[data-filter-clear]'), '"Clear filters" appears')

    pg.click('[data-filter-type="chalet"]')
    check('type=' not in pg.url and visible_cards(pg) == total, 'pressing the pressed "Chalets" again shows all')
    pg.click('[data-filter-type="chalet"]')
    pg.select_option('[data-filter-place]', 'megeve')
    n = visible_cards(pg)
    check(n == 20, f'chalets in Megève: {n} (20 expected)')
    check('place=megeve' in pg.url and 'type=chalet' in pg.url, 'the address keeps type and place')
    check(pg.inner_text('[data-filter-count]') == f'{n} stays', 'the count follows')

    pg.reload()
    check(visible_cards(pg) == 20 and pg.input_value('[data-filter-place]') == 'megeve'
          and pg.get_attribute('[data-filter-type="chalet"]', 'aria-pressed') == 'true', 'a reload keeps the filters')

    pg.goto(BASE + '/stay/?type=apartment')
    apts = visible_cards(pg)
    check(apts >= 2, f'"Apartments" shows apartments ({apts})')

    pg.goto(BASE + '/stay/?type=nonsense&place=atlantis')
    check(visible_cards(pg) == total and urlparse(pg.url).query == '', 'unknown values are dropped from the address')

    pg.goto('about:blank')  # a new load: a jump within the same page would not run the script again
    pg.goto(BASE + '/stay/#hotels')
    hotels = visible_cards(pg)
    check('type=hotel' in pg.url and '#hotels' not in pg.url and 0 < hotels < total, f'an old #hotels link shows the hotels ({hotels})')

    pg.goto(BASE + '/stay/?type=hotel&place=megeve')
    check(visible_cards(pg) == 0 and pg.is_visible('[data-filter-empty]'), 'no match: the empty note shows')
    href = pg.get_attribute('[data-filter-empty] a', 'href')
    check(href == '/enquire/?destination=megeve&type=hotel', f'the empty note leads to the enquiry with the filters ({href})')
    check(pg.inner_text('[data-filter-count]') == '0 stays', 'the count says 0 stays')

    # keyboard: Tab to "Hotels", Space; Clear by Enter returns the focus to "All"
    pg.goto(BASE + '/stay/')
    pg.focus('[data-filter-type=""]')
    pg.keyboard.press('Tab')
    pg.keyboard.press(' ')
    try:
        pg.wait_for_function("location.search.includes('type=hotel')", timeout=3000)
    except Exception:
        pass
    check('type=hotel' in pg.url, 'keyboard: Tab and Space choose "Hotels"')
    pg.focus('[data-filter-clear]')
    pg.keyboard.press('Enter')
    focused = pg.evaluate('document.activeElement.getAttribute("data-filter-type")')
    check(focused == '' and visible_cards(pg) == total, 'keyboard: "Clear filters" shows all and the focus goes to "All"')

    # the button lies above the card's link
    pg.goto(BASE + '/stay/?place=megeve')
    btn = pg.locator('#stay-grid > .card:not([hidden]) .card-enquire').first
    btn.click()
    pg.wait_for_url('**/enquire/**')
    check('/enquire/' in pg.url, 'a click on the card\'s button opens the enquiry, not the house')

    # ---- enquiry prefill and message
    pg.goto(BASE + '/stay/chalets-megeve/')
    link = pg.get_attribute('#chalet-cham-louka .card-enquire', 'href')
    pg.goto(BASE + link)
    check(pg.input_value('#f-destination') == 'megeve', 'prefill: destination')
    check(pg.input_value('#f-stay') == 'chalets-megeve', 'prefill: stay')
    check(pg.input_value('#f-type') == 'chalet', 'prefill: type')
    check(pg.input_value('#f-house') == "Chalet Cham Lou'Ka", f'prefill: house ({pg.input_value("#f-house")})')
    pg.fill('#f-name', 'Test Guest')
    pg.fill('#f-email', 'guest@example.org')
    pg.evaluate('window.__opened = []; window.open = function (u) { window.__opened.push(u); return null; }')
    pg.click('#send-whatsapp')
    url = pg.evaluate('window.__opened.filter(Boolean)[0] || ""')
    text = unquote(parse_qs(urlparse(url).query).get('text', [''])[0])
    check('Type of stay: Chalet' in text and "House: Chalet Cham Lou'Ka" in text, 'the WhatsApp message names the type and the house')
    check(text.index('Where to stay') < text.index('Type of stay') < text.index('House:'), 'the lines come in order')

    pg.goto(BASE + '/enquire/?destination=lech&stay=rote-wand&type=hotel&house=%3Cb%3Ex%3C%2Fb%3E')
    check(pg.input_value('#f-type') == 'hotel' and pg.input_value('#f-house') == '', 'an unknown house value is dropped (the house is a list now)')
    pg.goto(BASE + '/enquire/?type=castle')
    check(pg.input_value('#f-type') == '', 'an unknown type is ignored')

    # ---- lightbox button
    pg.goto(BASE + '/stay/chalets-megeve/')
    pg.click('#chalet-141 .photo-open >> nth=0')
    check(pg.is_visible('.lightbox-enquire'), 'the full-screen view shows the enquiry button')
    check(pg.inner_text('.lightbox-enquire') == 'Enquire about this chalet', 'its label names the chalet type')
    h = pg.get_attribute('.lightbox-enquire', 'href')
    check('house=Chalet%20141' in h and 'type=chalet' in h, f'it opens the enquiry for that house ({h})')
    pg.keyboard.press('Escape')
    pg.goto(BASE + '/stay/rote-wand/')
    pg.click('.gallery .photo-open >> nth=0')
    check(pg.inner_text('.lightbox-enquire') == 'Enquire about this hotel', 'on a hotel page it names the hotel')
    pg.keyboard.press('Escape')

    # focus on a house's photo strip rings the card
    pg.goto(BASE + '/stay/chalets-megeve/')
    pg.focus('#chalet-141 .gallery-track')
    ring = pg.evaluate('getComputedStyle(document.querySelector("#chalet-141")).outlineStyle')
    check(ring == 'solid', f"focus on the photos of a house rings the card ({ring})")
    # forced colours: the pressed type stands out
    fc = browser.new_context(viewport={'width': 1280, 'height': 900}, forced_colors='active')
    pf = fc.new_page()
    pf.goto(BASE + '/stay/?type=chalet')
    on = pf.evaluate('getComputedStyle(document.querySelector("[data-filter-type=chalet]")).backgroundColor')
    off = pf.evaluate('getComputedStyle(document.querySelector("[data-filter-type=hotel]")).backgroundColor')
    check(on != off, f'in forced colours the pressed type differs ({on} vs {off})')
    fc.close()
    check(not errors, f'no script errors ({errors[:2]})')

    # ---- without the script
    nojs = browser.new_context(java_script_enabled=False, viewport={'width': 1280, 'height': 900})
    p2 = nojs.new_page()
    p2.goto(BASE + '/stay/?type=chalet')
    check(not p2.is_visible('[data-stay-filters]'), 'without the script the filters stay hidden')
    check(p2.eval_on_selector_all('#stay-grid > .card', 'els => els.filter(e => e.offsetParent !== null).length') == total,
          'without the script every stay shows')
    nojs.close()

    # ---- widths
    pages = ['/', '/stay/', '/stay/chalets-megeve/', '/stay/pepper-collection/', '/stay/rote-wand/', '/stay/aurelio-lech/',
             '/enquire/', '/es/enquire/', '/pt/', '/destinations/lech/', '/es/destinations/lech/']
    for w in (320, 360, 390, 768, 1024, 1280, 1440):
        c = browser.new_context(viewport={'width': w, 'height': 900})
        p3 = c.new_page()
        for path in pages:
            p3.goto(BASE + path)
            over = p3.evaluate('document.documentElement.scrollWidth - window.innerWidth')
            if over > 0:
                check(False, f'{path} at {w}px scrolls sideways by {over}px')
        c.close()
    print('widths checked')
    browser.close()

print(f'{len(fails)} failures')
sys.exit(1 if fails else 0)
