$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

uv run ruff check .
uv run pytest
uv run mypy
uv run qgbench --validate-only
uv run stringbench audit
uv run python -m universe_lab.cli --json results/environment.json
