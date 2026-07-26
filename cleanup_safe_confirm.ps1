param(
    [switch]$DryRun = $true,
    [int]$TempOlderThanDays = 7,
    [int]$MaxItems = 300000,
    [int]$MaxSecondsPerTarget = 120
)

$ErrorActionPreference = 'Continue'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ScriptDir)) {
    $ScriptDir = (Get-Location).Path
}

$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogPath = Join-Path $ScriptDir ("cleanup_log_{0}.txt" -f $Timestamp)
$UserProfilePath = [Environment]::GetFolderPath('UserProfile')
$LocalAppDataPath = [Environment]::GetFolderPath('LocalApplicationData')

$EffectiveDryRun = $true
if ($PSBoundParameters.ContainsKey('DryRun')) {
    $EffectiveDryRun = [bool]$DryRun
}

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Format-Bytes {
    param([double]$Bytes)
    $units = @('B', 'KB', 'MB', 'GB', 'TB')
    $value = $Bytes
    $index = 0
    while ($value -ge 1024 -and $index -lt ($units.Length - 1)) {
        $value = $value / 1024
        $index++
    }
    if ($index -eq 0) {
        return ('{0:N0} {1}' -f $value, $units[$index])
    }
    return ('{0:N2} {1}' -f $value, $units[$index])
}

function Get-FullPathSafe {
    param([string]$Path)
    try {
        return [System.IO.Path]::GetFullPath($Path)
    }
    catch {
        return $null
    }
}

