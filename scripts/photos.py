#!/usr/bin/env python3
"""Turn an original photo into the web files the site uses: WebP, sRGB, no metadata, in up to
three widths (800, 1600 and 2400 px, never wider than the original) so that every screen loads
the size it needs, at a quality that keeps the photo sharp.

    uv run --with pillow python scripts/photos.py site <source> <assets/img/... base> [--widths 800,1600,2400] [--aspect 3:2] [--focus 0.5,0.4]
    uv run --with pillow python scripts/photos.py stay <partner-slug> <name> <source> [--aspect 3:2] [--focus x,y]
    uv run --with pillow python scripts/photos.py rebuild [<assets/img/... prefix>]
    uv run --with pillow python scripts/photos.py brand

<source> is a file in this repository, a path relative to the material folder (`material_root` in
library.local.json), a photo inside a zip there ("<zip>::<member>"), or a file of an earlier
commit ("git:<commit>:<path>"). The source path never enters the repository: every processed
photo is logged with its source and crop in photo-sources.json in the library folder (outside
the repository), and `rebuild` processes them all again from the originals, for instance after
a change of the sizes or the quality below.

`stay` processes a partner's photo only when the permission register says `site: yes` and
`photos: yes` for that partner (the register name is `register` in content/partners.json).
The credit line comes from content/partners.json and is shown under every photo.
"""
import csv
import glob
import io
import json
import os
import re
import subprocess
import sys
import zipfile

try:
    from PIL import Image, ImageCms, ImageFilter, ImageOps
except ImportError:
    print('STOP Pillow is missing: run with  uv run --with pillow python scripts/photos.py ...')
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTHS = (800, 1600, 2400)
QUALITIES = (84, 80, 76, 72)            # tried in this order until the file fits its limit


def limit_for(width):
    """Largest file size for a width: generous, so that quality is lowered only for very busy photos."""
    return 180 * 1024 if width <= 800 else 480 * 1024 if width <= 1600 else 900 * 1024


SRGB = ImageCms.createProfile('sRGB')


def fail(message):
    print('STOP', message)
    sys.exit(2)


def local_config():
    path = os.path.join(ROOT, 'library.local.json')
    if not os.path.isfile(path):
        fail('library.local.json is missing: copy library.example.json and fill in the paths')
    return json.load(open(path, encoding='utf-8-sig'))


def open_source(source):
    """Open a photo from the repository, an earlier commit, the material folder, or a zip there."""
    if source.startswith('git:'):
        _, rev, path = source.split(':', 2)
        data = subprocess.run(['git', 'show', f'{rev}:{path}'], cwd=ROOT, capture_output=True, check=True).stdout
        return Image.open(io.BytesIO(data))
    member = None
    if '::' in source:
        source, member = source.split('::', 1)
    path = source if os.path.isabs(source) else os.path.join(ROOT, source)
    if not os.path.exists(path):
        path = os.path.join(local_config()['material_root'], source)
    if not os.path.exists(path):
        fail(f'source not found: {source}')
    if member:
        with zipfile.ZipFile(path) as z:
            return Image.open(io.BytesIO(z.read(member)))
    return Image.open(path)


def to_srgb(img):
    img = ImageOps.exif_transpose(img)
    icc = img.info.get('icc_profile')
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            img = ImageCms.profileToProfile(img.convert('RGB') if img.mode not in ('RGB', 'RGBA') else img, src, SRGB,
                                            outputMode='RGB')
        except (ImageCms.PyCMSError, OSError):
            pass
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGBA')
        bg = Image.new('RGB', img.size, (244, 240, 232))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    return img.convert('RGB')


def crop(img, aspect, focus):
    if not aspect:
        return img
    aw, ah = (float(n) for n in aspect.split(':'))
    fx, fy = focus
    w, h = img.size
    target = aw / ah
    if w / h > target:          # too wide: cut the sides
        nw = round(h * target)
        left = min(max(round(fx * w - nw / 2), 0), w - nw)
        return img.crop((left, 0, left + nw, h))
    nh = round(w / target)      # too tall: cut top and bottom
    top = min(max(round(fy * h - nh / 2), 0), h - nh)
    return img.crop((0, top, w, top + nh))


def save_webp(img, target, width):
    """Resize to `width` (never up) and save as WebP within the limit for that width: quality first
    stays high and only steps down for very busy photos; the width shrinks only as a last resort."""
    w = min(width, img.width)
    limit = limit_for(width)
    while True:
        im = img if w == img.width else img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
        if w < img.width:
            im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=35, threshold=2))
        for q in QUALITIES:
            buf = io.BytesIO()
            im.save(buf, 'WEBP', quality=q, method=6)  # no exif=, no icc_profile=: nothing but pixels
            if buf.tell() <= limit:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'wb') as f:
                    f.write(buf.getvalue())
                return im.size, buf.tell(), q
        w = round(w * 0.9)


def process(source, base, widths, aspect=None, focus=(0.5, 0.5)):
    img = crop(to_srgb(open_source(source)), aspect, focus)
    for old in glob.glob(os.path.join(ROOT, f'{base}-*.webp')):
        os.remove(old)
    out = []
    for i, width in enumerate(widths):
        if i and img.width <= widths[i - 1] * 1.2:
            break  # the original is hardly wider than the previous file: a larger one would add nothing
        target = os.path.join(ROOT, f'{base}-{width}.webp')
        size, nbytes, q = save_webp(img, target, width)
        out.append(f'{os.path.relpath(target, ROOT)}  {size[0]}x{size[1]}  q{q}  {nbytes // 1024} KB')
    for line in out:
        print('wrote', line.replace(os.sep, '/'))


