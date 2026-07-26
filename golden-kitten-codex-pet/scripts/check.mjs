import { access, readFile, stat } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const root = dirname(dirname(fileURLToPath(import.meta.url)));

const requiredFiles = [
  'package.json',
  'README.md',
  'src/main.js',
  'src/preload.js',
  'src/renderer.js',
  'src/index.html',
  'src/styles.css',
  'scripts/codex-pet-hook.mjs',
  'scripts/launch.ps1',
  'scripts/open-codex.ps1',
  'scripts/write-state.mjs',
  'hooks.example.json',
  'assets/golden-kitten.png'
];

for (const file of requiredFiles) {
  await access(join(root, file));
}

const packageJson = JSON.parse(await readFile(join(root, 'package.json'), 'utf8'));
if (!packageJson.scripts?.start || !packageJson.scripts?.check) {
  throw new Error('package.json scripts.start/check are required');
}

const asset = await stat(join(root, 'assets/golden-kitten.png'));
if (asset.size < 10_000) {
  throw new Error('assets/golden-kitten.png looks too small');
}

for (const file of ['src/main.js', 'src/preload.js', 'src/renderer.js', 'scripts/codex-pet-hook.mjs']) {
  const result = spawnSync(process.execPath, ['--check', join(root, file)], {
    encoding: 'utf8'
  });
  if (result.status !== 0) {
    throw new Error(`${file} syntax check failed:\n${result.stderr || result.stdout}`);
  }
}

console.log('OK: golden-kitten-codex-pet project files and JavaScript syntax look valid.');
