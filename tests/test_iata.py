"""The IATA TIDS code: in the footer of every page, in the Impressum (German and English), in the structured data of
every home and in the summary for AI assistants (llms.txt); and no page calls EverFlow "IATA accredited".
Reads the built pages in _site/. python tests/test_iata.py <repo root>"""
import ast
import html
import json
import os
import re
import sys

ROOT = sys.argv[1]
SITE = os.path.join(ROOT, '_site')
TIDS = json.load(open(os.path.join(ROOT, 'content', 'site.json'), encoding='utf-8'))['tids']
# the rule scripts/check.py applies to every page (check.py runs on import, so the pattern is read from its source)
_rules = ast.parse(open(os.path.join(ROOT, 'scripts', 'check.py'), encoding='utf-8').read())
_node = next(n for n in _rules.body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'ACCREDITED')
ACCREDITED = eval(compile(ast.Expression(_node.value), 'check.py', 'eval'), {'re': re})
fails = []


def check(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond:
        fails.append(what)


def read(rel):
    with open(os.path.join(SITE, rel), encoding='utf-8') as f:
        return f.read()


def text_of(page):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', page)).split())


check(TIDS == '96253931', f'content/site.json holds the TIDS code ({TIDS})')
pages = sorted(os.path.relpath(os.path.join(dp, f), SITE).replace(os.sep, '/')
               for dp, _, fs in os.walk(SITE) if not os.path.relpath(dp, SITE).startswith('assets') for f in fs if f.endswith('.html'))
without = [p for p in pages if f'IATA TIDS {TIDS}' not in text_of(read(p).split('<footer', 1)[-1])]
check(pages and not without, f'every page ({len(pages)}) shows "IATA TIDS {TIDS}" in its footer ({without[:3]})')
footer = read('index.html').split('<div class="wrap footer-bottom">', 1)[-1].split('</div>', 1)[0]
check(footer.index('©') < footer.index('IATA TIDS'), 'the code comes after the copyright')

imp = text_of(read('impressum.html'))
check(f'IATA TIDS-Code: {TIDS} (TIDS sales intermediary; keine IATA-Akkreditierung).' in imp, 'the German Impressum names the code')
check(f'IATA TIDS code {TIDS} (TIDS sales intermediary; this is not IATA accreditation).' in imp, 'the English summary names the code')
german, english = imp.split('Imprint / Legal notice', 1) if 'Imprint / Legal notice' in imp else (imp, '')
check(german.index('Gewerbeanmeldung') < german.index('IATA TIDS-Code') < german.index('Umsatzsteuer'),
      'in German it stands under "Gewerbe und Register"')
check(english.index('Business registration') < english.index('IATA TIDS code') < english.index('ski and snowboard school'),
      'in English it follows the business registration')

for lang in ('', 'es/', 'pt/', 'de/'):
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', read(lang + 'index.html'), re.S)
    data = json.loads(block.group(1)) if block else {}
    check(data.get('identifier') == {'@type': 'PropertyValue', 'propertyID': 'IATA TIDS', 'value': TIDS},
          f'/{lang}: the structured data carries the code as an identifier')

summary = read('llms.txt')
check(f'- IATA TIDS code {TIDS} (registered TIDS sales intermediary).' in summary.split('## About', 1)[-1],
      'llms.txt names the code in its About part')

said = [(p, m.group(0)) for p in pages for m in ACCREDITED.finditer(text_of(read(p)))]
check(not said, f'no page says "IATA accredited" ({said[:3]})')
for good in ('keine IATA-Akkreditierung', 'this is not IATA accreditation', 'IATA TIDS 96253931'):
    check(not ACCREDITED.search(good), f'the rule lets "{good}" stand')
for bad in ('IATA accredited', 'IATA-accredited agency', 'accredited by IATA', 'IATA-akkreditierte Agentur',
            'von der IATA akkreditiert', 'agencia acreditada por la IATA', 'agência acreditada pela IATA'):
    check(bool(ACCREDITED.search(bad)), f'the rule catches "{bad}"')

print(f'{len(fails)} failures')
sys.exit(1 if fails else 0)
