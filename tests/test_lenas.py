"""Browser tests for Las Leñas: map, Argentina block, gallery, stays filter, enquiry, languages, widths.
python -X utf8 test_lenas.py <repo root>"""
import functools
import http.server
import json
import os
import re
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = sys.argv[1]
fails = []
# Juan, 25.10.2026: the Las Leñas pages stay simple and low profile, nothing about him or his family
PERSONAL = re.compile(r"founder|fundador|family of our|family's own|familia de nuestro|família do nosso|Juan Rodrigo|grew up skiing|creció esquiando|"
                      r"cresceu esquiando|born in Mendoza|nació en Mendoza|nasceu em Mendoza|let by EverFlow|lets them|we let them|los alquila|aluga-os", re.I)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
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
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    errors, outside = [], []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('request', lambda r: outside.append(r.url) if not r.url.startswith((BASE, 'data:', 'blob:')) else None)

    # ---- /destinations/: the drawn map, the pins, the Argentina block
    pg.goto(BASE + '/destinations/')
    pins = json.loads(pg.get_attribute('[data-pins]', 'data-pins'))
    names = [p['n'] for p in pins]
    check('Las Leñas' not in names and len(names) == 15, f'the map pins: {len(names)}, without Las Leñas')
    check(pg.locator('.map-beyond a[href="/destinations/las-lenas/"]').count() == 1, 'below the map: "Not on this map: Las Leñas"')
    check(pg.locator('#argentina').count() == 1, 'an Argentina block')
    check(pg.locator('#argentina a[href="/destinations/las-lenas/"]').count() >= 1, 'the block links to Las Leñas')
    check(not PERSONAL.search(pg.inner_text('#argentina')), '/destinations/: the Argentina block says nothing personal')
    order = pg.eval_on_selector_all('section[id]', 'els => els.map(e => e.id)')
    countries = [x for x in order if x in ('switzerland', 'austria', 'france', 'italy', 'germany', 'argentina')]
    check(countries == ['switzerland', 'austria', 'france', 'italy', 'germany', 'argentina'], f'the countries in order: {countries}')
    svg_pins = pg.eval_on_selector_all('.static-map a, .map-static a, svg a', 'els => els.map(e => e.getAttribute("href") || e.getAttribute("xlink:href"))')
    check('/destinations/las-lenas/' not in svg_pins, 'the drawn map has no Las Leñas link')
    # the interactive map loads its pins when asked
    before_map = list(outside)  # the interactive map fetches its tiles once asked, never on load
    pg.click('#map-load')
    try:
        pg.wait_for_selector('.leaflet-marker-icon', timeout=8000)
    except Exception:
        pass
    markers = pg.eval_on_selector_all('.leaflet-marker-icon', 'els => els.map(e => e.title)')
    check(len(markers) == 15 and 'Las Leñas' not in markers, f'the interactive map shows {len(markers)} pins, without Las Leñas')
    outside[:] = before_map

    # ---- /destinations/las-lenas/
    pg.goto(BASE + '/destinations/las-lenas/')
    check(pg.locator('h1').inner_text().strip() == 'Las Leñas', 'the page head says Las Leñas')
    body = pg.inner_text('main')
    check('2,240 m' in body and not PERSONAL.search(body), 'the page describes the resort, nothing about the founder or his family (Juan, 25.10.2026)')
    pg.goto(BASE + '/')
    check(pg.locator('#destinations .lead a[href="/destinations/las-lenas/"]').count() == 1, 'the home lead links Las Leñas')
    pg.goto(BASE + '/destinations/las-lenas/')
    check('Close by' not in body, 'no "Close by." without places near')
    check(pg.locator('.gallery .gallery-item').count() == 4, 'a gallery of four photos')
    credits = pg.eval_on_selector_all('.gallery .credit', 'els => els.map(e => e.innerText)')
    check(len(credits) == 4 and all(c.startswith('©') for c in credits), f'every gallery photo has its credit ({credits})')
    lic = pg.eval_on_selector_all('.gallery .credit a', 'els => els.map(e => e.href)')
    check(any('creativecommons.org' in h for h in lic), 'the gallery credits link the licence')
    pg.click('.gallery .photo-open >> nth=0')
    check(pg.is_visible('.lightbox'), 'a photo opens full screen')
    check(not pg.is_visible('.lightbox-enquire'), 'no enquiry button on a destination photo')
    labels = pg.evaluate('[".lightbox-close", ".lightbox-prev", ".lightbox-next"].map(s => document.querySelector(s).getAttribute("aria-label"))')
    check(labels == ['Close', 'Previous photo', 'Next photo'], f'English page: the full-screen buttons in English ({labels})')
    pg.keyboard.press('ArrowRight')
    pg.keyboard.press('Escape')
    check(not pg.is_visible('.lightbox'), 'Escape closes it')
    pg.click('.gallery [data-next]')
    try:
        pg.wait_for_function("document.querySelector('.gallery .gallery-count').textContent.startsWith('02')", timeout=4000)
    except Exception:
        pass
    check(pg.locator('.gallery .gallery-count').inner_text().strip().startswith('02'),
          f"the gallery buttons move to the next photo ({pg.locator('.gallery .gallery-count').inner_text()})")
    more = pg.locator('a[href="/stay/?place=las-lenas"]')
    check(more.count() >= 1, 'a link to every stay in Las Leñas')
    check(pg.locator('#stay .card').count() == 1, 'one stay on the page: the apartments')
    facts = pg.inner_text('main').lower()  # innerText follows the labels' text-transform
    check('flights' in facts and 'from buenos aires to san rafael and mendoza, in winter' in facts, 'the flights fact')
    check('where chains must be carried in winter' in facts, 'chains must be carried, not fitted, all winter')
    check('nearest airport' not in facts, 'no "nearest airport" claim')

    # ---- /stay/?place=las-lenas
    pg.goto(BASE + '/stay/?place=las-lenas')
    vis = pg.eval_on_selector_all('#stay-grid > .card', 'els => els.filter(e => !e.hidden).map(e => e.dataset.place + " " + e.dataset.type)')
    check(vis == ['las-lenas apartment'], f'the filter shows the apartments only ({vis})')
    check(pg.inner_text('[data-filter-count]') == '1 stay', 'the count says 1 stay')
    group = pg.evaluate('(() => { const o = document.querySelector("[data-filter-place] option[value=las-lenas]"); return o && o.parentElement.label })()')
    check(group == 'Argentina', f'the place sits under Argentina in the select ({group})')
    href = pg.get_attribute('#stay-grid > .card:not([hidden]) .card-enquire', 'href')
    check(href == '/enquire/?destination=las-lenas&stay=apartments-las-lenas&type=apartment', f'the card button ({href})')
    pg.click('#stay-grid > .card:not([hidden]) .card-enquire')
    pg.wait_for_url('**/enquire/**')
    check(pg.input_value('#f-destination') == 'las-lenas' and pg.input_value('#f-stay') == 'apartments-las-lenas'
          and pg.input_value('#f-type') == 'apartment', 'the enquiry is pre-filled: Las Leñas, the apartments, apartment')

    # ---- the stay page
    pg.goto(BASE + '/stay/apartments-las-lenas/')
    check(pg.locator('h1').inner_text().strip() == 'Atenas Building', 'the stay page head')
    row = pg.eval_on_selector_all('main .ticks li', 'els => els.map(e => e.innerText)')
    body = pg.inner_text('main')
    check('four guests' in body and '50 m²' in body and 'provided by their owner' in body, 'the stay page says four guests, 50 m², provided by their owner')
    check(0 < len(row) <= 5 and not PERSONAL.search(body), f'the stay page is short and says nothing about the founder or his family ({len(row)} facts)')
    check('ground floor' not in body.lower() and 'ground-floor' not in body.lower(),
          'no "ground floor" on its own: most apartments have two levels inside (review of 25.10.2026)')
    pg.goto(BASE + '/guides/first-week-from-south-america/')
    check(not PERSONAL.search(pg.inner_text('main')), 'the guide from South America says nothing personal')
    pg.goto(BASE + '/destinations/las-lenas/')
    desc = pg.get_attribute('meta[name="description"]', 'content')
    check('hotels and chalets' not in desc and 'June to September' in desc, f'the Las Leñas description promises no hotels or chalets ({desc})')
    pg.goto(BASE + '/stay/apartments-las-lenas/')
    caps = pg.eval_on_selector_all('.gallery .credit', 'els => [...new Set(els.map(e => e.innerText.trim()))]')
    check(caps == ['Photo courtesy of the owner'], f'the photo credit is the courtesy line ({caps})')
    pg.click('.gallery .photo-open >> nth=0')
    check(pg.inner_text('.lightbox-enquire') == 'Enquire about this apartment', 'full screen: "Enquire about this apartment"')
    pg.keyboard.press('Escape')

    # ---- Spanish and Portuguese
    for lang, words, flights in (('es', ['2.240 m', 'obligatorio llevar cadenas'], 'Vuelos'),
                                 ('pt', ['2.240 m', 'obrigatório levar correntes', 'Ruta 222'], 'Voos')):
        pg.goto(f'{BASE}/{lang}/destinations/las-lenas/')
        t = pg.inner_text('main').lower()
        check(all(w.lower() in t for w in words) and flights.lower() in t and not PERSONAL.search(t), f'/{lang}/: the resort and the flights fact, nothing personal')
        pg.goto(f'{BASE}/{lang}/destinations/')
        check(not PERSONAL.search(pg.inner_text('#argentina')), f'/{lang}/destinations/: the Argentina block says nothing personal')
        pg.goto(f'{BASE}/{lang}/guides/first-week-from-south-america/')
        check(not PERSONAL.search(pg.inner_text('main')), f'/{lang}/: the guide from South America says nothing personal')
        pg.goto(f'{BASE}/{lang}/destinations/las-lenas/')
        check(pg.get_attribute('html', 'lang').startswith(lang), f'/{lang}/: the page language')
        pg.click('.gallery .photo-open >> nth=0')
        labels = pg.evaluate('[".lightbox-close", ".lightbox-prev", ".lightbox-next"].map(s => document.querySelector(s).getAttribute("aria-label"))')
        want = {'es': ['Cerrar', 'Foto anterior', 'Siguiente foto'], 'pt': ['Fechar', 'Foto anterior', 'Próxima foto']}[lang]
        check(labels == want, f'/{lang}/: the full-screen buttons are named in the page language ({labels})')
        pg.keyboard.press('Escape')
        pg.goto(f'{BASE}/{lang}/destinations/')
        check(pg.locator('#argentina').count() == 1 and pg.locator('.map-beyond').count() == 1, f'/{lang}/destinations/: the block and the note')
    check(not errors, f'no script errors ({errors[:2]})')
    check(not outside, f'no request outside the site ({outside[:3]})')

    # ---- widths
    pages = ['/destinations/', '/destinations/las-lenas/', '/es/destinations/las-lenas/', '/pt/destinations/las-lenas/',
             '/stay/apartments-las-lenas/', '/stay/?place=las-lenas', '/', '/about/']
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

httpd.shutdown()
print(f'{len(fails)} failures')
sys.exit(1 if fails else 0)
