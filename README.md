# Workspace Snapshot and AI Reading Guide

This repository is a complete Windows workspace snapshot. The primary runnable project is [`golden-kitten-codex-pet/`](./golden-kitten-codex-pet/); see [`AI_CONTEXT.md`](./AI_CONTEXT.md) for the recommended entry points and a map of generated artifacts.

The PC health utilities documented below are retained as part of the snapshot.

This folder contains a read-only Windows PC health scanner and generated outputs.

Run scan:

```powershell
python .\pc_health_scan.py --output-dir .
```

Run cleanup preview:

```powershell
powershell -ExecutionPolicy Bypass -File .\cleanup_dry_run.ps1
```

The generated preview script only prints candidates, current sizes, and reasons.

## Safe confirmed cache cleanup

Default mode is dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\cleanup_safe_confirm.ps1
```

Explicit dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\cleanup_safe_confirm.ps1 -DryRun
```

Real cleanup requires `-DryRun:$false` and typing `YES` at the prompt.
When launching a new `powershell.exe`, use `-Command` so the boolean is parsed correctly:

```powershell
powershell -ExecutionPolicy Bypass -Command "& .\cleanup_safe_confirm.ps1 -DryRun:`$false"
```
