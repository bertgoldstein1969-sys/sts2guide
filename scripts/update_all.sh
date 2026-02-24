#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p logs data/cache
RUN_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LOG="logs/update_all_${RUN_TS//[:]/-}.log"
SUMMARY_JSON="data/run_summary.json"

before_hash="$(git ls-files -s | shasum | awk '{print $1}')"

{
  echo "[update_all] start $RUN_TS"
  echo "1) fetch sources"
  python3 scripts/fetch_sources.py

  echo "2) build datasets"
  python3 scripts/build_dataset.py

  echo "3) validate datasets"
  python3 scripts/validate_data.py

  echo "4) generate pages"
  python3 scripts/generate_pages.py

  echo "5) sanity checks"
  python3 scripts/sanity_check.py

  echo "6) update UI timestamps"
  python3 - <<'PY'
from pathlib import Path
from datetime import datetime, timezone
root=Path('.')
now=datetime.now(timezone.utc).isoformat()
for fp in [root/'index.html',root/'updates.html',root/'early-access.html']:
    t=fp.read_text()
    # minimal stamp marker for operator checks
    marker='data-last-updated="'
    if marker in t:
      import re
      t=re.sub(r'data-last-updated="[^"]*"', f'data-last-updated="{now}"', t)
    else:
      t=t.replace('<body>', f'<body data-last-updated="{now}">', 1)
    fp.write_text(t)
print('timestamps updated')
PY

  echo "7) run summary"
  python3 - <<'PY'
import json,glob,datetime
from pathlib import Path
root=Path('.')
data=root/'data'
counts={}
for k in ['cards','relics','characters','keywords','builds']:
    arr=json.loads((data/f'{k}.json').read_text())
    counts[k]=len(arr)

# rough diff/new/removed by ids vs previous run snapshot
prev_path=data/'change_log.json'
prev={}
if prev_path.exists():
    try: prev=json.loads(prev_path.read_text())
    except: prev={}
prev_ids=set(prev.get('allIds',[]))
cur_ids=set()
for k in ['cards','relics','characters','keywords','builds']:
    arr=json.loads((data/f'{k}.json').read_text())
    cur_ids.update([x['id'] for x in arr])
new_ids=sorted(cur_ids-prev_ids)
removed_ids=sorted(prev_ids-cur_ids)
updated_ids=sorted(cur_ids & prev_ids)[:50]
out={
  'runAt': datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'Z',
  'counts': counts,
  'newCount': len(new_ids),
  'removedCount': len(removed_ids),
  'updatedCount': len(updated_ids),
  'new': new_ids[:50],
  'removed': removed_ids[:50],
  'updated': updated_ids,
  'allIds': sorted(list(cur_ids))
}
(data/'change_log.json').write_text(json.dumps(out,indent=2))
(data/'run_summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
PY

  echo "[update_all] done"
} | tee "$LOG"

after_hash="$(git ls-files -s | shasum | awk '{print $1}')"

if [[ "$before_hash" == "$after_hash" ]]; then
  echo "NO_MEANINGFUL_CHANGES"
  exit 0
fi

echo "CHANGES_DETECTED"
exit 0
