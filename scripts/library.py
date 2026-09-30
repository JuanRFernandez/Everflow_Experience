#!/usr/bin/env python3
"""The hotel library: the material the hotels sent us, as searchable text.

Runs on Juan's machine only. It reads the PDFs in the allow-listed Drive folders and writes
one text file per document, one heading per page, into a folder OUTSIDE this repository.
This repository is public: the library, the local configuration and the permission register
never enter it (scripts/check.py fails the build if they do).

    uv run --with pypdf python scripts/library.py build            what would be read (dry run)
    uv run --with pypdf python scripts/library.py build --apply    write the library
    python scripts/library.py status           is the library older than the material?
    python scripts/library.py search kids club [--in berchtesgaden]
    python scripts/library.py verify <hotel>.facts.json
    python scripts/library.py permissions      what may go on the site, per hotel

Configuration: library.local.json in the repo root (git-ignored); copy library.example.json.
"""
import csv
import hashlib
import json
import logging
import os
import re
import sys
import time
import unicodedata
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, 'library.local.json')
MAX_MB = 60

# A file is never read when its name, or the name of a folder between it and the listed folder,
# says agreement, form, rate, payment or identity paper.
DENY = re.compile(
    r'agreement|vereinbarung|vertrag|contract|vendor|supplier|lieferant|kommission|commission|provision|comisi'
    r'|konditionen|conditions|(?<![a-z])terms(?![a-z])|(?<![a-z])agb(?![a-z])|(?<![a-z])nda(?![a-z])'
    r'|countersigned|(?<![a-z])signed|unterschr|unterzeichn|signiert|firmad'
    r'|bank(?!ett)|(?<![a-z])iban(?![a-z])|konto|(?<![a-z])sepa(?![a-z])|passport|reisepass|pasaporte|ausweis'
    r'|(?<![a-z])dni(?![a-z])|steuer|authoris|authoriz|vollmacht'
    r'|formular|(?<![a-z])forms?(?![a-z])|booking|buchung|reserv'
    r'|(?<![a-z])rates?(?![a-z])|rate[-_ ]?(?:sheet|card)|netto|preis|price|pricing|tarif'
    r'|invoice|rechnung|gewerbe', re.I)
# A folder of superseded material is not walked at all.
SHELVED = re.compile(r'archive|archiv|superseded', re.I)
FOLD = str.maketrans('’‘“”„–—', '\'\'"""--')


def fail(message):
    print('STOP', message)
    sys.exit(2)


def config():
    if not os.path.isfile(CONFIG):
        fail('library.local.json is missing: copy library.example.json and fill in the paths')
    cfg = json.load(open(CONFIG, encoding='utf-8-sig'))
    for key in ('material_root', 'folders', 'library', 'permissions'):
        if key not in cfg:
            fail(f'library.local.json has no "{key}"')
    for key in ('material_root', 'library', 'permissions'):
        if not os.path.isabs(cfg[key]):
            fail(f'"{key}" must be an absolute path')
    for key in ('library', 'permissions'):
        if inside_repo(cfg[key]):
            fail(f'"{key}" lies inside this public repository: choose a place outside it')
    if not isinstance(cfg['folders'], list):
        fail('"folders" must be a list')
    for folder in cfg['folders']:
        if os.path.isabs(folder) or not folder.strip('./\\ ') or '..' in re.split(r'[\\/]', folder):
            fail(f'"folders": "{folder}" must be a folder below material_root')
    return cfg


def inside_repo(path):
    here, root = (os.path.normcase(os.path.realpath(p)) for p in (path, ROOT))
    try:
        return os.path.commonpath([here, root]) == root
    except ValueError:  # another drive
        return False


def slug(text):
    """The end of the path carries language and version, so the end is kept; the mark keeps names apart."""
    mark = hashlib.sha1(text.encode('utf-8')).hexdigest()[:8]
    return re.sub(r'[^A-Za-z0-9]+', '-', text).strip('-')[-100:].strip('-') + '-' + mark


def clean(text):
    text = text.replace('­', '')
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n\s*\n+', '\n\n', text).strip()


def squash(text):
    """For comparing a quote with a page: case, spacing, soft hyphens and the shape of quotation
    marks and dashes do not count."""
    text = unicodedata.normalize('NFKC', text.replace('­', '')).translate(FOLD)
    return re.sub(r'\s+', ' ', text).strip().lower()


