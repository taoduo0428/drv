[CmdletBinding()]
param(
    [string]$SshExe = "",
    [string]$SshConfig = "$env:APPDATA\Code\User\ssh-seetacloud-split.conf",
    [string]$HostAlias = "seetacloud-gpu-tunnel-alex",
    [ValidateRange(5, 300)]
    [int]$ExistingCheckSeconds = 15,
    [ValidateRange(15, 600)]
    [int]$MaxBackoffSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SshExe)) {
    $sshCommand = Get-Command ssh.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($sshCommand) {
        $SshExe = $sshCommand.Source
    }
    else {
        $windowsDirectory = [Environment]::GetEnvironmentVariable(
            "WINDIR",
            "Machine"
        )
        if ([string]::IsNullOrWhiteSpace($windowsDirectory)) {
            throw "Could not resolve ssh.exe because WINDIR is unavailable."
        }
        $systemCandidate = Join-Path (
            Join-Path $windowsDirectory "System32"
        ) "OpenSSH\ssh.exe"
        if (-not (Test-Path -LiteralPath $systemCandidate -PathType Leaf)) {
            throw "ssh.exe not found at $systemCandidate"
        }
        $SshExe = $systemCandidate
    }
}

$mutexName = "Local\CodexSeetaCloudTunnelAlexWatchdog"
$createdNew = $false
$mutex = [System.Threading.Mutex]::new($true, $mutexName, [ref]$createdNew)

if (-not $createdNew) {
    $mutex.Dispose()
    exit 0
}

$logPath = Join-Path $PSScriptRoot "codex-seetacloud-tunnel-watchdog.log"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$maxLogBytes = 1MB
$remoteLeaseMarker = "codex-tunnel-alex-56608"
$remoteLeaseCommand = (
    'ownerPid=$PPID; exec -a {0}-sshd-$ownerPid sleep 2147483647' -f
    $remoteLeaseMarker
)

function Write-WatchdogLog {
    param([Parameter(Mandatory)][string]$Message)

    try {
        if ((Test-Path -LiteralPath $logPath) -and
            ((Get-Item -LiteralPath $logPath).Length -gt $maxLogBytes)) {
            $resetLine = "{0} [INFO] Log reset after reaching {1} bytes.{2}" -f (
                Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            ), $maxLogBytes, [Environment]::NewLine
            [System.IO.File]::WriteAllText($logPath, $resetLine, $utf8NoBom)
        }

        $line = "{0} {1}{2}" -f (
            Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        ), $Message, [Environment]::NewLine
        [System.IO.File]::AppendAllText($logPath, $line, $utf8NoBom)
    }
    catch {
        # Logging must never terminate the tunnel watchdog.
    }
}

function Test-ExistingTunnelProcess {
    try {
        $matches = @(
            Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction Stop |
                Where-Object {
                    $_.CommandLine -and
                    $_.CommandLine.IndexOf(
                        $HostAlias,
                        [System.StringComparison]::OrdinalIgnoreCase
                    ) -ge 0
                }
        )
        return $matches.Count -gt 0
    }
    catch {
        Write-WatchdogLog (
            "[WARN] Could not inspect existing ssh.exe processes: {0}" -f
            $_.Exception.Message
        )
        return $false
    }
}

