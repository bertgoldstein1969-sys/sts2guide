update-all:
	bash scripts/update_all.sh

validate:
	python3 scripts/validate_data.py
	python3 scripts/sanity_check.py

staging-build:
	python3 scripts/fetch_sources.py
	python3 scripts/build_dataset.py
	python3 scripts/validate_data.py
	python3 scripts/generate_pages.py
	python3 scripts/sanity_check.py

staging-preview:
	bash scripts/staging_preview.sh
