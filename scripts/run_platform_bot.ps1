$ErrorActionPreference = "Continue"
$root = "C:\Users\NikSouk\Desktop\Proj\school-funnel"
$python = "C:\Users\NikSouk\AppData\Local\Programs\Python\Python313\python.exe"
Set-Location $root
while ($true) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "$root\private\supervisor.log" -Value "[$stamp] starting platform bot"
    & $python -u "telegram_bots\platform_bot.py" 1>> "$root\private\platform-bot.log" 2>> "$root\private\platform-bot.err.log"
    $code = $LASTEXITCODE
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "$root\private\supervisor.log" -Value "[$stamp] exited code=$code, restart in 5s"
    Start-Sleep -Seconds 5
}
