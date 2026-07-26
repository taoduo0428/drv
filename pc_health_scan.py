"""
Read-only Windows PC health scanner.

It writes:
- a JSON scan snapshot
- pc_health_report.md
- cleanup_dry_run.ps1

The scanner itself only reads filesystem metadata and command output.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SizeResult:
    path: str
    exists: bool
    size_bytes: int = 0
    file_count: int = 0
    dir_count: int = 0
    error_count: int = 0
    skipped_count: int = 0
    truncated: bool = False
    elapsed_seconds: float = 0.0
    reason: str = ""
    risk: str = "review"


SKIP_DIR_NAMES = {
    "$recycle.bin",
    "system volume information",
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
}

DEV_DIR_NAMES = {
    "node_modules": "safe: dependency directory; usually recreated with npm/pnpm/yarn install",
    "__pycache__": "safe: Python bytecode cache",
    ".pytest_cache": "safe: pytest cache",
    ".mypy_cache": "safe: mypy cache",
    ".ruff_cache": "safe: ruff cache",
    ".next": "review: Next.js build cache/output; keep if deploy artifacts are stored only here",
    ".nuxt": "review: Nuxt build cache/output; keep if deploy artifacts are stored only here",
    "dist": "review: build output; keep if release artifacts are stored only here",
    "build": "review: build output; keep if release artifacts are stored only here",
    "target": "review: Rust/Java build output; can be recreated but may be large",
    ".venv": "review: Python virtual environment; safe only if dependencies are tracked",
    "venv": "review: Python virtual environment; safe only if dependencies are tracked",
    "env": "review: Python virtual environment; safe only if dependencies are tracked",
}


def human_bytes(n: int | float | None) -> str:
    if n is None:
        return "n/a"
    value = float(n)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if abs(value) < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


def run_command(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout if isinstance(exc.stdout, str) else ""
        return {
            "ok": False,
            "returncode": None,
            "stdout": out.strip(),
            "stderr": f"timeout after {timeout}s",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except Exception as exc:  # scanner should keep going on optional probes
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": repr(exc),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }


def run_powershell(script: str, timeout: int = 25) -> dict[str, Any]:
    return run_command(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=timeout,
    )


def parse_json_output(result: dict[str, Any]) -> Any:
    if not result.get("ok") or not result.get("stdout"):
        return {"error": result.get("stderr") or "empty output", "raw": result}
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        return {"error": f"json parse failed: {exc}", "raw": result}


def is_skipped_path(path: Path) -> bool:
    lower = str(path).lower()
    if "appdata\\local\\packages" in lower:
        return True
    parts = {part.lower() for part in path.parts}
    return bool(parts.intersection(SKIP_DIR_NAMES))


def dir_size(path: Path, max_files: int = 250_000, max_seconds: float = 25.0) -> SizeResult:
    started = time.monotonic()
    result = SizeResult(path=str(path), exists=path.exists())
    if not path.exists():
        result.reason = "path missing"
        return result

    if path.is_file():
        try:
            result.size_bytes = path.stat().st_size
            result.file_count = 1
        except OSError:
            result.error_count += 1
        result.elapsed_seconds = round(time.monotonic() - started, 3)
        return result

    stack = [path]
    while stack:
        if result.file_count >= max_files or (time.monotonic() - started) > max_seconds:
            result.truncated = True
            break
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if result.file_count >= max_files or (time.monotonic() - started) > max_seconds:
                        result.truncated = True
                        break
                    try:
                        if entry.is_symlink():
                            result.skipped_count += 1
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            entry_path = Path(entry.path)
                            if is_skipped_path(entry_path):
                                result.skipped_count += 1
                                continue
                            result.dir_count += 1
                            stack.append(entry_path)
                        elif entry.is_file(follow_symlinks=False):
                            result.file_count += 1
                            try:
                                result.size_bytes += entry.stat(follow_symlinks=False).st_size
                            except OSError:
                                result.error_count += 1
                    except OSError:
                        result.error_count += 1
        except OSError:
            result.error_count += 1

    result.elapsed_seconds = round(time.monotonic() - started, 3)
    return result


def known_dirs(user_profile: Path) -> dict[str, Path]:
    names = [
        "Desktop",
        "Downloads",
        "Documents",
        "Pictures",
        "Videos",
        "Music",
        "AppData/Local",
        "AppData/Roaming",
        ".cache",
        ".conda",
        ".docker",
        ".gradle",
        ".m2",
        ".nuget",
        ".vscode",
    ]
    return {name: user_profile / Path(name) for name in names}


def explicit_cache_paths(user_profile: Path) -> list[tuple[Path, str, str]]:
    local = Path(os.environ.get("LOCALAPPDATA", str(user_profile / "AppData/Local")))
    roaming = Path(os.environ.get("APPDATA", str(user_profile / "AppData/Roaming")))
    return [
        (local / "Temp", "safe", "user temp directory; close apps first"),
        (local / "pip" / "Cache", "safe", "pip download/build cache"),
        (roaming / "npm-cache", "safe", "npm cache"),
        (local / "npm-cache", "safe", "npm cache"),
        (local / "pnpm" / "store", "safe", "pnpm content-addressed store; prefer pnpm store prune"),
        (user_profile / ".pnpm-store", "safe", "pnpm store"),
        (local / "Yarn" / "Cache", "safe", "Yarn cache"),
        (user_profile / ".cache" / "yarn", "safe", "Yarn cache"),
        (user_profile / ".cache" / "pip", "safe", "pip cache"),
        (user_profile / ".conda" / "pkgs", "review", "conda package cache; prefer conda clean after checking envs"),
        (user_profile / "miniconda3" / "pkgs", "review", "conda package cache"),
        (user_profile / "anaconda3" / "pkgs", "review", "conda package cache"),
        (user_profile / ".gradle" / "caches", "safe", "Gradle cache"),
        (user_profile / ".m2" / "repository", "review", "Maven local repository; dependencies re-download if removed"),
        (user_profile / ".nuget" / "packages", "review", "NuGet package cache"),
        (local / "Docker", "review", "Docker Desktop local data; prefer docker system prune after review"),
        (user_profile / ".docker", "review", "Docker CLI/config data; do not blindly remove"),
        (local / "Microsoft" / "Windows" / "INetCache", "review", "Windows/browser internet cache"),
        (local / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache", "safe", "Edge browser cache"),
        (local / "Google" / "Chrome" / "User Data" / "Default" / "Cache", "safe", "Chrome browser cache"),
    ]


def find_named_dirs(roots: list[Path], max_hits: int, max_seconds: float) -> list[Path]:
    started = time.monotonic()
    stack = [root for root in roots if root.exists()]
    hits: list[Path] = []
    seen: set[str] = set()
    while stack and len(hits) < max_hits and (time.monotonic() - started) <= max_seconds:
        current = stack.pop()
        if is_skipped_path(current):
            continue
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if len(hits) >= max_hits or (time.monotonic() - started) > max_seconds:
                        break
                    try:
                        if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                            continue
                        entry_path = Path(entry.path)
                        name = entry.name.lower()
                        if name in DEV_DIR_NAMES:
                            key = str(entry_path).lower()
                            if key not in seen:
                                seen.add(key)
                                hits.append(entry_path)
                            continue
                        if not is_skipped_path(entry_path):
                            stack.append(entry_path)
                    except OSError:
                        continue
        except OSError:
            continue
    return hits


def find_large_files(roots: list[Path], min_bytes: int, max_hits: int, max_seconds: float) -> list[dict[str, Any]]:
    started = time.monotonic()
    stack = [root for root in roots if root.exists()]
    hits: list[dict[str, Any]] = []
    while stack and len(hits) < max_hits and (time.monotonic() - started) <= max_seconds:
        current = stack.pop()
        if is_skipped_path(current):
            continue
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if len(hits) >= max_hits or (time.monotonic() - started) > max_seconds:
                        break
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            entry_path = Path(entry.path)
                            if not is_skipped_path(entry_path):
                                stack.append(entry_path)
                            continue
                        if entry.is_file(follow_symlinks=False):
                            stat = entry.stat(follow_symlinks=False)
                            if stat.st_size >= min_bytes:
                                hits.append(
                                    {
                                        "path": entry.path,
                                        "size_bytes": stat.st_size,
                                        "size_human": human_bytes(stat.st_size),
                                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                                    }
                                )
                    except OSError:
                        continue
        except OSError:
            continue
    hits.sort(key=lambda row: row["size_bytes"], reverse=True)
    return hits[:max_hits]


def collect_disks() -> dict[str, Any]:
    ps = "Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,DriveType,VolumeName,Size,FreeSpace | ConvertTo-Json -Depth 3"
    data = parse_json_output(run_powershell(ps, timeout=15))
    if isinstance(data, dict) and data.get("error"):
        items = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if not Path(drive).exists():
                continue
            try:
                usage = shutil.disk_usage(drive)
                items.append({"DeviceID": f"{letter}:", "Size": usage.total, "FreeSpace": usage.free})
            except OSError:
                pass
        data = items
    items = [data] if isinstance(data, dict) and not data.get("error") else data
    items = items or []
    for item in items:
        size = int(item.get("Size") or 0)
        free = int(item.get("FreeSpace") or 0)
        item["SizeHuman"] = human_bytes(size)
        item["FreeHuman"] = human_bytes(free)
        item["UsedHuman"] = human_bytes(size - free)
        item["FreePercent"] = round((free / size) * 100, 1) if size else None
    return {"items": items}


def collect_startup() -> dict[str, Any]:
    start_cmd = "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location,User | ConvertTo-Json -Depth 4"
    task_cmd = "Get-ScheduledTask | Where-Object {$_.State -in @('Ready','Running') -and $_.TaskPath -notlike '\\Microsoft*'} | Select-Object -First 80 TaskName,TaskPath,State,Author | ConvertTo-Json -Depth 4"
    return {
        "startup_commands": parse_json_output(run_powershell(start_cmd, timeout=20)),
        "scheduled_tasks_non_microsoft_first80": parse_json_output(run_powershell(task_cmd, timeout=25)),
    }


def collect_processes() -> Any:
    ps = "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 25 Name,Id,CPU,WorkingSet64,Path | ConvertTo-Json -Depth 4"
    return parse_json_output(run_powershell(ps, timeout=20))


def collect_tools() -> dict[str, Any]:
    commands = {
        "python": ["python", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "pnpm": ["pnpm", "--version"],
        "yarn": ["yarn", "--version"],
        "git": ["git", "--version"],
        "docker": ["docker", "--version"],
    }
    return {name: run_command(cmd, timeout=8) for name, cmd in commands.items()}


def collect_docker() -> dict[str, Any]:
    return {
        "version": run_command(["docker", "--version"], timeout=10),
        "system_df": run_command(["docker", "system", "df"], timeout=25),
    }


def risk_sort_key(item: SizeResult) -> tuple[int, int]:
    rank = {"safe": 0, "review": 1, "avoid": 2}
    return (rank.get(item.risk, 1), -item.size_bytes)


def write_report(data: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# PC Health Read-Only Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Safety scope")
    lines.append("- Read-only scan only.")
    lines.append("- No registry edits, service changes, or cleanup actions were performed.")
    lines.append("- Size scans are bounded; truncated rows need deeper review.")
    lines.append("")

    lines.append("## Disk usage")
    lines.append("| Drive | Volume | Size | Free | Free % |")
    lines.append("|---|---|---:|---:|---:|")
    for disk in data.get("disks", {}).get("items", []):
        lines.append(
            f"| {disk.get('DeviceID','')} | {disk.get('VolumeName','') or ''} | "
            f"{disk.get('SizeHuman','')} | {disk.get('FreeHuman','')} | {disk.get('FreePercent','')} |"
        )
    lines.append("")

    lines.append("## Largest known user folders")
    lines.append("| Path | Size | Files | Truncated | Errors |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in data.get("top_known_dirs", [])[:30]:
        lines.append(
            f"| `{row['path']}` | {human_bytes(row['size_bytes'])} | {row['file_count']} | "
            f"{row['truncated']} | {row['error_count']} |"
        )
    lines.append("")

    lines.append("## Cleanup candidates by explicit cache path")
    lines.append("| Risk | Path | Size | Reason | Truncated |")
    lines.append("|---|---|---:|---|---:|")
    cache_rows = [SizeResult(**row) for row in data.get("cache_candidates", []) if row.get("exists")]
    for row in sorted(cache_rows, key=risk_sort_key):
        lines.append(f"| {row.risk} | `{row.path}` | {human_bytes(row.size_bytes)} | {row.reason} | {row.truncated} |")
    lines.append("")

    lines.append("## Development residue candidates")
    lines.append("| Risk | Path | Size | Reason | Truncated |")
    lines.append("|---|---|---:|---|---:|")
    dev_rows = [SizeResult(**row) for row in data.get("dev_residue", []) if row.get("exists")]
    for row in sorted(dev_rows, key=lambda r: r.size_bytes, reverse=True)[:80]:
        lines.append(f"| {row.risk} | `{row.path}` | {human_bytes(row.size_bytes)} | {row.reason} | {row.truncated} |")
    lines.append("")

    lines.append("## Large files in common user folders")
    lines.append("| Size | Modified | Path |")
    lines.append("|---:|---|---|")
    for row in data.get("large_files", [])[:80]:
        lines.append(f"| {row.get('size_human')} | {row.get('modified')} | `{row.get('path')}` |")
    lines.append("")

    lines.append("## Top processes by working set")
    lines.append("| Name | PID | Working set | CPU | Path |")
    lines.append("|---|---:|---:|---:|---|")
    processes = data.get("processes", [])
    if isinstance(processes, dict):
        processes = [processes] if not processes.get("error") else []
    for proc in processes[:25]:
        lines.append(
            f"| {proc.get('Name','')} | {proc.get('Id','')} | {human_bytes(proc.get('WorkingSet64'))} | "
            f"{proc.get('CPU','')} | `{proc.get('Path','') or ''}` |"
        )
    lines.append("")

    lines.append("## Startup items")
    startup = data.get("startup", {}).get("startup_commands", [])
    if isinstance(startup, dict):
        startup_rows = [startup] if not startup.get("error") else []
    else:
        startup_rows = startup or []
    lines.append(f"Win32_StartupCommand count: {len(startup_rows)}")
    lines.append("| Name | Location | User | Command |")
    lines.append("|---|---|---|---|")
    for row in startup_rows[:60]:
        command = str(row.get("Command", "")).replace("|", "\\|")
        lines.append(f"| {row.get('Name','')} | {row.get('Location','')} | {row.get('User','')} | `{command}` |")
    lines.append("")

    lines.append("## Docker summary")
    docker_df = data.get("docker", {}).get("system_df", {})
    if docker_df.get("ok"):
        lines.append("```text")
        lines.append(docker_df.get("stdout", ""))
        lines.append("```")
    else:
        lines.append(f"Docker system df unavailable: {docker_df.get('stderr') or docker_df.get('stdout')}")
    lines.append("")

    lines.append("## Risk labels")
    lines.append("- safe: cache/build output that is usually reproducible.")
    lines.append("- review: likely removable, but confirm project or app impact first.")
    lines.append("- avoid: not listed for automatic cleanup.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ps_escape_single(value: str) -> str:
    return value.replace("'", "''")


def write_dry_run(data: dict[str, Any], path: Path) -> None:
    candidates = []
    for group in ("cache_candidates", "dev_residue"):
        for item in data.get(group, []):
            if not item.get("exists") or item.get("risk") not in {"safe", "review"}:
                continue
            size = int(item.get("size_bytes") or 0)
            if size < 10 * 1024 * 1024:
                continue
            candidates.append(
                {
                    "Path": item.get("path", ""),
                    "Risk": item.get("risk", "review"),
                    "Reason": item.get("reason", ""),
                    "ObservedSizeBytes": size,
                }
            )
    candidates.sort(key=lambda item: item["ObservedSizeBytes"], reverse=True)
    candidates = candidates[:120]

    lines = [
        "# Generated cleanup preview. It only prints candidates.",
        "param([switch]$ShowChildren)",
        "$ErrorActionPreference = 'Continue'",
        "$Candidates = @(",
    ]
    for item in candidates:
        lines.extend(
            [
                "    [pscustomobject]@{",
                f"        Path = '{ps_escape_single(item['Path'])}'",
                f"        Risk = '{ps_escape_single(item['Risk'])}'",
                f"        Reason = '{ps_escape_single(item['Reason'])}'",
                f"        ObservedSizeBytes = {item['ObservedSizeBytes']}",
                "    }",
            ]
        )
    lines.extend(
        [
            ")",
            "",
            "function Format-Bytes([double]$Bytes) {",
            "    $units = @('B','KB','MB','GB','TB')",
            "    $value = $Bytes",
            "    $i = 0",
            "    while ($value -ge 1024 -and $i -lt $units.Length - 1) { $value = $value / 1024; $i++ }",
            "    if ($i -eq 0) { return ('{0:N0} {1}' -f $value, $units[$i]) }",
            "    return ('{0:N2} {1}' -f $value, $units[$i])",
            "}",
            "",
            "function Get-FolderSizeSafe([string]$Path) {",
            "    try {",
            "        if (-not (Test-Path -LiteralPath $Path)) { return $null }",
            "        $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop",
            "        if (-not $item.PSIsContainer) { return $item.Length }",
            "        $sum = 0L",
            "        Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { $sum += $_.Length }",
            "        return $sum",
            "    } catch { return $null }",
            "}",
            "",
            "Write-Host 'DRY RUN ONLY - no cleanup action will be performed.'",
            "$total = 0L",
            "foreach ($c in $Candidates) {",
            "    $current = Get-FolderSizeSafe -Path $c.Path",
            "    if ($null -eq $current) {",
            "        Write-Host ('MISSING  {0}  {1}' -f $c.Risk, $c.Path)",
            "        continue",
            "    }",
            "    $total += [int64]$current",
            "    Write-Host ('CANDIDATE [{0}] {1}  Observed={2} Current={3}' -f $c.Risk, $c.Path, (Format-Bytes $c.ObservedSizeBytes), (Format-Bytes $current))",
            "    Write-Host ('  Reason: {0}' -f $c.Reason)",
            "    if ($ShowChildren -and (Test-Path -LiteralPath $c.Path -PathType Container)) {",
            "        Get-ChildItem -LiteralPath $c.Path -Force -ErrorAction SilentlyContinue | Select-Object -First 20 FullName,Length,LastWriteTime | Format-Table -AutoSize",
            "    }",
            "}",
            "Write-Host ('Potential space represented by listed candidates: {0}' -f (Format-Bytes $total))",
            "Write-Host 'Review the report before creating any explicit cleanup plan.'",
        ]
    )
    # Windows PowerShell 5.1 reads UTF-8 .ps1 files reliably when a BOM is present.
    # This matters for non-ASCII user paths.
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Windows PC health scanner")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    parser.add_argument("--large-file-gb", type=float, default=1.0)
    parser.add_argument("--max-dev-hits", type=int, default=250)
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    dirs = known_dirs(user_profile)
    scan_roots = [
        dirs.get("Desktop"),
        dirs.get("Downloads"),
        dirs.get("Documents"),
        dirs.get("Pictures"),
        dirs.get("Videos"),
        user_profile / "source",
        user_profile / "repos",
        user_profile / "projects",
    ]
    scan_roots = [root for root in scan_roots if root and root.exists()]

    data: dict[str, Any] = {
        "system": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python": sys.version.replace("\n", " "),
            "user": os.environ.get("USERNAME"),
            "computer": os.environ.get("COMPUTERNAME"),
            "cwd": str(Path.cwd()),
        },
        "tools": collect_tools(),
        "disks": collect_disks(),
    }

    top_known: list[SizeResult] = []
    for name, folder in dirs.items():
        if folder.exists():
            result = dir_size(folder, max_files=300_000, max_seconds=30.0)
            result.reason = name
            top_known.append(result)
    data["top_known_dirs"] = [asdict(row) for row in sorted(top_known, key=lambda r: r.size_bytes, reverse=True)]

    cache_results: list[SizeResult] = []
    for folder, risk, reason in explicit_cache_paths(user_profile):
        result = dir_size(folder, max_files=250_000, max_seconds=20.0)
        result.risk = risk
        result.reason = reason
        cache_results.append(result)
    data["cache_candidates"] = [asdict(row) for row in sorted(cache_results, key=lambda r: r.size_bytes, reverse=True)]

    dev_results: list[SizeResult] = []
    for folder in find_named_dirs(scan_roots, max_hits=args.max_dev_hits, max_seconds=80.0):
        result = dir_size(folder, max_files=250_000, max_seconds=20.0)
        reason = DEV_DIR_NAMES.get(folder.name.lower(), "review: development residue")
        if reason.startswith("safe:"):
            result.risk = "safe"
            result.reason = reason[5:].strip()
        elif reason.startswith("review:"):
            result.risk = "review"
            result.reason = reason[7:].strip()
        else:
            result.reason = reason
        dev_results.append(result)
    data["dev_residue"] = [asdict(row) for row in sorted(dev_results, key=lambda r: r.size_bytes, reverse=True)]

    data["large_files"] = find_large_files(
        scan_roots,
        min_bytes=int(args.large_file_gb * 1024**3),
        max_hits=120,
        max_seconds=80.0,
    )
    data["processes"] = collect_processes()
    data["startup"] = collect_startup()
    data["docker"] = collect_docker()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"pc_health_scan_{stamp}.json"
    report_path = output_dir / "pc_health_report.md"
    dry_run_path = output_dir / "cleanup_dry_run.ps1"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(data, report_path)
    write_dry_run(data, dry_run_path)
    print(json.dumps({"json": str(json_path), "report": str(report_path), "dry_run": str(dry_run_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
