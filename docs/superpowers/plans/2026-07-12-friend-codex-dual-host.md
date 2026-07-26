# Friend Codex 双端隔离与自动恢复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在同伴自己的 Windows 电脑上实现“Windows 本地 Codex + SeetaCloud 远程 Codex”同时可用，并让 `56609` 反向隧道在换 Wi-Fi、VPN 切换和睡眠恢复后自动重连，同时不影响成员 A 的 `56608`、`/root/.codex-alex` 和 `codex-vscode-alex.exe`。

**Architecture:** 将旧的单连接结构拆成两个 SSH Host：`seetacloud-gpu-vscode-friend` 只承载 VS Code Remote-SSH，`seetacloud-gpu-tunnel-friend` 只承载 `127.0.0.1:56609 -> 127.0.0.1:54929`。VS Code 的 application-scope `chatgpt.cliExecutable` 只写跨平台同名命令 `codex-vscode-friend.exe`；Windows 将它映射到本地官方扩展内置 CLI，Linux 将它映射到设置 `CODEX_HOME=/root/.codex-friend` 的包装器。远程 VS Code Server 独占 `/root/autodl-tmp/.vscode-server-friend`。

**Tech Stack:** Windows PowerShell 5.1、Windows OpenSSH、VS Code Remote-SSH、OpenAI 官方 Codex 扩展、Bash、Codex CLI、Cockpit Tools API。

---

## 0. 已知事实、未知值和硬边界

### 已知且固定

| 项目 | 值 |
|---|---|
| 同伴 Windows Cockpit | `127.0.0.1:54929` |
| 同伴服务器入口 | `127.0.0.1:56609` |
| Provider | `cockpit_b` |
| 同伴服务端 Codex 目录 | `/root/.codex-friend` |
| 同伴服务端 CLI | `/root/.local/bin/codex-friend` |
| 新跨平台命令名 | `codex-vscode-friend.exe` |
| 新 VS Code SSH Host | `seetacloud-gpu-vscode-friend` |
| 新隧道 SSH Host | `seetacloud-gpu-tunnel-friend` |
| 新 VS Code Server 目录 | `/root/autodl-tmp/.vscode-server-friend` |

### 禁止影响

```text
127.0.0.1:56608
/root/.codex-alex
/root/.local/bin/codex-alex
codex-vscode-alex.exe
成员 A 的 Windows SSH 配置、watchdog、启动项和 VS Code Server
```

不得修改 `/root/.codex`，不得向 `/root/.bashrc`、`/root/.profile` 或全局环境写入 `CODEX_HOME`。不得使用 `killall ssh`、`pkill ssh`、`taskkill /IM ssh.exe`、`rm -rf` 或整文件覆盖现有设置。

### 必须现场发现，禁止猜测

1. 同伴 Windows 用户目录：用 `$env:USERPROFILE`。
2. VS Code User 目录：用 `$env:APPDATA\Code\User`。
3. 旧 SSH Host 的真实 `HostName`、`Port`、`User`、`IdentityFile`：用 `ssh -G AutoDL-VLR`。
4. OpenSSH 路径：用 `Get-Command ssh.exe`。
5. 官方 Codex 扩展和内置 CLI 路径：扫描 `$env:USERPROFILE\.vscode\extensions\openai.chatgpt-*` 并核对 `package.json` 的 publisher/name。
6. Windows 可写且已经位于 PATH 的别名目录：只允许优先使用 `$env:APPDATA\npm` 或 `$env:LOCALAPPDATA\Microsoft\WindowsApps`；两者都不在 PATH 时停止，不擅自修改 PATH。
7. 同伴真实模型 ID：从经过认证的 `GET /v1/models` 获取，不复制成员 A 的模型 ID。
8. 远程扩展宿主的 PATH 是否包含 `/root/.local/bin`：通过非交互 SSH 的 `command -v codex-vscode-friend.exe` 验证。

### 可靠性故障图

| 故障 | 检测 | 抑制 | 恢复 |
|---|---|---|---|
| Cockpit 未启动/54929 未监听 | 本地 `/v1/models` 超时或拒绝 | 5 秒超时，不无限等待 | 启动 Cockpit，隧道无需重建 |
| Wi-Fi/VPN/睡眠切断 SSH | ssh 子进程退出、watchdog 日志 | 单实例、15 秒 keepalive、最多 60 秒退避 | watchdog 自动重拨 |
| 旧会话暂占 56609 | `remote port forwarding failed` | lease marker 记录其 owner sshd PID | watchdog 核验 marker、owner 为 sshd 且两者年龄一致后，只终止该精确 owner 和 marker；无可信映射时不误杀 |
| 多窗口争抢 56609 | 多个 ssh 命令行或绑定失败 | 只有 tunnel Host 可绑定；互斥锁防止重复 watchdog | 保留唯一 friend tunnel 进程 |
| AutoDL Host/Port 改变 | `ConnectTimeout=10` 后失败 | 两个别名共用一个 SSH 公共块 | 更新公共块一次并重启 watchdog |
| Codex 扩展升级 | Windows alias 与最新内置 CLI 哈希不同 | 登录时执行 alias repair | 原子替换 alias；旧文件先备份 |
| 远程 CLI/扩展版本不一致 | 本地/远端 `--version`、IDE app-server 报错 | Linux wrapper 优先选择独立远程扩展内置 CLI | 重新运行 wrapper/扩展验证 |
| 两人共享 root | 任一 root 可读另一方文件 | 只做配置隔离，不宣称权限隔离 | 真正保密只能改用不同 Linux 用户 |

---

## Task 1：在同伴电脑做只读基线审计

**Files:** 不修改文件。

- [ ] **Step 1：确认命令和用户路径**

在同伴 Windows PowerShell 中执行：

```powershell
$ErrorActionPreference = "Stop"
$LegacyHost = "AutoDL-VLR"
$SshExe = (Get-Command ssh.exe -ErrorAction Stop).Source
$CodeUserDir = Join-Path $env:APPDATA "Code\User"
$SettingsPath = Join-Path $CodeUserDir "settings.json"
$MainSshConfig = Join-Path $env:USERPROFILE ".ssh\config"
$BridgeRoot = Join-Path $env:LOCALAPPDATA "CodexFriendBridge"

[pscustomobject]@{
    UserProfile   = $env:USERPROFILE
    CodeUserDir   = $CodeUserDir
    SettingsPath  = $SettingsPath
    MainSshConfig = $MainSshConfig
    BridgeRoot    = $BridgeRoot
    SshExe        = $SshExe
} | Format-List
```

预期：所有路径都指向同伴自己的 Windows 用户，而不是 `C:\Users\lenovo`。任何路径不存在时先报告，不猜测。

- [ ] **Step 2：解析旧 Host 的真实连接参数**

```powershell
$Resolved = & $SshExe -G $LegacyHost
$Resolved | Select-String -Pattern '^(hostname|port|user|identityfile|proxyjump|proxycommand) '
```

预期至少出现：`hostname`、`port`、`user root` 和一个真实存在的 `identityfile`。只显示私钥路径，不读取私钥内容。

