import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { homedir } from 'node:os';

const allowedStates = new Set([
  'idle',
  'thinking',
  'running',
  'reviewing',
  'success',
  'failure',
  'attention'
]);

const stateFile = process.env.CODEX_PET_STATE_FILE
  || join(homedir(), '.codex', 'runtime', 'pet-state.json');

const args = process.argv.slice(2);
const state = args.shift() || 'idle';

if (!allowedStates.has(state)) {
  console.error(`Invalid state "${state}". Allowed: ${[...allowedStates].join(', ')}`);
  process.exit(2);
}

let message = '';
for (let index = 0; index < args.length; index += 1) {
  const arg = args[index];
  if (arg === '--message-file') {
    const file = args[index + 1];
    if (!file) {
      console.error('--message-file requires a path');
      process.exit(2);
    }
    message = await readFile(file, 'utf8');
    index += 1;
  } else if (arg === '--message-b64') {
    const encoded = args[index + 1];
    if (!encoded) {
      console.error('--message-b64 requires a base64 value');
      process.exit(2);
    }
    message = Buffer.from(encoded, 'base64').toString('utf8');
    index += 1;
  } else {
    message = `${message}${message ? ' ' : ''}${arg}`;
  }
}

message = message.replace(/^\uFEFF/, '').trim();

const payload = {
  state,
  message: message.slice(0, 140) || undefined,
  source: 'manual-script',
  updatedAt: new Date().toISOString()
};

await mkdir(dirname(stateFile), { recursive: true });
const tempFile = `${stateFile}.${process.pid}.tmp`;
await writeFile(tempFile, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
await rename(tempFile, stateFile);

console.log(`Wrote ${state} -> ${stateFile}`);