function Test-PathUnderRoot {
    param(
        [string]$Path,
        [string]$Root
    )
    $full = Get-FullPathSafe -Path $Path
    $rootFull = Get-FullPathSafe -Path $Root
    if ([string]::IsNullOrWhiteSpace($full) -or [string]::IsNullOrWhiteSpace($rootFull)) {
        return $false
    }
    $rootWithSlash = $rootFull.TrimEnd('\') + '\'
    return $full.StartsWith($rootWithSlash, [System.StringComparison]::OrdinalIgnoreCase)
}

function Test-SafeTargetRoot {
    param([string]$Root)
    $full = Get-FullPathSafe -Path $Root
    if ([string]::IsNullOrWhiteSpace($full)) {
        return $false
    }

    $userWithSlash = $UserProfilePath.TrimEnd('\') + '\'
    if (-not $full.StartsWith($userWithSlash, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $false
    }

    $blockedRoots = @(
        $env:SystemRoot,
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        $env:ProgramData,
        (Join-Path $LocalAppDataPath 'Docker'),
        (Join-Path $UserProfilePath '.docker')
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    foreach ($blocked in $blockedRoots) {
        $blockedFull = Get-FullPathSafe -Path $blocked
        if ([string]::IsNullOrWhiteSpace($blockedFull)) {
            continue
        }
        $blockedWithSlash = $blockedFull.TrimEnd('\') + '\'
        if ($full.Equals($blockedFull, [System.StringComparison]::OrdinalIgnoreCase) -or
            $full.StartsWith($blockedWithSlash, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $false
        }
    }
    return $true
}

function Test-BlockedFragment {
    param([string]$Path)
    $full = (Get-FullPathSafe -Path $Path)
    if ([string]::IsNullOrWhiteSpace($full)) {
        return $true
    }
    $fragments = @(
        '\Docker\',
        '\.docker\',
        '\node_modules\',
        '\.venv\',
        '\venv\',
        '\.next\',
        '\build\',
        '\dist\'
    )
    foreach ($fragment in $fragments) {
        if ($full.IndexOf($fragment, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
    }
    return $false
}

function Test-ReparsePoint {
    param($Item)
    return (($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
}

function Get-EligibleItems {
    param($Target)
    if (-not (Test-Path -LiteralPath $Target.Root)) {
        return @()
    }
    if (-not (Test-SafeTargetRoot -Root $Target.Root)) {
        Write-Log ("SKIP unsafe target root: {0}" -f $Target.Root)
        return @()
    }

    $children = @(Get-ChildItem -LiteralPath $Target.Root -Force -ErrorAction SilentlyContinue)
    if ($Target.Mode -eq 'TempOlderThan') {
        $cutoff = (Get-Date).AddDays(-1 * $TempOlderThanDays)
        $children = @($children | Where-Object { (-not $_.PSIsContainer) -and $_.LastWriteTime -lt $cutoff })
    }

    $eligible = New-Object System.Collections.ArrayList
    foreach ($child in $children) {
        if (Test-ReparsePoint -Item $child) {
            continue
        }
        if (-not (Test-PathUnderRoot -Path $child.FullName -Root $Target.Root)) {
            continue
        }
        if (Test-BlockedFragment -Path $child.FullName) {
            continue
        }
        [void]$eligible.Add($child)
    }
    return @($eligible.ToArray())
}

function Measure-EligibleItems {
    param(
        [object[]]$Items,
        [int]$ItemLimit,
        [int]$SecondsLimit
    )

    $started = Get-Date
    $stack = New-Object System.Collections.Stack
    foreach ($item in $Items) {
        $stack.Push($item)
    }

    $bytes = 0L
    $count = 0
    $errors = 0
    $skipped = 0
    $truncated = $false

    while ($stack.Count -gt 0) {
        if ($count -ge $ItemLimit -or ((Get-Date) - $started).TotalSeconds -gt $SecondsLimit) {
            $truncated = $true
            break
        }

        $item = $stack.Pop()
        try {
            if (Test-ReparsePoint -Item $item) {
                $skipped++
                continue
            }
            $count++
            if ($item.PSIsContainer) {
                $children = @(Get-ChildItem -LiteralPath $item.FullName -Force -ErrorAction SilentlyContinue)
                foreach ($child in $children) {
                    if (Test-ReparsePoint -Item $child) {
                        $skipped++
                        continue
                    }
                    $stack.Push($child)
                }
            }
            else {
                $bytes += [int64]$item.Length
            }
        }
        catch {
            $errors++
        }
    }

    return [pscustomobject]@{
        Bytes = $bytes
        Count = $count
        Errors = $errors
        Skipped = $skipped
        Truncated = $truncated
        ElapsedSeconds = [math]::Round(((Get-Date) - $started).TotalSeconds, 2)
    }
}

$Targets = @(
    [pscustomobject]@{
        Name = 'npm-cache'
        Root = Join-Path $LocalAppDataPath 'npm-cache'
        Mode = 'AllChildren'
        Reason = 'npm cache'
    },
    [pscustomobject]@{
        Name = 'pip Cache'
        Root = Join-Path $LocalAppDataPath 'pip\Cache'
        Mode = 'AllChildren'
        Reason = 'pip download/build cache'
    },
    [pscustomobject]@{
        Name = 'Gradle caches'
        Root = Join-Path $UserProfilePath '.gradle\caches'
        Mode = 'AllChildren'
        Reason = 'Gradle dependency/build cache'
    },
    [pscustomobject]@{
        Name = 'Local Temp older than threshold'
        Root = Join-Path $LocalAppDataPath 'Temp'
        Mode = 'TempOlderThan'
        Reason = 'AppData Local Temp direct children older than threshold'
    },
    [pscustomobject]@{
        Name = 'Edge default cache'
        Root = Join-Path $LocalAppDataPath 'Microsoft\Edge\User Data\Default\Cache'
        Mode = 'AllChildren'
        Reason = 'Edge browser cache'
    },
    [pscustomobject]@{
        Name = 'Chrome default cache'
        Root = Join-Path $LocalAppDataPath 'Google\Chrome\User Data\Default\Cache'
        Mode = 'AllChildren'
        Reason = 'Chrome browser cache'
    }
)

Write-Log 'Safe cache cleanup confirmation script started.'
Write-Log ("Mode: {0}" -f ($(if ($EffectiveDryRun) { 'DRY RUN' } else { 'CONFIRMED RUN REQUESTED' })))
Write-Log ("Log file: {0}" -f $LogPath)
Write-Log ("Temp threshold: older than {0} days" -f $TempOlderThanDays)
Write-Log 'Explicit exclusions: Docker, .docker, .venv, venv, node_modules, .next, build, dist, registry, services.'

$Plans = New-Object System.Collections.Generic.List[object]
$TotalBytes = 0L

foreach ($target in $Targets) {
    $items = @(Get-EligibleItems -Target $target)
    if ($items.Count -eq 0) {
        Write-Log ("TARGET {0}: no eligible items or path missing. Root={1}" -f $target.Name, $target.Root)
        continue
    }

    $stats = Measure-EligibleItems -Items $items -ItemLimit $MaxItems -SecondsLimit $MaxSecondsPerTarget
    $TotalBytes += [int64]$stats.Bytes
    $plan = [pscustomobject]@{
        Target = $target
        Items = $items
        Stats = $stats
    }
    $Plans.Add($plan) | Out-Null

    Write-Log ("TARGET {0}: root={1}" -f $target.Name, $target.Root)
    Write-Log ("  Reason={0}" -f $target.Reason)
    Write-Log ("  EligibleRoots={0}, ItemsScanned={1}, Size={2}, Errors={3}, Skipped={4}, Truncated={5}" -f $items.Count, $stats.Count, (Format-Bytes $stats.Bytes), $stats.Errors, $stats.Skipped, $stats.Truncated)
}

Write-Log ("Estimated removable cache size: {0}" -f (Format-Bytes $TotalBytes))

if ($Plans.Count -eq 0) {
    Write-Log 'No eligible cache items found.'
    exit 0
}

if ($EffectiveDryRun) {
    Write-Log 'DRY RUN complete. No filesystem changes were made.'
    Write-Log 'To request a real run, call this script with -DryRun:$false and type YES at the prompt.'
    exit 0
}

$truncatedPlans = @($Plans | Where-Object { $_.Stats.Truncated })
if ($truncatedPlans.Count -gt 0) {
    Write-Log 'Refusing real run because at least one target scan was truncated. Increase limits or inspect manually.'
    exit 3
}

Write-Log 'Real run requested. Type YES to proceed. Any other input aborts.'
$answer = Read-Host 'Type YES to clean only the listed safe cache candidates'
if ($answer -cne 'YES') {
    Write-Log 'User did not type YES. Aborted without filesystem changes.'
    exit 2
}

$removedRoots = 0
$failedRoots = 0

foreach ($plan in $Plans) {
    $target = $plan.Target
    foreach ($item in $plan.Items) {
        if (-not (Test-PathUnderRoot -Path $item.FullName -Root $target.Root)) {
            Write-Log ("SKIP outside root: {0}" -f $item.FullName)
            continue
        }
        if (Test-BlockedFragment -Path $item.FullName) {
            Write-Log ("SKIP blocked fragment: {0}" -f $item.FullName)
            continue
        }
        if (Test-ReparsePoint -Item $item) {
            Write-Log ("SKIP reparse point: {0}" -f $item.FullName)
            continue
        }
        try {
            Remove-Item -LiteralPath $item.FullName -Recurse -Force -ErrorAction Stop
            $removedRoots++
            Write-Log ("REMOVED: {0}" -f $item.FullName)
        }
        catch {
            $failedRoots++
            Write-Log ("FAILED: {0} :: {1}" -f $item.FullName, $_.Exception.Message)
        }
    }
}

Write-Log ("Finished. Removed root items={0}, failed root items={1}" -f $removedRoots, $failedRoots)
Write-Log 'If some cache files failed, close related apps and rerun only after reviewing this log.'
