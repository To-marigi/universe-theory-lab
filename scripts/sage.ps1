param(
    [ValidateSet("start", "stop", "logs", "status", "shell", "pull")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

try {
    docker info *> $null
} catch {
    throw "Docker Desktopが起動していません。起動後にもう一度実行してください。"
}

switch ($Action) {
    "start" {
        docker compose up -d sage
        $SagePort = if ($env:SAGE_PORT) { $env:SAGE_PORT } else { "8889" }
        Write-Host "SageMath: http://localhost:$SagePort"
        Write-Host "初期トークン: .env の SAGE_TOKEN"
    }
    "stop" { docker compose down }
    "logs" { docker compose logs -f sage }
    "status" { docker compose ps }
    "shell" { docker compose exec sage sage }
    "pull" { docker compose pull sage }
}
