#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p logs data/cache
RUN_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LOG="logs/update_all_${RUN_TS//[:]/-}.log"
SUMMARY_JSON="data/run_summary.json"

DATA_FILES=(data/cards.json data/relics.json data/characters.json data/keywords.json data/builds.json)
RAW_FILE="data/raw_sources.json"

hash_files() {
  shasum "$@" 2>/dev/null | shasum | awk '{print $1}'
}

DATA_HASH_BEFORE="$(hash_files "${DATA_FILES[@]}")"

echo "[update_all] start $RUN_TS" | tee "$LOG"

run_step() {
  local name="$1"; shift
  echo "[$(date -u +%H:%M:%S)] STEP $name" | tee -a "$LOG"
  if "$@" >>"$LOG" 2>&1; then
    echo "[$(date -u +%H:%M:%S)] OK   $name" | tee -a "$LOG"
    return 0
  fi
  echo "[$(date -u +%H:%M:%S)] FAIL $name" | tee -a "$LOG"
  return 1
}

# 1) fetch (fail-safe at source script layer)
if ! run_step "fetch_sources" python3 scripts/fetch_sources.py; then
  echo "[update_all] fetch failed -> preserving last known good dataset/pages" | tee -a "$LOG"
  exit 1
fi

# 2) build
run_step "build_dataset" python3 scripts/build_dataset.py

DATA_HASH_AFTER_BUILD="$(hash_files "${DATA_FILES[@]}")"
if [[ "$DATA_HASH_BEFORE" == "$DATA_HASH_AFTER_BUILD" ]]; then
  echo "[update_all] no data changes detected, skipping generate/sanity" | tee -a "$LOG"
  python3 - <<'PY' >>"$LOG" 2>&1
import json, datetime
from pathlib import Path
root=Path('.')
data=root/'data'
counts={}
for k in ['cards','relics','characters','keywords','builds']:
    arr=json.loads((data/f'{k}.json').read_text())
    counts[k]=len(arr)
out={
  'runAt': datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'Z',
  'dataChanged': False,
  'pagesGenerated': 0,
  'counts': counts,
  'errors': []
}
(data/'run_summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
PY
  echo "NO_MEANINGFUL_CHANGES" | tee -a "$LOG"
  exit 0
fi

# 3) validate gate (hard stop on fail)
run_step "validate_data" python3 scripts/validate_data.py

# 4) atomic-ish page generation: backup then restore on failure
BACKUP_DIR="$(mktemp -d /tmp/sts2-pages-backup.XXXXXX)"
for p in cards relics builds keywords characters tier sitemap.xml robots.txt; do
  if [[ -e "$p" ]]; then
    cp -R "$p" "$BACKUP_DIR/"
  fi
done

restore_backup() {
  for p in cards relics builds keywords characters tier sitemap.xml robots.txt; do
    rm -rf "$p"
    if [[ -e "$BACKUP_DIR/$p" ]]; then
      cp -R "$BACKUP_DIR/$p" "$p"
    fi
  done
}

if ! run_step "generate_pages" python3 scripts/generate_pages.py; then
  echo "[update_all] generate failed -> restoring previous site output" | tee -a "$LOG"
  restore_backup
  rm -rf "$BACKUP_DIR"
  exit 1
fi

if ! run_step "sanity_check" python3 scripts/sanity_check.py; then
  echo "[update_all] sanity failed -> restoring previous site output" | tee -a "$LOG"
  restore_backup
  rm -rf "$BACKUP_DIR"
  exit 1
fi

rm -rf "$BACKUP_DIR"

# 5) summary
python3 - <<'PY' >>"$LOG" 2>&1
import json, datetime
from pathlib import Path
root=Path('.')
data=root/'data'
counts={}
for k in ['cards','relics','characters','keywords','builds']:
    arr=json.loads((data/f'{k}.json').read_text())
    counts[k]=len(arr)
pages=0
for s in ['cards','relics','builds','keywords','characters']:
    p=root/s
    if p.exists():
      pages += len([x for x in p.iterdir() if x.is_dir()])
out={
  'runAt': datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'Z',
  'dataChanged': True,
  'pagesGenerated': pages,
  'counts': counts,
  'errors': []
}
(data/'run_summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
PY

echo "[update_all] done" | tee -a "$LOG"
exit 0
