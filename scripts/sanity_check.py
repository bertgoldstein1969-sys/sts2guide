#!/usr/bin/env python3
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]

hubs = ['cards','relics','characters','keywords','builds','tier']
for h in hubs:
    p = root / h / 'index.html'
    if not p.exists():
        raise SystemExit(f'SANITY_FAIL missing hub page: {p}')

# empty hubs
for h in ['cards','relics','characters','keywords','builds']:
    cnt = len([x for x in (root/h).iterdir() if x.is_dir()])
    if cnt == 0:
        raise SystemExit(f'SANITY_FAIL empty hub: {h}')

# check links to generated pages exist
missing = []
for html in root.rglob('*.html'):
    t = html.read_text(errors='ignore')
    for href in re.findall(r"href=['\"]([^'\"]+)['\"]", t):
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'):
            continue
        if '${' in href or '{' in href or '}' in href:
            continue
        if href.startswith('/'):
            path = root / href.lstrip('/')
        else:
            path = (html.parent / href).resolve()
        if href.endswith('/'):
            path = path / 'index.html'
        if not path.exists() and not href.startswith('javascript:'):
            # allow component script route in local preview; must exist in root path
            missing.append((str(html.relative_to(root)), href))

# filter known dynamic path placeholders none
if missing:
    # keep first 20
    msg='; '.join([f'{a}->{b}' for a,b in missing[:20]])
    raise SystemExit('SANITY_FAIL missing links: '+msg)

print('SANITY_OK')
