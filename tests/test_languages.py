"""Browser tests for the four languages and the guests from Brazil: the language menu (English, Español, Português,
Deutsch), the German pages, the section for Brazil and Argentina, the Portuguese question of the FAQ, the summary for
AI assistants (llms.txt) and the structured data. python tests/test_languages.py <repo root>"""
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
LABELS = ['English', 'Español', 'Português', 'Deutsch']


def check(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond:
        fails.append(what)


def menu(pg):
    return pg.eval_on_selector_all('.lang-menu .lang-list a', 'els => els.map(e => [e.textContent.trim(), e.getAttribute("href"), e.hasAttribute("aria-current")])')


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL', 'chrome') or None, headless=True)
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    errors, outside = [], []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('request', lambda r: outside.append(r.url) if not r.url.startswith((BASE, 'data:', 'blob:')) else None)

    # ---- the language menu
    pg.goto(BASE + '/')
    items = menu(pg)
    check([x[0] for x in items] == LABELS, f'the menu lists English, Español, Português, Deutsch, German last ({[x[0] for x in items]})')
    check([x[1] for x in items] == ['/', '/es/', '/pt/', '/de/'], f'on the home page it leads to each home ({[x[1] for x in items]})')
    check([x[2] for x in items] == [True, False, False, False], 'English is marked as the current language')
    check(not pg.is_visible('.lang-list'), 'the list is closed at first')
    check(pg.inner_text('.lang-current').strip() == 'EN', f'the closed menu shows the current language ({pg.inner_text(".lang-current").strip()})')
    name = pg.eval_on_selector('.lang-menu summary', 'e => e.textContent.trim()')
    check(name == 'EN, Language: English' and not pg.get_attribute('.lang-current', 'aria-hidden'),
          f'its name starts with what it shows, so a speech-input user can say "EN" ({name!r})')
    pg.click('.lang-menu summary')
    check(pg.is_visible('.lang-list a[href="/de/"]'), 'a click opens the list')
    pg.mouse.click(1000, 600)
    check(not pg.is_visible('.lang-list'), 'a click elsewhere closes it')
    pg.focus('.lang-menu summary')
    pg.keyboard.press('Enter')
    check(pg.is_visible('.lang-list'), 'Enter on the menu opens it')
    pg.keyboard.press('Escape')
    check(not pg.is_visible('.lang-list') and pg.evaluate('document.activeElement.tagName') == 'SUMMARY', 'Escape closes it and the focus stays on the menu')
    pg.keyboard.press('Enter')
    for _ in range(5):  # English, Español, Português, Deutsch, then out of the menu
        pg.keyboard.press('Tab')
    check(not pg.is_visible('.lang-list'), 'Tab out of the open list closes it, so it covers nothing the keyboard reaches next')
    pg.goto(BASE + '/de/enquire/')
    pg.click('.lang-menu summary')
    pg.focus('#f-name')
    check(not pg.is_visible('.lang-list'), 'the list closes when the focus moves into the form')
    pg.keyboard.type('Ana')
    pg.keyboard.press('Escape')
    check(pg.evaluate('document.activeElement.id') == 'f-name', 'Escape in a form field leaves the focus there')
    pg.goto(BASE + '/destinations/lech/')
    check([x[1] for x in menu(pg)] == ['/destinations/lech/', '/es/destinations/lech/', '/pt/destinations/lech/', '/de/destinations/lech/'], 'on a destination it keeps the page')
    pg.goto(BASE + '/stay/')
    check([x[1] for x in menu(pg)] == ['/stay/', '/es/', '/pt/', '/de/'], 'on an English-only page it leads to the other homes')
    for legal in ('/datenschutz.html', '/impressum.html'):
        pg.goto(BASE + legal)
        hrefs = [x[1] for x in menu(pg)]
        check(hrefs == [legal + '#en', '/es/', '/pt/', legal + '#de'], f'{legal}: English and Deutsch lead to the text on the same page ({hrefs})')
        pg.click('.lang-menu summary')
        pg.click('.lang-list a[hreflang="de"]')
        check(pg.evaluate('location.hash') == '#de' and not pg.is_visible('.lang-list'), f'{legal}: Deutsch jumps to the German text and the list closes')

    # ---- German
    pg.goto(BASE + '/de/')
    check(pg.get_attribute('html', 'lang') == 'de', 'the German home is lang="de"')
    check(pg.inner_text('.lang-current').strip() == 'DE' and [x[2] for x in menu(pg)] == [False, False, False, True], 'Deutsch is current on /de/')
    nav = pg.eval_on_selector_all('.site-nav > a:not(.button)', 'els => els.map(e => e.textContent.trim())')
    check(nav[0] == 'Reiseziele' and 'Über uns' in nav[3], f'the German menu ({nav})')
    marks = pg.eval_on_selector_all('.site-nav a .lang-mark', 'els => els.map(e => e.closest("a").getAttribute("href"))')
    check(sorted(marks) == ['/about/', '/experiences/', '/stay/'], f'the English-only pages are marked EN ({marks})')
    check(pg.locator('.faq-item').count() == 13, 'the German FAQ has 13 questions')
    check(pg.inner_text('.hero-note').startswith('Ihr Gastgeber: Juan Rodrigo Fernandez'), f'the German hero note ({pg.inner_text(".hero-note")[:60]})')
    check(pg.title() == 'Maßgeschneiderte Skireisen in den Alpen — EverFlow Experience', f'the German title ({pg.title()})')
    main = pg.inner_text('main')
    check(not re.search(r'\b(?:du|dich|dir|dein(?:e[mnrs]?)?|euch|eu(?:er|re[mnrs]?))\b', main, re.I), 'the German home addresses the reader with "Sie"')
    footer = pg.inner_text('.site-footer')
    check('Argentinien' in footer and 'Argentina' not in footer, 'the German footer says "Argentinien"')
    check(pg.get_attribute('.site-footer a[href^="/datenschutz.html"]', 'href') == '/datenschutz.html#de', 'the German footer opens the German privacy policy')
    pg.goto(BASE + '/de/destinations/')
    check(pg.locator('h1').inner_text().strip() == 'Wo wir Gäste betreuen.', f'/de/destinations/ heading ({pg.locator("h1").inner_text()})')
    check(pg.locator('main a[href="/datenschutz.html#karte"]').count() == 1, 'the German map note leads to the German map section of the privacy policy')
    pg.goto(BASE + '/de/guides/')
    check(pg.locator('.card').count() == 4 and pg.locator('.page-head .eyebrow').evaluate('e => e.textContent').strip() == 'Ratgeber', '/de/guides/: four guides, "Ratgeber"')
    pg.goto(BASE + '/de/enquire/?destination=megeve&stay=chalets-megeve&house=Chalet%20141&type=chalet')
    check(pg.inner_text('label[for="f-destination"]').strip() == 'Reiseziel', 'the German form labels')
    pg.fill('#f-name', 'Test Gast')
    pg.fill('#f-email', 'gast@example.org')
    pg.evaluate('window.__opened = []; window.open = function (u) { window.__opened.push(u); return null; }')
    pg.click('#send-whatsapp')
    url = pg.evaluate('window.__opened.filter(Boolean)[0] || ""')
    from urllib.parse import parse_qs, unquote, urlparse
    text = unquote(parse_qs(urlparse(url).query).get('text', [''])[0])
    check('Haus: Chalet 141' in text and 'Reiseziel: Megève' in text and 'Seite: /de/enquire/ (de)' in text, f'the WhatsApp message is in German ({text[:120]!r})')
    check('Art der Unterkunft: Chalet' in text, 'the German message names the type of stay "Art der Unterkunft"')
    check(pg.locator('#enquiry a[href="/datenschutz.html#de"]').count() == 1, 'the German form leads to the German privacy policy')
    pg.goto(BASE + '/de/destinations/las-lenas/')
    check('Atenas-Gebäude' in pg.inner_text('#stay'), 'the building is "Atenas-Gebäude" on the German page')

    # ---- the section for Brazil and Argentina
    for lang, first in (('', False), ('es', True), ('pt', True), ('de', False)):
        pg.goto(f'{BASE}/{lang + "/" if lang else ""}')
        order = pg.eval_on_selector_all('main > section[id]', 'els => els.map(e => e.id)')
        check('from-south-america' in order, f'/{lang}: the section for Brazil and Argentina is there')
        if 'from-south-america' in order:
            if first:
                check(order.index('from-south-america') == 0, f'/{lang}: it comes right after the hero ({order[:3]})')
            else:
                check(order.index('from-south-america') == order.index('how') + 1, f'/{lang}: it comes after "how it works" ({order[:5]})')
        href = pg.get_attribute('#from-south-america .arrow-link', 'href')
        check(href == f'{"/" + lang if lang else ""}/guides/first-week-from-south-america/', f'/{lang}: it links the guide in the page language ({href})')
        check(pg.locator('#from-south-america .ticks li').count() == 3, f'/{lang}: three points')
    pg.goto(BASE + '/')
    points = pg.eval_on_selector_all('#from-south-america .ticks li', 'els => els.map(e => e.textContent.trim())')
    check('Non-stop flights to Europe from São Paulo and Buenos Aires' in points, f'the flights point says where they go: to Europe ({points})')
    pg.goto(BASE + '/pt/')
    check('Do Brasil e da Argentina' in pg.locator('#from-south-america').evaluate('e => e.textContent'), 'the Portuguese section says "Do Brasil e da Argentina"')
    check(pg.title() == 'Viagens de esqui nos Alpes com aulas em português — EverFlow Experience', f'the Portuguese home title names the lessons in Portuguese ({pg.title()})')
    check('Vocês têm instrutores de esqui que falam português?' in pg.locator('#faq').evaluate('e => e.textContent'), 'the Portuguese FAQ asks about Portuguese-speaking instructors')
    pg.goto(BASE + '/')
    check('Do you have ski instructors who speak Portuguese?' in pg.locator('#faq').evaluate('e => e.textContent'), 'the English FAQ asks about Portuguese-speaking instructors')
    pg.goto(BASE + '/experiences/')
    check('Private coaching in English, Spanish, Portuguese and German' in pg.inner_text('#ski-coaching'), 'the coaching names its languages')

    # ---- structured data and the summary for AI assistants
    for lang in ('', 'es/', 'pt/', 'de/'):
        pg.goto(f'{BASE}/{lang}')
        blocks = pg.eval_on_selector_all('script[type="application/ld+json"]', 'els => els.map(e => e.textContent)')
        data = json.loads(blocks[0]) if blocks else {}
        check(data.get('@type') == 'TravelAgency' and data.get('knowsLanguage') == ['en', 'es', 'pt', 'de'], f'/{lang}: structured data with the four languages')
    r = pg.request.get(BASE + '/llms.txt')
    body = r.text()
    check(r.ok and body.startswith('# EverFlow Experience') and 'Portuguese' in body and '/guides/first-week-from-south-america/' in body,
          'llms.txt is served and names the Portuguese coaching and the guide')
    check('/de/' in body and 'Do you have ski instructors who speak Portuguese?' in body, 'llms.txt names the German site and the Portuguese question')
    check('the other pages are in English' in body and '/es/guides/first-week-from-south-america/' in body and 'Non-stop flights to Europe' in body,
          'llms.txt says which pages exist in four languages, links the Spanish guide and says the flights go to Europe')
    check(not errors, f'no script errors ({errors[:2]})')
    check(not outside, f'no request outside the site ({outside[:3]})')

    # ---- without the script: the menu still opens
    nojs = browser.new_context(java_script_enabled=False, viewport={'width': 1280, 'height': 900})
    p2 = nojs.new_page()
    p2.goto(BASE + '/es/')
    p2.click('.lang-menu summary')
    check(p2.is_visible('.lang-list a[href="/de/"]'), 'without the script the language menu opens too')
    nojs.close()

    # ---- phones: the menu inside the phone menu; no sideways scroll
    phone = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
    p3 = phone.new_page()
    p3.goto(BASE + '/de/')
    p3.click('.menu-toggle')
    p3.click('.lang-menu summary')
    check(p3.is_visible('.lang-list a[href="/pt/"]'), 'phone: the list opens inside the menu')
    box = p3.evaluate('(() => { const r = document.querySelector(".lang-list").getBoundingClientRect(); return [r.left, r.right, window.innerWidth]; })()')
    check(box[0] >= 0 and box[1] <= box[2], f'phone: the list stays on the screen ({box})')
    p3.goto(BASE + '/de/enquire/')
    p3.focus('.menu-toggle')
    p3.keyboard.press('Enter')
    for _ in range(40):  # through the phone menu and on into the form
        p3.keyboard.press('Tab')
        if p3.evaluate('document.activeElement.id') == 'f-name':
            break
    check(not p3.evaluate('document.querySelector(".site-header").classList.contains("is-open")'), 'phone: the menu closes when the keyboard leaves it')
    p3.keyboard.type('Ana')
    p3.keyboard.press('Escape')
    check(p3.evaluate('document.activeElement.id') == 'f-name' and p3.input_value('#f-name') == 'Ana', 'phone: Escape in a form field leaves the focus there')
    phone.close()
    for w in (320, 360, 390, 768, 1024, 1280, 1440):
        c = browser.new_context(viewport={'width': w, 'height': 900})
        p4 = c.new_page()
        for path in ['/', '/de/', '/de/enquire/', '/de/destinations/lech/', '/de/guides/first-week-from-south-america/', '/pt/', '/es/']:
            p4.goto(BASE + path)
            over = p4.evaluate('document.documentElement.scrollWidth - window.innerWidth')
            if over > 0:
                check(False, f'{path} at {w}px scrolls sideways by {over}px')
        c.close()
    print('widths checked')
    browser.close()

httpd.shutdown()
print(f'{len(fails)} failures')
sys.exit(1 if fails else 0)