def sources(cfg):
    """Every PDF under the allow-listed folders, with the reason when it will not be read."""
    root = cfg['material_root']
    for folder in cfg['folders']:
        top = os.path.join(root, folder)
        if not os.path.isdir(top):
            yield folder, None, 'folder not found'
            continue
        for path, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if not SHELVED.search(d)]
            for name in sorted(files):
                if not name.lower().endswith('.pdf'):
                    continue
                full = os.path.join(path, name)
                rel = os.path.relpath(full, root).replace(os.sep, '/')
                if DENY.search(os.path.relpath(full, top)):
                    yield rel, full, 'never read: the name says agreement, form, rate or identity paper'
                elif os.path.getsize(full) > MAX_MB * 1e6:
                    yield rel, full, f'larger than {MAX_MB} MB'
                else:
                    yield rel, full, ''


def read_pages(full):
    from pypdf import PdfReader
    return [clean(page.extract_text() or '') for page in PdfReader(full).pages]


def build(cfg, apply):
    try:
        import pypdf  # noqa: F401  (before anything is deleted)
    except ImportError:
        fail('pypdf is missing: uv run --with pypdf python scripts/library.py build')
    warnings.filterwarnings('ignore')
    logging.getLogger('pypdf').setLevel(logging.ERROR)
    found = list(sources(cfg))
    readable = [s for s in found if not s[2]]
    print(f'{len(readable)} document(s) to read, {len(found) - len(readable)} left out')
    for rel, _full, why in found:
        if why:
            print(f'  left out  {rel}  ({why})')
    if not apply:
        for rel, _full, _why in readable:
            print(f'  would read  {rel}')
        print('dry run: nothing was written; add --apply')
        return
    if not readable:
        fail('nothing to read (is Drive running?): the library stays as it is')
    out = cfg['library']
    os.makedirs(out, exist_ok=True)
    before = os.path.join(out, 'index.json')
    if os.path.isfile(before):
        own = {e.get('file') for e in json.load(open(before, encoding='utf-8'))['documents']} | {'index.json'}
    elif any(os.path.isfile(os.path.join(out, name)) for name in os.listdir(out)):
        fail(f'"{out}" holds files and no index.json: the library needs a folder of its own')
    else:
        own = set()
    for old in os.listdir(out):
        if old in own:
            os.remove(os.path.join(out, old))
    index = []
    for rel, full, _why in readable:
        try:
            pages = read_pages(full)
        except Exception as exc:  # a damaged PDF must not stop the others
            index.append({'source': rel, 'status': f'unreadable ({type(exc).__name__})'})
            continue
        chars = sum(len(p) for p in pages)
        entry = {'source': rel, 'pages': len(pages), 'modified': int(os.path.getmtime(full))}
        if chars < 200:
            entry['status'] = 'scan without text'
        else:
            name = slug(rel) + '.md'
            body = [f'---\nsource: {rel}\npages: {len(pages)}\n---\n']
            body += [f'## page {n}\n\n{text}\n' for n, text in enumerate(pages, 1) if text]
            with open(os.path.join(out, name), 'w', encoding='utf-8', newline='\n') as handle:
                handle.write('\n'.join(body))
            entry.update(status='ok', file=name, chars=chars)
        index.append(entry)
    index += [{'source': rel, 'status': why} for rel, _full, why in found if why]
    with open(os.path.join(out, 'index.json'), 'w', encoding='utf-8', newline='\n') as handle:
        json.dump({'built': int(time.time()), 'documents': index}, handle, ensure_ascii=False, indent=1)
    ok = [e for e in index if e['status'] == 'ok']
    print(f'library written: {len(ok)} document(s), {sum(e["pages"] for e in ok)} pages, to {out}')
    for entry in index:
        if entry['status'] not in ('ok',) and not entry['status'].startswith('never read'):
            print(f'  not in the library  {entry["source"]}  ({entry["status"]})')


def load_index(cfg):
    path = os.path.join(cfg['library'], 'index.json')
    if not os.path.isfile(path):
        fail('no library yet: run "library.py build --apply"')
    return json.load(open(path, encoding='utf-8'))


def status(cfg):
    index = load_index(cfg)
    known = {e['source']: e for e in index['documents']}
    print('library built', time.strftime('%d.%m.%Y %H:%M', time.localtime(index['built'])))
    stale, here = 0, set()
    for rel, full, why in sources(cfg):
        if why:
            continue
        here.add(rel)
        entry = known.get(rel)
        if entry is None:
            print(f'  new in Drive      {rel}')
            stale += 1
        elif entry.get('modified') and int(os.path.getmtime(full)) > entry['modified']:
            print(f'  changed in Drive  {rel}')
            stale += 1
    for entry in index['documents']:
        if entry['status'] == 'ok' and entry['source'] not in here:
            print(f'  gone from Drive   {entry["source"]}')
            stale += 1
        elif entry['status'] != 'ok' and not entry['status'].startswith('never read'):
            print(f'  not searchable    {entry["source"]}  ({entry["status"]})')
    print('up to date' if not stale else f'{stale} document(s) differ from the library: run "build --apply"')
    return stale


