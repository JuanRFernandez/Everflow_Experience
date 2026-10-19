#!/usr/bin/env python3
"""Site checks, run locally (python scripts/check.py) and in CI on every pull request.

 1. The pages are what content/*.json gives (python scripts/build.py --check).
 2. Every local src/href/srcset/poster/data-src/url() resolves to a file in the repository, and every
    link to an anchor (#x, /page/#x) finds that id on the target page.
 3. Nothing is loaded from a third-party host on page view: no <link>, <script>, <img>, <iframe>,
    <video>, <audio>, <source>, <object> or <embed> with an external URL, and no CSS @import /
    url(http...). Fonts and Leaflet are self-hosted; map tiles load only after "Show map".
 4. HTML tags are balanced; every page has one <main> and one <h1>; generated pages carry no inline
    style, script or event handler (the Content-Security-Policy forbids them); every form field has
    a label; every <img> has alt, width and height.
 5. Images: at most 950 KB, no EXIF or XMP metadata; every photo of a partner sits in a <figure>
    whose caption starts with "©" and names the partner's credit; every credit is in the Impressum.
 6. Words: no price anywhere; no booking, commission or "racers" outside the legal pages; no regional brand line;
    German quotes close with “; names that must never appear on the site do not.
 7. This repository is public: nothing of the hotel library is in it (local configuration, extracted
    text, facts files, the permission register, internal hotel documents), and no text file holds a
    Drive path, a local path, a Drive link or an e-mail address other than the site's own.
 8. sitemap.xml lists exactly the pages that may be indexed.
Unreferenced files under assets/img, assets/video, assets/css, assets/js are reported as warnings.
Exit code 1 on any failure.
"""
import codecs
import html
import html.parser
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import build  # noqa: E402

SKIP_DIRS = {'.git', 'content', 'assets', 'scripts', 'docs', 'node_modules', '.claude', '.github'}
PAGES = []
for dp, dirs, files in os.walk('.'):
    dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
    for f in sorted(files):
        if f.endswith('.html'):
            PAGES.append(os.path.relpath(os.path.join(dp, f), '.').replace(os.sep, '/'))
CSS = sorted(os.path.join(dp, f).replace(os.sep, '/') for dp, _, fs in os.walk('assets') for f in fs if f.endswith('.css'))
LEGAL = {'impressum.html', 'datenschutz.html'}

ATTR = re.compile(r'\b(?:src|href|poster|data|data-src)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>"\']+))', re.I)
SRCSET = re.compile(r'\bsrcset\s*=\s*"([^"]*)"', re.I)
URLFN = re.compile(r'url\(\s*(?:"([^"]*)"|\'([^\']*)\'|([^)\s"\']+))\s*\)', re.I)
OG = re.compile(r'<meta\s+property="og:image"\s+content="https://everflowexperience\.com/([^"]+)"', re.I)
EXTERNAL_TAG = re.compile(
    r'<(link|script|img|iframe|video|audio|source|object|embed)\b([^>]*?)\b(?:href|src|poster|data)\s*=\s*["\']?((?:https?:)?//[^"\'\s>]+)',
    re.I | re.S)
EXTERNAL_CSS = re.compile(r'@import\s+(?:url\()?\s*["\']?(?:https?:)?//|url\(\s*["\']?(?:https?:)?//', re.I)
SKIP = ('http://', 'https://', '//', 'mailto:', 'tel:', 'data:', 'javascript:', '#')
MONEY = r'(?:EUR|CHF|USD|GBP|euros?|dollars?|franken|francs?)'
PRICE = re.compile(rf'(?:[€$£]|\b{MONEY})\s?\d|\d[\d.,]*(?:\s?[-–])?\s?(?:[€$£]|{MONEY}\b)', re.I)
PRICE_JS = re.compile(rf'(?:[€£]|\b{MONEY})\s?\d|\d[\d.,]*(?:\s?[-–])?\s?(?:[€£]|{MONEY}\b)', re.I)  # "$1" is code
CODE = re.compile(r'<script\b.*?</script>|<style\b.*?</style>', re.I | re.S)
TAGS = re.compile(r'<[^>]+>')
BOOKING = re.compile(r'\bbook(?:s|ed|ing|ings)?\b|request has been received', re.I)
NOT_SAID = re.compile(r'\bcommissions?\b|\bracers?\b', re.I)  # Juan, 19.10.2026: no commissions, no "racers"
REGIONAL = re.compile('bavarian' + r'\s+' + 'alps', re.I)
NEVER = [codecs.decode(w, 'rot13') for w in ('rqra yhkhel', 'rqrayhkhel', 'ubgry qnf gveby', 'enr cvafba')]
DE_QUOTE = re.compile(r'„[^“"]{0,200}"')
PRIVATE = re.compile(
    r'(^|/)(library\.local\.json|\.library/|assets/Hotels/|facts/)|(^|[/.])facts\.json$|permission[^/]*\.csv$', re.I)
