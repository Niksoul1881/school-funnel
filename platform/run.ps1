$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Школа AI-агентов · MVP"
Write-Host "http://127.0.0.1:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