- [ ] **Step 3：验证非交互 SSH**

```powershell
& $SshExe -o BatchMode=yes -o ClearAllForwardings=yes -o ConnectTimeout=10 `
    $LegacyHost "printf 'FRIEND_SSH_OK\n'"
```

预期：`FRIEND_SSH_OK`。如果要求密码、验证码或 Host Key 确认，先人工完成一次普通 SSH 连接，再重测；watchdog 不能依赖交互输入。

- [ ] **Step 4：核对本地 Cockpit**

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object LocalPort -eq 54929 |
    Select-Object LocalAddress,LocalPort,OwningProcess

try {
    Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:54929/v1/models' `
        -TimeoutSec 5 | Select-Object StatusCode
}
catch {
    if ($_.Exception.Response) {
        [int]$_.Exception.Response.StatusCode
    }
    else {
        throw
    }
}
```

预期：监听地址是 `127.0.0.1`，无 Key 请求返回 `401`。如果实际 Cockpit 端口不是 54929，停止实施并记录真实端口，后续所有配置统一替换，不能同时保留两个猜测值。

- [ ] **Step 5：核对当前 VS Code/Codex 状态**

```powershell
Get-Content -LiteralPath $SettingsPath -Encoding UTF8 |
    Select-String -Pattern 'chatgpt.cliExecutable|remote.SSH.configFile|remote.SSH.serverInstallPath'

Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE '.vscode\extensions') `
    -Directory -Filter 'openai.chatgpt-*' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name,FullName,LastWriteTime
```

确认旧值仍是 `/root/.local/bin/codex-friend`，并记录同伴实际扩展版本。

- [ ] **Step 6：记录服务器端口基线**

```powershell
& $SshExe -o BatchMode=yes -o ClearAllForwardings=yes $LegacyHost `
    "ss -lntp | grep -E '127.0.0.1:(56608|56609)' || true"
```

记录 56608 和 56609 当前状态。不得停止 56608。

**Gate 1：** SSH、54929、扩展路径和旧设置都已得到真实证据；否则不进入写入阶段。

---

## Task 2：创建最小时间戳备份

**Files:**
- Backup: `%LOCALAPPDATA%\CodexFriendBridge\backup\YYYYMMDD-HHMMSS\settings.json`
- Backup: `%LOCALAPPDATA%\CodexFriendBridge\backup\YYYYMMDD-HHMMSS\ssh-config`
- Backup: 已存在的 friend split config 和脚本（如有）

- [ ] **Step 1：只备份将触碰的 Windows 文件**

```powershell
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $BridgeRoot "backup\$Stamp"
New-Item -ItemType Directory -Path $BackupDir | Out-Null

foreach ($item in @(
    @{ Path = $SettingsPath; Name = 'settings.json' },
    @{ Path = $MainSshConfig; Name = 'ssh-config' },
    @{ Path = (Join-Path $CodeUserDir 'ssh-seetacloud-friend.conf'); Name = 'ssh-seetacloud-friend.conf' },
    @{ Path = (Join-Path $BridgeRoot 'repair-codex-friend-cli-alias.ps1'); Name = 'repair-codex-friend-cli-alias.ps1' },
    @{ Path = (Join-Path $BridgeRoot 'codex-seetacloud-tunnel-watchdog-friend.ps1'); Name = 'codex-seetacloud-tunnel-watchdog-friend.ps1' },
    @{ Path = (Join-Path $BridgeRoot 'start-codex-friend-bridge.ps1'); Name = 'start-codex-friend-bridge.ps1' },
    @{ Path = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\Codex-SeetaCloud-Tunnel-Friend.lnk'); Name = 'Codex-SeetaCloud-Tunnel-Friend.lnk' }
)) {
    if (Test-Path -LiteralPath $item.Path -PathType Leaf) {
        Copy-Item -LiteralPath $item.Path -Destination (Join-Path $BackupDir $item.Name)
    }
}

Get-ChildItem -LiteralPath $BackupDir -File |
    Get-FileHash -Algorithm SHA256 |
    Select-Object Path,Hash
```

不备份整个用户目录，不复制 SSH 私钥，不复制 Cockpit Key。

- [ ] **Step 2：只备份将触碰的服务端配置/脚本**

在服务器终端中执行以下代码。备份目录名由 `date +%Y%m%d-%H%M%S` 生成，不需要人工填写：

```bash
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="/root/.codex-friend/backups/$stamp"
mkdir -p "$backup_dir"

for source in \
  /root/.codex-friend/config.toml \
  /root/.local/bin/codex-friend \
  /root/.local/bin/codex-vscode-friend.exe \
  /root/.local/bin/read-cockpit-b-key
do
  if [[ -e "$source" || -L "$source" ]]; then
    cp -a "$source" "$backup_dir/"
  fi
done

printf 'SERVER_BACKUP_DIR=%s\n' "$backup_dir"
ls -la "$backup_dir"
```

只复制以下已存在文件：

```text
/root/.codex-friend/config.toml
/root/.local/bin/codex-friend
/root/.local/bin/codex-vscode-friend.exe
/root/.local/bin/read-cockpit-b-key
```

不复制 `/root/.codex-friend/secrets/cockpit-b.key`，避免产生额外 Key 副本。

**Gate 2：** touched files 均有可读备份；不存在的文件明确记录为“新建”。

---

## Task 3：创建独立 SSH 配置，不再让 VS Code 连接承载 56609

**Files:**
- Create/Modify: `%APPDATA%\Code\User\ssh-seetacloud-friend.conf`

- [ ] **Step 1：从 `ssh -G AutoDL-VLR` 生成新配置**

```powershell
$SplitConfig = Join-Path $CodeUserDir 'ssh-seetacloud-friend.conf'
$Resolved = & $SshExe -G $LegacyHost

function Get-SshResolvedValue {
    param([Parameter(Mandatory)][string]$Name)
    $line = $Resolved | Where-Object { $_ -match "^$([regex]::Escape($Name))\s+" } |
        Select-Object -First 1
    if (-not $line) { throw "ssh -G did not return $Name" }
    return ($line -replace "^$([regex]::Escape($Name))\s+", '').Trim()
}

$HostNameValue = Get-SshResolvedValue 'hostname'
$PortValue = Get-SshResolvedValue 'port'
$UserValue = Get-SshResolvedValue 'user'
$IdentityValues = @(
    $Resolved | Where-Object { $_ -match '^identityfile\s+' } |
        ForEach-Object { ($_ -replace '^identityfile\s+', '').Trim() }
)
$IdentityFileValue = $IdentityValues | Where-Object {
    $expanded = $_ -replace '^~', $env:USERPROFILE
    Test-Path -LiteralPath $expanded -PathType Leaf
} | Select-Object -First 1

if (-not $IdentityFileValue) {
    throw 'No existing IdentityFile from ssh -G could be verified.'
}

$IncludePath = $MainSshConfig.Replace('\','/')
$IdentityForConfig = ($IdentityFileValue -replace '^~', $env:USERPROFILE).Replace('\','/')
$Content = @"
Host seetacloud-gpu-vscode-friend seetacloud-gpu-tunnel-friend
    HostName $HostNameValue
    User $UserValue
    Port $PortValue
    IdentityFile "$IdentityForConfig"
    IdentitiesOnly yes
    ServerAliveInterval 15
    ServerAliveCountMax 2
    TCPKeepAlive yes

Host seetacloud-gpu-tunnel-friend
    RemoteForward 127.0.0.1:56609 127.0.0.1:54929
    ExitOnForwardFailure yes

Include "$IncludePath"
"@

$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($SplitConfig, $Content, $Utf8NoBom)
```

公共连接参数只写一次，AutoDL Host/Port 变化时只需改一个块。

- [ ] **Step 2：验证两个 Host 的职责没有混合**

```powershell
& $SshExe -F $SplitConfig -G seetacloud-gpu-vscode-friend |
    Select-String -Pattern '^(hostname|port|user|identityfile|remoteforward) '

& $SshExe -F $SplitConfig -G seetacloud-gpu-tunnel-friend |
    Select-String -Pattern '^(hostname|port|user|identityfile|remoteforward|exitonforwardfailure) '
```

验收：

```text
seetacloud-gpu-vscode-friend   不得出现 56609 RemoteForward
seetacloud-gpu-tunnel-friend   必须出现 127.0.0.1:56609 -> 127.0.0.1:54929
```

- [ ] **Step 3：验证新 VS Code Host 的普通 SSH**

```powershell
& $SshExe -F $SplitConfig -o BatchMode=yes -o ClearAllForwardings=yes `
    -o ConnectTimeout=10 seetacloud-gpu-vscode-friend `
    "printf 'FRIEND_NEW_HOST_OK\n'"
```

预期：`FRIEND_NEW_HOST_OK`。

**Gate 3：** 两个 Host 均可解析，只有 tunnel Host 携带 56609。

---

## Task 4：创建 Windows 端 `codex-vscode-friend.exe` 自动修复器

**Files:**
- Create: `%LOCALAPPDATA%\CodexFriendBridge\repair-codex-friend-cli-alias.ps1`
- Create at runtime: PATH 中的 `codex-vscode-friend.exe`

- [ ] **Step 1：创建 BridgeRoot**

```powershell
if (-not (Test-Path -LiteralPath $BridgeRoot)) {
    New-Item -ItemType Directory -Path $BridgeRoot | Out-Null
}
```

- [ ] **Step 2：写入完整 repair 脚本**

```powershell
[CmdletBinding()]
param([string]$AliasName = 'codex-vscode-friend.exe')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$extensionRoots = @(
    (Join-Path $env:USERPROFILE '.vscode\extensions'),
    (Join-Path $env:USERPROFILE '.vscode-insiders\extensions')
)

$officialExtensions = foreach ($root in $extensionRoots) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
    foreach ($dir in Get-ChildItem -LiteralPath $root -Directory -Filter 'openai.chatgpt-*') {
        $packagePath = Join-Path $dir.FullName 'package.json'
        if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) { continue }
        try {
            $package = Get-Content -LiteralPath $packagePath -Raw -Encoding UTF8 |
                ConvertFrom-Json
            if ($package.publisher -eq 'openai' -and $package.name -eq 'chatgpt') {
                [pscustomobject]@{
                    Path = $dir.FullName
                    Version = [string]$package.version
                    LastWriteTime = $dir.LastWriteTimeUtc
                }
            }
        }
        catch { continue }
    }
}

$selectedExtension = $officialExtensions |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $selectedExtension) {
    throw 'Official openai.chatgpt extension was not found in the local VS Code extension roots.'
}

