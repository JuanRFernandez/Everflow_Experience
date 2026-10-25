"""Browser checks for the enquiry-links branch: the linked enquiry form (destination, stay, type, house) in EN, ES and PT,
the stay labels, Atenas Building, Interalpen 5,400 m², the FAQ, the hero note, experiences without a status, the SVG
wordmark, members without a photo and the guests' words. python -X utf8 test_enquiry.py <repo root>"""
import functools
import http.server
import json
import os
import re
import sys
import threading
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import sync_playwright

ROOT = sys.argv[1]
fails = []
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import build  # noqa: E402

PARTNERS = build.PARTNERS
HOTELS = [p['slug'] for p in PARTNERS if 'hotel' in build.stay_types(p)]
HOUSES = [r['name'] for p in PARTNERS for r in p.get('residences', [])]
NOT_SAID = re.compile(r'\breserv\w*|\b(?:pre|pré-?)?p[aá]g(?!in|od|an[aoi]|es?\b)\w*|\bcomisi(?:ón|ones)\b|\bcomiss(?:ão|ões)\b', re.I)  # as scripts/check.py


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


# ---------------------------------------------------------------- Python-level: rendering with content the site does not have yet
sample = {'quote': 'A week we still talk about.', 'name': 'Marina', 'country': 'Brazil', 'trip': 'A family week in Megève', 'season': 'February 2026'}
build.LANG = 'en'
build.PAGES['testimonials'] = [sample]
home = build.home()
enq = build.enquire_page()
check('id="guests"' in home and 'A week we still talk about.' in home and 'Marina, Brazil · A family week in Megève, February 2026' in home,
      'with a testimonial, the home shows the guests\' section with the quote and the attribution')
check(home.index('id="team"') < home.index('id="guests"') < home.index('id="guides"'), 'the guests\' section sits between the team and the guides')
check('quote--aside' in enq and 'Marina, Brazil</figcaption>' in enq, 'the enquiry aside shows the first quote with name and country only')
build.PAGES['testimonials'] = []
check('id="guests"' not in build.home() and 'quote--aside' not in build.enquire_page(), 'without testimonials nothing of it is rendered')
photo = build.TEAM[1].pop('photo')
about = build.about_page()
check('member member--text' in about and about.count('class="portrait"') == len(build.TEAM) - 1, 'a member without a photo: no <img>, the text takes the row')
build.TEAM[1]['photo'] = photo
juan_photo = build.TEAM[0].pop('photo')
h2 = build.home()
check('class="wrap">' in h2.split('id="team"')[1][:60] and 'split-media' not in h2.split('id="team"')[1].split('</section>')[0],
      'home: without the founder\'s photo the team section has no empty media column')
check('member--lead member--text' in build.about_page(), 'about: the founder without a photo gets the text layout')
build.TEAM[0]['photo'] = juan_photo
try:
    build.PAGES['testimonials'] = [{'quote': 'x', 'name': 'Y'}]
    build.validate()
    check(False, 'validate accepts a testimonial without country, trip and season')
except build.BuildError as err:
    check('country' in str(err) and 'season' in str(err), 'validate names the missing fields of a testimonial')
build.PAGES['testimonials'] = []
build.validate()
data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', build.home(), re.S).group(1))
check(data.get('founder', {}).get('name') == 'Juan Rodrigo Fernandez' and data.get('knowsLanguage') == ['en', 'es', 'pt', 'de'], 'JSON-LD names the founder and the four languages')

for lang in ('es', 'pt'):
    for name in ('index.html', 'destinations/lech/index.html', 'destinations/las-lenas/index.html'):
        text = open(os.path.join(ROOT, '_site', lang, name), encoding='utf-8').read()
        check(not NOT_SAID.search(text.split('<main')[1]), f'/{lang}/{name}: no reserva, pago or comisión')


def opts(pg, sel):
    return pg.eval_on_selector_all(f'{sel} option', 'els => els.map(o => o.value).filter(Boolean)')


def texts(pg, sel):
    return pg.eval_on_selector_all(f'{sel} option', 'els => els.map(o => o.textContent)')


def val(pg, sel):
    return pg.input_value(sel)


def house_hidden(pg):
    return pg.evaluate('document.querySelector("#f-house").closest(".field").hidden')


