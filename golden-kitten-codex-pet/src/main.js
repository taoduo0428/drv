const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain, shell, screen } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawn } = require('node:child_process');

const PROJECT_ROOT = path.join(__dirname, '..');
const ASSET_PATH = path.join(PROJECT_ROOT, 'assets', 'golden-kitten.png');
const OPEN_CODEX_SCRIPT = path.join(PROJECT_ROOT, 'scripts', 'open-codex.ps1');
const STATE_FILE = process.env.CODEX_PET_STATE_FILE
  || path.join(os.homedir(), '.codex', 'runtime', 'pet-state.json');

const ALLOWED_STATES = new Set([
  'idle',
  'thinking',
  'running',
  'reviewing',
  'success',
  'failure',
  'attention'
]);

const DEFAULT_MESSAGES = {
  idle: '喵，我在桌面待命。',
  thinking: '正在思考下一步……',
  running: '正在帮你跑命令。',
  reviewing: '需要你看一眼。',
  success: '完成啦，喵！',
  failure: '这里好像失败了。',
  attention: '主人，有新情况。'
};

const PET_SIZES = {
  small: { width: 240, height: 280, label: '小' },
  medium: { width: 280, height: 320, label: '中' },
  large: { width: 340, height: 390, label: '大' }
};

let sizeKey = 'medium';
let mainWindow;
let tray;
let stateWatcher;
let stateReadTimer;
let isPinned = true;
let isClickThrough = false;
let openCodexInFlight = false;

const hasSingleInstanceLock = app.requestSingleInstanceLock();
const isHookLaunch = process.argv.includes('--pet-hook-launch');

function showMainWindow(options = {}) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  enforceWindowSize();
  const inactive = Boolean(options.inactive);
  if (!mainWindow.isVisible()) {
    inactive ? mainWindow.showInactive() : mainWindow.show();
  }
  if (mainWindow.isMinimized()) mainWindow.restore();
  if (!inactive) mainWindow.focus();
}

function getCurrentSize() {
  return PET_SIZES[sizeKey] || PET_SIZES.medium;
}

function defaultWindowBounds(targetSize = getCurrentSize()) {
  const { workArea } = screen.getPrimaryDisplay();
  return {
    width: targetSize.width,
    height: targetSize.height,
    x: Math.max(workArea.x, workArea.x + workArea.width - targetSize.width - 36),
    y: Math.max(workArea.y, workArea.y + workArea.height - targetSize.height - 36)
  };
}

function enforceWindowSize() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  const targetSize = getCurrentSize();
  if (mainWindow.isMaximized()) mainWindow.unmaximize();
  if (mainWindow.isFullScreen()) mainWindow.setFullScreen(false);
  const bounds = mainWindow.getBounds();
  if (bounds.width !== targetSize.width || bounds.height !== targetSize.height) {
    mainWindow.setSize(targetSize.width, targetSize.height, false);
  }
}

function setPetSize(nextSizeKey, resetPosition = false) {
  if (!PET_SIZES[nextSizeKey]) return;
  sizeKey = nextSizeKey;
  if (!mainWindow || mainWindow.isDestroyed()) return;
  const target = getCurrentSize();
  if (resetPosition) {
    mainWindow.setBounds(defaultWindowBounds(target), false);
  } else {
    mainWindow.setSize(target.width, target.height, false);
  }
  if (tray) tray.setContextMenu(buildMenu());
}

function normalizeState(input) {
  const raw = input && typeof input === 'object' ? input : {};
  const state = ALLOWED_STATES.has(raw.state) ? raw.state : 'idle';
  const message = typeof raw.message === 'string' && raw.message.trim()
    ? raw.message.trim().slice(0, 140)
    : DEFAULT_MESSAGES[state];

  return {
    state,
    message,
    source: typeof raw.source === 'string' ? raw.source.slice(0, 40) : 'codex-pet',
    updatedAt: typeof raw.updatedAt === 'string' ? raw.updatedAt : new Date().toISOString()
  };
}

function sendState(payload) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send('pet-state', normalizeState(payload));
}

function updateStateFile(payload) {
  const normalized = normalizeState(payload);
  const tempFile = `${STATE_FILE}.${process.pid}.tmp`;
  try {
    fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
    fs.writeFileSync(tempFile, `${JSON.stringify(normalized, null, 2)}\n`, 'utf8');
    fs.renameSync(tempFile, STATE_FILE);
  } catch {
    sendState(normalized);
  }
}

