env:
	uv venv

rmenv:
	rm -rf .venv

install: install-prod

install-dev:
	uv sync --all-extras

install-prod:
	uv sync --all-extras --no-dev

run:
	uv run launcher.py

format:
	ruff check --select I --fix .
	ruff format .

clean:
	rm -f logs/*.log

clean-all:
	rm -f logs/*.log
	rm -f logs/errors/*.log

.PHONY: env rmenv install install-dev install-prod run format clean clean-all
.DEFAULT_GOAL := run
