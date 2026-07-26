"""
Read-only disk inspection for C: overview and D: deep junk-candidate search.

Outputs JSON + Markdown. It does not change files.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SizeStat:
    path: str
    size_bytes: int = 0
    files: int = 0
    dirs: int = 0
    errors: int = 0
    skipped: int = 0
    truncated: bool = False
    elapsed_seconds: float = 0.0


@dataclass
class Candidate:
    path: str
    kind: str
    risk: str
    size_bytes: int
    modified: str
    reason: str


SKIP_DIR_NAMES = {"system volume information"}

LOW_RISK_DIRS = {
    "__pycache__": "Python bytecode cache",
    ".pytest_cache": "pytest cache",
    ".mypy_cache": "mypy cache",
    ".ruff_cache": "ruff cache",
    ".parcel-cache": "parcel build cache",
    ".turbo": "turbo build cache",
}

REVIEW_DIRS = {
    "node_modules": "project dependency directory; only remove if project can reinstall dependencies",
    ".venv": "Python virtual environment; only remove if dependencies are tracked",
    "venv": "Python virtual environment; only remove if dependencies are tracked",
    "env": "Python virtual environment; only remove if dependencies are tracked",
    ".next": "Next.js build output/cache",
    ".nuxt": "Nuxt build output/cache",
    "dist": "build output; keep if release artifacts live only here",
    "build": "build output; keep if release artifacts live only here",
    "target": "build output; can be large but may be expensive to rebuild",
    "cache": "application cache directory; app-specific review needed",
    "caches": "application cache directory; app-specific review needed",
    "logs": "application log directory; app-specific review needed",
    "log": "application log directory; app-specific review needed",
    "temp": "temporary directory; app-specific review needed",
    "tmp": "temporary directory; app-specific review needed",
}

LOW_RISK_FILE_NAMES = {"thumbs.db", ".ds_store"}
LOW_RISK_SUFFIXES = {".tmp", ".temp", ".part", ".crdownload"}
REVIEW_SUFFIXES = {
    ".log",
    ".dmp",
    ".etl",
    ".trace",
    ".old",
    ".bak",
    ".backup",
}
ARCHIVE_INSTALLER_SUFFIXES = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".tgz",
    ".xz",
    ".iso",
    ".msi",
    ".exe",
    ".apk",
}


def human_bytes(value: int | float | None) -> str:
    if value is None:
        return "n/a"
    n = float(value)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if abs(n) < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(n)} {unit}"
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


def iso_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return ""


def is_reparse_or_link(path: Path) -> bool:
    try:
        return path.is_symlink()
    except OSError:
        return True


def should_skip_dir(path: Path) -> bool:
    if path.name.lower() in SKIP_DIR_NAMES:
        return True
    return is_reparse_or_link(path)


def dir_size_limited(path: Path, max_files: int, max_seconds: float) -> SizeStat:
    started = time.monotonic()
    stat = SizeStat(path=str(path))
    if not path.exists():
        stat.truncated = False
        return stat
    if path.is_file():
        try:
            stat.size_bytes = path.stat().st_size
            stat.files = 1
        except OSError:
            stat.errors += 1
        stat.elapsed_seconds = round(time.monotonic() - started, 3)
        return stat

    stack = [path]
    while stack:
        if stat.files >= max_files or (time.monotonic() - started) > max_seconds:
            stat.truncated = True
            break
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if stat.files >= max_files or (time.monotonic() - started) > max_seconds:
                        stat.truncated = True
                        break
                    try:
                        if entry.is_symlink():
                            stat.skipped += 1
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            child = Path(entry.path)
                            if should_skip_dir(child):
                                stat.skipped += 1
                                continue
                            stat.dirs += 1
                            stack.append(child)
                        elif entry.is_file(follow_symlinks=False):
                            stat.files += 1
                            try:
                                stat.size_bytes += entry.stat(follow_symlinks=False).st_size
                            except OSError:
                                stat.errors += 1
                    except OSError:
                        stat.errors += 1
        except OSError:
            stat.errors += 1
    stat.elapsed_seconds = round(time.monotonic() - started, 3)
    return stat


def disk_usage(path: str) -> dict[str, Any]:
    usage = shutil.disk_usage(path)
    return {
        "path": path,
        "total_bytes": usage.total,
        "free_bytes": usage.free,
        "used_bytes": usage.used,
        "total_human": human_bytes(usage.total),
        "free_human": human_bytes(usage.free),
        "used_human": human_bytes(usage.used),
        "free_percent": round(usage.free / usage.total * 100, 1) if usage.total else None,
    }


def top_level_sizes(root: Path, max_files: int, max_seconds_each: float) -> list[SizeStat]:
    rows: list[SizeStat] = []
    try:
        children = list(root.iterdir())
    except OSError:
        return rows
    for child in children:
        if child.name.lower() == "system volume information":
            continue
        rows.append(dir_size_limited(child, max_files=max_files, max_seconds=max_seconds_each))
    rows.sort(key=lambda row: row.size_bytes, reverse=True)
    return rows


def add_candidate(candidates: list[Candidate], candidate: Candidate, max_candidates: int) -> None:
    candidates.append(candidate)
    if len(candidates) > max_candidates * 2:
        candidates.sort(key=lambda item: item.size_bytes, reverse=True)
        del candidates[max_candidates:]


def scan_d_drive(root: Path, max_seconds: float, max_files: int, max_candidates: int) -> dict[str, Any]:
    started = time.monotonic()
    candidates: list[Candidate] = []
    largest_files: list[Candidate] = []
    large_by_name_size: dict[tuple[str, int], list[str]] = {}
    stack = [root]
    files_seen = 0
    dirs_seen = 0
    errors = 0
    skipped = 0
    truncated = False
    now = time.time()

    while stack:
        if files_seen >= max_files or (time.monotonic() - started) > max_seconds:
            truncated = True
            break
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if files_seen >= max_files or (time.monotonic() - started) > max_seconds:
                        truncated = True
                        break
                    try:
                        if entry.is_symlink():
                            skipped += 1
                            continue
                        path = Path(entry.path)
                        name_l = entry.name.lower()
                        if entry.is_dir(follow_symlinks=False):
                            if should_skip_dir(path):
                                skipped += 1
                                continue
                            dirs_seen += 1
                            if name_l in LOW_RISK_DIRS or name_l in REVIEW_DIRS or name_l == "$recycle.bin":
                                size_stat = dir_size_limited(path, max_files=250_000, max_seconds=35.0)
                                if name_l in LOW_RISK_DIRS:
                                    risk = "低风险"
                                    reason = LOW_RISK_DIRS[name_l]
                                    kind = "cache-dir"
                                elif name_l == "$recycle.bin":
                                    risk = "需确认"
                                    reason = "Recycle Bin on D drive; safe for system but may contain restorable user files"
                                    kind = "recycle-bin"
                                else:
                                    risk = "需确认"
                                    reason = REVIEW_DIRS[name_l]
                                    kind = "review-dir"
                                if size_stat.size_bytes > 0:
                                    add_candidate(
                                        candidates,
                                        Candidate(
                                            path=str(path),
                                            kind=kind,
                                            risk=risk,
                                            size_bytes=size_stat.size_bytes,
                                            modified=iso_mtime(path),
                                            reason=reason + ("; scan truncated" if size_stat.truncated else ""),
                                        ),
                                        max_candidates,
                                    )
                                # Do not descend into known candidate directories to avoid double counting.
                                continue
                            stack.append(path)
                            continue

                        if entry.is_file(follow_symlinks=False):
                            files_seen += 1
                            st = entry.stat(follow_symlinks=False)
                            size = int(st.st_size)
                            suffix = path.suffix.lower()
                            age_days = (now - st.st_mtime) / 86400 if st.st_mtime else 0
                            modified = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")

                            if size >= 1 * 1024**3:
                                add_candidate(
                                    largest_files,
                                    Candidate(str(path), "large-file", "信息", size, modified, "file is at least 1GB"),
                                    200,
                                )

                            if size >= 100 * 1024**2:
                                key = (path.name.lower(), size)
                                large_by_name_size.setdefault(key, []).append(str(path))

                            if name_l in LOW_RISK_FILE_NAMES or suffix in LOW_RISK_SUFFIXES:
                                add_candidate(
                                    candidates,
                                    Candidate(str(path), "temp-file", "低风险", size, modified, "temporary/cache marker file"),
                                    max_candidates,
                                )
                            elif suffix in REVIEW_SUFFIXES and (size >= 10 * 1024**2 or age_days >= 30):
                                add_candidate(
                                    candidates,
                                    Candidate(str(path), "log-dump-backup", "需确认", size, modified, "old or large log/dump/backup-like file"),
                                    max_candidates,
                                )
                            elif suffix in ARCHIVE_INSTALLER_SUFFIXES and size >= 100 * 1024**2:
                                add_candidate(
                                    candidates,
                                    Candidate(str(path), "installer-archive", "需确认", size, modified, "large installer/archive package"),
                                    max_candidates,
                                )
                    except OSError:
                        errors += 1
        except OSError:
            errors += 1

    duplicate_groups = []
    for (name, size), paths in large_by_name_size.items():
        if len(paths) >= 2:
            duplicate_groups.append(
                {
                    "name": name,
                    "size_bytes": size,
                    "size_human": human_bytes(size),
                    "paths": paths[:20],
                    "count": len(paths),
                }
            )
    duplicate_groups.sort(key=lambda row: row["size_bytes"] * row["count"], reverse=True)

    candidates.sort(key=lambda item: item.size_bytes, reverse=True)
    largest_files.sort(key=lambda item: item.size_bytes, reverse=True)
    return {
        "root": str(root),
        "files_seen": files_seen,
        "dirs_seen": dirs_seen,
        "errors": errors,
        "skipped": skipped,
        "truncated": truncated,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "candidates": [asdict(item) | {"size_human": human_bytes(item.size_bytes)} for item in candidates[:max_candidates]],
        "largest_files": [asdict(item) | {"size_human": human_bytes(item.size_bytes)} for item in largest_files[:100]],
        "possible_duplicate_large_name_size": duplicate_groups[:50],
    }


def summarize_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for row in candidates:
        key = f"{row['risk']} / {row['kind']}"
        bucket = summary.setdefault(key, {"count": 0, "size_bytes": 0, "size_human": ""})
        bucket["count"] += 1
        bucket["size_bytes"] += int(row.get("size_bytes") or 0)
    for bucket in summary.values():
        bucket["size_human"] = human_bytes(bucket["size_bytes"])
    return dict(sorted(summary.items(), key=lambda item: item[1]["size_bytes"], reverse=True))


def write_report(data: dict[str, Any], path: Path) -> None:
    d_scan = data["d_scan"]
    candidates = d_scan["candidates"]
    summary = summarize_candidates(candidates)
    lines: list[str] = []
    lines.append("# C/D Disk Read-only Deep Scan")
    lines.append("")
    lines.append(f"Generated: {data['generated']}")
    lines.append("")
    lines.append("## Scope")
    lines.append("- Read-only scan. No files were changed.")
    lines.append("- C drive: bounded overview.")
    lines.append("- D drive: deeper junk-candidate search with risk labels.")
    lines.append("- `低风险` means low risk to system operation, not automatic permission to remove user data.")
    lines.append("")

    lines.append("## Disk usage")
    lines.append("| Drive | Total | Used | Free | Free % |")
    lines.append("|---|---:|---:|---:|---:|")
    for drive in ["c_usage", "d_usage"]:
        usage = data[drive]
        lines.append(
            f"| {usage['path']} | {usage['total_human']} | {usage['used_human']} | {usage['free_human']} | {usage['free_percent']} |"
        )
    lines.append("")

    lines.append("## C drive top-level overview")
    lines.append("| Path | Size | Files | Truncated | Errors |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in data["c_top"][:20]:
        lines.append(
            f"| `{row['path']}` | {human_bytes(row['size_bytes'])} | {row['files']} | {row['truncated']} | {row['errors']} |"
        )
    lines.append("")

    lines.append("## D drive top-level overview")
    lines.append("| Path | Size | Files | Truncated | Errors |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in data["d_top"][:30]:
        lines.append(
            f"| `{row['path']}` | {human_bytes(row['size_bytes'])} | {row['files']} | {row['truncated']} | {row['errors']} |"
        )
    lines.append("")

    lines.append("## D drive scan status")
    lines.append(f"- Files seen: {d_scan['files_seen']}")
    lines.append(f"- Dirs seen: {d_scan['dirs_seen']}")
    lines.append(f"- Errors: {d_scan['errors']}")
    lines.append(f"- Skipped: {d_scan['skipped']}")
    lines.append(f"- Truncated: {d_scan['truncated']}")
    lines.append(f"- Elapsed seconds: {d_scan['elapsed_seconds']}")
    lines.append("")

    lines.append("## D candidate summary")
    lines.append("| Group | Count | Size |")
    lines.append("|---|---:|---:|")
    for group, bucket in summary.items():
        lines.append(f"| {group} | {bucket['count']} | {bucket['size_human']} |")
    lines.append("")

    lines.append("## D top candidates")
    lines.append("| Risk | Kind | Size | Modified | Path | Reason |")
    lines.append("|---|---|---:|---|---|---|")
    for row in candidates[:100]:
        lines.append(
            f"| {row['risk']} | {row['kind']} | {row['size_human']} | {row['modified']} | `{row['path']}` | {row['reason']} |"
        )
    lines.append("")

    lines.append("## D largest files >= 1GB")
    lines.append("| Size | Modified | Path |")
    lines.append("|---:|---|---|")
    for row in d_scan["largest_files"][:80]:
        lines.append(f"| {row['size_human']} | {row['modified']} | `{row['path']}` |")
    lines.append("")

    lines.append("## D possible duplicate large files by same name and size")
    lines.append("| Name | Size | Count | Paths |")
    lines.append("|---|---:|---:|---|")
    for row in d_scan["possible_duplicate_large_name_size"][:30]:
        paths = "<br>".join(f"`{p}`" for p in row["paths"])
        lines.append(f"| {row['name']} | {row['size_human']} | {row['count']} | {paths} |")
    lines.append("")

    lines.append("## Suggested handling")
    lines.append("- Low-risk cache markers can be considered first, but still review paths.")
    lines.append("- Installer/archive packages are often removable if you no longer need offline installers.")
    lines.append("- Recycle Bin contents are safe for Windows itself, but may contain files you might want to restore.")
    lines.append("- Project dependency/build directories on D are not system-critical, but may cost time to rebuild; keep unless you confirm the project can reinstall/rebuild.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    parser.add_argument("--d-max-seconds", type=float, default=900.0)
    parser.add_argument("--d-max-files", type=int, default=2_000_000)
    parser.add_argument("--max-candidates", type=int, default=1500)
    args = parser.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    data: dict[str, Any] = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "c_usage": disk_usage("C:\\"),
        "d_usage": disk_usage("D:\\"),
        "c_top": [asdict(row) for row in top_level_sizes(Path("C:\\"), max_files=250_000, max_seconds_each=20.0)],
        "d_top": [asdict(row) for row in top_level_sizes(Path("D:\\"), max_files=250_000, max_seconds_each=30.0)],
        "d_scan": scan_d_drive(Path("D:\\"), args.d_max_seconds, args.d_max_files, args.max_candidates),
    }

    json_path = out / f"deep_disk_scan_{stamp}.json"
    report_path = out / "deep_disk_report.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(data, report_path)
    print(json.dumps({"json": str(json_path), "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
