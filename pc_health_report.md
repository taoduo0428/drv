# PC Health Read-Only Report

Generated: 2026-07-06T23:25:08

## Safety scope
- Read-only scan only.
- No registry edits, service changes, or cleanup actions were performed.
- Size scans are bounded; truncated rows need deeper review.

## Disk usage
| Drive | Volume | Size | Free | Free % |
|---|---|---:|---:|---:|
| C: | Windows-SSD | 300.00 GB | 96.51 GB | 32.2 |
| D: | 新加卷 | 169.71 GB | 103.24 GB | 60.8 |
| E: | 新加卷 | 5.00 GB | 1.45 GB | 29.0 |

## Largest known user folders
| Path | Size | Files | Truncated | Errors |
|---|---:|---:|---:|---:|
| `C:\Users\lenovo\Desktop` | 13.01 GB | 178305 | False | 0 |
| `C:\Users\lenovo\AppData\Roaming` | 11.52 GB | 112274 | False | 0 |
| `C:\Users\lenovo\AppData\Local` | 9.48 GB | 300000 | True | 13 |
| `C:\Users\lenovo\.vscode` | 2.16 GB | 30313 | False | 0 |
| `C:\Users\lenovo\.cache` | 1.60 GB | 29251 | False | 0 |
| `C:\Users\lenovo\Downloads` | 843.50 MB | 179 | False | 0 |
| `C:\Users\lenovo\.gradle` | 453.84 MB | 22456 | False | 0 |
| `C:\Users\lenovo\.docker` | 377.85 MB | 12 | False | 0 |
| `C:\Users\lenovo\Videos` | 80.49 MB | 3 | False | 0 |
| `C:\Users\lenovo\Music` | 504 B | 1 | False | 0 |
| `C:\Users\lenovo\Documents` | 0 B | 0 | False | 3 |

## Cleanup candidates by explicit cache path
| Risk | Path | Size | Reason | Truncated |
|---|---|---:|---|---:|
| safe | `C:\Users\lenovo\AppData\Local\npm-cache` | 633.19 MB | npm cache | False |
| safe | `C:\Users\lenovo\AppData\Local\Temp` | 365.15 MB | user temp directory; close apps first | False |
| safe | `C:\Users\lenovo\AppData\Local\Microsoft\Edge\User Data\Default\Cache` | 380.95 KB | Edge browser cache | False |
| safe | `C:\Users\lenovo\AppData\Local\pip\Cache` | 0 B | pip download/build cache | False |
| safe | `C:\Users\lenovo\.gradle\caches` | 0 B | Gradle cache | False |
| safe | `C:\Users\lenovo\AppData\Local\Google\Chrome\User Data\Default\Cache` | 0 B | Chrome browser cache | False |
| review | `C:\Users\lenovo\AppData\Local\Docker` | 2.48 GB | Docker Desktop local data; prefer docker system prune after review | False |
| review | `C:\Users\lenovo\.docker` | 377.85 MB | Docker CLI/config data; do not blindly remove | False |
| review | `C:\Users\lenovo\AppData\Local\Microsoft\Windows\INetCache` | 0 B | Windows/browser internet cache | False |