$archFolder = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
    'windows-aarch64'
}
else {
    'windows-x86_64'
}

$sourceCli = Get-ChildItem -LiteralPath $selectedExtension.Path -Recurse -File `
    -Filter 'codex.exe' |
    Where-Object { $_.FullName -like "*\bin\$archFolder\codex.exe" } |
    Select-Object -First 1
if (-not $sourceCli) {
    throw "Bundled Codex CLI for $archFolder was not found under $($selectedExtension.Path)."
}

$pathEntries = @(
    $env:PATH -split ';' |
        Where-Object { $_ } |
        ForEach-Object {
            try { [System.IO.Path]::GetFullPath($_).TrimEnd('\') } catch { $null }
        }
)
$approvedAliasDirs = @(
    (Join-Path $env:APPDATA 'npm'),
    (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps')
)

$aliasDir = $approvedAliasDirs | Where-Object {
    $candidate = [System.IO.Path]::GetFullPath($_).TrimEnd('\')
    $pathEntries | Where-Object {
        $_.Equals($candidate, [System.StringComparison]::OrdinalIgnoreCase)
    }
} | Select-Object -First 1

if (-not $aliasDir) {
    throw 'Neither %APPDATA%\npm nor %LOCALAPPDATA%\Microsoft\WindowsApps is currently on PATH. Stop and obtain approval before changing PATH.'
}
if (-not (Test-Path -LiteralPath $aliasDir -PathType Container)) {
    New-Item -ItemType Directory -Path $aliasDir | Out-Null
}

$aliasPath = Join-Path $aliasDir $AliasName
$sourceHash = (Get-FileHash -LiteralPath $sourceCli.FullName -Algorithm SHA256).Hash

if (Test-Path -LiteralPath $aliasPath -PathType Leaf) {
    $currentHash = (Get-FileHash -LiteralPath $aliasPath -Algorithm SHA256).Hash
    if ($currentHash -eq $sourceHash) {
        $resolvedCurrent = (Get-Command $AliasName -ErrorAction Stop).Source
        if (-not $resolvedCurrent.Equals(
            $aliasPath,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw "PATH resolves $AliasName to $resolvedCurrent instead of $aliasPath."
        }
        Write-Output "Alias already current: $aliasPath"
        exit 0
    }
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$tempPath = Join-Path $aliasDir "$AliasName.new-$PID-$stamp"
$backupPath = $null
$sameVolume = [System.IO.Path]::GetPathRoot($sourceCli.FullName).Equals(
    [System.IO.Path]::GetPathRoot($aliasPath),
    [System.StringComparison]::OrdinalIgnoreCase
)

if ($sameVolume) {
    try {
        New-Item -ItemType HardLink -Path $tempPath -Target $sourceCli.FullName |
            Out-Null
    }
    catch {
        Copy-Item -LiteralPath $sourceCli.FullName -Destination $tempPath
    }
}
else {
    Copy-Item -LiteralPath $sourceCli.FullName -Destination $tempPath
}

$tempHash = (Get-FileHash -LiteralPath $tempPath -Algorithm SHA256).Hash
if ($tempHash -ne $sourceHash) {
    throw 'Temporary alias hash does not match the official bundled CLI.'
}

try {
    if (Test-Path -LiteralPath $aliasPath -PathType Leaf) {
        $backupPath = "$aliasPath.backup-$stamp"
        Move-Item -LiteralPath $aliasPath -Destination $backupPath
    }
    Move-Item -LiteralPath $tempPath -Destination $aliasPath
}
catch {
    if ($backupPath -and
        (Test-Path -LiteralPath $backupPath -PathType Leaf) -and
        -not (Test-Path -LiteralPath $aliasPath)) {
        Move-Item -LiteralPath $backupPath -Destination $aliasPath
    }
    throw
}

$resolved = (Get-Command $AliasName -ErrorAction Stop).Source
if (-not $resolved.Equals(
    $aliasPath,
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    throw "PATH resolves $AliasName to $resolved instead of $aliasPath."
}
Write-Output "Alias repaired: $resolved"
Write-Output "Extension version: $($selectedExtension.Version)"
```