TEXT = ('.html', '.css', '.js', '.md', '.json', '.yml', '.yaml', '.txt', '.py', '.svg', '.xml')
INTERNAL = re.compile(  # a Drive folder of the team, a drive-letter path, a Drive link
    r'\b\d\d_[A-Z][A-Z0-9_&-]{2,}|[A-Za-z]:[\\/](?![\\/ ])|(?i:my[ ]drive|meine[ ]ablage|(?:drive|docs|sheets)\.google\.com)')
MAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}')
OWN_MAIL = {'info@everflowexperience.com'}  # an address meant to be public is added here, on purpose
IMG_MAX = 950 * 1024  # scripts/photos.py keeps 800 px under 180 KB, 1600 px under 480 KB, 2400 px under 900 KB

failures, warnings, referenced = [], [], set()


def resolve(page, ref):
    """Repository path a reference points to: /x from the root, x from the page's folder; dir/ -> dir/index.html."""
    if ref.startswith('/'):
        path = ref.lstrip('/')
    else:
        base = os.path.dirname(page)
        path = os.path.normpath(os.path.join(base, ref)).replace(os.sep, '/')
    if path == '' or path.endswith('/'):
        path += 'index.html'
    return path


def local_refs(path, text):
    for m in list(ATTR.finditer(text)) + list(URLFN.finditer(text)):
        yield next((g for g in m.groups() if g), '').strip()
    for m in SRCSET.finditer(text):
        for part in m.group(1).split(','):
            if part.strip():
                yield part.strip().split()[0]
    for m in OG.finditer(text):
        yield '/' + m.group(1)


