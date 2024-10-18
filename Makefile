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
	uv sync --no-dev

dev:
	uv sync --all-extras

format:
	ruff check --select I --fix .
	ruff format .

run:
	uv run launcher.py

clean:
	$(RM) $(RM_FLAGS) logs$(SEP)*.log $(RM_FLAGS_ALL)

clean-all:
	$(RM) $(RM_FLAGS) logs$(SEP)*.log $(RM_FLAGS_ALL)
	$(RM) $(RM_FLAGS) logs$(SEP)errors$(SEP)*.log $(RM_FLAGS_ALL)

.PHONY: env dev format run clean clean-all
.DEFAULT_GOAL := run
