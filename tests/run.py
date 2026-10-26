#!/usr/bin/env python3
"""Run every browser test suite against the built site in _site/ (Playwright, Chrome; the bundled Chromium when
BROWSER_CHANNEL is empty, as in CI). Each suite serves _site/ on a free port, prints one line per check and ends
with "N failures"; this runner prints the totals and exits 1 if any suite failed.

    pip install -r requirements-dev.txt && python -m playwright install chromium
    python scripts/build.py
    python tests/run.py                 every suite
    python tests/run.py enquiry guides  only these
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUITES = ['enquiry', 'guides', 'stay', 'review', 'lenas', 'languages']


def main(argv):
    if not os.path.isfile(os.path.join(ROOT, '_site', 'index.html')):
        print('STOP _site/ is missing: run python scripts/build.py first')
        return 2
    chosen = argv or SUITES
    failed, passed = [], 0
    for suite in chosen:
        script = os.path.join(HERE, f'test_{suite}.py')
        print(f'=== {suite} ===', flush=True)
        run = subprocess.run([sys.executable, '-X', 'utf8', script, ROOT], capture_output=True, text=True, encoding='utf-8')
        lines = run.stdout.splitlines()
        for line in lines:
            if line.startswith('FAIL'):
                print(line)
        ok = sum(1 for line in lines if line.startswith('ok'))
        passed += ok
        m = re.search(r'(\d+) failures', run.stdout)
        bad = int(m.group(1)) if m else -1
        if run.returncode != 0 or bad != 0:
            failed.append(suite)
            print(run.stderr[-2000:])
        print(f'{suite}: {ok} ok, {bad if bad >= 0 else "?"} failures')
    print(f'{passed} checks passed; suites failed: {", ".join(failed) if failed else "none"}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
