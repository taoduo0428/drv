[CmdletBinding()]
param(
    [string]$ScriptPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ScriptPath)) {
    $ScriptPath = Join-Path $PSScriptRoot 'codex-seetacloud-tunnel-watchdog.ps1'
}

if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
    throw "Watchdog script not found: $ScriptPath"
}

$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $ScriptPath,
    [ref]$tokens,
    [ref]$parseErrors
) | Out-Null

if ($parseErrors.Count -gt 0) {
    throw "Watchdog script has $($parseErrors.Count) PowerShell parse error(s)."
}

$content = Get-Content -LiteralPath $ScriptPath -Raw -Encoding UTF8
$requiredFragments = @(
    'codex-tunnel-alex-56608',
    'Clear-StaleRemoteTunnelLease',
    'STALE_LEASE_TERMINATED=',
    'ClearAllForwardings=yes',
    'ownerPid=$PPID',
    '-sshd-$ownerPid sleep 2147483647'
)

$missing = @(
    $requiredFragments | Where-Object {
        $content.IndexOf($_, [System.StringComparison]::Ordinal) -lt 0
    }
)

if ($missing.Count -gt 0) {
    throw "Missing stale-lease safeguards: $($missing -join ', ')"
}

$sshArgumentsMatch = [regex]::Match(
    $content,
    '(?s)\$sshArguments\s*=\s*@\((.*?)\)'
)
if (-not $sshArgumentsMatch.Success) {
    throw 'Could not locate $sshArguments.'
}
if ($sshArgumentsMatch.Groups[1].Value -match '["'']-N["'']') {
    throw 'The production SSH invocation still uses -N, so the remote lease marker cannot run.'
}

$cleanupArgumentsMatch = [regex]::Match(
    $content,
    '(?s)\$cleanupArguments\s*=\s*@\((.*?)\)'
)
if (-not $cleanupArgumentsMatch.Success) {
    throw 'Could not locate $cleanupArguments.'
}
$cleanupArgumentsBody = $cleanupArgumentsMatch.Groups[1].Value
if ($cleanupArgumentsBody.IndexOf(
        '$cleanupCommand',
        [System.StringComparison]::Ordinal
    ) -lt 0) {
    throw 'Cleanup SSH invocation does not pass the generated inline command.'
}

foreach ($requiredFragment in @(
    "markerPrefix='__REMOTE_LEASE_MARKER__-sshd-'",
    'index($3,prefix)==1 {print $1, $2, $3}',
    'while [ $# -ge 3 ]; do',
    'shift 3',
    'ownerPid=${markerName##*-sshd-}',
    'ownerComm="$(ps -p "$ownerPid" -o comm=',
    'ownerAge="$(ps -p "$ownerPid" -o etimes=',
    'if [ "x$ownerComm" != xsshd ]; then',
    'delta=$((ownerAge - markerAge))',
    'if [ $delta -gt 30 ]; then',
    'kill -TERM "$ownerPid"',
    'STALE_OWNER_REJECTED=',
    '$cleanupCommand = $cleanupTemplate.Replace('
)) {
    if ($content.IndexOf(
            $requiredFragment,
            [System.StringComparison]::Ordinal
        ) -lt 0) {
        throw "Cleanup cannot safely recover the owning sshd: $requiredFragment"
    }
}

if ($content -match '(?m)^\s*\$cleanupTemplate\s*\|\s*&\s*\$SshExe') {
    throw 'Windows PowerShell 5.1 adds a UTF-8 BOM when piping text to native SSH.'
}

if ($content.IndexOf(
        'exec -a $remoteLeaseMarker sleep 2147483647',
        [System.StringComparison]::Ordinal
    ) -ge 0) {
    throw 'Lease marker does not retain the owning sshd PID.'
}

if ($content.IndexOf(
        'print $1 ":" $2 ":" $3',
        [System.StringComparison]::Ordinal
    ) -ge 0) {
    throw 'Nested AWK double quotes are stripped by Windows native argument passing.'
}

Write-Output 'WATCHDOG_STATIC_TEST_OK'
