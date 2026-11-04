$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONIOENCODING = "utf-8"
Write-Host ""
Write-Host "  Платформа практики · локальный стенд" -ForegroundColor Magenta
Write-Host "  http://127.0.0.1:8090" -ForegroundColor Cyan
Write-Host "  Ctrl+C — остановить" -ForegroundColor DarkGray
Write-Host ""
python -m uvicorn local_practice.app:app --host 127.0.0.1 --port 8090
