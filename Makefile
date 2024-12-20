ifeq ($(OS),Windows_NT)
    RM = powershell
    RM_FLAGS = -Command "Remove-Item -Path"
    RM_FLAGS_ALL = -Recurse -Force
    SEP = \\
else
    RM = rm
    RM_FLAGS = -f
    RM_FLAGS_ALL =
    SEP = /
endif

env:
	uv venv

rmenv:
	rm -rf .venv

install:
	uv sync --no-dev

install-dev:
	uv sync --extra dev

install-extras:
	uv sync --all-extras --no-dev

run:
	uv run launcher.py

format:
	ruff check --select I --fix .
	ruff format .

clean:
	$(RM) $(RM_FLAGS) logs$(SEP)*.log $(RM_FLAGS_ALL)

clean-all:
	$(RM) $(RM_FLAGS) logs$(SEP)*.log $(RM_FLAGS_ALL)
	$(RM) $(RM_FLAGS) logs$(SEP)errors$(SEP)*.log $(RM_FLAGS_ALL)

.PHONY: env rmenv install install-dev install-extras run format clean clean-all
.DEFAULT_GOAL := run