- [ ] **Step 3：运行并验证 repair**

```powershell
$RepairScript = Join-Path $BridgeRoot 'repair-codex-friend-cli-alias.ps1'
& powershell.exe -NoLogo -NoProfile -NonInteractive -File $RepairScript

$Alias = Get-Command codex-vscode-friend.exe -ErrorAction Stop
$Alias.Source
& $Alias.Source --version
```

预期：命令解析到同伴自己的用户级 PATH 目录，版本可输出。不得把 alias 放入系统目录或成员 A 的目录。

**Gate 4：** Windows 本地能运行 `codex-vscode-friend.exe --version`。

---

## Task 5：建立 Linux 端同名命令和独立 CODEX_HOME

**Files:**
- Modify: `/root/.local/bin/codex-friend`
- Create: `/root/.local/bin/codex-vscode-friend.exe`
- Verify only: `/root/.codex-friend/config.toml`
- Verify only: `/root/.local/bin/read-cockpit-b-key`

- [ ] **Step 1：验证现有 friend 资产，不显示 Key**

在服务器终端执行：

```bash
test -d /root/.codex-friend
test -s /root/.codex-friend/config.toml
test -x /root/.local/bin/read-cockpit-b-key
test -s /root/.codex-friend/secrets/cockpit-b.key
stat -c '%a %U %G %n' \
  /root/.codex-friend \
  /root/.codex-friend/config.toml \
  /root/.codex-friend/secrets/cockpit-b.key \
  /root/.local/bin/read-cockpit-b-key
```

预期：目录 700、配置/Key 600、helper 700。不要执行会把 helper 输出打印到屏幕的命令。

- [ ] **Step 2：将 `codex-friend` 改成“优先使用独立远程扩展内置 CLI”的包装器**

写入以下完整内容；先按 Task 2 备份旧文件，再使用临时文件 + rename 替换：

```bash
#!/usr/bin/env bash
set -euo pipefail

export CODEX_HOME=/root/.codex-friend

select_codex_cli() {
  local extension_root=/root/autodl-tmp/.vscode-server-friend/extensions
  local pattern="$extension_root/openai.chatgpt-*/bin/linux-*/codex"
  local -a candidates=()
  local candidate

  while IFS= read -r candidate; do
    candidates+=("$candidate")
  done < <(compgen -G "$pattern" | sort -V)

  local index
  for ((index=${#candidates[@]}-1; index>=0; index--)); do
    if [[ -x "${candidates[$index]}" ]]; then
      printf '%s\n' "${candidates[$index]}"
      return 0
    fi
  done

  candidate="$(type -P codex || true)"
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  return 1
}

codex_cli="$(select_codex_cli)" || {
  printf '%s\n' 'No usable Codex CLI was found.' >&2
  exit 127
}

exec "$codex_cli" "$@"
```

重要：包装器不再因为 56609 暂时离线而拒绝启动。这样 IDE 可以正常加载，隧道恢复后下一次请求即可恢复，不需要重新加载整个 VS Code。

- [ ] **Step 3：创建 Linux 同名 alias**

```bash
chmod 700 /root/.local/bin/codex-friend
alias_path=/root/.local/bin/codex-vscode-friend.exe
if [[ -e "$alias_path" || -L "$alias_path" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  mv "$alias_path" "${alias_path}.backup-${stamp}"
fi
ln -s /root/.local/bin/codex-friend "$alias_path"
```

旧 alias 只移动到时间戳备份，不盲目覆盖。

- [ ] **Step 4：验证非交互 PATH**

从同伴 Windows 执行：

```powershell
& $SshExe -F $SplitConfig -o BatchMode=yes -o ClearAllForwardings=yes `
    seetacloud-gpu-vscode-friend `
    "printf 'PATH=%s\n' \"\$PATH\"; command -v codex-vscode-friend.exe; codex-vscode-friend.exe --version"
```

预期：`command -v` 返回 `/root/.local/bin/codex-vscode-friend.exe`。如果找不到，停止并报告远程 PATH；不得擅自改 `/root/.bashrc`、`/root/.profile` 或 `/etc/environment`。此时只有两个可接受分支：

1. 经明确确认，把唯一名称 `codex-vscode-friend.exe` 安装到 `command -v codex` 所在的现有 PATH 目录；或
2. 改用同伴专用 Linux 用户，天然获得独立 HOME/PATH。

- [ ] **Step 5：验证 Provider 和 API**

如果 Task 1 已确认旧 Remote-SSH 正在提供 56609，则现在执行本步骤；如果 56609 当前离线，则先完成静态配置核对，并把下面的认证测试延后到 Task 9 Step 3。不能为了通过本步骤临时把 RemoteForward 加回 VS Code Host。

先读取当前配置中的模型，再用同伴自己的 Key 验证该模型确实存在；命令不会输出 Key：

```bash
current_model="$(python3 - <<'PY'
import tomllib

with open('/root/.codex-friend/config.toml', 'rb') as handle:
    config = tomllib.load(handle)
model = config.get('model')
if not isinstance(model, str) or not model.strip():
    raise SystemExit('config.toml has no usable top-level model')
print(model)
PY
)"

key="$(/root/.local/bin/read-cockpit-b-key)"
models_json="$(curl --silent --show-error --fail-with-body --max-time 15 \
  -H "Authorization: Bearer $key" \
  http://127.0.0.1:56609/v1/models)"
unset key

printf '%s' "$models_json" | CURRENT_MODEL="$current_model" python3 -c '
import json, os, sys
payload = json.load(sys.stdin)
ids = [row.get("id") for row in payload.get("data", []) if row.get("id")]
print("CURRENT_MODEL=" + os.environ["CURRENT_MODEL"])
print("MODEL_IDS=" + ",".join(ids))
if os.environ["CURRENT_MODEL"] not in ids:
    raise SystemExit("current model is not present in authenticated /v1/models")
'
unset models_json
```

如果当前模型不在 `MODEL_IDS` 中，停止并让同伴从实际列表中明确选择，不自动取第一项。随后检查 `/root/.codex-friend/config.toml` 的静态配置满足：

```toml
model_provider = "cockpit_b"

[model_providers.cockpit_b]
name = "Friend Cockpit via SSH"
base_url = "http://127.0.0.1:56609/v1"
wire_api = "responses"
request_max_retries = 4
stream_max_retries = 5
stream_idle_timeout_ms = 300000

[model_providers.cockpit_b.auth]
command = "/root/.local/bin/read-cockpit-b-key"
timeout_ms = 3000
refresh_interval_ms = 0
```