function Clear-StaleRemoteTunnelLease {
    $cleanupTemplate = @'
markerPrefix='__REMOTE_LEASE_MARKER__-sshd-'
fields="$(ps -eo pid=,etimes=,args= | awk -v prefix="$markerPrefix" 'index($3,prefix)==1 {print $1, $2, $3}')"
set -- $fields
if [ $# -eq 0 ]; then
    printf 'STALE_LEASE_NOT_FOUND\n'
    exit 0
fi

terminated=0
while [ $# -ge 3 ]; do
    markerPid=$1
    markerAge=$2
    markerName=$3
    shift 3
    ownerPid=${markerName##*-sshd-}

    case $ownerPid in
        ''|*[!0-9]*)
            printf 'STALE_OWNER_REJECTED=marker:%s reason:bad-owner-pid\n' "$markerPid"
            continue
            ;;
    esac

    ownerComm="$(ps -p "$ownerPid" -o comm= | awk 'NR==1 {print $1}')"
    ownerAge="$(ps -p "$ownerPid" -o etimes= | awk 'NR==1 {print $1}')"
    if [ "x$ownerComm" != xsshd ]; then
        printf 'STALE_OWNER_REJECTED=owner:%s marker:%s reason:not-sshd\n' "$ownerPid" "$markerPid"
        continue
    fi
    case $ownerAge in
        ''|*[!0-9]*)
            printf 'STALE_OWNER_REJECTED=owner:%s marker:%s reason:bad-owner-age\n' "$ownerPid" "$markerPid"
            continue
            ;;
    esac

    delta=$((ownerAge - markerAge))
    if [ $delta -lt 0 ]; then
        delta=$((-delta))
    fi
    if [ $delta -gt 30 ]; then
        printf 'STALE_OWNER_REJECTED=owner:%s marker:%s reason:age-mismatch-%s\n' "$ownerPid" "$markerPid" "$delta"
        continue
    fi

    if kill -TERM "$ownerPid"; then
        kill -TERM "$markerPid" 2>/dev/null || true
        printf 'STALE_LEASE_TERMINATED=owner:%s marker:%s\n' "$ownerPid" "$markerPid"
        terminated=1
    else
        printf 'STALE_OWNER_REJECTED=owner:%s marker:%s reason:kill-failed\n' "$ownerPid" "$markerPid"
    fi
done

if [ $terminated -eq 0 ]; then
    printf 'STALE_LEASE_NOT_FOUND\n'
fi
'@
    $cleanupCommand = $cleanupTemplate.Replace(
        "__REMOTE_LEASE_MARKER__",
        $remoteLeaseMarker
    )
    $cleanupArguments = @(
        "-T",
        "-F", $SshConfig,
        "-o", "BatchMode=yes",
        "-o", "ClearAllForwardings=yes",
        "-o", "ConnectTimeout=10",
        "-o", "ConnectionAttempts=1",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=2",
        "-o", "LogLevel=ERROR",
        $HostAlias,
        $cleanupCommand
    )

    Write-WatchdogLog (
        "[WARN] Remote port is occupied; checking marker {0}." -f
        $remoteLeaseMarker
    )

    try {
        $cleanupOutput = @(& $SshExe @cleanupArguments 2>&1)
        $cleanupExitCode = $LASTEXITCODE
        $terminated = $false

        foreach ($entry in $cleanupOutput) {
            $message = $entry.ToString().Trim()
            if ($message.Length -eq 0) {
                continue
            }
            Write-WatchdogLog ("[LEASE] {0}" -f $message)
            if ($message -match '^STALE_LEASE_TERMINATED=') {
                $terminated = $true
            }
        }

        if ($cleanupExitCode -ne 0) {
            Write-WatchdogLog (
                "[WARN] Remote lease check exited with code {0}." -f
                $cleanupExitCode
            )
            return $false
        }

        return $terminated
    }
    catch {
        Write-WatchdogLog (
            "[WARN] Remote lease check failed: {0}" -f
            $_.Exception.Message
        )
        return $false
    }
}

$sshArguments = @(
    "-T",
    "-F", $SshConfig,
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=10",
    "-o", "ConnectionAttempts=1",
    "-o", "ExitOnForwardFailure=yes",
    "-o", "ServerAliveInterval=15",
    "-o", "ServerAliveCountMax=2",
    "-o", "TCPKeepAlive=yes",
    "-o", "LogLevel=ERROR",
    $HostAlias,
    $remoteLeaseCommand
)

$retryDelaySeconds = 5
$reportedExistingTunnel = $false

Write-WatchdogLog (
    "[INFO] Watchdog started. host={0} config={1}" -f
    $HostAlias, $SshConfig
)

try {
    while ($true) {
        try {
            if (-not (Test-Path -LiteralPath $SshExe -PathType Leaf)) {
                throw "ssh.exe not found at $SshExe"
            }

            if (-not (Test-Path -LiteralPath $SshConfig -PathType Leaf)) {
                throw "SSH config not found at $SshConfig"
            }

            if (Test-ExistingTunnelProcess) {
                if (-not $reportedExistingTunnel) {
                    Write-WatchdogLog (
                        "[INFO] Existing tunnel process detected; monitoring it."
                    )
                    $reportedExistingTunnel = $true
                }

                Start-Sleep -Seconds $ExistingCheckSeconds
                continue
            }

            $reportedExistingTunnel = $false
            $startedAt = [DateTime]::UtcNow
            Write-WatchdogLog "[INFO] Starting SSH reverse tunnel."

            & $SshExe @sshArguments 2>&1 |
                ForEach-Object {
                    if ($_ -ne $null -and $_.ToString().Length -gt 0) {
                        Write-WatchdogLog (
                            "[SSH] {0}" -f $_.ToString().Trim()
                        )
                    }
                }

            $exitCode = $LASTEXITCODE
            $lifetimeSeconds = [int](
                ([DateTime]::UtcNow - $startedAt).TotalSeconds
            )

            if ($lifetimeSeconds -ge 60) {
                $retryDelaySeconds = 5
            }
            else {
                $retryDelaySeconds = [Math]::Min(
                    $MaxBackoffSeconds,
                    [Math]::Max(5, $retryDelaySeconds * 2)
                )
            }

            Write-WatchdogLog (
                "[WARN] SSH tunnel exited. code={0} lifetime={1}s retry={2}s" -f
                $exitCode, $lifetimeSeconds, $retryDelaySeconds
            )
        }
        catch {
            $errorMessage = $_.Exception.Message
            $leaseCleared = $false

            if ($errorMessage -match
                'remote port forwarding failed for listen port 56608') {
                $leaseCleared = Clear-StaleRemoteTunnelLease
            }

            if ($leaseCleared) {
                $retryDelaySeconds = 5
            }
            else {
                $retryDelaySeconds = [Math]::Min(
                    $MaxBackoffSeconds,
                    [Math]::Max(15, $retryDelaySeconds * 2)
                )
            }
            Write-WatchdogLog (
                "[ERROR] Watchdog cycle failed: {0}; retry={1}s" -f
                $errorMessage, $retryDelaySeconds
            )
        }

        Start-Sleep -Seconds $retryDelaySeconds
    }
}
finally {
    Write-WatchdogLog "[INFO] Watchdog stopped."
    if ($createdNew) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}
