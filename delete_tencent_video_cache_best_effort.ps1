param(
    [switch]$DryRun = $true
)

$ErrorActionPreference = 'Stop'
$Target = 'C:\5ddee7b0b73c09d07f96460afbf9db91'
$LogPath = Join-Path $PSScriptRoot ("delete_tencent_video_cache_best_effort_{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Format-Bytes {
    param([double]$Bytes)
    $units = @('B','KB','MB','GB','TB')
    $value = $Bytes
    $i = 0
    while ($value -ge 1024 -and $i -lt $units.Length - 1) {
        $value = $value / 1024
        $i++
    }
    if ($i -eq 0) { return ('{0:N0} {1}' -f $value, $units[$i]) }
    return ('{0:N2} {1}' -f $value, $units[$i])
}

function Assert-TargetSafe {
    if (-not (Test-Path -LiteralPath $Target -PathType Container)) {
        Write-Log 'Target directory does not exist. Nothing to do.'
        exit 0
    }
    $item = Get-Item -LiteralPath $Target -Force
    $resolved = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd('\')
    $expected = [System.IO.Path]::GetFullPath($Target).TrimEnd('\')
    if ($resolved -ne $expected) {
        throw "Resolved path mismatch: $resolved"
    }
    if ($expected -notmatch '^C:\\[0-9a-f]{32}$') {
        throw "Unexpected target shape: $expected"
    }
    $desc = Join-Path $Target '目录说明.txt'
    if (-not (Test-Path -LiteralPath $desc -PathType Leaf)) {
        throw '目录说明.txt not found; refusing to proceed.'
    }
    $descText = Get-Content -LiteralPath $desc -Raw -Encoding UTF8
    if ($descText -notmatch '腾讯视频') {
        throw 'Description file does not mention Tencent Video; refusing to proceed.'
    }
}

function Get-CacheStats {
    $files = @(Get-ChildItem -LiteralPath $Target -Force -Recurse -File -ErrorAction SilentlyContinue)
    $bytes = 0L
    foreach ($file in $files) {
        $bytes += [int64]$file.Length
    }
    [pscustomobject]@{
        Files = $files.Count
        Bytes = $bytes
    }
}

try {
    Assert-TargetSafe
    $beforeStats = Get-CacheStats
    $diskBefore = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    Write-Log ("Target: {0}" -f $Target)
    Write-Log ("Verified Tencent Video cache. Files={0}, Size={1}" -f $beforeStats.Files, (Format-Bytes $beforeStats.Bytes))
    Write-Log ("C free before: {0}" -f (Format-Bytes $diskBefore.FreeSpace))

    if ($DryRun) {
        Write-Log 'DRY RUN only. No files were deleted.'
        exit 0
    }

    $answer = Read-Host 'Type YES to best-effort delete Tencent Video cache files'
    if ($answer -cne 'YES') {
        Write-Log 'User did not type YES. Aborted.'
        exit 2
    }

    $removedFiles = 0
    $removedBytes = 0L
    $failedFiles = 0
    $files = @(Get-ChildItem -LiteralPath $Target -Force -Recurse -File -ErrorAction SilentlyContinue)
    foreach ($file in $files) {
        try {
            $len = [int64]$file.Length
            Remove-Item -LiteralPath $file.FullName -Force -ErrorAction Stop
            $removedFiles++
            $removedBytes += $len
        }
        catch {
            $failedFiles++
            Write-Log ("FAILED file: {0} :: {1}" -f $file.FullName, $_.Exception.Message)
        }
    }

    $removedDirs = 0
    $failedDirs = 0
    $dirs = @(Get-ChildItem -LiteralPath $Target -Force -Recurse -Directory -ErrorAction SilentlyContinue | Sort-Object { $_.FullName.Length } -Descending)
    foreach ($dir in $dirs) {
        try {
            Remove-Item -LiteralPath $dir.FullName -Force -ErrorAction Stop
            $removedDirs++
        }
        catch {
            $failedDirs++
        }
    }

    try {
        Remove-Item -LiteralPath $Target -Force -ErrorAction Stop
        Write-Log 'Removed target root directory.'
    }
    catch {
        Write-Log ("Target root not removed, likely because locked files remain: {0}" -f $_.Exception.Message)
    }

    $afterExists = Test-Path -LiteralPath $Target
    $afterStats = if ($afterExists) { Get-CacheStats } else { [pscustomobject]@{ Files = 0; Bytes = 0 } }
    $diskAfter = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    Write-Log ("Removed files={0}, removed bytes={1}" -f $removedFiles, (Format-Bytes $removedBytes))
    Write-Log ("Failed files={0}, removed dirs={1}, failed dirs={2}" -f $failedFiles, $removedDirs, $failedDirs)
    Write-Log ("Target exists after: {0}" -f $afterExists)
    Write-Log ("Remaining files={0}, remaining size={1}" -f $afterStats.Files, (Format-Bytes $afterStats.Bytes))
    Write-Log ("C free after: {0}" -f (Format-Bytes $diskAfter.FreeSpace))
    Write-Log ("C free delta: {0}" -f (Format-Bytes ($diskAfter.FreeSpace - $diskBefore.FreeSpace)))
    if ($afterExists) { exit 4 }
    exit 0
}
catch {
    Write-Log ("FAILED: {0}" -f $_.Exception.Message)
    exit 1
}
