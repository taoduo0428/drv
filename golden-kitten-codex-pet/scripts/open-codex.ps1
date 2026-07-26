param(
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"

function Write-Result([string]$Status, [string]$Detail) {
  if (-not $Quiet) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::WriteLine("$Status`t$Detail")
  }
}

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Win32Window {
  [DllImport("user32.dll")]
  public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")]
  public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
}
"@

function Focus-CodexWindow {
  $candidates = Get-Process -Name "Codex" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } |
    Sort-Object @{Expression = { if ($_.MainWindowTitle -eq "Codex") { 0 } else { 1 } } }, Id

  foreach ($process in $candidates) {
    try {
      [Win32Window]::ShowWindowAsync($process.MainWindowHandle, 9) | Out-Null
      [Win32Window]::SetForegroundWindow($process.MainWindowHandle) | Out-Null
      Write-Result "focused" "pid=$($process.Id) title=$($process.MainWindowTitle)"
      return $true
    } catch {
    }
  }

  try {
    $shell = New-Object -ComObject WScript.Shell
    if ($shell.AppActivate("Codex")) {
      Write-Result "focused" "AppActivate(Codex)"
      return $true
    }
  } catch {
  }

  return $false
}

function Start-CodexApp {
  $processPath = Get-Process -Name "Codex" -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and (Test-Path -LiteralPath $_.Path) } |
    Select-Object -First 1 -ExpandProperty Path

  if ($processPath) {
    Start-Process -FilePath $processPath | Out-Null
    Write-Result "started" $processPath
    return $true
  }

  $shortcutRoots = @(
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
    [Environment]::GetFolderPath("Desktop")
  )

  foreach ($root in $shortcutRoots) {
    if (-not (Test-Path -LiteralPath $root)) { continue }
    $shortcut = Get-ChildItem -LiteralPath $root -Recurse -Filter "*Codex*.lnk" -ErrorAction SilentlyContinue |
      Select-Object -First 1
    if ($shortcut) {
      Start-Process -FilePath $shortcut.FullName | Out-Null
      Write-Result "started" $shortcut.FullName
      return $true
    }
  }

  try {
    Start-Process "shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App" | Out-Null
    Write-Result "started" "shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App"
    return $true
  } catch {
  }

  return $false
}

if (Focus-CodexWindow) { exit 0 }
if (Start-CodexApp) {
  Start-Sleep -Milliseconds 900
  Focus-CodexWindow | Out-Null
  exit 0
}

Write-Result "not-found" "Codex process/window/shortcut not found"
exit 2