class Page(html.parser.HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.ids, self.labels, self.controls = [], [], set(), set(), []
        self.h1 = self.main = 0
        self.inline, self.imgs, self.figure, self.loose = [], [], [], []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d:
            self.ids.add(d['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'main':
            self.main += 1
        if tag == 'label' and d.get('for'):
            self.labels.add(d['for'])
        if tag in ('input', 'select', 'textarea') and d.get('type') not in ('hidden', 'submit', 'button'):
            self.controls.append(d.get('id'))
        if 'style' in d:
            self.inline.append(f'style= on <{tag}>')
        for k in d:
            if k.startswith('on'):
                self.inline.append(f'{k}= on <{tag}>')
        if tag == 'script' and not d.get('src') and d.get('type') != 'application/ld+json':
            self.inline.append('inline <script>')
        if tag == 'style':
            self.inline.append('<style> block')
        if tag == 'figure':
            self.figure.append({'stay': False, 'caption': ''})
        if tag == 'img':
            self.imgs.append(d)
            if (d.get('src') or '').startswith('/assets/img/stays/'):
                if self.figure:
                    self.figure[-1]['stay'] = d['src']
                else:
                    self.loose.append(d['src'])
        if tag == 'figcaption' and self.figure:
            self.figure[-1]['in_caption'] = True
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_data(self, data):
        if self.figure and self.figure[-1].get('in_caption'):
            self.figure[-1]['caption'] += data

    def handle_endtag(self, tag):
        if tag == 'figcaption' and self.figure:
            self.figure[-1]['in_caption'] = False
        if tag == 'figure' and self.figure:
            fig = self.figure.pop()
            if fig['stay']:
                self.stay_figures.append(fig)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append((tag, self.getpos()))

    stay_figures = None


def parse(text):
    p = Page()
    p.stay_figures = []
    p.feed(text)
    return p


def image_meta(path):
    """True when a JPEG or WebP file carries EXIF or XMP metadata."""
    with open(path, 'rb') as f:
        data = f.read()
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return b'EXIF' in data[12:4096] or b'XMP ' in data[12:4096]
    if data[:2] == b'\xff\xd8':
        return b'Exif\x00\x00' in data[:65536] or b'http://ns.adobe.com/xap/1.0/' in data[:65536]
    return False


# ---------------------------------------------------------------- 1. generated pages are current
try:
    out = build.render_all()
except build.BuildError as err:
    failures.append(f'content/: {err}')
    out = {}
for path, text in out.items():
    if not os.path.isfile(path) or open(path, encoding='utf-8', newline='').read() != text:
        failures.append(f'{path} is not what content/ gives: run python scripts/build.py (never edit a generated page)')
for path in build.generated_on_disk():
    if out and path not in out:
        failures.append(f'{path} was generated before but no longer is: run python scripts/build.py')

partners = json.load(open('content/partners.json', encoding='utf-8'))
credits = {p['slug']: {build.credit_text(c) for c in build.partner_credits(p)} for p in partners}

# ---------------------------------------------------------------- 2-6. every page
parsed = {}
for page in PAGES:
    text = open(page, encoding='utf-8').read()
    parsed[page] = p = parse(text)
    for raw in local_refs(page, text):
        ref = raw.split('?')[0].split('#')[0]
        if not ref or raw.lower().startswith(SKIP):
            continue
        target = resolve(page, ref)
        referenced.add(target)
        if not os.path.isfile(target):
            failures.append(f'{page}: broken reference {raw}')
    for m in EXTERNAL_TAG.finditer(text):
        if m.group(1).lower() == 'link' and re.search(r'rel\s*=\s*["\']?canonical', m.group(2) + text[m.end():m.end() + 80], re.I):
            continue
        failures.append(f'{page}: external <{m.group(1).lower()}> loaded on page view: {m.group(3)}')
    if p.stack or p.errors:
        failures.append(f'{page}: unbalanced tags {p.stack[:5]} {p.errors[:5]}')
    if p.h1 != 1:
        failures.append(f'{page}: {p.h1} <h1> elements (one per page)')
    if p.main != 1:
        failures.append(f'{page}: {p.main} <main> elements (one per page)')
    if build.MARK in text:
        for what in sorted(set(p.inline)):
            failures.append(f'{page}: {what} (the Content-Security-Policy blocks inline code and style)')
    for cid in p.controls:
        if not cid or cid not in p.labels:
            failures.append(f'{page}: form field {cid or "(no id)"} has no <label for>')
    for d in p.imgs:
        for attr in ('alt', 'width', 'height'):
            if attr not in d:
                failures.append(f'{page}: <img src="{d.get("src")}"> has no {attr}')
    for src in p.loose:
        failures.append(f'{page}: photo {src} is shown without a <figure> and its "©" credit')
    for fig in p.stay_figures:
        slug = fig['stay'].split('/')[4]
        caption = fig['caption'].strip()
        if not caption.startswith('©'):
            failures.append(f'{page}: photo {fig["stay"]} has no "©" credit under it')
        elif slug in credits and caption not in credits[slug]:
            failures.append(f'{page}: photo {fig["stay"]} is credited "{caption}", which is not a credit line of {slug} in content/partners.json')
    visible = html.unescape(TAGS.sub(' ', CODE.sub(' ', text)))
    for m in PRICE.finditer(html.unescape(CODE.sub(' ', text))):  # attributes count: alt, title, meta
        failures.append(f'{page}: shows a price ("{m.group(0).strip()}"); prices never go on the site')
    if page not in LEGAL:
        for m in BOOKING.finditer(visible):
            failures.append(f'{page}: says "{m.group(0)}"; the site takes no bookings (say plan, arrange, enquire)')
        for m in NOT_SAID.finditer(visible):
            failures.append(f'{page}: says "{m.group(0)}"; the site does not mention commissions or racers')
    for m in DE_QUOTE.finditer(visible):
        failures.append(f'{page}: German quote closed with a straight quote: {m.group(0)[:40]}')

# Anchors (#x on the same page, /page/#x on another) must find their id.
for page in PAGES:
    text = open(page, encoding='utf-8').read()
    for m in re.finditer(r'\bhref\s*=\s*"([^"]*#[^"]+)"', text):
        href = m.group(1)
        if href.lower().startswith(SKIP[:6]):
            continue
        target_ref, anchor = href.split('#', 1)
        target = page if not target_ref else resolve(page, target_ref.split('?')[0])
        if target in parsed and anchor not in parsed[target].ids:
            failures.append(f'{page}: link to #{anchor} on {target}, which has no such id')

# Every credit shown under a photo is listed in the Impressum.
if 'impressum.html' in parsed:
    imp = html.unescape(open('impressum.html', encoding='utf-8').read())
    for slug, cs in credits.items():
        for c in sorted(cs):
            if c not in imp:
                failures.append(f'impressum.html: the photo credit "{c}" ({slug}) is missing from "Urheberrecht und Bildnachweise"')

for css in CSS:
    text = open(css, encoding='utf-8').read()
    if EXTERNAL_CSS.search(text):
        failures.append(f'{css}: loads a resource from a third-party host (@import / url(http...))')
    for raw in local_refs(css, text):
        ref = raw.split('?')[0].split('#')[0]
        if not ref or raw.lower().startswith(SKIP):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(css), ref)).replace(os.sep, '/')
        referenced.add(target)
        if not os.path.isfile(target):
            failures.append(f'{css}: broken url() {raw}')

for dp, _, fs in os.walk('assets/js'):
    for f in fs:
        p = os.path.join(dp, f).replace(os.sep, '/')
        for m in PRICE_JS.finditer(open(p, encoding='utf-8').read()):
            failures.append(f'{p}: shows a price ("{m.group(0).strip()}"); prices never go on the site')
        referenced.update(re.findall(r"'/(assets/vendor/[^']+)'", open(p, encoding='utf-8').read()))

for folder in ('assets/img', 'assets/video', 'assets/css', 'assets/js', 'assets/stays'):
    for dp, _, fs in os.walk(folder):
        for f in fs:
            p = os.path.join(dp, f).replace(os.sep, '/')
            if p not in referenced:
                warnings.append(f'unreferenced asset: {p}')
            if p.startswith('assets/img/') and p.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
                if os.path.getsize(p) > IMG_MAX:
                    failures.append(f'{p}: {os.path.getsize(p) // 1024} KB; images stay under {IMG_MAX // 1024} KB (scripts/photos.py)')
                if image_meta(p):
                    failures.append(f'{p}: carries EXIF/XMP metadata; export it with scripts/photos.py')

# ---------------------------------------------------------------- 8. sitemap
if os.path.isfile('sitemap.xml'):
    listed = set(re.findall(r'<loc>https://everflowexperience\.com(/[^<]*)</loc>', open('sitemap.xml', encoding='utf-8').read()))
    for page in PAGES:
        text = open(page, encoding='utf-8').read()
        url = build.url_of(page)
        indexable = 'name="robots" content="noindex' not in text
        if indexable and url not in listed:
            failures.append(f'sitemap.xml: {url} is missing')
        if not indexable and url in listed:
            failures.append(f'sitemap.xml: {url} is noindex but listed')
    for url in listed:
        if resolve('index.html', url) not in PAGES:
            failures.append(f'sitemap.xml: {url} has no page')

# ---------------------------------------------------------------- 7. public repository
try:  # what is tracked, and what "git add -A" would take
    listed = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                            capture_output=True, check=True).stdout
    tracked = [p for p in listed.decode('utf-8', 'replace').split('\0') if p]
