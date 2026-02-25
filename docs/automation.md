# STS2 Automation Operator Guide

## Branch / Deployment Model
- **Production deploy branch:** `main` (Netlify watches this branch)
- **Automation workflow:** `.github/workflows/sts2_update.yml`
- **Triggers:** `schedule` (every 6 hours) + `workflow_dispatch` only
- **No `push` trigger** is used, which prevents self-trigger loops.

## Local commands
- Full pipeline: `make update-all`
- Validation only: `make validate`
- Build staging assets: `make staging-build`
- Preview locally: `make staging-preview` then open `http://localhost:4399`

## What `update-all` does
1. Fetch source feeds with cache/retry/timeouts (`scripts/fetch_sources.py`)
2. Build normalized datasets (`scripts/build_dataset.py`)
3. Validate schema + references (`scripts/validate_data.py`)
4. Generate programmatic pages + sitemap/robots (`scripts/generate_pages.py`)
5. Run sanity checks (`scripts/sanity_check.py`)
6. Write run summary (`data/run_summary.json`)
7. Exit safely with `NO_MEANINGFUL_CHANGES` when no data changes are detected

## Auto-commit behavior (main)
When meaningful changes exist, workflow commits directly to `main` as:
- `user.name`: `github-actions[bot]`
- `user.email`: `41898282+github-actions[bot]@users.noreply.github.com`
- message format: `chore(sts2): auto-update datasets/pages [<UTC>] [skip ci]`

## Loop-prevention guardrails
1. Workflow is **not** triggered by pushes (schedule/manual only).
2. Commit message includes `[skip ci]` for extra protection.
3. Before commit, workflow stages all files then excludes run-only artifacts from meaningful change detection:
   - `data/run_summary.json`
   - `data/cache/http_meta.json`
   - `logs/`
4. If no meaningful changes remain staged, workflow prints `NO_MEANINGFUL_CHANGES` and exits without commit.

### Policy choice: `run_summary.json`-only changes
- **Chosen behavior:** skip commit.
- Rationale: avoid noisy commits from run metadata churn when content/pages are unchanged.

## Safety behavior on failures
- If fetch fails, pipeline exits non-zero and preserves last known good data/pages.
- If validation fails, generation is blocked.
- If generate/sanity fails, backup/restore keeps prior output intact.

## Debugging
- Inspect latest logs in `logs/`
- Inspect `data/raw_sources.json` for source errors
- Run directly:
  - `python3 scripts/validate_data.py`
  - `python3 scripts/sanity_check.py`
