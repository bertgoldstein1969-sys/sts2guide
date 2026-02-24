# STS2 Automation Operator Guide

## Branch
Work branch: `sts2-auto-update`

## Local commands
- Full pipeline:
  - `make update-all`
- Validation only:
  - `make validate`
- Build staging assets:
  - `make staging-build`
- Preview locally:
  - `make staging-preview`
  - open `http://localhost:4399`

## What update-all does
1. Fetch source feeds with cache/retry/timeouts (`scripts/fetch_sources.py`)
2. Build normalized datasets (`scripts/build_dataset.py`)
3. Validate schema + references (`scripts/validate_data.py`)
4. Generate programmatic pages + sitemap/robots (`scripts/generate_pages.py`)
5. Sanity checks for links/hubs (`scripts/sanity_check.py`)
6. Write run summary (`data/run_summary.json`) + change log (`data/change_log.json`)
7. Exit 0 with `NO_MEANINGFUL_CHANGES` if no effective changes

## Debugging
- Check latest logs in `logs/`
- Inspect `data/raw_sources.json` for fetch errors
- Run:
  - `python3 scripts/validate_data.py`
  - `python3 scripts/sanity_check.py`

## GitHub Actions
Workflow: `.github/workflows/sts2_update.yml`
- schedule: every 6 hours
- manual trigger: `workflow_dispatch`
- pushes updates to `sts2-auto-update` branch
- opens/updates PR to `main`
- uploads artifacts on failure

## Safety
- No direct deploy step in this automation
- No push to `main` by automation
