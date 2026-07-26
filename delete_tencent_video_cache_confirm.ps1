param(
    [switch]$DryRun = $true
)

$ErrorActionPreference = 'Stop'
$Target = 'C:\5ddee7b0b73c09d07f96460afbf9db91'
$LogPath = Join-Path $PSScriptRoot ("delete_tencent_video_cache_{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Get-FolderSizeSafe {
    param([string]$Path)
    $sum = 0L
    $count = 0
    Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $sum += [int64]$_.Length
        $count++
    }
    [pscustomobject]@{
        Bytes = $sum
        Files = $count
    }
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

try {
    Write-Log "Target: $Target"
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

    $size = Get-FolderSizeSafe -Path $Target
    $diskBefore = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    Write-Log ("Verified Tencent Video cache. Files={0}, Size={1}" -f $size.Files, (Format-Bytes $size.Bytes))
    Write-Log ("C free before: {0}" -f (Format-Bytes $diskBefore.FreeSpace))

    if ($DryRun) {
        Write-Log 'DRY RUN only. No files were deleted.'
        Write-Log 'To delete, run this script with -DryRun:$false and type YES.'
        exit 0
    }

    $answer = Read-Host 'Type YES to delete this Tencent Video cache directory'
    if ($answer -cne 'YES') {
        Write-Log 'User did not type YES. Aborted.'
        exit 2
    }

    Remove-Item -LiteralPath $Target -Recurse -Force -ErrorAction Stop
    $exists = Test-Path -LiteralPath $Target
    $diskAfter = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    Write-Log ("Target exists after delete: {0}" -f $exists)
    Write-Log ("C free after: {0}" -f (Format-Bytes $diskAfter.FreeSpace))
    Write-Log ("C free delta: {0}" -f (Format-Bytes ($diskAfter.FreeSpace - $diskBefore.FreeSpace)))
    if ($exists) { exit 3 }
    exit 0
}
catch {
    Write-Log ("FAILED: {0}" -f $_.Exception.Message)
    exit 1
}
