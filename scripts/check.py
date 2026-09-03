#!/usr/bin/env python3
"""Site checks, run locally (python scripts/check.py) and in CI on every PR.

1. Every local src/href/poster/url() in the HTML and CSS resolves to a file in the repo.
2. Nothing is loaded from a third-party host on page view: no <link>, <script>, <img>, <iframe>,
   <video>, <audio>, <source>, <object> or <embed> with an external URL, and no CSS @import / url(http...)
   (privacy rule: zero external requests on page load — fonts and Leaflet are self-hosted;
   map tiles load only after the visitor clicks "Show map"). Plain <a href> links are fine.
3. HTML tags are balanced in every page.
4. Every file under assets/img, assets/video, assets/css, assets/js is referenced somewhere
   (orphans are reported as warnings, not failures).
Exit code 1 on any failure.
"""
import html.parser
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PAGES = sorted(f for f in os.listdir('.') if f.endswith('.html'))
CSS = sorted(os.path.join(dp, f).replace(os.sep, '/') for dp, _, fs in os.walk('assets') for f in fs if f.endswith('.css'))

ATTR = re.compile(r'\b(?:src|href|poster|data)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>"\']+))', re.I)
URLFN = re.compile(r'url\(\s*(?:"([^"]*)"|\'([^\']*)\'|([^)\s"\']+))\s*\)', re.I)
EXTERNAL_TAG = re.compile(
    r'<(link|script|img|iframe|video|audio|source|object|embed)\b[^>]*?\b(?:href|src|poster|data)\s*=\s*["\']?((?:https?:)?//[^"\'\s>]+)',
    re.I | re.S)
EXTERNAL_CSS = re.compile(r'@import\s+(?:url\()?\s*["\']?(?:https?:)?//|url\(\s*["\']?(?:https?:)?//', re.I)
SKIP = ('http://', 'https://', '//', 'mailto:', 'tel:', 'data:', 'javascript:', '#')

failures, warnings, referenced = [], [], set()


def local_refs(path, text):
    """Yield (reference as written, resolved repo path) for every local resource reference."""
    base = os.path.dirname(path) if path.startswith('assets/') else '.'
    for m in list(ATTR.finditer(text)) + list(URLFN.finditer(text)):
        p = next((g for g in m.groups() if g), '').strip()
        p = p.split('?')[0].split('#')[0]
        if not p or p.lower().startswith(SKIP):
            continue
        yield p, os.path.normpath(os.path.join(base, p)).replace(os.sep, '/')


class Balance(html.parser.HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append((tag, self.getpos()))


for page in PAGES:
    text = open(page, encoding='utf-8').read()
    for raw, resolved in local_refs(page, text):
        referenced.add(resolved)
        if not os.path.isfile(resolved):
            failures.append(f'{page}: broken reference {raw}')
    for m in EXTERNAL_TAG.finditer(text):
        failures.append(f'{page}: external <{m.group(1).lower()}> loaded on page view: {m.group(2)}')
    b = Balance()
    b.feed(text)
    if b.stack or b.errors:
        failures.append(f'{page}: unbalanced tags {b.stack[:5]} {b.errors[:5]}')

for css in CSS:
    text = open(css, encoding='utf-8').read()
    if EXTERNAL_CSS.search(text):
        failures.append(f'{css}: loads a resource from a third-party host (@import / url(http...))')
    for raw, resolved in local_refs(css, text):
        referenced.add(resolved)
        if not os.path.isfile(resolved):
            failures.append(f'{css}: broken url() {raw}')

for folder in ('assets/img', 'assets/video', 'assets/css', 'assets/js'):
    for dp, _, fs in os.walk(folder):
        for f in fs:
            p = os.path.join(dp, f).replace(os.sep, '/')
            if p not in referenced:
                warnings.append(f'unreferenced asset: {p}')

for w in warnings:
    print('WARN', w)
for f in failures:
    print('FAIL', f)
print(f'{len(PAGES)} pages, {len(CSS)} stylesheets, {len(referenced)} local references checked, '
      f'{len(failures)} failures, {len(warnings)} warnings')
sys.exit(1 if failures else 0)
