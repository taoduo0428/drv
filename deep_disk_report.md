# C/D Disk Read-only Deep Scan

Generated: 2026-07-06T23:35:59

## Scope
- Read-only scan. No files were changed.
- C drive: bounded overview.
- D drive: deeper junk-candidate search with risk labels.
- `低风险` means low risk to system operation, not automatic permission to remove user data.

## Disk usage
| Drive | Total | Used | Free | Free % |
|---|---:|---:|---:|---:|
| C:\ | 300.00 GB | 193.06 GB | 106.94 GB | 35.6 |
| D:\ | 169.71 GB | 66.47 GB | 103.24 GB | 60.8 |

## C drive top-level overview
| Path | Size | Files | Truncated | Errors |
|---|---:|---:|---:|---:|
| `C:\Users` | 73.27 GB | 250000 | True | 14 |
| `C:\Program Files` | 14.84 GB | 47309 | False | 4 |
| `C:\Windows` | 12.47 GB | 91872 | True | 9 |
| `C:\Program Files (x86)` | 11.46 GB | 14938 | False | 0 |
| `C:\5ddee7b0b73c09d07f96460afbf9db91` | 7.02 GB | 1419 | False | 0 |
| `C:\hiberfil.sys` | 6.32 GB | 1 | False | 0 |
| `C:\ProgramData` | 2.71 GB | 5564 | False | 53 |
| `C:\swapfile.sys` | 256.00 MB | 1 | False | 0 |
| `C:\tmp` | 20.50 MB | 8902 | False | 0 |
| `C:\DumpStack.log.tmp` | 12.00 KB | 1 | False | 0 |
| `C:\$Recycle.Bin` | 1.23 KB | 11 | False | 1 |
| `C:\Documents and Settings` | 0 B | 0 | False | 1 |
| `C:\PerfLogs` | 0 B | 0 | False | 1 |
| `C:\Recovery` | 0 B | 0 | False | 1 |

## D drive top-level overview
| Path | Size | Files | Truncated | Errors |
|---|---:|---:|---:|---:|
| `D:\pagefile.sys` | 21.21 GB | 1 | False | 0 |
| `D:\latex` | 9.02 GB | 244684 | False | 0 |
| `D:\WSL` | 7.10 GB | 3 | False | 0 |
| `D:\OneDrive` | 6.39 GB | 32959 | False | 0 |
| `D:\DTLFolder` | 5.10 GB | 1058 | False | 0 |
| `D:\BaiduNetdisk` | 4.50 GB | 1052 | False | 0 |
| `D:\WPS Office` | 2.88 GB | 11479 | False | 0 |
| `D:\腾讯会议` | 1.52 GB | 10399 | False | 0 |
| `D:\CC` | 1.28 GB | 36 | False | 0 |
| `D:\qq` | 1.17 GB | 1805 | False | 0 |
| `D:\QuarkCloudDrive` | 1.17 GB | 511 | False | 0 |
| `D:\Microsoft VS Code` | 909.56 MB | 6280 | False | 0 |
| `D:\Weixin` | 811.89 MB | 32 | False | 0 |
| `D:\QQLive` | 779.72 MB | 6180 | False | 0 |
| `D:\Mineradio` | 388.05 MB | 2327 | False | 0 |
| `D:\obsidian` | 349.69 MB | 84 | False | 0 |
| `D:\有道` | 344.44 MB | 1165 | False | 0 |
| `D:\DTLSoft` | 267.97 MB | 125 | False | 0 |
| `D:\雅思哥` | 216.94 MB | 76 | False | 0 |
| `D:\Clash Verge` | 131.42 MB | 11 | False | 0 |
| `D:\nodejs` | 100.58 MB | 1982 | False | 0 |
| `D:\npm-cache` | 72.11 MB | 24 | False | 0 |
| `D:\ProgramData` | 1.70 MB | 4 | False | 0 |
| `D:\mdbx.dat` | 192.00 KB | 1 | False | 0 |
| `D:\MineradioCache` | 85.41 KB | 6 | False | 0 |
| `D:\DumpStack.log.tmp` | 12.00 KB | 1 | False | 0 |
| `D:\elevoc_dnn_kernel.log` | 2.30 KB | 1 | False | 0 |
| `D:\.appdata` | 1.00 KB | 1 | False | 0 |
| `D:\$RECYCLE.BIN` | 321 B | 2 | False | 0 |
| `D:\BaiduNetdiskDownload` | 0 B | 0 | False | 0 |