## Development residue candidates
| Risk | Path | Size | Reason | Truncated |
|---|---|---:|---|---:|
| review | `C:\Users\lenovo\Desktop\自学\ciu-learn-landing\.next` | 1.37 GB | Next.js build cache/output; keep if deploy artifacts are stored only here | False |
| safe | `C:\Users\lenovo\Desktop\自学\ciu-learn-landing\node_modules` | 472.37 MB | dependency directory; usually recreated with npm/pnpm/yarn install | False |
| review | `C:\Users\lenovo\Desktop\zjl项目\MAS-Market-Sim\.venv` | 428.02 MB | Python virtual environment; safe only if dependencies are tracked | False |
| review | `C:\Users\lenovo\Desktop\大学\大三上\数据挖掘\.venv` | 203.42 MB | Python virtual environment; safe only if dependencies are tracked | False |
| review | `C:\Users\lenovo\Desktop\个人知识库\项目\douyin\.venv` | 183.75 MB | Python virtual environment; safe only if dependencies are tracked | False |
| review | `C:\Users\lenovo\Desktop\工作简历\Leeway-master\.venv` | 69.89 MB | Python virtual environment; safe only if dependencies are tracked | False |
| review | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\skills\mcp\ReverseLabToolsMCP\.venv` | 47.41 MB | Python virtual environment; safe only if dependencies are tracked | False |
| review | `C:\Users\lenovo\Desktop\个人知识库\工作\js\项目合并\douyin\.venv` | 39.33 MB | Python virtual environment; safe only if dependencies are tracked | False |
| review | `C:\Users\lenovo\Desktop\自学\ciu-learn-landing\android\app\build` | 30.50 MB | build output; keep if release artifacts are stored only here | False |
| review | `C:\Users\lenovo\Desktop\雅思\.venv` | 2.58 MB | Python virtual environment; safe only if dependencies are tracked | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\rich\__pycache__` | 1.07 MB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\chardet\__pycache__` | 957.30 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\thirdparty\chardet\__pycache__` | 843.99 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\skills\mcp\ReverseLabToolsMCP\reverselab_mcp\tools\__pycache__` | 491.24 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\distlib\__pycache__` | 458.79 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\pyparsing\__pycache__` | 428.33 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\lib\utils\__pycache__` | 325.94 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\zjl项目\MAS-Market-Sim\scripts\__pycache__` | 324.00 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\tests\__pycache__` | 314.06 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\idna\__pycache__` | 277.22 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\plugins\generic\__pycache__` | 254.59 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\thirdparty\bottle\__pycache__` | 245.93 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\zjl项目\MAS-Market-Sim\tests\__pycache__` | 241.80 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\工作简历\Leeway-master\tests\test_workflow\__pycache__` | 208.57 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\requests\__pycache__` | 197.97 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\__pycache__` | 164.16 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\urllib3\__pycache__` | 163.36 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\pygments\__pycache__` | 162.79 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\pygments\formatters\__pycache__` | 158.83 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\utils\__pycache__` | 152.35 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\commands\__pycache__` | 144.36 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\pkg_resources\__pycache__` | 143.07 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\thirdparty\clientform\__pycache__` | 139.54 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\数据预处理\测试\修改H2\完整成功版代码（假设检验等）\__pycache__` | 138.65 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\数据预处理\测试\修改H2\完整成功版代码（假设检验等）\__pycache__` | 138.65 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\tamper\__pycache__` | 127.78 KB | Python bytecode cache | False |
| review | `C:\Users\lenovo\Desktop\自学\ciu-learn-landing\android\build` | 127.68 KB | build output; keep if release artifacts are stored only here | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\req\__pycache__` | 122.62 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\pygments\lexers\__pycache__` | 118.93 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\packaging\__pycache__` | 117.83 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\lib\takeover\__pycache__` | 114.00 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\resolution\resolvelib\__pycache__` | 113.88 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\备份-老O\数据预处理\测试\修改H2\完整成功版代码（假设检验等）\__pycache__` | 112.99 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\备份-新o\数据预处理\测试\修改H2\完整成功版代码（假设检验等）\__pycache__` | 112.99 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\原SOR\测试\修改H2\完整成功版代码（假设检验等）\__pycache__` | 112.99 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\工作简历\Leeway-master\src\leeway\workflow\__pycache__` | 110.91 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\__pycache__` | 106.24 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\cli\__pycache__` | 101.17 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\urllib3\util\__pycache__` | 98.02 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\工作简历\Leeway-master\src\leeway\tools\__pycache__` | 94.40 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\skills\mcp\ReverseLabToolsMCP\__pycache__` | 89.02 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\urllib3\contrib\__pycache__` | 85.02 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\thirdparty\beautifulsoup\__pycache__` | 84.03 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\工作简历\AnalystGPT-main\tests\__pycache__` | 83.28 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\备份-老O\数据预处理\测试\完整数据处理流程\Stage2_O变量计算_99列\代码\__pycache__` | 81.60 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\tplmap\tests\__pycache__` | 79.33 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\tenacity\__pycache__` | 74.40 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\index\__pycache__` | 73.80 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\个人知识库\工作\js\项目合并\__pycache__` | 73.27 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\vcs\__pycache__` | 72.09 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\network\__pycache__` | 71.47 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\platformdirs\__pycache__` | 69.05 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\数据预处理\__pycache__` | 67.72 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\备份-老O\数据预处理\__pycache__` | 67.72 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\备份-新o\数据预处理\__pycache__` | 67.72 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\论文\总备份\原SOR\__pycache__` | 67.72 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\数据预处理\__pycache__` | 67.72 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\yasi\IELTS Listening 虾滑\scripts\__pycache__` | 67.32 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\plugins\dbms\mssqlserver\__pycache__` | 66.18 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\工作简历\Leeway-master\src\leeway\ui\__pycache__` | 65.52 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\models\__pycache__` | 65.18 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\tplmap\core\__pycache__` | 64.17 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_internal\metadata\__pycache__` | 58.96 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\open-reverselab-main\tools\ctf-website\sqlmap\lib\techniques\union\__pycache__` | 56.67 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\msgpack\__pycache__` | 54.90 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\网页版260610\output\story_pipeline\scripts\__pycache__` | 53.85 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\distro\__pycache__` | 53.80 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\工作简历\Leeway-master\tests\test_skills\__pycache__` | 51.30 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\工作简历\Leeway-master\src\leeway\engine\__pycache__` | 51.23 KB | Python bytecode cache | False |
| safe | `C:\Users\lenovo\Desktop\留学\港中深IMBA笔面经\.venv_ocr\lib\python3.12\site-packages\pip\_vendor\truststore\__pycache__` | 50.86 KB | Python bytecode cache | False |

## Large files in common user folders
| Size | Modified | Path |
|---:|---|---|

## Top processes by working set
| Name | PID | Working set | CPU | Path |
|---|---:|---:|---:|---|
| Memory Compression | 3716 | 1.26 GB | None | `` |
| msedge | 10768 | 466.10 MB | 5312.4375 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| QQLive | 12988 | 364.86 MB | 59308.578125 | `D:\QQLive\QQLive.exe` |
| msedgewebview2 | 12044 | 197.58 MB | 2113.640625 | `C:\Program Files (x86)\Microsoft\EdgeWebView\Application\149.0.4022.98\msedgewebview2.exe` |
| msedge | 25204 | 109.99 MB | 1072.9375 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| WeChatAppEx | 20672 | 93.23 MB | 4817.828125 | `C:\Users\lenovo\AppData\Roaming\Tencent\xwechat\xplugin\plugins\RadiumWMPF\20005\extracted\runtime\WeChatAppEx.exe` |
| msedge | 14496 | 92.68 MB | 782.9375 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| Weixin | 38244 | 86.32 MB | 14870.34375 | `D:\Weixin\Weixin.exe` |
| powershell | 56116 | 86.26 MB | 0.53125 | `C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe` |
| msedge | 38260 | 76.09 MB | 25.890625 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| powershell | 46920 | 71.55 MB | 0.421875 | `C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe` |
| msedge | 52660 | 70.38 MB | 2047.953125 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| Codex | 31220 | 69.17 MB | 170.671875 | `C:\Program Files\WindowsApps\OpenAI.Codex_26.623.13972.0_x64__2p2nqsd0c76g0\app\Codex.exe` |
| explorer | 26804 | 65.66 MB | 396.625 | `C:\windows\Explorer.EXE` |
| Secure System | 284 | 64.12 MB | None | `` |
| msedge | 24372 | 57.77 MB | 132.515625 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| WeChatAppEx | 44364 | 54.64 MB | 13.125 | `C:\Users\lenovo\AppData\Roaming\Tencent\xwechat\xplugin\plugins\RadiumWMPF\20005\extracted\runtime\WeChatAppEx.exe` |
| WmiPrvSE | 5644 | 47.46 MB | None | `` |
| msedge | 49372 | 43.80 MB | 52.484375 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| Codex | 52956 | 41.27 MB | 309.953125 | `C:\Program Files\WindowsApps\OpenAI.Codex_26.623.13972.0_x64__2p2nqsd0c76g0\app\Codex.exe` |
| QQ | 45924 | 41.24 MB | 1604.5 | `D:\qq\QQ.exe` |
| WeChatAppEx | 25156 | 33.98 MB | 482.09375 | `C:\Users\lenovo\AppData\Roaming\Tencent\xwechat\xplugin\plugins\RadiumWMPF\20005\extracted\runtime\WeChatAppEx.exe` |
| dwm | 2032 | 32.07 MB | None | `` |
| BaiduNetdiskUnite | 37464 | 31.04 MB | 2934.671875 | `D:\BaiduNetdisk\module\BrowserEngine\BaiduNetdiskUnite.exe` |
| QQEX | 34124 | 30.52 MB | 628.84375 | `D:\qq\QQEX.exe` |

## Startup items
Win32_StartupCommand count: 8
| Name | Location | User | Command |
|---|---|---|---|
| OneDrive | HKU\S-1-5-21-2110431085-260148478-1084129449-1007\SOFTWARE\Microsoft\Windows\CurrentVersion\Run | LAPTOP-P0PGAG6H\lenovo | `"C:\Program Files\Microsoft OneDrive\OneDrive.exe" /background` |
| qqlive_mini | HKU\S-1-5-21-2110431085-260148478-1084129449-1007\SOFTWARE\Microsoft\Windows\CurrentVersion\Run | LAPTOP-P0PGAG6H\lenovo | `"D:\QQLive\11.172.8587.0\QQLiveMini.exe" -mini_startup` |
| qqlive | HKU\S-1-5-21-2110431085-260148478-1084129449-1007\SOFTWARE\Microsoft\Windows\CurrentVersion\Run | LAPTOP-P0PGAG6H\lenovo | `"D:\QQLive\QQLive.exe" -system_startup` |
| GoogleChromeAutoLaunch_EE07359CBB5DF117C451479D648E72F4 | HKU\S-1-5-21-2110431085-260148478-1084129449-1007\SOFTWARE\Microsoft\Windows\CurrentVersion\Run | LAPTOP-P0PGAG6H\lenovo | `"C:\Program Files\Google\Chrome\Application\chrome.exe" --no-startup-window /prefetch:5` |
| MicrosoftEdgeAutoLaunch_B8188322885C6DD24FAC5C8FE26E079B | HKU\S-1-5-21-2110431085-260148478-1084129449-1007\SOFTWARE\Microsoft\Windows\CurrentVersion\Run | LAPTOP-P0PGAG6H\lenovo | `"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --no-startup-window --win-session-start` |
| Tailscale | Common Startup | Public | `C:\PROGRA~1\TAILSC~1\TAILSC~1.EXE ` |
| SecurityHealth | HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run | Public | `%windir%\system32\SecurityHealthSystray.exe` |
| RtkAudUService | HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run | Public | `"C:\windows\System32\DriverStore\FileRepository\realtekservice.inf_amd64_04ff63d068f8c626\RtkAudUService64.exe" -background` |

## Docker summary
Docker system df unavailable: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.

## Risk labels
- safe: cache/build output that is usually reproducible.
- review: likely removable, but confirm project or app impact first.
- avoid: not listed for automatic cleanup.