def log_path():
    return os.path.join(local_config()['library'], 'photo-sources.json')


def read_log():
    path = log_path()
    return json.load(open(path, encoding='utf-8')) if os.path.isfile(path) else {}


def write_log(entries):
    with open(log_path(), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(sorted(entries.items())), f, ensure_ascii=False, indent=1)
        f.write('\n')


def remember(base, entry):
    entries = read_log()
    entries[base] = entry
    write_log(entries)


def register_row(name):
    cfg = local_config()
    for row in csv.DictReader(open(cfg['permissions'], encoding='utf-8-sig')):
        if row['hotel'].strip() == name:
            return row
    fail(f'"{name}" is not in the permission register')


def partner(slug):
    for p in json.load(open(os.path.join(ROOT, 'content', 'partners.json'), encoding='utf-8')):
        if p['slug'] == slug:
            return p
    fail(f'no partner "{slug}" in content/partners.json')


def allowed(slug):
    p = partner(slug)
    row = register_row(p['register'])
    if row['on_website'].strip().lower() != 'yes' or row['photos'].strip().lower() != 'yes':
        fail(f'the permission register does not allow photos of {p["register"]} on the site')


def run(base, entry):
    if entry['kind'] == 'stay':
        allowed(entry['partner'])
    process(entry['source'], base, entry['widths'], entry.get('aspect'), tuple(entry.get('focus', (0.5, 0.5))))
    remember(base, entry)


def brand():
    """The wordmark in ink and in white for the pages (SVG files coloured from brand/everflow-wordmark.svg, the vector
    wordmark with one <g fill> around its letters), and the icons, cut from the top line of the PNG."""
    vector = os.path.join(ROOT, 'brand/everflow-wordmark.svg')
    if not os.path.isfile(vector):
        fail('brand/everflow-wordmark.svg is missing: the pages link the SVG wordmark written from it')
    with open(vector, encoding='utf-8') as f:
        svg = f.read()
    if svg.count('<g fill="') != 1:
        fail('brand/everflow-wordmark.svg: expected one <g fill="…"> around the letters')
    for name, colour in (('ink', '#17140f'), ('white', '#ffffff')):
        out = re.sub(r'<g fill="[^"]*"', f'<g fill="{colour}"', svg, count=1)
        target = os.path.join(ROOT, f'assets/img/brand/wordmark-{name}.svg')
        with open(target, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('wrote', os.path.relpath(target, ROOT).replace(os.sep, '/'), f'{len(out.encode("utf-8")) // 1024} KB')
    src = Image.open(os.path.join(ROOT, 'brand/everflow-wordmark.png')).convert('RGBA')
    letters = src.crop(src.getchannel('A').point(lambda a: 255 if a > 24 else 0).getbbox())
    # Icon: "EVER FLOW" (without the EXPERIENCE line) in cream on ink, square.
    alpha = letters.getchannel('A')
    top = alpha.crop((0, 0, letters.width, round(letters.height * 0.84)))
    top = top.crop(top.point(lambda a: 255 if a > 24 else 0).getbbox())
    for size in (32, 180):
        pad = round(size * 0.14)
        inner = size - 2 * pad
        scale = min(inner / top.width, inner / top.height)
        mask = top.resize((round(top.width * scale), round(top.height * scale)), Image.LANCZOS)
        icon = Image.new('RGB', (size, size), (23, 20, 15))
        fill = Image.new('RGB', mask.size, (244, 240, 232))
        icon.paste(fill, ((size - mask.width) // 2, (size - mask.height) // 2), mask)
        target = os.path.join(ROOT, f'assets/img/brand/icon-{size}.png')
        icon.save(target, optimize=True)
        print('wrote', os.path.relpath(target, ROOT).replace(os.sep, '/'), icon.size)


def main(argv):
    if not argv:
        print(__doc__)
        return
    opts = {}
    args = []
    it = iter(argv[1:])
    for a in it:
        if a.startswith('--'):
            opts[a[2:]] = next(it)
        else:
            args.append(a)
    aspect = opts.get('aspect')
    focus = [float(n) for n in opts.get('focus', '0.5,0.5').split(',')]
    widths = [int(w) for w in opts['widths'].split(',')] if 'widths' in opts else list(WIDTHS)
    if argv[0] == 'site':
        source, base = args
        run(base, {'kind': 'site', 'source': source, 'widths': widths, 'aspect': aspect, 'focus': focus})
    elif argv[0] == 'stay':
        slug, name, source = args
        run(f'assets/img/stays/{slug}/{name}', {'kind': 'stay', 'partner': slug, 'source': source, 'widths': widths,
                                                'aspect': aspect or '3:2', 'focus': focus})
    elif argv[0] == 'rebuild':
        prefix = args[0] if args else ''
        entries = read_log()
        todo = {b: e for b, e in entries.items() if b.startswith(prefix)}
        if not todo:
            fail(f'no logged photo starts with "{prefix}"')
        for base, entry in todo.items():
            if 'widths' not in opts and entry['kind'] == 'stay':
                entry['widths'] = list(WIDTHS)
            run(base, entry)
    elif argv[0] == 'brand':
        brand()
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
