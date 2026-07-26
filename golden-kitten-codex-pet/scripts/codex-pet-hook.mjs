import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { homedir } from 'node:os';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const projectRoot = dirname(dirname(fileURLToPath(import.meta.url)));

const stateFile = process.env.CODEX_PET_STATE_FILE
  || join(homedir(), '.codex', 'runtime', 'pet-state.json');
const progressFile = process.env.CODEX_PET_PROGRESS_FILE
  || join(homedir(), '.codex', 'runtime', 'pet-progress.json');

const allowedStates = new Set([
  'idle',
  'thinking',
  'running',
  'reviewing',
  'success',
  'failure',
  'attention'
]);

function readStdin() {
  return new Promise((resolve) => {
    let text = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      text += chunk;
      if (text.length > 1_000_000) {
        process.stdin.destroy();
      }
    });
    process.stdin.on('end', () => resolve(text));
    process.stdin.on('error', () => resolve(text));
  });
}

function get(obj, names) {
  if (!obj || typeof obj !== 'object') return undefined;
  for (const name of names) {
    if (Object.prototype.hasOwnProperty.call(obj, name)) return obj[name];
  }
  return undefined;
}

function stringValue(value, max = 160) {
  if (value === undefined || value === null) return '';
  if (typeof value === 'string') return value.slice(0, max);
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  try {
    return JSON.stringify(value).slice(0, max);
  } catch {
    return '';
  }
}

function collectValues(obj, keyPattern, limit = 12, found = []) {
  if (!obj || typeof obj !== 'object' || found.length >= limit) return found;
  for (const [key, value] of Object.entries(obj)) {
    if (keyPattern.test(key)) found.push(value);
    if (value && typeof value === 'object') collectValues(value, keyPattern, limit, found);
    if (found.length >= limit) break;
  }
  return found;
}

function hasFailureSignal(payload) {
  const exitValues = collectValues(payload, /^(exit_?code|status_?code|code)$/i, 16);
  for (const value of exitValues) {
    if (typeof value === 'number' && value !== 0) return true;
    if (typeof value === 'string' && /^\d+$/.test(value) && Number(value) !== 0) return true;
  }

  const errorValues = collectValues(payload, /(error|exception|traceback|failed|failure|stderr)/i, 16);
  return errorValues.some((value) => {
    const text = stringValue(value, 300).toLowerCase();
    if (!text || text === 'false' || text === 'null' || text === 'undefined') return false;
    return /error|exception|traceback|failed|failure|denied|timed out|timeout/.test(text);
  });
}

function baseProgressForState(state) {
  switch (state) {
    case 'idle': return 0.05;
    case 'thinking': return 0.18;
    case 'running': return 0.55;
    case 'reviewing': return 0.65;
    case 'failure': return 0.9;
    case 'success': return 1;
    case 'attention': return 0.35;
    default: return 0;
  }
}

async function readProgressContext() {
  try {
    const text = await readFile(progressFile, 'utf8');
    const data = JSON.parse(text);
    return {
      turn: Number.isFinite(data.turn) ? data.turn : 0,
      tools: Number.isFinite(data.tools) ? data.tools : 0,
      events: Number.isFinite(data.events) ? data.events : 0
    };
  } catch {
    return { turn: 0, tools: 0, events: 0 };
  }
}

async function writeProgressContext(context) {
  await mkdir(dirname(progressFile), { recursive: true });
  const tempFile = `${progressFile}.${process.pid}.tmp`;
  await writeFile(tempFile, `${JSON.stringify(context, null, 2)}\n`, 'utf8');
  await rename(tempFile, progressFile);
}

async function nextProgressContext(event, payload) {
  const context = await readProgressContext();
  const failed = hasFailureSignal(payload);
  context.events += 1;
  context.lastEvent = event || 'unknown';
  context.updatedAt = new Date().toISOString();

  if (event === 'SessionStart') {
    context.tools = 0;
    context.progress = 0.05;
  } else if (event === 'UserPromptSubmit') {
    context.turn += 1;
    context.tools = 0;
    context.progress = 0.16;
  } else if (event === 'PreToolUse') {
    context.tools += 1;
    context.progress = Math.min(0.82, 0.28 + context.tools * 0.1);
  } else if (event === 'PostToolUse') {
    context.progress = failed ? 0.9 : Math.min(0.88, 0.42 + Math.max(context.tools, 1) * 0.1);
  } else if (event === 'Stop') {
    context.progress = 1;
  } else {
    context.progress = Math.max(0.2, Number(context.progress) || 0.2);
  }

  await writeProgressContext(context);
  return context;
}