顶层 `model` 必须保持为上一步打印的 `CURRENT_MODEL` 原始字符串。

若当前文件已经符合并通过真实请求，不改写。若不符合，备份后只改相关键；不写明文 Key，不复制 `cockpit_a` 的模型 ID。

**Gate 5：** 非交互 SSH 能找到 Linux alias，实际 `codex-vscode-friend.exe --version` 使用 `/root/.codex-friend` 且不要求输入 Key。

---

## Task 6：创建 friend 专用反向隧道 watchdog

**Files:**
- Create: `%LOCALAPPDATA%\CodexFriendBridge\codex-seetacloud-tunnel-watchdog-friend.ps1`
- Runtime log: `%LOCALAPPDATA%\CodexFriendBridge\codex-seetacloud-tunnel-watchdog-friend.log`

- [ ] **Step 1：写入完整 watchdog**

```powershell
[CmdletBinding()]
param(
    [string]$SshExe = '',
    [string]$SshConfig = "$env:APPDATA\Code\User\ssh-seetacloud-friend.conf",
    [string]$HostAlias = 'seetacloud-gpu-tunnel-friend',
    [ValidateRange(5, 300)][int]$ExistingCheckSeconds = 15,
    [ValidateRange(15, 600)][int]$MaxBackoffSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($SshExe)) {
    $sshCommand = Get-Command ssh.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($sshCommand) {
        $SshExe = $sshCommand.Source
    }
    else {
        $windowsDirectory = [Environment]::GetEnvironmentVariable(
            'WINDIR',
            'Machine'
        )
        if ([string]::IsNullOrWhiteSpace($windowsDirectory)) {
            throw 'Could not resolve ssh.exe because WINDIR is unavailable.'
        }
        $systemCandidate = Join-Path (
            Join-Path $windowsDirectory 'System32'
        ) 'OpenSSH\ssh.exe'
        if (-not (Test-Path -LiteralPath $systemCandidate -PathType Leaf)) {
            throw "ssh.exe not found at $systemCandidate"
        }
        $SshExe = $systemCandidate
    }
}

$mutexName = 'Local\CodexSeetaCloudTunnelFriendWatchdog'
$createdNew = $false
$mutex = [System.Threading.Mutex]::new($true, $mutexName, [ref]$createdNew)
if (-not $createdNew) {
    $mutex.Dispose()
    exit 0
}

$logPath = Join-Path $PSScriptRoot 'codex-seetacloud-tunnel-watchdog-friend.log'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$maxLogBytes = 1MB
$remoteLeaseMarker = 'codex-tunnel-friend-56609'
$remoteLeaseCommand = (
    'ownerPid=$PPID; exec -a {0}-sshd-$ownerPid sleep 2147483647' -f
    $remoteLeaseMarker
)

function Write-WatchdogLog {
    param([Parameter(Mandatory)][string]$Message)
    try {
        if ((Test-Path -LiteralPath $logPath) -and
            ((Get-Item -LiteralPath $logPath).Length -gt $maxLogBytes)) {
            $reset = "{0} [INFO] Log reset at {1} bytes.{2}" -f `
                (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $maxLogBytes, `
                [Environment]::NewLine
            [System.IO.File]::WriteAllText($logPath, $reset, $utf8NoBom)
        }
        $line = "{0} {1}{2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), `
            $Message, [Environment]::NewLine
        [System.IO.File]::AppendAllText($logPath, $line, $utf8NoBom)
    }
    catch {
        # Logging failure must not terminate the tunnel.
    }
}

function Get-ExistingTunnelProcesses {
    try {
        return @(
            Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction Stop |
                Where-Object {
                    $_.CommandLine -and
                    [regex]::IsMatch(
                        $_.CommandLine,
                        '(^|\s|\")' + [regex]::Escape($HostAlias) + '(\s|\"|$)',
                        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
                    )
                }
        )
    }
    catch {
        Write-WatchdogLog "[WARN] ssh.exe inspection failed: $($_.Exception.Message)"
        return @()
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
        '__REMOTE_LEASE_MARKER__',
        $remoteLeaseMarker
    )
    $cleanupArguments = @(
        '-T',
        '-F', $SshConfig,
        '-o', 'BatchMode=yes',
        '-o', 'ClearAllForwardings=yes',
        '-o', 'ConnectTimeout=10',
        '-o', 'ConnectionAttempts=1',
        '-o', 'ServerAliveInterval=15',
        '-o', 'ServerAliveCountMax=2',
        '-o', 'LogLevel=ERROR',
        $HostAlias,
        $cleanupCommand
    )

    Write-WatchdogLog "[WARN] Remote port is occupied; checking marker $remoteLeaseMarker."
    try {
        $cleanupOutput = @(& $SshExe @cleanupArguments 2>&1)
        $cleanupExitCode = $LASTEXITCODE
        $terminated = $false
        foreach ($entry in $cleanupOutput) {
            $message = $entry.ToString().Trim()
            if ($message.Length -eq 0) { continue }
            Write-WatchdogLog "[LEASE] $message"
            if ($message -match '^STALE_LEASE_TERMINATED=') {
                $terminated = $true
            }
        }
        if ($cleanupExitCode -ne 0) {
            Write-WatchdogLog "[WARN] Remote lease check exited with code $cleanupExitCode."
            return $false
        }
        return $terminated
    }
    catch {
        Write-WatchdogLog "[WARN] Remote lease check failed: $($_.Exception.Message)"
        return $false
    }
}

$sshArguments = @(
    '-T',
    '-F', $SshConfig,
    '-o', 'BatchMode=yes',
    '-o', 'ConnectTimeout=10',
    '-o', 'ConnectionAttempts=1',
    '-o', 'ExitOnForwardFailure=yes',
    '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=2',
    '-o', 'TCPKeepAlive=yes',
    '-o', 'LogLevel=ERROR',
    $HostAlias,
    $remoteLeaseCommand
)

$retryDelaySeconds = 5
$reportedExisting = $false
Write-WatchdogLog "[INFO] Watchdog started. host=$HostAlias config=$SshConfig"

