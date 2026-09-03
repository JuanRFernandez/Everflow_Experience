#!/usr/bin/env python3
"""Site checks, run locally (python scripts/check.py) and in CI on every PR.

1. Every local src/href/poster/url() in the HTML and CSS resolves to a file in the repo.
2. No <link> or <script> loads from a third-party host (privacy rule: zero external
   requests on page load — fonts and Leaflet are self-hosted; map tiles load only on click).
3. HTML tags are balanced in every page.
4. Every file under assets/img, assets/video, assets/css, assets/js is referenced somewhere
   (orphans are reported as warnings, not failures).
Exit code 1 on any failure.
"""
import html.parser, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PAGES = [f for f in os.listdir('.') if f.endswith('.html')]
CSS = [os.path.join(dp, f) for dp, _, fs in os.walk('assets/css') for f in fs if f.endswith('.css')] if os.path.isdir('assets/css') else []
failures, warnings, referenced = [], [], set()

def local_refs(path, text):
    base = os.path.dirname(path) if path.startswith('assets/') else '.'
    for m in re.finditer(r'(?:src|href|poster)="([^"#?]+)"|url\(\s*[\'"]?([^)\'"]+)', text):
        p = (m.group(1) or m.group(2) or '').strip()
        if not p or p.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', 'data:', '#')):
            continue
        yield p, os.path.normpath(os.path.join(base, p)).replace(os.sep, '/')

class Balance(html.parser.HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
    def __init__(self):
        super().__init__(); self.stack = []; self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID: self.stack.append(tag)
    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag: self.stack.pop()
        else: self.errors.append((tag, self.getpos()))

for page in PAGES:
    text = open(page, encoding='utf-8').read()
    for raw, resolved in local_refs(page, text):
        referenced.add(resolved)
        if not os.path.isfile(resolved): failures.append(f'{page}: broken reference {raw}')
    for m in re.finditer(r'<(link|script)\b[^>]*\b(?:href|src)="((?:https?:)?//[^"]+)"', text):
        failures.append(f'{page}: external {m.group(1)} on page load: {m.group(2)}')
    b = Balance(); b.feed(text)
    if b.stack or b.errors: failures.append(f'{page}: unbalanced tags {b.stack[:5]} {b.errors[:5]}')
for css in CSS:
    text = open(css, encoding='utf-8').read()
    for raw, resolved in local_refs(css, text):
        referenced.add(resolved)
        if not os.path.isfile(resolved): failures.append(f'{css}: broken url() {raw}')
for folder in ('assets/img', 'assets/video', 'assets/css', 'assets/js'):
    for dp, _, fs in os.walk(folder):
        for f in fs:
            p = os.path.join(dp, f).replace(os.sep, '/')
            if p not in referenced: warnings.append(f'unreferenced asset: {p}')

for w in warnings: print('WARN', w)
for f in failures: print('FAIL', f)
print(f'{len(PAGES)} pages, {len(referenced)} local references checked, {len(failures)} failures, {len(warnings)} warnings')
sys.exit(1 if failures else 0)