## D drive scan status
- Files seen: 310329
- Dirs seen: 27536
- Errors: 1
- Skipped: 17
- Truncated: False
- Elapsed seconds: 23.723

## D candidate summary
| Group | Count | Size |
|---|---:|---:|
| 需确认 / installer-archive | 14 | 6.39 GB |
| 需确认 / review-dir | 91 | 1.86 GB |
| 需确认 / log-dump-backup | 73 | 6.19 MB |
| 低风险 / temp-file | 15 | 68.04 KB |
| 需确认 / recycle-bin | 1 | 321 B |

## D top candidates
| Risk | Kind | Size | Modified | Path | Reason |
|---|---|---:|---|---|---|
| 需确认 | installer-archive | 1.41 GB | 2026-05-07T00:32:21 | `D:\WSL\Backup\Ubuntu.tar` | large installer/archive package |
| 需确认 | review-dir | 1.28 GB | 2026-06-05T13:03:52 | `D:\CC\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | installer-archive | 1.14 GB | 2026-05-23T15:23:44 | `D:\DTLFolder\DriversBackup\NVIDIA GeForce RTX 3050 Ti Laptop GPU_32.0.15.9636_2026-05-23 15 22 14.zip` | large installer/archive package |
| 需确认 | installer-archive | 1.01 GB | 2026-05-23T15:22:07 | `D:\DTLFolder\DriversDownLoad\9A16B8482986520384BA5CD88B8B1217.7z` | large installer/archive package |
| 需确认 | installer-archive | 788.02 MB | 2026-05-04T18:17:41 | `D:\DTLFolder\DriversBackup\NVIDIA GeForce RTX 3050 Ti Laptop GPU_31.0.15.4630_2026-05-04 18 17 12.zip` | large installer/archive package |
| 需确认 | installer-archive | 427.41 MB | 2026-06-27T15:21:41 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-06\2023312312邹佳立(2).zip` | large installer/archive package |
| 需确认 | installer-archive | 221.54 MB | 2026-06-26T00:03:26 | `D:\Mineradio\Mineradio.exe` | large installer/archive package |
| 需确认 | installer-archive | 220.71 MB | 2026-07-05T14:51:22 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-07\zjl项目(1).zip` | large installer/archive package |
| 需确认 | review-dir | 210.04 MB | 2026-07-03T02:20:56 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | installer-archive | 208.02 MB | 2026-06-30T09:26:20 | `D:\Microsoft VS Code\Code.exe` | large installer/archive package |
| 需确认 | installer-archive | 205.31 MB | 2026-05-04T16:01:54 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-05\codex-backup-20260427-012403.tar.gz` | large installer/archive package |
| 需确认 | installer-archive | 201.17 MB | 2026-03-23T23:18:04 | `D:\obsidian\Obsidian.exe` | large installer/archive package |
| 需确认 | installer-archive | 184.58 MB | 2026-07-03T10:18:23 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-07\zjl项目.zip` | large installer/archive package |
| 需确认 | installer-archive | 172.78 MB | 2026-06-20T09:16:56 | `D:\qq\versions\9.9.30-48762-9.9.31-49738.zip` | large installer/archive package |
| 需确认 | installer-archive | 146.92 MB | 2026-02-14T15:00:04 | `D:\雅思哥\yasige\雅思哥机考软件.exe` | large installer/archive package |
| 需确认 | installer-archive | 130.08 MB | 2026-07-03T13:54:38 | `D:\BaiduNetdisk\module\BrowserEngine\BaiduNetdiskUnite.exe` | large installer/archive package |
| 需确认 | review-dir | 126.66 MB | 2026-07-03T14:04:35 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\cache` | application cache directory; app-specific review needed |
| 需确认 | review-dir | 57.58 MB | 2026-07-03T02:20:31 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\copilot\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | review-dir | 53.30 MB | 2026-07-03T02:20:28 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\copilot\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 30.24 MB | 2026-07-01T02:40:54 | `D:\Mineradio\resources\app\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | review-dir | 20.87 MB | 2026-07-06T23:00:00 | `D:\OneDrive\文档\Tencent Files\488424574\nt_qq\nt_data\log` | application log directory; app-specific review needed |
| 需确认 | review-dir | 16.66 MB | 2026-07-03T02:20:36 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | review-dir | 12.32 MB | 2026-06-28T22:45:03 | `D:\nodejs\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | review-dir | 9.62 MB | 2026-05-04T15:07:53 | `D:\QuarkCloudDrive\6.5.5.724\Resources\app.asar.unpacked\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | review-dir | 7.26 MB | 2026-05-20T18:54:01 | `D:\latex\texlive\2026\texmf-var\fonts\cache` | application cache directory; app-specific review needed |
| 需确认 | review-dir | 3.80 MB | 2026-07-03T02:20:35 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\microsoft-authentication\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 3.53 MB | 2026-06-04T20:01:25 | `D:\WPS Office\12.1.0.26895\office6\addons\kpubaigcbox\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 3.53 MB | 2026-05-14T19:21:14 | `D:\WPS Office\12.1.0.26375\office6\addons\kpubaigcbox\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 3.00 MB | 2026-07-03T02:20:33 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\markdown-language-features\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 2.85 MB | 2026-07-06T17:53:34 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\business\favorite\temp` | temporary directory; app-specific review needed |
| 需确认 | review-dir | 1.74 MB | 2026-06-04T20:01:20 | `D:\WPS Office\12.1.0.26895\office6\addons\kpdfaigcbox\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.74 MB | 2026-05-14T19:21:10 | `D:\WPS Office\12.1.0.26375\office6\addons\kpdfaigcbox\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.73 MB | 2026-05-14T19:21:59 | `D:\WPS Office\12.1.0.26375\office6\addons\wpsbox\mui\default\html\wpsclouddisk\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.73 MB | 2026-06-04T20:02:11 | `D:\WPS Office\12.1.0.26895\office6\addons\wpsbox\mui\default\html\wpsclouddisk\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.63 MB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\html-language-features\server\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.41 MB | 2026-07-03T02:20:37 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\terminal-suggest\dist` | build output; keep if release artifacts live only here |
| 需确认 | log-dump-backup | 1.28 MB | 2026-05-31T21:03:34 | `D:\BaiduNetdisk\sysres\YunShellCommand64.dll.old` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 1.22 MB | 2026-05-20T18:54:04 | `D:\latex\texlive\2026\install-tl.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 1.21 MB | 2026-05-20T18:46:53 | `D:\latex\texlive\2026\texmf-var\web2c\updmap.log` | old or large log/dump/backup-like file |
| 需确认 | review-dir | 1.19 MB | 2026-05-14T19:20:53 | `D:\WPS Office\12.1.0.26375\office6\addons\karticlewebcloudsummary\mui\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.19 MB | 2026-06-04T20:01:07 | `D:\WPS Office\12.1.0.26895\office6\addons\karticlewebcloudsummary\mui\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.18 MB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\css-language-features\server\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.03 MB | 2026-06-04T20:01:18 | `D:\WPS Office\12.1.0.26895\office6\addons\kmultcatalog\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.03 MB | 2026-05-14T19:21:07 | `D:\WPS Office\12.1.0.26375\office6\addons\kmultcatalog\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.01 MB | 2026-06-04T20:02:12 | `D:\WPS Office\12.1.0.26895\office6\addons\yunbox\mui\default\html\cloudsettingsdlg\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.01 MB | 2026-06-04T20:02:09 | `D:\WPS Office\12.1.0.26895\office6\addons\wpsbox\mui\default\html\cloudsettingsdlg\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.01 MB | 2026-05-14T19:22:00 | `D:\WPS Office\12.1.0.26375\office6\addons\yunbox\mui\default\html\cloudsettingsdlg\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 1.01 MB | 2026-05-14T19:21:58 | `D:\WPS Office\12.1.0.26375\office6\addons\wpsbox\mui\default\html\cloudsettingsdlg\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 850.94 KB | 2026-06-04T20:02:12 | `D:\WPS Office\12.1.0.26895\office6\addons\yunbox\mui\default\html\folderselector\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 850.94 KB | 2026-06-04T20:02:09 | `D:\WPS Office\12.1.0.26895\office6\addons\wpsbox\mui\default\html\folderselector\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 850.94 KB | 2026-06-04T20:01:45 | `D:\WPS Office\12.1.0.26895\office6\addons\kwpscloudmodule\mui\default\html\folderselector\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 850.94 KB | 2026-05-14T19:22:00 | `D:\WPS Office\12.1.0.26375\office6\addons\yunbox\mui\default\html\folderselector\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 850.94 KB | 2026-05-14T19:21:58 | `D:\WPS Office\12.1.0.26375\office6\addons\wpsbox\mui\default\html\folderselector\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 850.94 KB | 2026-05-14T19:21:34 | `D:\WPS Office\12.1.0.26375\office6\addons\kwpscloudmodule\mui\default\html\folderselector\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 742.86 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\git\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 683.09 KB | 2026-07-06T17:53:44 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\temp` | temporary directory; app-specific review needed |
| 需确认 | review-dir | 637.06 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\json-language-features\client\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 610.08 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\html-language-features\client\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 511.15 KB | 2026-06-04T20:02:09 | `D:\WPS Office\12.1.0.26895\office6\addons\wpsbox\mui\default\html\cachemove\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 511.15 KB | 2026-05-14T19:21:58 | `D:\WPS Office\12.1.0.26375\office6\addons\wpsbox\mui\default\html\cachemove\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 482.19 KB | 2026-06-04T20:02:12 | `D:\WPS Office\12.1.0.26895\office6\addons\yunbox\mui\default\html\fileradar\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 482.19 KB | 2026-06-04T20:02:09 | `D:\WPS Office\12.1.0.26895\office6\addons\wpsbox\mui\default\html\fileradar\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 482.19 KB | 2026-05-14T19:22:00 | `D:\WPS Office\12.1.0.26375\office6\addons\yunbox\mui\default\html\fileradar\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 482.19 KB | 2026-05-14T19:21:58 | `D:\WPS Office\12.1.0.26375\office6\addons\wpsbox\mui\default\html\fileradar\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 479.41 KB | 2026-06-04T20:01:59 | `D:\WPS Office\12.1.0.26895\office6\addons\qing\mui\default\res\trusteddevice\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 479.41 KB | 2026-05-14T19:21:47 | `D:\WPS Office\12.1.0.26375\office6\addons\qing\mui\default\res\trusteddevice\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 471.93 KB | 2026-07-03T02:20:37 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\typescript-language-features\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 443.83 KB | 2026-07-03T02:20:31 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\css-language-features\client\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 443.82 KB | 2026-05-20T10:29:54 | `D:\OneDrive\文档\Tencent Files\nt_qq\global\nt_data\Log` | application log directory; app-specific review needed |
| 需确认 | log-dump-backup | 399.58 KB | 2026-05-05T11:11:32 | `D:\BaiduNetdisk\install.log` | old or large log/dump/backup-like file |
| 需确认 | review-dir | 362.09 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\extension-editing\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 355.38 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\json-language-features\server\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 312.32 KB | 2026-07-01T02:40:27 | `D:\Mineradio\resources\app\build` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 304.67 KB | 2026-05-24T22:28:33 | `D:\obsidian\resources\app.asar.unpacked\node_modules` | project dependency directory; only remove if project can reinstall dependencies |
| 需确认 | review-dir | 294.74 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\github\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 273.00 KB | 2026-07-03T02:20:33 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\markdown-math\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 261.31 KB | 2026-07-03T02:20:56 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\node_modules.asar.unpacked\vsda\build` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 227.17 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\emmet\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 218.12 KB | 2026-07-03T02:20:37 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\php-language-features\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 208.99 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\github-authentication\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 187.01 KB | 2026-07-03T02:20:37 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\npm\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 182.70 KB | 2026-07-03T02:20:33 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\merge-conflict\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 171.86 KB | 2026-07-03T02:20:32 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\ipynb\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 161.59 KB | 2026-07-06T18:00:44 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\business\emoticon\Temp` | temporary directory; app-specific review needed |
| 需确认 | review-dir | 146.81 KB | 2026-06-04T20:01:21 | `D:\WPS Office\12.1.0.26895\office6\addons\kpdfcorporateglossary\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 146.81 KB | 2026-05-14T19:21:10 | `D:\WPS Office\12.1.0.26375\office6\addons\kpdfcorporateglossary\res\dist` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 124.94 KB | 2026-06-27T14:56:08 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-06\2023312312邹佳立(1)\2023312312邹佳立\信鸽\信鸽虹膜识别系统_代码\信鸽虹膜识别系统\android\build` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 124.94 KB | 2026-06-27T14:39:49 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-06\2023312312邹佳立\2023312312邹佳立\信鸽\信鸽虹膜识别系统_代码\信鸽虹膜识别系统\android\build` | build output; keep if release artifacts live only here |
| 需确认 | review-dir | 124.79 KB | 2026-07-03T02:20:26 | `D:\Microsoft VS Code\4fe60c8b1c\resources\app\extensions\configuration-editing\dist` | build output; keep if release artifacts live only here |
| 需确认 | log-dump-backup | 120.36 KB | 2026-05-20T18:48:30 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\jadetex.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 120.17 KB | 2026-05-20T18:52:24 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\pdfjadetex.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 92.22 KB | 2026-05-20T18:49:45 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\pdfxmltex.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 92.14 KB | 2026-05-20T18:50:12 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\pdflatex-dev.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 92.03 KB | 2026-05-20T18:49:01 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\xmltex.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 91.95 KB | 2026-05-20T18:51:23 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\latex-dev.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 91.95 KB | 2026-05-20T18:50:34 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\pdflatex.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 91.75 KB | 2026-05-20T18:49:30 | `D:\latex\texlive\2026\texmf-var\web2c\pdftex\latex.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 91.41 KB | 2026-05-20T18:50:49 | `D:\latex\texlive\2026\texmf-var\web2c\euptex\uplatex-dev.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 91.22 KB | 2026-05-20T18:51:07 | `D:\latex\texlive\2026\texmf-var\web2c\euptex\uplatex.log` | old or large log/dump/backup-like file |
| 需确认 | log-dump-backup | 89.30 KB | 2026-05-20T18:49:20 | `D:\latex\texlive\2026\texmf-var\web2c\euptex\platex-dev.log` | old or large log/dump/backup-like file |

