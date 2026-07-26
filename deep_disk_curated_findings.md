# C/D 盘深度检索人工分级

生成时间：2026-07-06 23:45 左右

本文件是对 `deep_disk_report.md` 的人工分级版。扫描过程只读，没有删除、移动或修改文件。

## C 盘结论

C 盘当前空间健康：

- C 盘总容量：300GB
- 已用：约 193GB
- 可用：约 107GB
- 空闲比例：约 35.6%

最值得注意的是：

| 分级 | 路径 | 大小 | 说明 |
|---|---|---:|---|
| 可清理，但先关闭腾讯视频 | `C:\5ddee7b0b73c09d07f96460afbf9db91` | 约 7.02GB | 目录说明确认是腾讯视频缓存。保留只会减少播放缓冲等待；关闭腾讯视频后清理不影响系统。 |
| 不建议动 | `C:\hiberfil.sys` | 约 6.32GB | Windows 休眠文件，清理需要改系统休眠设置，不属于普通垃圾。 |
| 不建议动 | `C:\Windows` / `C:\Program Files` / `C:\Program Files (x86)` | 多 GB | 系统和软件目录，不做手动清理。 |

腾讯视频缓存说明文件原文确认：该目录为腾讯视频缓存；如果磁盘空间不足，可以在关闭腾讯视频客户端的情况下清理该目录下文件。

## D 盘结论

D 盘当前空间也健康：

- D 盘总容量：169.71GB
- 已用：约 66.47GB
- 可用：约 103.24GB
- 空闲比例：约 60.8%

## D 盘不建议动

这些虽然大，但会影响系统、虚拟机、软件或应用完整性：

| 路径 | 大小 | 原因 |
|---|---:|---|
| `D:\pagefile.sys` | 约 21.21GB | Windows 页面文件，不要手动删除。 |
| `D:\WSL\Ubuntu\ext4.vhdx` | 约 5.69GB | WSL Ubuntu 虚拟磁盘，删除会破坏 WSL。 |
| `D:\latex` | 约 9.02GB | TeXLive/LaTeX 环境，不是垃圾。 |
| `D:\Microsoft VS Code` | 约 909MB | VS Code 安装目录，不要删内部 `node_modules/dist`。 |
| `D:\nodejs` | 至少 12MB+ | Node.js 环境，不要删内部 `node_modules`。 |
| `D:\Weixin` / `D:\qq` / `D:\QQLive` / `D:\BaiduNetdisk` 程序根目录 | 多 GB | 应用安装目录，不能按文件夹直接删。 |

## D 盘可考虑清理，但需要你确认

这些不影响 Windows 正常运行，但可能是备份、离线安装包或用户文件。建议先看文件名，确认不再需要后再清。

| 路径 | 大小 | 建议 |
|---|---:|---|
| `D:\WSL\Backup\Ubuntu.tar` | 约 1.41GB | WSL 备份包；如果已有新备份或不需要回滚，可删。 |
| `D:\DTLFolder\DriversBackup` | 约 2.07GB | 驱动备份；不影响当前驱动运行，但会失去本地回滚备份。 |
| `D:\DTLFolder\DriversDownLoad` | 约 1.06GB | 驱动下载包；不影响当前驱动运行，必要时可重新下载。 |
| `D:\DTLFolder\SoftwareDownload` | 约 1.97GB | 软件下载安装包集合；逐项确认后可清。 |
| `D:\OneDrive\文档\xwechat_files\...\2023312312邹佳立(2).zip` | 约 427MB | 微信接收压缩包；确认不需要后可清。 |
| `D:\OneDrive\文档\xwechat_files\...\zjl项目(1).zip` | 约 221MB | 微信接收压缩包；确认不需要后可清。 |
| `D:\OneDrive\文档\xwechat_files\...\zjl项目.zip` | 约 185MB | 微信接收压缩包；确认不需要后可清。 |
| `D:\OneDrive\文档\xwechat_files\...\codex-backup-20260427-012403.tar.gz` | 约 205MB | 旧备份包；确认不需要后可清。 |

这批如果都确认不需要，约可回收 7GB 左右；但其中不少属于“备份/安装包/用户文件”，不建议自动删除。

## D 盘应用缓存类

| 路径 | 大小 | 建议 |
|---|---:|---|
| `D:\BaiduNetdisk\module\BrowserEngine\users\...\filecache.db` | 约 1.16GB | 百度网盘浏览/文件缓存；建议优先在百度网盘设置里清缓存，不建议手动删数据库文件。 |
| `D:\OneDrive\文档\xwechat_files\...\cache` | 约 126MB | 微信文件缓存；可通过微信清理工具或确认后清。 |
| `D:\OneDrive\文档\Tencent Files\488424574\nt_qq\nt_data\log` | 约 21MB | QQ 日志；体积不大，清理价值低。 |

## D 盘重复文件线索

发现一个较明确的大文件重复线索：

| 文件名 | 单个大小 | 数量 | 说明 |
|---|---:|---:|---|
| `best_recognition.pt` | 约 129.20MB | 2 | 两份路径都在微信接收的项目压缩解包目录里，可能是重复项目交付内容。确认其中一份不需要后可清。 |

## 建议顺序

1. 先处理 C 盘腾讯视频缓存，前提是关闭腾讯视频。
2. D 盘先看 `D:\DTLFolder` 的驱动备份/下载包和 `D:\WSL\Backup\Ubuntu.tar`。
3. 再看微信接收的压缩包和重复模型文件。
4. 不碰 `pagefile.sys`、WSL 的 `ext4.vhdx`、LaTeX、VS Code、Node.js、微信/QQ/百度网盘/QQLive 安装目录。
