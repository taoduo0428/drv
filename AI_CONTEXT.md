# AI Reading Guide

This repository is a full Windows workspace snapshot, not a minimal single-project repository.

## Primary Project

The main runnable project is `golden-kitten-codex-pet/`.

Start with:

- `golden-kitten-codex-pet/README.md`
- `golden-kitten-codex-pet/package.json`
- `golden-kitten-codex-pet/src/main.js`
- `golden-kitten-codex-pet/src/renderer.js`
- `golden-kitten-codex-pet/src/preload.js`
- `golden-kitten-codex-pet/src/styles.css`
- `golden-kitten-codex-pet/scripts/`

The project includes a checked-in `node_modules/` snapshot because this repository was requested as a complete workspace upload. Treat it as dependency data, not source code. The Electron executable is stored with Git LFS.

## Other Workspace Material

- `pc_health_scan.py` and related `cleanup_*.ps1` files: Windows health/cleanup utilities.
- `deep_disk_scan.py` and `pc_health_report.md`: disk diagnostic utilities and reports.
- `chrome-extension-backup-20260707-122846/`: browser extension backup; not part of the primary project.
- `.playwright-mcp/`, `tmp/`, `output/`, `*.log`, `__pycache__/`: generated artifacts and runtime traces.

For code review or implementation questions, focus on `golden-kitten-codex-pet/` unless the question explicitly names another path.
