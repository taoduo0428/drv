param()

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$MessageFile = Join-Path $ProjectRoot "tmp\launch-message.txt"

if (-not (Test-Path -LiteralPath (Split-Path -Parent $MessageFile))) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $MessageFile) | Out-Null
}

[System.IO.File]::WriteAllText($MessageFile, "Golden kitten desktop pet is awake.", [System.Text.UTF8Encoding]::new($false))

Push-Location $ProjectRoot
try {
  & npm.cmd run state -- attention --message-file $MessageFile | Out-Host
  $proc = Start-Process -FilePath "npm.cmd" -ArgumentList "start" -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru
  $pidFile = Join-Path $ProjectRoot "tmp\app-launcher.pid"
  [System.IO.File]::WriteAllText($pidFile, [string]$proc.Id, [System.Text.UTF8Encoding]::new($false))
  Start-Sleep -Seconds 3
  Get-Process electron -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "*golden-kitten-codex-pet*" -or $_.MainWindowTitle -eq "金渐层 Codex 小猫" } |
    Select-Object Id, ProcessName, MainWindowTitle
}
finally {
  Pop-Location
}