def pages_of(cfg, entry):
    text = open(os.path.join(cfg['library'], entry['file']), encoding='utf-8').read()
    parts = re.split(r'\n## page (\d+)\n', text)
    return {int(n): body for n, body in zip(parts[1::2], parts[2::2])}


def search(cfg, terms, only=None):
    index = load_index(cfg)
    ok = [e for e in index['documents'] if e['status'] == 'ok']
    if only and not any(only.lower() in e['source'].lower() for e in ok):
        fail(f'no document of the library has "{only}" in its folder or file name')
    wanted = [t.lower() for t in terms]
    hits = 0
    for entry in ok:
        if only and only.lower() not in entry['source'].lower():
            continue
        for number, body in pages_of(cfg, entry).items():
            low = body.lower()
            if not all(t in low for t in wanted):
                continue
            hits += 1
            print(f'{entry["source"]} · page {number}')
            shown = 0
            for line in body.splitlines():
                if any(t in line.lower() for t in wanted) and shown < 3:
                    print('    ' + line.strip()[:160])
                    shown += 1
    print(f'{hits} page(s) found' if hits else 'not found in the library (scans and left-out files are not searched)')
    return hits


def verify(cfg, path):
    """Every fact names a document, a page and a quote; the quote must stand on that page."""
    facts = json.load(open(path, encoding='utf-8-sig'))
    by_source = {e['source']: e for e in load_index(cfg)['documents'] if e['status'] == 'ok'}
    wrong = 0
    for fact in facts:
        found = [e for s, e in by_source.items() if fact['source'] and s.endswith(fact['source'])]
        entry = found[0] if len(found) == 1 else None
        page = pages_of(cfg, entry).get(int(fact['page']), '') if entry else ''
        quote = squash(fact['quote'])
        if quote and quote in squash(page):
            print(f'  ok     {fact["claim"][:90]}')
        else:
            wrong += 1
            reason = ('the fact has no quote' if not quote else 'document not in the library' if not found
                      else f'{len(found)} documents end with that name' if len(found) > 1
                      else f'quote not on page {fact["page"]}')
            print(f'  WRONG  {fact["claim"][:90]}  ({reason})')
    print(f'{len(facts) - wrong} of {len(facts)} facts stand on the page they cite')
    return wrong


def permissions(cfg):
    path = cfg['permissions']
    if not os.path.isfile(path):
        fail(f'the permission register is missing: {path}')
    today = time.strftime('%Y-%m-%d')
    for row in csv.DictReader(open(path, encoding='utf-8-sig')):
        cell = {key: (value or '').strip() for key, value in row.items() if key}
        if 'hotel' not in cell or 'on_website' not in cell:
            fail('the permission register needs the columns "hotel" and "on_website", separated by commas')
        until = cell.get('valid_until', '')
        if until and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', until):
            fail(f'{cell["hotel"]}: valid_until "{until}" must be written YYYY-MM-DD')
        ended = until and until < today
        show = f'no (ended {until})' if ended else cell['on_website'] or 'no'
        photos = 'no' if ended else cell.get('photos') or 'no'
        print(f'{cell["hotel"]:<44} site: {show:<8} photos: {photos:<8} visited: {cell.get("visited_by_us") or "-":<11}'
              f' brochure: {cell.get("brochure_download") or "no":<6} credit: {cell.get("credit_line") or "-"}')


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    cfg = config()
    command, rest = argv[0], argv[1:]
    if command == 'build':
        build(cfg, '--apply' in rest)
    elif command == 'status':
        return 1 if status(cfg) else 0
    elif command == 'search':
        only = None
        if '--in' in rest:
            at = rest.index('--in')
            if at + 1 == len(rest):
                fail('--in needs a part of the folder or file name')
            only, rest = rest[at + 1], rest[:at] + rest[at + 2:]
        if not rest or any(t.startswith('--') for t in rest):
            fail('search needs at least one word; its only option is "--in <name>"')
        search(cfg, rest, only)
    elif command == 'verify':
        if not rest:
            fail('verify needs the facts file')
        if inside_repo(rest[0]):
            fail('the facts file lies inside this public repository: keep it next to the library')
        return 1 if verify(cfg, rest[0]) else 0
    elif command == 'permissions':
        permissions(cfg)
    else:
        fail(f'unknown command "{command}"')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
