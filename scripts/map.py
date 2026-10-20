#!/usr/bin/env python3
"""Draw the background of the destinations map, assets/img/map/alps.svg, from Natural Earth data
(public domain, naturalearthdata.com): land and borders, lakes, rivers, the Adriatic. Standard library only.

    python scripts/map.py <ne_10m_admin_0_countries.geojson> <ne_10m_lakes.geojson> <ne_10m_rivers_lake_centerlines.geojson>

The GeoJSON files come from github.com/nvkelso/natural-earth-vector (folder geojson); they are not kept in
the repository. The frame and the projection are build.py's (MAP_BOX, map_xy), so the pins that build.py
draws on top fall on the right spot. Run this again only when the frame changes.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

W, H = build.MAP_W, build.MAP_H
PAD = 30                                  # draw a little beyond the frame, so no edge shows
MAIN = {'DEU', 'AUT', 'CHE', 'FRA', 'ITA'}
SEA, LAND, OTHER, BORDER, WATER, RIVER = '#dde3e0', '#f6f2ea', '#ece7dc', '#c2b9a6', '#d7dfdc', '#cbd5d2'


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)['features']


def rings(geom):
    if geom['type'] == 'Polygon':
        yield from geom['coordinates']
    elif geom['type'] == 'MultiPolygon':
        for poly in geom['coordinates']:
            yield from poly


def lines(geom):
    if geom['type'] == 'LineString':
        yield geom['coordinates']
    elif geom['type'] == 'MultiLineString':
        yield from geom['coordinates']


def project(points):
    return [build.map_xy(lat, lon) for lon, lat in points]


def clip(poly):
    """Sutherland-Hodgman: the polygon cut to the frame (plus PAD)."""
    edges = [(0, -PAD, 1), (0, W + PAD, -1), (1, -PAD, 1), (1, H + PAD, -1)]
    for axis, limit, side in edges:
        if not poly:
            return []
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            cin, pin = (cur[axis] - limit) * side >= 0, (prev[axis] - limit) * side >= 0
            if cin != pin:
                t = (limit - prev[axis]) / (cur[axis] - prev[axis])
                out.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
            if cin:
                out.append(cur)
        poly = out
    return poly


def simplify(pts, tol=0.45):
    """Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = (dx * dx + dy * dy) ** 0.5 or 1e-9
    far, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / norm
        if d > far:
            far, idx = d, i
    if far <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def inside(x, y, pad=PAD):
    return -pad <= x <= W + pad and -pad <= y <= H + pad


def path(pts, close):
    d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    return d + ('Z' if close else '')


def polygons(features, keep=lambda f: True):
    out = []
    for f in features:
        if not f.get('geometry') or not keep(f):
            continue
        for ring in rings(f['geometry']):
            pts = clip(project(ring))
            if pts and pts[0] == pts[-1]:
                pts = pts[:-1]       # a closed ring: simplify it open, Z closes it again
            pts = simplify(pts)
            if len(pts) >= 3:
                out.append(path(pts, True))
    return out


def rivers(features):
    out = []
    for f in features:
        if not f.get('geometry') or f['properties'].get('featurecla') != 'River' or (f['properties'].get('scalerank') or 99) > 9:
            continue
        for line in lines(f['geometry']):
            run = []
            for x, y in project(line):
                if inside(x, y):
                    run.append((x, y))
                elif run:
                    if len(run) > 1:
                        out.append(path(simplify(run, 0.6), False))
                    run = []
            if len(run) > 1:
                out.append(path(simplify(run, 0.6), False))
    return out


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    countries, lakes, river_lines = (load(p) for p in argv)
    code = lambda f: f['properties'].get('ADM0_A3')  # noqa: E731
    other = polygons(countries, lambda f: code(f) not in MAIN)
    main_land = polygons(countries, lambda f: code(f) in MAIN)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<!-- Drawn by scripts/map.py from Natural Earth (public domain). -->
<rect width="{W}" height="{H}" fill="{SEA}"/>
<g fill="{OTHER}" stroke="{BORDER}" stroke-width="0.8" stroke-linejoin="round"><path d="{" ".join(other)}"/></g>
<g fill="{LAND}" stroke="{BORDER}" stroke-width="0.9" stroke-linejoin="round"><path d="{" ".join(main_land)}"/></g>
<g fill="none" stroke="{RIVER}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="{" ".join(rivers(river_lines))}"/></g>
<g fill="{WATER}" stroke="{RIVER}" stroke-width="0.6"><path d="{" ".join(polygons(lakes))}"/></g>
</svg>
'''
    target = os.path.join(build.ROOT, 'assets', 'img', 'map', 'alps.svg')
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'w', encoding='utf-8', newline='\n') as f:
        f.write(svg)
    print(f'wrote assets/img/map/alps.svg  {len(svg) // 1024} KB')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
