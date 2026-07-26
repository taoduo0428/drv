# 金渐层 Codex 桌面小猫

这是一个 Windows 可跑的 Electron 桌面宠物 MVP：透明窗口、置顶、可拖动、托盘菜单、状态气泡、金渐层小猫图片资产。它可以独立卖萌，也可以通过状态文件接收 Codex/脚本状态。

## 运行

```powershell
cd C:\Users\lenovo\Desktop\obdiant\golden-kitten-codex-pet
npm install
npm start
```

如果没看到窗口，直接运行这个启动脚本。它会重新唤起已有窗口，或者启动一个新窗口：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\launch.ps1
```

如果只想做静态检查：

```powershell
npm run check
```

## 状态联动

桌宠默认监听：

```text
%USERPROFILE%\.codex\runtime\pet-state.json
```

你可以手动写状态：

```powershell
npm run state -- thinking "正在分析项目结构……"
npm run state -- running "正在跑测试。"
npm run state -- success "测试通过，喵！"
npm run state -- failure "有一个命令失败了。"
```

如果你在 Windows PowerShell 5.1 里遇到中文参数乱码，用 UTF-8 消息文件更稳：

```powershell
"正在跑测试。" | Set-Content -Encoding UTF8 .\tmp-message.txt
npm run state -- running --message-file .\tmp-message.txt
```

也可以让 Codex hooks、其他脚本或 MCP 小服务写同一个 JSON 文件。格式参考：

```json
{
  "state": "thinking",
  "message": "正在分析项目结构……",
  "source": "codex-hook",
  "updatedAt": "2026-07-07T00:00:00.000Z"
}
```

支持状态：

```text
idle, thinking, running, reviewing, success, failure, attention
```

## 接入 Codex hooks

项目内已经准备好 hook 脚本：

```powershell
npm run hook
```

它从 stdin 读取 Codex hook JSON，把事件映射成桌宠状态，然后写入：

```text
%USERPROFILE%\.codex\runtime\pet-state.json
```

映射规则：

```text
SessionStart      -> idle，并静默启动桌宠，不抢焦点
UserPromptSubmit  -> thinking，并静默启动桌宠，不抢焦点
PreToolUse        -> running
PostToolUse       -> running / failure
Stop              -> success
```

示例配置在：

```text
C:\Users\lenovo\Desktop\obdiant\golden-kitten-codex-pet\hooks.example.json
```

我没有自动改你的全局 `C:\Users\lenovo\.codex\hooks.json`。因为你那里面已有治理 hooks，直接改会影响全局 Codex 行为。确认要接入时，再把 `hooks.example.json` 里的 command 追加到对应事件。

## 当前功能

- 透明、无边框、置顶桌面小窗。
- 按住小猫或气泡即可拖动，不再依赖 Electron 原生拖拽区域。
- 默认隐藏 Windows 任务栏图标，只保留托盘菜单。
- 鼠标悬停出现“换状态 / 隐藏”按钮。
- 托盘菜单支持显示隐藏、置顶切换、点击穿透、打开状态文件位置、退出。
- 托盘菜单支持“唤起 Codex”；双击小猫或点击底部 `Codex` 按钮也会唤起 Codex。
- 底部 `大小` 按钮可在小/中/大之间切换，`重置` 会恢复默认大小和右下角位置。
- 防止窗口被误最大化/全屏/贴边拉伸；如果异常变宽，点 `重置` 或重启小猫即可恢复。
- 没有外部状态时会自动循环演示状态；收到一次 Codex hook 后停止 demo 自动乱跳。
- 有外部状态文件时，读取 JSON 后更新表情动画、气泡、阶段和进度条。

## 可靠性约定

- 外部状态 JSON 只接受固定状态枚举，未知状态会回退到 `idle`。
- 状态消息最多 140 字，避免 UI 被撑爆。
- `scripts/write-state.mjs` 使用临时文件加 rename 写入，避免半写入 JSON。
- `scripts/codex-pet-hook.mjs` 出错时不会阻塞 Codex，默认静默失败；需要排查时可加 `--debug`。
- 主进程读取失败会显示失败状态，不会静默吞掉。
- 没有状态文件时不报错，继续使用本地 demo 状态。

## 后续可以加

1. 用正式 8×9 spritesheet 替换单张小猫图，做更细腻的眨眼、走路、趴下动画。
2. 接入 Codex hooks：命令开始时 `running`，等待用户时 `reviewing`，任务完成时 `success`。
3. 加“点击小猫 -> 总结当前线程 / 打开项目 / 运行测试”的快捷动作。
4. 加多只宠物包：金渐层、银渐层、布偶、狸花。