function openCodex() {
  return new Promise((resolve) => {
    if (openCodexInFlight) {
      resolve({ ok: true, message: '正在唤起 Codex。' });
      return;
    }
    openCodexInFlight = true;
    const child = spawn('powershell', [
      '-NoProfile',
      '-ExecutionPolicy',
      'Bypass',
      '-File',
      OPEN_CODEX_SCRIPT
    ], {
      cwd: PROJECT_ROOT,
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk.toString('utf8'); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString('utf8'); });
    child.on('close', (code) => {
      openCodexInFlight = false;
      if (code === 0) {
        const detail = stdout.trim();
        const message = detail.startsWith('focused') ? 'Codex 已回到前台。' : '已唤起 Codex。';
        updateStateFile({ state: 'attention', phase: 'Codex 已唤起', progress: 0.2, message, source: 'pet' });
        resolve({ ok: true, message, detail });
      } else {
        const message = (stderr || stdout || '没有找到 Codex 窗口或启动入口。').trim();
        updateStateFile({ state: 'failure', phase: '唤起失败', progress: 0.2, message, source: 'pet' });
        resolve({ ok: false, message });
      }
    });
    child.on('error', (error) => {
      openCodexInFlight = false;
      const message = `唤起 Codex 失败：${error.message}`;
      updateStateFile({ state: 'failure', phase: '唤起失败', progress: 0.2, message, source: 'pet' });
      resolve({ ok: false, message });
    });
  });
}

function readStateFile() {
  fs.readFile(STATE_FILE, 'utf8', (error, text) => {
    if (error) {
      if (error.code !== 'ENOENT') {
        sendState({ state: 'failure', message: `状态文件读取失败：${error.code}`, source: 'watcher' });
      }
      return;
    }

    try {
      const data = JSON.parse(text);
      sendState(data);
    } catch {
      sendState({ state: 'failure', message: '状态文件 JSON 格式不对。', source: 'watcher' });
    }
  });
}

function watchStateFile() {
  const dir = path.dirname(STATE_FILE);
  if (!fs.existsSync(dir)) return;

  try {
    stateWatcher = fs.watch(dir, { persistent: false }, (_event, filename) => {
      if (filename && filename.toString() !== path.basename(STATE_FILE)) return;
      clearTimeout(stateReadTimer);
      stateReadTimer = setTimeout(readStateFile, 80);
    });
    readStateFile();
  } catch (error) {
    sendState({ state: 'failure', message: `状态监听失败：${error.code || 'UNKNOWN'}`, source: 'watcher' });
  }
}

