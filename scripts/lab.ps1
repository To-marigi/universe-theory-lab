$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
uv run jupyter lab --notebook-dir=. --ServerApp.root_dir=. --no-browser