function mapPayloadToState(payload, context = {}) {
  const event = stringValue(get(payload, ['hook_event_name', 'hookEventName', 'event', 'name']), 60);
  const toolName = stringValue(get(payload, ['tool_name', 'toolName', 'tool', 'recipient_name']), 50);
  const toolInput = get(payload, ['tool_input', 'toolInput', 'input']);
  const command = stringValue(get(toolInput, ['command', 'cmd']), 80);
  const toolLabel = command || toolName || '工具';
  const progress = Number.isFinite(context.progress) ? context.progress : undefined;
  const toolStep = Number.isFinite(context.tools) && context.tools > 0 ? context.tools : 0;

  switch (event) {
    case 'SessionStart':
      return { state: 'idle', phase: 'Codex 已连接', progress, message: '喵，新 Codex 会话开始了。', source: 'codex-hook' };
    case 'UserPromptSubmit':
      return { state: 'thinking', phase: `第 ${context.turn || 1} 轮任务`, progress, message: '收到新任务，开始思考。', source: 'codex-hook' };
    case 'PreToolUse': {
      return {
        state: 'running',
        phase: toolStep ? `第 ${toolStep} 个工具` : '正在执行工具',
        progress,
        tool: toolLabel,
        message: `正在使用 ${toolLabel}。`,
        source: 'codex-hook'
      };
    }
    case 'PostToolUse': {
      const failed = hasFailureSignal(payload);
      return failed
        ? { state: 'failure', phase: '工具失败', progress, tool: toolLabel, message: `${toolLabel} 执行失败，等我修。`, source: 'codex-hook' }
        : { state: 'running', phase: '工具完成', progress, tool: toolLabel, message: `${toolLabel} 执行完成，继续处理。`, source: 'codex-hook' };
    }
    case 'Stop':
      return { state: 'success', phase: '本轮完成', progress, message: '这轮处理完了，喵！', source: 'codex-hook' };
    default:
      return { state: 'attention', phase: 'Codex 事件', progress: progress ?? 0.35, message: event ? `Codex 事件：${event}` : '收到 Codex 状态事件。', source: 'codex-hook' };
  }
}

function ensurePetRuntime(event) {
  if (!['SessionStart', 'UserPromptSubmit'].includes(event)) return;
  if (process.argv.includes('--no-launch')) return;

  try {
    const electronBinary = join(
      projectRoot,
      'node_modules',
      'electron',
      'dist',
      process.platform === 'win32' ? 'electron.exe' : 'electron'
    );
    const command = existsSync(electronBinary)
      ? electronBinary
      : (process.platform === 'win32' ? 'npm.cmd' : 'npm');
    const args = existsSync(electronBinary) ? [projectRoot, '--pet-hook-launch'] : ['start'];
    const child = spawn(command, args, {
      cwd: projectRoot,
      detached: true,
      stdio: 'ignore',
      windowsHide: true
    });
    child.unref();
  } catch {
    // Starting the pet is best-effort. State writing below still works.
  }
}

async function writeState(payload) {
  const normalized = {
    state: allowedStates.has(payload.state) ? payload.state : 'idle',
    message: stringValue(payload.message, 140) || '喵。',
    phase: stringValue(payload.phase, 48) || '',
    tool: stringValue(payload.tool, 96) || '',
    progress: Number.isFinite(payload.progress) ? Math.max(0, Math.min(1, payload.progress)) : baseProgressForState(payload.state),
    source: stringValue(payload.source, 40) || 'codex-hook',
    updatedAt: new Date().toISOString()
  };

  await mkdir(dirname(stateFile), { recursive: true });
  const tempFile = `${stateFile}.${process.pid}.tmp`;
  await writeFile(tempFile, `${JSON.stringify(normalized, null, 2)}\n`, 'utf8');
  await rename(tempFile, stateFile);
  return normalized;
}

async function main() {
  try {
    const raw = await readStdin();
    const payload = raw.trim() ? JSON.parse(raw) : {};
    const event = stringValue(get(payload, ['hook_event_name', 'hookEventName', 'event', 'name']), 60);
    ensurePetRuntime(event);
    const context = await nextProgressContext(event, payload);
    const state = mapPayloadToState(payload, context);
    const written = await writeState(state);
    if (process.argv.includes('--print')) {
      process.stdout.write(`${JSON.stringify(written, null, 2)}\n`);
    }
  } catch (error) {
    // Hooks must never block Codex. Emit diagnostics only in explicit debug mode.
    if (process.argv.includes('--debug')) {
      process.stderr.write(`${error?.stack || error}\n`);
    }
  }
}

await main();