function createWindow() {
  const bounds = defaultWindowBounds();

  mainWindow = new BrowserWindow({
    ...bounds,
    frame: false,
    transparent: true,
    resizable: false,
    maximizable: false,
    minimizable: false,
    fullscreenable: false,
    movable: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    show: false,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  mainWindow.setResizable(false);
  mainWindow.setMaximizable(false);
  mainWindow.setFullScreenable(false);
  mainWindow.setAlwaysOnTop(true, 'floating');
  mainWindow.setSkipTaskbar(true);
  mainWindow.on('resize', enforceWindowSize);
  mainWindow.on('maximize', () => {
    mainWindow.unmaximize();
    enforceWindowSize();
  });
  mainWindow.on('enter-full-screen', () => {
    mainWindow.setFullScreen(false);
    enforceWindowSize();
  });
  mainWindow.loadFile(path.join(__dirname, 'index.html'));
  mainWindow.once('ready-to-show', () => {
    isHookLaunch ? mainWindow.showInactive() : mainWindow.show();
    sendState({ state: 'idle', message: DEFAULT_MESSAGES.idle, source: 'app' });
  });

  mainWindow.on('closed', () => {
    mainWindow = undefined;
  });
}

function buildMenu() {
  return Menu.buildFromTemplate([
    {
      label: mainWindow && mainWindow.isVisible() ? '隐藏小猫' : '显示小猫',
      click: () => {
        if (!mainWindow) return;
        mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
      }
    },
    {
      label: isPinned ? '取消置顶' : '保持置顶',
      click: () => {
        isPinned = !isPinned;
        if (mainWindow) mainWindow.setAlwaysOnTop(isPinned, 'floating');
      }
    },
    {
      label: isClickThrough ? '恢复点击' : '点击穿透',
      click: () => {
        isClickThrough = !isClickThrough;
        if (mainWindow) mainWindow.setIgnoreMouseEvents(isClickThrough, { forward: true });
      }
    },
    { type: 'separator' },
    {
      label: `大小：${getCurrentSize().label}`,
      submenu: [
        { label: '小', type: 'radio', checked: sizeKey === 'small', click: () => setPetSize('small') },
        { label: '中', type: 'radio', checked: sizeKey === 'medium', click: () => setPetSize('medium') },
        { label: '大', type: 'radio', checked: sizeKey === 'large', click: () => setPetSize('large') },
        { type: 'separator' },
        { label: '恢复默认位置', click: () => setPetSize(sizeKey, true) }
      ]
    },
    { type: 'separator' },
    {
      label: '唤起 Codex',
      click: () => {
        openCodex();
      }
    },
    {
      label: '打开状态文件位置',
      click: () => shell.showItemInFolder(STATE_FILE)
    },
    {
      label: '退出',
      click: () => app.quit()
    }
  ]);
}

function createTray() {
  const trayImage = nativeImage.createFromPath(ASSET_PATH).resize({ width: 16, height: 16 });
  tray = new Tray(trayImage);
  tray.setToolTip('金渐层 Codex 小猫');
  tray.setContextMenu(buildMenu());
  tray.on('click', () => {
    if (!mainWindow) return;
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    tray.setContextMenu(buildMenu());
  });
}

ipcMain.handle('pet:get-config', () => ({
  assetPath: ASSET_PATH,
  stateFile: STATE_FILE,
  allowedStates: [...ALLOWED_STATES]
}));

ipcMain.handle('pet:hide', () => {
  if (mainWindow) mainWindow.hide();
  if (tray) tray.setContextMenu(buildMenu());
});

ipcMain.handle('pet:open-state-file', () => {
  shell.showItemInFolder(STATE_FILE);
});

ipcMain.handle('pet:open-codex', () => openCodex());

ipcMain.handle('pet:cycle-size', () => {
  const order = ['small', 'medium', 'large'];
  const next = order[(order.indexOf(sizeKey) + 1) % order.length] || 'medium';
  setPetSize(next);
  return { size: next, label: getCurrentSize().label };
});

ipcMain.handle('pet:reset-window', () => {
  setPetSize('medium', true);
  return { size: sizeKey, label: getCurrentSize().label };
});

ipcMain.handle('pet:get-window-position', () => {
  if (!mainWindow || mainWindow.isDestroyed()) return { x: 0, y: 0 };
  const [x, y] = mainWindow.getPosition();
  return { x, y };
});

ipcMain.handle('pet:set-window-position', (_event, nextPosition) => {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  const x = Number(nextPosition?.x);
  const y = Number(nextPosition?.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;

  const displays = screen.getAllDisplays();
  const bounds = mainWindow.getBounds();
  const virtualBounds = displays.reduce((acc, display) => {
    const area = display.workArea;
    return {
      minX: Math.min(acc.minX, area.x),
      minY: Math.min(acc.minY, area.y),
      maxX: Math.max(acc.maxX, area.x + area.width),
      maxY: Math.max(acc.maxY, area.y + area.height)
    };
  }, { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity });

  const clampedX = Math.max(virtualBounds.minX - bounds.width + 48, Math.min(x, virtualBounds.maxX - 48));
  const clampedY = Math.max(virtualBounds.minY, Math.min(y, virtualBounds.maxY - 48));
  mainWindow.setPosition(Math.round(clampedX), Math.round(clampedY), false);
});

if (!hasSingleInstanceLock) {
  app.quit();
} else {
  app.on('second-instance', (_event, commandLine) => {
    const fromHook = Array.isArray(commandLine) && commandLine.includes('--pet-hook-launch');
    showMainWindow({ inactive: fromHook });
    sendState({ state: 'attention', message: '我已经在桌面啦。', source: 'app' });
  });

  app.whenReady().then(() => {
    app.setAppUserModelId('local.golden-kitten-codex-pet');
    createWindow();
    createTray();
    watchStateFile();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      } else {
        showMainWindow();
      }
    });
  });

  app.on('window-all-closed', (event) => {
    event.preventDefault();
    if (mainWindow) mainWindow.hide();
  });

  app.on('before-quit', () => {
    clearTimeout(stateReadTimer);
    if (stateWatcher) stateWatcher.close();
  });
}