## D largest files >= 1GB
| Size | Modified | Path |
|---:|---|---|
| 21.21 GB | 2026-07-06T22:46:18 | `D:\pagefile.sys` |
| 5.69 GB | 2026-07-05T22:42:48 | `D:\WSL\Ubuntu\ext4.vhdx` |
| 1.41 GB | 2026-05-07T00:32:21 | `D:\WSL\Backup\Ubuntu.tar` |
| 1.16 GB | 2026-07-05T20:50:01 | `D:\BaiduNetdisk\module\BrowserEngine\users\5c87ab3bce61650676b8d904e0d3cc3d\filecache.db` |
| 1.14 GB | 2026-05-23T15:23:44 | `D:\DTLFolder\DriversBackup\NVIDIA GeForce RTX 3050 Ti Laptop GPU_32.0.15.9636_2026-05-23 15 22 14.zip` |
| 1.01 GB | 2026-05-23T15:22:07 | `D:\DTLFolder\DriversDownLoad\9A16B8482986520384BA5CD88B8B1217.7z` |

## D possible duplicate large files by same name and size
| Name | Size | Count | Paths |
|---|---:|---:|---|
| best_recognition.pt | 129.20 MB | 2 | `D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-06\2023312312邹佳立(1)\2023312312邹佳立\信鸽\信鸽虹膜识别系统_代码\信鸽虹膜识别系统\C_delivery\models\best_recognition.pt`<br>`D:\OneDrive\文档\xwechat_files\wxid_urovbkkpo2jk22_bb4e\msg\file\2026-06\2023312312邹佳立\2023312312邹佳立\信鸽\信鸽虹膜识别系统_代码\信鸽虹膜识别系统\C_delivery\models\best_recognition.pt` |

## Suggested handling
- Low-risk cache markers can be considered first, but still review paths.
- Installer/archive packages are often removable if you no longer need offline installers.
- Recycle Bin contents are safe for Windows itself, but may contain files you might want to restore.
- Project dependency/build directories on D are not system-critical, but may cost time to rebuild; keep unless you confirm the project can reinstall/rebuild.