def whatsapp_text(pg):
    pg.fill('#f-name', 'Test Guest')
    pg.fill('#f-email', 'guest@example.org')
    pg.evaluate('window.__opened = []; window.open = function (u) { window.__opened.push(u); return null; }')
    pg.click('#send-whatsapp')
    url = pg.evaluate('window.__opened.filter(Boolean)[0] || ""')
    return unquote(parse_qs(urlparse(url).query).get('text', [''])[0])


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL', 'chrome') or None, headless=True)
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))

    # 1. fresh
    pg.goto(BASE + '/enquire/')
    check(len(opts(pg, '#f-destination')) == len(build.PLACES), f'fresh: every destination ({len(build.PLACES)})')
    check(len(opts(pg, '#f-stay')) == len(PARTNERS), f'fresh: every stay ({len(PARTNERS)})')
    check(house_hidden(pg), 'fresh: the House field is hidden')
    check(opts(pg, '#f-type') == ['hotel', 'chalet', 'apartment'], 'fresh: the three types')
    labels = texts(pg, '#f-stay')
    for want in ('Kempinski Palace Engelberg', 'Chalets in Megève', 'Alpin Resort Sacher Seefeld', 'Hotel Vier Jahreszeiten Kempinski München',
                 'rocksresort, Laax', 'Rote Wand Gourmet Hotel, Lech am Arlberg', 'Interalpen-Hotel Tyrol, Seefeld in Tirol', 'Atenas Building, Las Leñas',
                 'pepper-collection, Lech am Arlberg', 'Hotel & Chalet Aurelio, Lech am Arlberg'):
        check(want in labels, f'label: "{want}"')
    check(not any(x.count('Engelberg') > 1 or x.count('Seefeld') > 1 or x.count('München') > 1 or x.count('Megève') > 1 for x in labels), 'no label repeats its place')

    # 2. destination -> stays
    pg.select_option('#f-destination', 'lech')
    check(opts(pg, '#f-stay') == ['pepper-collection', 'aurelio-lech', 'rote-wand'], f'lech: the three stays ({opts(pg, "#f-stay")})')
    pg.select_option('#f-destination', 'zermatt')
    check(texts(pg, '#f-stay') == ['No preference'], 'zermatt: only "No preference"')
    pg.select_option('#f-destination', 'seefeld')
    check(texts(pg, '#f-stay') == ['No preference', 'Alpin Resort Sacher Seefeld', 'Interalpen-Hotel Tyrol, Seefeld in Tirol'], f'seefeld: {texts(pg, "#f-stay")}')

    # 3. stay -> destination, houses
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-stay', 'chalets-megeve')
    check(val(pg, '#f-destination') == 'megeve', 'chalets-megeve: the destination becomes Megève')
    check(not house_hidden(pg) and len(opts(pg, '#f-house')) == 22, f'chalets-megeve: the House list shows the 22 houses ({len(opts(pg, "#f-house"))})')
    check(val(pg, '#f-type') == '', 'chalets-megeve (chalets and apartments): the type stays open')
    check(pg.eval_on_selector_all('#f-house optgroup', 'els => els.map(e => e.label)') == ['Chalets in Megève'], 'the houses are grouped under their collection')

    # 4. + type; the Type list offers only what is in reach
    check(opts(pg, '#f-type') == ['chalet', 'apartment'], f'chalets-megeve: the Type list offers chalet and apartment only ({opts(pg, "#f-type")})')
    pg.select_option('#f-type', 'apartment')
    check(opts(pg, '#f-house') == ['Lodge Elan', 'Lodge Manou'] and val(pg, '#f-stay') == 'chalets-megeve', 'apartment: the two lodges, the stay kept')
    pg.select_option('#f-destination', 'seefeld')
    check(val(pg, '#f-stay') == '' and house_hidden(pg) and val(pg, '#f-type') == '' and opts(pg, '#f-type') == ['hotel'],
          'Seefeld after that: the stay goes, the House field hides, apartment is no longer offered, only hotel')
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-destination', 'megeve')
    check(opts(pg, '#f-type') == ['chalet', 'apartment'] and texts(pg, '#f-type')[0] == 'Not sure yet', 'Megève: no hotel in the Type list, "Not sure yet" stays')
    pg.select_option('#f-destination', 'laax')
    check(opts(pg, '#f-type') == ['apartment'] and opts(pg, '#f-stay') == ['rocksresort-laax'], 'Laax: only apartment and rocksresort')
    pg.select_option('#f-stay', 'rocksresort-laax')
    check(val(pg, '#f-type') == 'apartment' and opts(pg, '#f-type') == ['apartment'], 'rocksresort: the type is apartment and nothing else is offered')
    pg.select_option('#f-destination', 'zermatt')
    check(opts(pg, '#f-type') == ['hotel', 'chalet', 'apartment'] and val(pg, '#f-type') == '', 'Zermatt (no listed stay): all three types, the stay\'s type let go')
    pg.select_option('#f-destination', 'lech')
    check(opts(pg, '#f-type') == ['hotel', 'chalet', 'apartment'], 'Lech: all three types')

    # 5. type -> stays; a hotel sets its type softly
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-type', 'hotel')
    check(sorted(opts(pg, '#f-stay')) == sorted(HOTELS), f'hotel: the {len(HOTELS)} hotels')
    pg.select_option('#f-stay', 'rote-wand')
    check(val(pg, '#f-destination') == 'lech' and val(pg, '#f-type') == 'hotel', 'rote-wand: destination Lech, type Hotel')
    check(sorted(opts(pg, '#f-stay')) == sorted(HOTELS), f'choosing a stay leaves its list as it was: the {len(HOTELS)} hotels ({len(opts(pg, "#f-stay"))})')
    pg.select_option('#f-destination', 'lech')
    check(opts(pg, '#f-stay') == ['aurelio-lech', 'rote-wand'] and val(pg, '#f-stay') == 'rote-wand', f'a type the visitor chose keeps narrowing the stays ({opts(pg, "#f-stay")})')
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-stay', 'rote-wand')
    check(val(pg, '#f-type') == 'hotel' and len(opts(pg, '#f-stay')) == len(PARTNERS),
          'rote-wand from a fresh form: the type shows Hotel, every stay stays listed')
    pg.select_option('#f-type', 'hotel')
    check(sorted(opts(pg, '#f-stay')) == sorted([s for s in HOTELS if build.PARTNER[s]['place'] == 'lech']) and val(pg, '#f-stay') == 'rote-wand',
          'then choosing Hotel oneself narrows the list to the hotels of Lech')
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-stay', 'rote-wand')
    pg.select_option('#f-stay', 'interalpen-tyrol')
    check(val(pg, '#f-destination') == 'seefeld' and val(pg, '#f-type') == 'hotel', 'another stay straight after: the destination follows (Seefeld)')
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-stay', 'rote-wand')
    pg.select_option('#f-stay', 'aurelio-lech')
    check(val(pg, '#f-type') == '' and opts(pg, '#f-type') == ['hotel', 'chalet'], 'aurelio (hotel and chalet): the type the script had set is cleared, two types offered')
    pg.select_option('#f-stay', 'rote-wand')
    pg.select_option('#f-stay', '')
    check(val(pg, '#f-type') == '' and val(pg, '#f-destination') == 'lech', '"No preference" again: the type the script had set goes, the destination stays')
    pg.select_option('#f-stay', 'rote-wand')
    pg.select_option('#f-destination', 'seefeld')
    check(val(pg, '#f-stay') == '' and val(pg, '#f-type') == '', 'another destination drops the stay and the type it had set')

    # 6. pepper-collection
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-stay', 'pepper-collection')
    pg.select_option('#f-house', 'ULA Signature')
    pg.select_option('#f-type', 'chalet')
    check(val(pg, '#f-house') == '' and opts(pg, '#f-house') == ['Chalet Mimi', 'The Barn', 'The Falcon', 'Arla Luxury Home', 'Chalet Toda', 'Skyfall'],
          f'ULA Signature + chalet: the house goes, six chalets stay ({opts(pg, "#f-house")})')
    pg.select_option('#f-house', 'Skyfall')
    pg.select_option('#f-type', 'apartment')
    check(val(pg, '#f-house') == 'Skyfall' and opts(pg, '#f-house') == ['Skyfall', 'ULA Signature', 'ULA Easy Stay'], 'Skyfall (chalet and apartments) survives both types')
    pg.select_option('#f-type', 'chalet')
    check(val(pg, '#f-house') == 'Skyfall', 'Skyfall survives the chalet type too')

    # 7. another destination after a house
    pg.goto(BASE + '/enquire/')
    pg.select_option('#f-stay', 'chalets-megeve')
    pg.select_option('#f-house', 'Chalet 141')
    pg.select_option('#f-destination', 'lech')
    check(val(pg, '#f-stay') == '' and val(pg, '#f-house') == '' and house_hidden(pg), 'Lech after Chalet 141: stay and house go, the field hides')

    # 8. the real link of a house
    pg.goto(BASE + '/stay/chalets-megeve/')
    link = pg.get_attribute('#chalet-cham-louka .card-enquire', 'href')
    pg.goto(BASE + link)
    check(val(pg, '#f-destination') == 'megeve' and val(pg, '#f-stay') == 'chalets-megeve' and val(pg, '#f-type') == 'chalet'
          and val(pg, '#f-house') == "Chalet Cham Lou'Ka", f'the link of Chalet Cham Lou\'Ka fills the four fields ({link})')
    check(len(opts(pg, '#f-house')) == 20, 'the House list shows the 20 chalets (type chalet)')
    text = whatsapp_text(pg)
    check("House: Chalet Cham Lou'Ka" in text and 'Where to stay: Chalets in Megève\n' in text and 'Type of stay: Chalet' in text and 'Destination: Megève' in text,
          'the WhatsApp message names house, stay (without the place twice), type and destination')
    check(', Megève' not in text, 'no ", Megève" after the stay')

    # 9. an unknown house
    pg.goto(BASE + '/enquire/?destination=megeve&stay=chalets-megeve&house=Chalet%20Nowhere')
    check(val(pg, '#f-house') == '' and not house_hidden(pg) and len(opts(pg, '#f-house')) == 22, 'an unknown house is dropped; the list of the stay shows')

    # 10. conflicts in the link
    pg.goto(BASE + '/enquire/?destination=lech&stay=chalets-megeve')
    check(val(pg, '#f-destination') == 'megeve' and val(pg, '#f-stay') == 'chalets-megeve', 'destination lech + stay chalets-megeve: the stay wins, Megève')
    pg.goto(BASE + '/enquire/?type=hotel&stay=chalets-megeve')
    check(val(pg, '#f-type') == '' and val(pg, '#f-stay') == 'chalets-megeve', 'type hotel + stay chalets-megeve: the type the stay lacks goes')
    pg.goto(BASE + '/enquire/?destination=lech&type=chalet')
    check(opts(pg, '#f-stay') == ['pepper-collection', 'aurelio-lech'] and val(pg, '#f-type') == 'chalet', 'lech + chalet: the two stays with chalets')
    pg.goto(BASE + '/enquire/?type=castle&house=x')
    check(val(pg, '#f-type') == '' and val(pg, '#f-house') == '' and house_hidden(pg), 'unknown values are ignored')

    # 11. a hotel link: no House line
    pg.goto(BASE + '/enquire/?stay=rote-wand')
    text = whatsapp_text(pg)
    check('House:' not in text and 'Type of stay: Hotel' in text and 'Destination: Lech am Arlberg' in text and 'Where to stay: Rote Wand Gourmet Hotel, Lech am Arlberg' in text,
          'rote-wand: no House line; type, destination and stay named')

    # 12. the Type field takes the row when House is hidden; the status line says when the list comes and goes
    pg.goto(BASE + '/enquire/')
    row = pg.evaluate('document.querySelector("#f-type").closest(".field-row").getBoundingClientRect().width')
    field = pg.evaluate('document.querySelector("#f-type").closest(".field").getBoundingClientRect().width')
    check(abs(row - field) < 2, f'House hidden: the Type field fills the row ({field:.0f} of {row:.0f}px)')
    check(pg.inner_text('#form-status').strip() == '', 'fresh: the status line is empty')
    pg.select_option('#f-stay', 'chalets-megeve')
    field2 = pg.evaluate('document.querySelector("#f-type").closest(".field").getBoundingClientRect().width')
    check(field2 < row * 0.6, f'House shown: two columns ({field2:.0f} of {row:.0f}px)')
    check(pg.inner_text('#form-status').strip() == 'House: 22 houses of this stay to choose from.', f'the status line announces the houses ({pg.inner_text("#form-status")})')
    pg.select_option('#f-stay', 'rote-wand')
    check(pg.inner_text('#form-status').strip() == 'House: this stay has no separate houses.', f'the status line announces that the list went ({pg.inner_text("#form-status")})')
    pg.goto(BASE + '/enquire/?stay=nowhere&destination=lech&type=chalet')
    check(opts(pg, '#f-stay') == ['pepper-collection', 'aurelio-lech'], 'an unknown stay in the link: destination and type still narrow the list')

    # 13. Atenas Building, Interalpen, FAQ, hero note, experiences, logo (English)
    pg.goto(BASE + '/stay/apartments-las-lenas/')
    check(pg.inner_text('h1').strip() == 'Atenas Building', 'the stay page is "Atenas Building"')
    check('Edificio' not in pg.inner_text('main'), 'no "Edificio" on the English page')
    pg.goto(BASE + '/stay/interalpen-tyrol/')
    body = pg.inner_text('main')
    check('5,400 m²' in body and '5,300' not in body, 'Interalpen: more than 5,400 m²')
    pg.goto(BASE + '/guides/chalet-or-hotel/')
    check('5,400 m²' in pg.inner_text('main'), 'the guide says 5,400 m² too')
    pg.goto(BASE + '/')
    check(pg.locator('.faq-item').count() == 13, f'home: 13 questions ({pg.locator(".faq-item").count()})')
    qs = pg.eval_on_selector_all('.faq-item summary', 'els => els.map(e => e.textContent)')
    check('How fast do you answer?' in qs and 'Why plan the stay through you rather than directly with the hotel?' in qs, 'the new questions are there')
    check('A first proposal within 24 hours' in pg.locator('#faq').evaluate('e => e.textContent'), 'the FAQ promises a first proposal within 24 hours')
    check(pg.inner_text('.hero-note').startswith('Hosted by Juan Rodrigo Fernandez, former Argentinian Ski Team.'), 'the hero note')
    check('By request' not in pg.inner_text('main') and 'Available now' not in pg.inner_text('main'), 'home: no "By request"')
    logo = pg.evaluate('(() => { const i = document.querySelector(".brand img"); return [i.getAttribute("src"), i.naturalWidth > 0, i.getBoundingClientRect().height]; })()')
    check(logo[0] == '/assets/img/brand/wordmark-ink.svg' and logo[1] and 40 < logo[2] < 44, f'the header wordmark is the SVG and renders ({logo})')
    flogo = pg.evaluate('(() => { const i = document.querySelector(".footer-brand img"); return [i.getAttribute("src"), i.naturalWidth > 0]; })()')
    check(flogo == ['/assets/img/brand/wordmark-white.svg', True], f'the footer wordmark is the white SVG ({flogo})')
    check(pg.locator('#guests').count() == 0, 'no guests\' section while there are no testimonials')
    marks = pg.evaluate('''() => { const f = document.createElement("figure"); f.className = "quote"; f.innerHTML = "<blockquote><p>x</p></blockquote>";
        document.body.appendChild(f); const p = f.querySelector("p");
        return [getComputedStyle(p, "::before").content, getComputedStyle(p, "::after").content]; }''')
    check(marks == ['"“"', '"”"'], f'a quote gets curly quotation marks from the stylesheet ({marks})')
    forced = browser.new_context(viewport={'width': 1280, 'height': 900}, forced_colors='active')
    pf = forced.new_page()
    pf.goto(BASE + '/')
    plates = pf.evaluate('[".brand img", ".footer-brand img"].map(s => getComputedStyle(document.querySelector(s)).backgroundColor)')
    check(plates == ['rgb(244, 240, 232)', 'rgb(23, 20, 15)'], f'forced colours: the wordmarks keep their plates ({plates})')
    forced.close()
    pg.goto(BASE + '/experiences/')
    check('By request' not in pg.inner_text('main') and pg.locator('.feature-meta .step-num').count() == 8, 'experiences: the numbers stay, the status is gone')
    pg.goto(BASE + '/enquire/')
    check('first proposal within 24 hours' in pg.inner_text('.page-head'), 'the enquiry lead promises the answer time')
    pg.goto(BASE + '/about/')
    check(pg.locator('.member img.portrait').count() == 6 and pg.locator('.member--text').count() == 0, 'about: the six members keep their photos')

    # 14-15. Spanish and Portuguese
    for lang, none, chalet, house_label, dest_label, stay_label, atenas in (
            ('es', 'Sin preferencia', 'Chalet', 'Casa: Chalet 141', 'Destino: Megève', 'Dónde hospedarse: Chalets en Megève', 'Edificio Atenas, Las Leñas'),
            ('pt', 'Sem preferência', 'Chalé', 'Casa: Chalet 141', 'Destino: Megève', 'Onde se hospedar: Chalés em Megève', 'Edifício Atenas, Las Leñas')):
        pg.goto(f'{BASE}/{lang}/enquire/?destination=megeve&stay=chalets-megeve&house=Chalet%20141&type=chalet')
        check(texts(pg, '#f-stay')[0] == none and texts(pg, '#f-house')[0] == none, f'/{lang}/: "{none}" in both lists')
        check(val(pg, '#f-house') == 'Chalet 141' and len(opts(pg, '#f-house')) == 20, f'/{lang}/: Chalet 141 among the 20 chalets')
        check(chalet in texts(pg, '#f-type'), f'/{lang}/: the type "{chalet}"')
        text = whatsapp_text(pg)
        check(house_label in text and dest_label in text and stay_label in text, f'/{lang}/: the message says {house_label} · {dest_label} · {stay_label}')
        pg.goto(f'{BASE}/{lang}/enquire/')
        check(atenas in texts(pg, '#f-stay'), f'/{lang}/: the stay list says "{atenas}"')
        megeve = {'es': 'Chalets en Megève', 'pt': 'Chalés em Megève'}[lang]
        check(megeve in texts(pg, '#f-stay'), f'/{lang}/: "{megeve}" in the stay list')
        pg.select_option('#f-stay', 'chalets-megeve')
        check(pg.eval_on_selector_all('#f-house optgroup', 'els => els.map(e => e.label)') == [megeve], f'/{lang}/: the houses grouped under "{megeve}"')
        check(pg.inner_text('#form-status').strip() == {'es': 'Casa: 22 casas de este alojamiento para elegir.', 'pt': 'Casa: 22 casas desta acomodação para escolher.'}[lang],
              f'/{lang}/: the status line in the page language ({pg.inner_text("#form-status")})')
        check(not NOT_SAID.search(pg.content().split('<main')[1]), f'/{lang}/enquire/: no reserva, pago or comisión in the markup')
        pg.goto(f'{BASE}/{lang}/destinations/las-lenas/')
        check(pg.inner_text('#stay .card-title') == atenas.split(',')[0], f'/{lang}/destinations/las-lenas/: the card is "{atenas.split(",")[0]}"')
        hidden = pg.eval_on_selector('#stay .card-enquire .visually-hidden', 'e => e.textContent')
        check(atenas.split(',')[0] in hidden, f'/{lang}/: the button names the building in the page\'s language ({hidden.strip()})')
        pg.goto(f'{BASE}/{lang}/')
        check(pg.locator('.faq-item').count() == 13 and pg.locator('.hero-note').count() == 1, f'/{lang}/: 13 questions and the hero note')
        check('A pedido' not in pg.inner_text('main') and 'Ya disponible' not in pg.inner_text('main') and 'Já disponível' not in pg.inner_text('main'), f'/{lang}/: no status on the experiences')
        pg.goto(f'{BASE}/{lang}/destinations/seefeld/')
        check('5.400 m²' in pg.inner_text('main'), f'/{lang}/: Interalpen 5.400 m² on the Seefeld page')
    check(not errors, f'no script errors ({errors[:2]})')

    # 16. without the script
    nojs = browser.new_context(java_script_enabled=False, viewport={'width': 1280, 'height': 900})
    p2 = nojs.new_page()
    p2.goto(BASE + '/enquire/')
    check(p2.is_visible('#f-house') and len(opts(p2, '#f-house')) == len(HOUSES) and p2.locator('#f-house optgroup').count() == 2,
          f'no script: the House list shows all {len(HOUSES)} houses in two groups')
    check(len(opts(p2, '#f-stay')) == len(PARTNERS), 'no script: every stay shows')
    nojs.close()

    # 18. the lightbox button still carries the house
    pg.goto(BASE + '/stay/chalets-megeve/')
    pg.click('#chalet-141 .photo-open >> nth=0')
    h = pg.get_attribute('.lightbox-enquire', 'href')
    check('house=Chalet%20141' in h and 'type=chalet' in h, f'the full-screen button opens the enquiry for the house ({h})')
    pg.keyboard.press('Escape')

    # 17. widths
    for w in (320, 360, 390, 768, 1024, 1280, 1440):
        c = browser.new_context(viewport={'width': w, 'height': 900})
        p3 = c.new_page()
        for path in ['/', '/es/', '/pt/', '/enquire/', '/es/enquire/', '/pt/enquire/', '/enquire/?destination=megeve&stay=chalets-megeve&type=chalet',
                     '/about/', '/experiences/', '/stay/apartments-las-lenas/']:
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
