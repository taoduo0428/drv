# Generated cleanup preview. It only prints candidates.
param([switch]$ShowChildren)
$ErrorActionPreference = 'Continue'
$Candidates = @(
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\AppData\Local\Docker'
        Risk = 'review'
        Reason = 'Docker Desktop local data; prefer docker system prune after review'
        ObservedSizeBytes = 2660637205
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\自学\ciu-learn-landing\.next'
        Risk = 'review'
        Reason = 'Next.js build cache/output; keep if deploy artifacts are stored only here'
        ObservedSizeBytes = 1470336950
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\AppData\Local\npm-cache'
        Risk = 'safe'
        Reason = 'npm cache'
        ObservedSizeBytes = 663951995
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\自学\ciu-learn-landing\node_modules'
        Risk = 'safe'
        Reason = 'dependency directory; usually recreated with npm/pnpm/yarn install'
        ObservedSizeBytes = 495313339
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\zjl项目\MAS-Market-Sim\.venv'
        Risk = 'review'
        Reason = 'Python virtual environment; safe only if dependencies are tracked'
        ObservedSizeBytes = 448813428
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\.docker'
        Risk = 'review'
        Reason = 'Docker CLI/config data; do not blindly remove'
        ObservedSizeBytes = 396201816
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\AppData\Local\Temp'
        Risk = 'safe'
        Reason = 'user temp directory; close apps first'
        ObservedSizeBytes = 382887573
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\大学\大三上\数据挖掘\.venv'
        Risk = 'review'
        Reason = 'Python virtual environment; safe only if dependencies are tracked'
        ObservedSizeBytes = 213305582
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\个人知识库\项目\douyin\.venv'
        Risk = 'review'
        Reason = 'Python virtual environment; safe only if dependencies are tracked'
        ObservedSizeBytes = 192677480
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\工作简历\Leeway-master\.venv'
        Risk = 'review'
        Reason = 'Python virtual environment; safe only if dependencies are tracked'
        ObservedSizeBytes = 73281325
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\open-reverselab-main\tools\skills\mcp\ReverseLabToolsMCP\.venv'
        Risk = 'review'
        Reason = 'Python virtual environment; safe only if dependencies are tracked'
        ObservedSizeBytes = 49715881
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\个人知识库\工作\js\项目合并\douyin\.venv'
        Risk = 'review'
        Reason = 'Python virtual environment; safe only if dependencies are tracked'
        ObservedSizeBytes = 41235290
    }
    [pscustomobject]@{
        Path = 'C:\Users\lenovo\Desktop\自学\ciu-learn-landing\android\app\build'
        Risk = 'review'
        Reason = 'build output; keep if release artifacts are stored only here'
        ObservedSizeBytes = 31979800
    }
)

function Format-Bytes([double]$Bytes) {
    $units = @('B','KB','MB','GB','TB')
    $value = $Bytes
    $i = 0
    while ($value -ge 1024 -and $i -lt $units.Length - 1) { $value = $value / 1024; $i++ }
    if ($i -eq 0) { return ('{0:N0} {1}' -f $value, $units[$i]) }
    return ('{0:N2} {1}' -f $value, $units[$i])
}

function Get-FolderSizeSafe([string]$Path) {
    try {
        if (-not (Test-Path -LiteralPath $Path)) { return $null }
        $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
        if (-not $item.PSIsContainer) { return $item.Length }
        $sum = 0L
        Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { $sum += $_.Length }
        return $sum
    } catch { return $null }
}

Write-Host 'DRY RUN ONLY - no cleanup action will be performed.'
$total = 0L
foreach ($c in $Candidates) {
    $current = Get-FolderSizeSafe -Path $c.Path
    if ($null -eq $current) {
        Write-Host ('MISSING  {0}  {1}' -f $c.Risk, $c.Path)
        continue
    }
    $total += [int64]$current
    Write-Host ('CANDIDATE [{0}] {1}  Observed={2} Current={3}' -f $c.Risk, $c.Path, (Format-Bytes $c.ObservedSizeBytes), (Format-Bytes $current))
    Write-Host ('  Reason: {0}' -f $c.Reason)
    if ($ShowChildren -and (Test-Path -LiteralPath $c.Path -PathType Container)) {
        Get-ChildItem -LiteralPath $c.Path -Force -ErrorAction SilentlyContinue | Select-Object -First 20 FullName,Length,LastWriteTime | Format-Table -AutoSize
    }
}
Write-Host ('Potential space represented by listed candidates: {0}' -f (Format-Bytes $total))
Write-Host 'Review the report before creating any explicit cleanup plan.'