try {
    while ($true) {
        try {
            if (-not (Test-Path -LiteralPath $SshExe -PathType Leaf)) {
                throw "ssh.exe not found at $SshExe"
            }
            if (-not (Test-Path -LiteralPath $SshConfig -PathType Leaf)) {
                throw "SSH config not found at $SshConfig"
            }

            $existing = @(Get-ExistingTunnelProcesses)
            if ($existing.Count -gt 0) {
                if (-not $reportedExisting) {
                    Write-WatchdogLog "[INFO] Existing tunnel process count=$($existing.Count); monitoring."
                    if ($existing.Count -gt 1) {
                        Write-WatchdogLog '[WARN] Multiple friend tunnel processes detected; manual exact-PID audit required.'
                    }
                    $reportedExisting = $true
                }
                Start-Sleep -Seconds $ExistingCheckSeconds
                continue
            }

            $reportedExisting = $false
            $startedAt = [DateTime]::UtcNow
            Write-WatchdogLog '[INFO] Starting SSH reverse tunnel.'

            & $SshExe @sshArguments 2>&1 | ForEach-Object {
                if ($_ -ne $null -and $_.ToString().Length -gt 0) {
                    Write-WatchdogLog "[SSH] $($_.ToString().Trim())"
                }
            }

            $exitCode = $LASTEXITCODE
            $lifetime = [int](([DateTime]::UtcNow - $startedAt).TotalSeconds)
            if ($lifetime -ge 60) {
                $retryDelaySeconds = 5
            }
            else {
                $retryDelaySeconds = [Math]::Min(
                    $MaxBackoffSeconds,
                    [Math]::Max(5, $retryDelaySeconds * 2)
                )
            }
            Write-WatchdogLog "[WARN] SSH exited. code=$exitCode lifetime=${lifetime}s retry=${retryDelaySeconds}s"
        }
        catch {
            $errorMessage = $_.Exception.Message
            $leaseCleared = $false
            if ($errorMessage -match
                'remote port forwarding failed for listen port 56609') {
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
            Write-WatchdogLog "[ERROR] Cycle failed: $errorMessage; retry=${retryDelaySeconds}s"
        }
        Start-Sleep -Seconds $retryDelaySeconds
    }
}
finally {
    Write-WatchdogLog '[INFO] Watchdog stopped.'
    if ($createdNew) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
```

该循环是有意的常驻守护流程；每次只有一个 ssh 子进程，重试有 5–60 秒退避，日志上限 1MB。远端 marker 名称记录创建它的 owner sshd PID；端口冲突时，只有在 marker 前缀匹配、owner 仍为 `sshd` 且两者启动年龄相差不超过 30 秒时，才终止该精确 owner 和 marker。它不会批量终止 sshd，不会处理 VS Code、成员 A 的 `56608` 或其他 SSH。

- [ ] **Step 2：语法验证，不启动**

```powershell
$WatchdogScript = Join-Path $BridgeRoot 'codex-seetacloud-tunnel-watchdog-friend.ps1'
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $WatchdogScript,
    [ref]$null,
    [ref]$errors
) | Out-Null
if ($errors.Count -gt 0) { $errors | Format-List; throw 'Watchdog parse failed.' }
```

**Gate 6：** 语法零错误，HostAlias、mutex 和日志名全部包含 `friend`，没有 alex 名称或 56608。

---

## Task 7：创建登录启动入口

**Files:**
- Create: `%LOCALAPPDATA%\CodexFriendBridge\start-codex-friend-bridge.ps1`
- Create: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Codex-SeetaCloud-Tunnel-Friend.lnk`

- [ ] **Step 1：创建 bootstrap 脚本**

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$repair = Join-Path $root 'repair-codex-friend-cli-alias.ps1'
$watchdog = Join-Path $root 'codex-seetacloud-tunnel-watchdog-friend.ps1'
$bootstrapLog = Join-Path $root 'codex-friend-bootstrap.log'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$bootstrapLogLimit = 256KB

if ((Test-Path -LiteralPath $bootstrapLog -PathType Leaf) -and
    ((Get-Item -LiteralPath $bootstrapLog).Length -gt $bootstrapLogLimit)) {
    [System.IO.File]::WriteAllText(
        $bootstrapLog,
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [INFO] Bootstrap log reset.$([Environment]::NewLine)",
        $utf8NoBom
    )
}

try {
    & powershell.exe -NoLogo -NoProfile -NonInteractive -File $repair 2>&1 |
        ForEach-Object {
            [System.IO.File]::AppendAllText(
                $bootstrapLog,
                "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [ALIAS] $_$([Environment]::NewLine)",
                $utf8NoBom
            )
        }
}
catch {
    [System.IO.File]::AppendAllText(
        $bootstrapLog,
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [ALIAS-ERROR] $($_.Exception.Message)$([Environment]::NewLine)",
        $utf8NoBom
    )
}

& powershell.exe -NoLogo -NoProfile -NonInteractive -File $watchdog
exit $LASTEXITCODE
```

alias repair 失败时仍启动隧道，避免一个辅助功能拖垮网络链路。

- [ ] **Step 2：创建隐藏启动快捷方式**

```powershell
$StartupDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$ShortcutPath = Join-Path $StartupDir 'Codex-SeetaCloud-Tunnel-Friend.lnk'
$Bootstrap = Join-Path $BridgeRoot 'start-codex-friend-bridge.ps1'
$PowerShellExe = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $PowerShellExe
$shortcut.Arguments = "-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -File `"$Bootstrap`""
$shortcut.WorkingDirectory = $BridgeRoot
$shortcut.WindowStyle = 7
$shortcut.Description = 'Friend SeetaCloud Codex reverse tunnel watchdog'
$shortcut.Save()
```

不创建与 alex 同名的启动项，不依赖 Windows Scheduled Task。

- [ ] **Step 3：人工首次启动并确认单实例**

```powershell
$firstStartArguments = "-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -File `"$Bootstrap`""
Start-Process -FilePath $PowerShellExe -WindowStyle Hidden `
    -ArgumentList $firstStartArguments

Start-Sleep -Seconds 5
Get-Content -LiteralPath (Join-Path $BridgeRoot 'codex-seetacloud-tunnel-watchdog-friend.log') -Tail 30
```

再次运行同一 bootstrap，确认 mutex 阻止第二个 watchdog。不得通过杀死所有 ssh 进程来验证。

**Gate 7：** 登录启动项存在，日志显示 tunnel Host，friend ssh 进程不超过一个。

---

## Task 8：修改 VS Code User Settings，使用跨平台同名命令和独立 Server

**Files:**
- Modify: `%APPDATA%\Code\User\settings.json`

- [ ] **Step 1：做 JSONC 最小合并**

在现有文件中只合并以下键，不覆盖无关设置和现有 map 项：

先打印真实 split config 的 JSON 字符串：

```powershell
$SplitConfig | ConvertTo-Json -Compress
```

历史记录显示同伴用户名为 ASUS 时，输出应类似 `"C:\\Users\\ASUS\\AppData\\Roaming\\Code\\User\\ssh-seetacloud-friend.conf"`。下面给出该已知历史路径的完整 JSONC；若现场 `$SplitConfig` 输出不同，只替换这一项的字符串值：

```jsonc
{
  "chatgpt.runCodexInWindowsSubsystemForLinux": false,
  "chatgpt.cliExecutable": "codex-vscode-friend.exe",
  "remote.SSH.configFile": "C:\\Users\\ASUS\\AppData\\Roaming\\Code\\User\\ssh-seetacloud-friend.conf",
  "remote.SSH.remotePlatform": {
    "seetacloud-gpu-vscode-friend": "linux"
  },
  "remote.SSH.serverInstallPath": {
    "seetacloud-gpu-vscode-friend": "/root/autodl-tmp/.vscode-server-friend"
  }
}
```

这里唯一需要现场写入的是 `$SplitConfig` 的实际绝对路径，例如同伴历史用户名若仍为 ASUS，通常会解析为：

```text
C:\Users\ASUS\AppData\Roaming\Code\User\ssh-seetacloud-friend.conf
```

必须以 `$SplitConfig` 实际输出为准。`remote.SSH.remotePlatform` 和 `remote.SSH.serverInstallPath` 若已有其他 Host，追加 friend 项，不得重建整个对象。

- [ ] **Step 2：验证 JSONC 和关键值**

使用 VS Code 打开 Settings JSON；确认没有红色语法错误。搜索并确认：

```text
chatgpt.cliExecutable = codex-vscode-friend.exe
seetacloud-gpu-vscode-friend = /root/autodl-tmp/.vscode-server-friend
旧的 /root/.local/bin/codex-friend 不再是 application-scope 设置值
```

- [ ] **Step 3：先验证 Windows 本地 Codex**

完全关闭所有 VS Code 窗口后重新打开一个 Windows 本地目录。Codex 侧边栏发送：

```text
不要执行命令，不要修改文件，只回复 FRIEND_WINDOWS_IDE_OK
```

必须实际收到 `FRIEND_WINDOWS_IDE_OK`。如果出现登录页或 CLI spawn 错误，先检查：

```powershell
Get-Command codex-vscode-friend.exe
codex-vscode-friend.exe --version
```

此时不继续远程配置，先修复本地 alias 或同伴现有 `%USERPROFILE%\.codex`。不得用服务器配置覆盖 Windows 本地 Codex 配置。

**Gate 8：** application-scope 设置已改成同名命令，并且 Windows 本地 IDE 真实回复成功。

---

## Task 9：切换隧道并清除旧 Host 的 RemoteForward

**Files:**
- Modify after validation: `%USERPROFILE%\.ssh\config` 中 `Host AutoDL-VLR` 的旧 friend RemoteForward 行

- [ ] **Step 1：关闭同伴所有旧 `AutoDL-VLR` 远程窗口**

只关闭同伴自己的旧 VS Code Remote-SSH 窗口，不关闭成员 A 的连接。等待服务器释放旧 56609；watchdog 会自动重试。

- [ ] **Step 2：验证新 watchdog 建立的 56609**

```powershell
& $SshExe -F $SplitConfig -o BatchMode=yes -o ClearAllForwardings=yes `
    seetacloud-gpu-vscode-friend `
    "ss -lntp | grep '127.0.0.1:56609' || true; curl -sS -o /dev/null -w '%{http_code}\n' --max-time 5 http://127.0.0.1:56609/v1/models"
```

预期：只监听 `127.0.0.1:56609`，无 Key 返回 `401`。不得出现 `0.0.0.0:56609` 或 `[::]:56609`。

- [ ] **Step 3：执行认证 `/v1/models` 与 `/v1/responses` 测试**

在服务器终端执行；Key 只存在于当前进程变量，不会打印：

```bash
set -euo pipefail

current_model="$(python3 - <<'PY'
import tomllib
with open('/root/.codex-friend/config.toml', 'rb') as handle:
    config = tomllib.load(handle)
model = config.get('model')
if not isinstance(model, str) or not model.strip():
    raise SystemExit('config.toml has no usable top-level model')
print(model)
PY
)"

key="$(/root/.local/bin/read-cockpit-b-key)"
models_json="$(curl --silent --show-error --fail-with-body --max-time 15 \
  -H "Authorization: Bearer $key" \
  http://127.0.0.1:56609/v1/models)"

printf '%s' "$models_json" | CURRENT_MODEL="$current_model" python3 -c '
import json, os, sys
payload = json.load(sys.stdin)
ids = [row.get("id") for row in payload.get("data", []) if row.get("id")]
if os.environ["CURRENT_MODEL"] not in ids:
    raise SystemExit("configured model is absent from authenticated /v1/models")
print("FRIEND_MODELS_AUTH_OK")
'

request_json="$(CURRENT_MODEL="$current_model" python3 - <<'PY'
import json, os
print(json.dumps({
    'model': os.environ['CURRENT_MODEL'],
    'input': '只回复 FRIEND_TUNNEL_API_OK',
    'stream': False,
}, ensure_ascii=False))
PY
)"

response_json="$(curl --silent --show-error --fail-with-body --max-time 60 \
  -X POST \
  -H "Authorization: Bearer $key" \
  -H 'Content-Type: application/json' \
  --data "$request_json" \
  http://127.0.0.1:56609/v1/responses)"
unset key request_json models_json

printf '%s' "$response_json" | python3 -c '
import json, sys
payload = json.load(sys.stdin)
parts = []
if isinstance(payload.get("output_text"), str):
    parts.append(payload["output_text"])
for item in payload.get("output", []):
    for content in item.get("content", []):
        text = content.get("text")
        if isinstance(text, str):
            parts.append(text)
combined = "".join(parts)
if "FRIEND_TUNNEL_API_OK" not in combined:
    raise SystemExit("Responses API did not return FRIEND_TUNNEL_API_OK")
print("FRIEND_RESPONSES_AUTH_OK")
'
unset response_json
```

预期依次输出 `FRIEND_MODELS_AUTH_OK` 和 `FRIEND_RESPONSES_AUTH_OK`。

- [ ] **Step 4：确认新隧道稳定后，移除旧 Host 的 friend RemoteForward**

从同伴 `%USERPROFILE%\.ssh\config` 的 `Host AutoDL-VLR` 块中只移除：

```text
RemoteForward 127.0.0.1:56609 127.0.0.1:54929
```

如果 `ExitOnForwardFailure yes` 只为该 RemoteForward 添加，也可一起移除；`IdentityFile`、HostName、Port、keepalive 和其他 Host 全部保留。

验证：

```powershell
& $SshExe -G AutoDL-VLR | Select-String -Pattern 'remoteforward|56609'
```

预期无输出。这样以后误开旧 Host 也不会争抢 56609。

- [ ] **Step 5：处理“旧端口长时间不释放”**

如果 watchdog 日志持续出现 `remote port forwarding failed for listen port 56609`：

```powershell
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" |
    Where-Object CommandLine -match 'AutoDL-VLR|seetacloud-gpu-tunnel-friend' |
    Select-Object ProcessId,CommandLine
```

先查看 friend watchdog 日志。若出现 `STALE_LEASE_TERMINATED=owner:<PID> marker:<PID>`，等待下一次 5 秒重拨；若出现 `STALE_OWNER_REJECTED=`，再识别同伴自己的旧 `AutoDL-VLR` PID。未经确认不得停止进程；确认后也只能处理该精确 PID，禁止按进程名批量结束。

**Gate 9：** 56609 由唯一 tunnel Host 持有，旧 Host 不再携带 RemoteForward，56608 仍正常。

---

## Task 10：首次连接独立 VS Code Server 并安装远程扩展

**Files:**
- Runtime create by VS Code: `/root/autodl-tmp/.vscode-server-friend`

- [ ] **Step 1：连接新 Host**

在 VS Code 中执行：

```text
Remote-SSH: Connect to Host...
seetacloud-gpu-vscode-friend
```

首次连接会在 `/root/autodl-tmp/.vscode-server-friend` 安装一套新的 VS Code Server。它不是新 GPU 实例，不复制或移动项目；原项目仍在原路径。

- [ ] **Step 2：安装官方远程 Codex 扩展**

扩展面板选择 OpenAI 官方 `openai.chatgpt`，确认发布者为 OpenAI，然后点击：

```text
Install in SSH: seetacloud-gpu-vscode-friend
```

不得安装同名第三方扩展。安装后运行 `Developer: Reload Window`。

- [ ] **Step 3：验证独立 Server 路径和 CLI**

在新远程终端执行：

```bash
printf 'HOME=%s\nPATH=%s\n' "$HOME" "$PATH"
command -v codex-vscode-friend.exe
codex-vscode-friend.exe --version
test -d /root/autodl-tmp/.vscode-server-friend
```

随后在 Codex Settings 中打开 `config.toml`，必须实际打开：

```text
/root/.codex-friend/config.toml
```

如果打开 `/root/.codex/config.toml` 或 `/root/.codex-alex/config.toml`，判定失败，不得通过修改错误目录来掩盖。

- [ ] **Step 4：验证远程 IDE 真实请求**

打开一个小型测试目录，从远程 Codex 侧边栏发送：

```text
不要执行命令，不要创建、删除或修改文件，只回复 FRIEND_REMOTE_IDE_OK
```

必须实际收到 `FRIEND_REMOTE_IDE_OK`，Provider 为 `cockpit_b`，请求经过 56609，且不出现 ChatGPT 官方登录。

**Gate 10：** 新远程窗口、独立 Server、独立 CODEX_HOME 和真实 IDE 请求全部通过。

---

## Task 11：完整验收矩阵与故障注入

**Files:** 只读验证；日志位于 BridgeRoot。

- [ ] **Test A：Windows 本地与服务器同时使用**

同时保持一个 Windows 本地 VS Code 窗口和一个 `seetacloud-gpu-vscode-friend` 窗口，分别请求：

```text
FRIEND_WINDOWS_CONCURRENT_OK
FRIEND_REMOTE_CONCURRENT_OK
```

两边都必须成功。本地读取同伴 Windows Codex 配置；远端读取 `/root/.codex-friend`。

- [ ] **Test B：两位成员同时使用**

在服务器检查：

```text
127.0.0.1:56608   成员 A
127.0.0.1:56609   成员 B
```

分别做无 Key 测试，均应返回 401；分别用自己的 Key 做 Responses 测试，均应成功。确认 friend 未读取 `/root/.codex-alex`，alex 未被改动。

- [ ] **Test C：两个 friend 远程窗口**

同时打开两个 `seetacloud-gpu-vscode-friend` 窗口。因为该 Host 没有 RemoteForward，两个窗口都应连接；56609 始终只由 watchdog 持有。

- [ ] **Test D：换 Wi-Fi/VPN**

保持 watchdog 和 VS Code 开启，切换 Wi-Fi 或 VPN。预期：

1. 旧 SSH tunnel 断开；
2. 日志记录退出和有界重试；
3. 网络恢复且旧端口释放后，56609 自动重新出现；
4. 再次发送 Codex 请求成功；
5. 不需要重新输入 Key或重新修改 JSON。

目标恢复时间通常小于 2 分钟；若旧服务端会话释放更慢，日志应持续显示端口占用而不是无提示卡死。

- [ ] **Test E：睡眠/恢复**

让 Windows 睡眠后恢复。watchdog 进程应继续存在，旧 ssh 子进程退出后自动重拨，56609 恢复。

- [ ] **Test F：Cockpit 停止/恢复**

关闭同伴 Cockpit 时，56609 的 SSH listener 可以仍存在，但 API 请求应快速失败；重新启动 Cockpit 54929 后，无需重启 VS Code 或 watchdog，下一次请求应恢复。

- [ ] **Test G：Windows 重登录**

重启或注销/登录同伴 Windows。Startup 快捷方式应自动启动 bootstrap，repair alias，并建立 tunnel。确认日志只有一个 watchdog 和一个 tunnel ssh。

- [ ] **Test H：扩展升级**

升级 OpenAI Codex 扩展后运行：

```powershell
& (Join-Path $BridgeRoot 'repair-codex-friend-cli-alias.ps1')
codex-vscode-friend.exe --version
```

alias 应指向新扩展内置 CLI；旧 alias 被移到时间戳备份，不原地破坏。

- [ ] **Test I：AutoDL endpoint 变化**

当 SeetaCloud 提供新的 HostName/Port 时，只更新 `ssh-seetacloud-friend.conf` 公共 Host 块中的 `HostName` 和 `Port`，然后重新运行 bootstrap。两个 alias 应同时使用新 endpoint。

**最终验收标准：** A–I 全部通过；任何一项失败都不得宣称“完美解决”。

---

## Task 12：回滚方案

### Windows 回滚

1. 将 Startup 快捷方式移动到 Task 2 的备份目录，不直接删除。
2. 只停止命令行明确包含 `seetacloud-gpu-tunnel-friend` 的 watchdog/ssh 精确 PID；不得批量停止 SSH。
3. 从时间戳备份恢复 `settings.json` 和 `.ssh\config`。
4. 恢复旧 split config（若原先存在）。
5. `codex-vscode-friend.exe` 若需回退，使用 repair 脚本生成的 `.backup-YYYYMMDD-HHMMSS` 文件恢复。

### 服务器回滚

1. 从 Task 2 输出的实际 `SERVER_BACKUP_DIR` 恢复 `codex-friend` 和 alias。
2. 恢复 `/root/.codex-friend/config.toml`。
3. 不删除 `/root/autodl-tmp/.vscode-server-friend`；移除 settings 映射后它只是未使用数据。
4. 不触碰 `/root/.codex-alex`、56608 和项目文件。

### 回滚后验证

```text
旧 AutoDL-VLR 能连接
成员 A 的 56608 正常
同伴本地 VS Code 设置恢复
没有遗留自动启动的 friend watchdog
```

---

## 计划自检

- **需求覆盖：** 双端本地/远端、application-scope CLI、独立 VS Code Server、独立隧道、自动重连、共享 root 隔离、并发、升级、回滚均有对应 Task 和 Gate。
- **未知路径：** Windows 用户名、SSH endpoint、私钥路径、扩展 CLI 路径、PATH 目录和模型 ID 都有发现命令；没有靠猜测填值。
- **破坏面：** 只修改 friend 文件和 friend 唯一名称；旧文件先备份；没有全局 CODEX_HOME、全量进程终止或递归删除。
- **验证：** 包含本地、远程、双人并发、双窗口、Wi-Fi、VPN、睡眠、Cockpit、重登录、扩展升级和 endpoint 变化。
- **已知无法“配置解决”的边界：** 两人都以 root 登录时不存在真正权限隔离；若要求互相无法读取 Key/会话，必须创建不同 Linux 用户。