except (OSError, subprocess.CalledProcessError):
    tracked = []
    (failures if os.environ.get('CI') else warnings).append(
        'git is not available: could not check that nothing internal is in the repository')
for path in tracked:
    if PRIVATE.search(path):
        failures.append(f'{path}: belongs outside this public repository')
    if not path.lower().endswith(TEXT) or path.startswith('assets/vendor/') or not os.path.isfile(path):
        continue
    text = open(path, encoding='utf-8', errors='replace').read()
    for m in INTERNAL.finditer(text):
        failures.append(f'{path}: names an internal path or link ("{m.group(0)}"); this repository is public')
    for address in sorted({m.group(0) for m in MAIL.finditer(text)} - OWN_MAIL):
        failures.append(f'{path}: holds the e-mail address {address}; only the site\'s own address goes in')
    low = text.lower()
    for word in NEVER:
        if word in low:
            failures.append(f'{path}: names a partner that is never named in this repository')
    if REGIONAL.search(text):
        failures.append(f'{path}: uses the old regional brand line; the line is "{build.SITE["line"]}"')

for w in warnings:
    print('WARN', w)
for f in failures:
    print('FAIL', f)
print(f'{len(PAGES)} pages, {len(CSS)} stylesheets, {len(referenced)} local references checked, '
      f'{len(failures)} failures, {len(warnings)} warnings')
sys.exit(1 if failures else 0)
