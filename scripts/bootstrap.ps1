$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Python 3.12 と研究用依存関係を同期しています..."
uv python install 3.12
uv sync --all-groups

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host ""
Write-Host "導入完了。検算を実行します。"
uv run python -m universe_lab.cli --json results/environment.json
