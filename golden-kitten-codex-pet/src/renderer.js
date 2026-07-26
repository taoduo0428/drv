const shell = document.querySelector('.pet-shell');
const bubbleText = document.querySelector('.bubble-text');
const petImage = document.querySelector('.pet-image');
const phaseText = document.querySelector('.phase-text');
const progressFill = document.querySelector('.progress-fill');
const progressPercent = document.querySelector('.progress-percent');
const openCodexButton = document.querySelector('#open-codex');
const resizeButton = document.querySelector('#resize-pet');
const resetButton = document.querySelector('#reset-pet');
const hideButton = document.querySelector('#hide-pet');

const states = [
  ['idle', '喵，我在桌面待命。'],
  ['thinking', '正在思考下一步……'],
  ['running', '正在帮你跑命令。'],
  ['reviewing', '需要你看一眼。'],
  ['success', '完成啦，喵！'],
  ['failure', '这里好像失败了。'],
  ['attention', '主人，有新情况。']
];

let stateIndex = 0;
let lastExternalStateAt = 0;
let hasExternalState = false;
let dragStart = null;

function defaultProgress(state) {
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

function applyState(payload, external = false) {
  const state = typeof payload?.state === 'string' ? payload.state : 'idle';
  const message = typeof payload?.message === 'string' ? payload.message : states[0][1];
  const phase = typeof payload?.phase === 'string' && payload.phase ? payload.phase : state;
  const progressRaw = Number.isFinite(payload?.progress) ? payload.progress : defaultProgress(state);
  const progress = Math.max(0, Math.min(1, progressRaw));

  shell.dataset.state = state;
  bubbleText.textContent = message;
  phaseText.textContent = phase;
  progressFill.style.width = `${Math.round(progress * 100)}%`;
  progressPercent.textContent = `${Math.round(progress * 100)}%`;

  if (external) {
    hasExternalState = true;
    lastExternalStateAt = Date.now();
  }
}

function showNextDemoState() {
  stateIndex = (stateIndex + 1) % states.length;
  const [state, message] = states[stateIndex];
  applyState({ state, message }, false);
}

if (window.goldenKittenPet) {
  window.goldenKittenPet.onState((payload) => applyState(payload, true));
}

resizeButton.addEventListener('click', async (event) => {
  event.stopPropagation();
  const result = await window.goldenKittenPet?.cycleSize?.();
  applyState({
    state: 'attention',
    phase: '调节大小',
    progress: 0.35,
    message: result?.label ? `已切换为${result.label}号小猫。` : '已调节大小。'
  }, false);
});

resetButton.addEventListener('click', async (event) => {
  event.stopPropagation();
  await window.goldenKittenPet?.resetWindow?.();
  applyState({ state: 'attention', phase: '恢复窗口', progress: 0.35, message: '已恢复默认大小和位置。' }, false);
});

hideButton.addEventListener('click', (event) => {
  event.stopPropagation();
  window.goldenKittenPet?.hide();
});

openCodexButton.addEventListener('click', async (event) => {
  event.stopPropagation();
  applyState({ state: 'attention', phase: '唤起 Codex', progress: 0.2, message: '正在把 Codex 叫回来……' }, false);
  await window.goldenKittenPet?.openCodex?.();
});

async function startDrag(event) {
  if (event.button !== 0) return;
  if (event.target.closest('button')) return;
  if (!window.goldenKittenPet?.getWindowPosition) return;

  const position = await window.goldenKittenPet.getWindowPosition();
  dragStart = {
    pointerId: event.pointerId,
    screenX: event.screenX,
    screenY: event.screenY,
    windowX: position.x,
    windowY: position.y,
    moved: false
  };
  shell.setPointerCapture(event.pointerId);
}

function moveDrag(event) {
  if (!dragStart || event.pointerId !== dragStart.pointerId) return;
  const dx = event.screenX - dragStart.screenX;
  const dy = event.screenY - dragStart.screenY;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragStart.moved = true;
  window.goldenKittenPet?.setWindowPosition?.({
    x: dragStart.windowX + dx,
    y: dragStart.windowY + dy
  });
}

function endDrag(event) {
  if (!dragStart || event.pointerId !== dragStart.pointerId) return;
  try {
    shell.releasePointerCapture(event.pointerId);
  } catch {
    // Pointer capture may already be released by the browser.
  }
  setTimeout(() => {
    dragStart = null;
  }, 0);
}

shell.addEventListener('pointerdown', startDrag);
shell.addEventListener('pointermove', moveDrag);
shell.addEventListener('pointerup', endDrag);
shell.addEventListener('pointercancel', endDrag);

petImage.addEventListener('click', () => {
  if (dragStart?.moved) return;
  const phrases = [
    '喵～',
    '我盯着 Codex 呢。',
    '测试通过我就跳一下。',
    '有报错我会提醒你。'
  ];
  const message = phrases[Math.floor(Math.random() * phrases.length)];
  applyState({ state: 'attention', message }, false);
});

petImage.addEventListener('dblclick', async () => {
  applyState({ state: 'attention', phase: '唤起 Codex', progress: 0.2, message: '正在把 Codex 叫回来……' }, false);
  await window.goldenKittenPet?.openCodex?.();
});

setInterval(() => {
  if (!hasExternalState && Date.now() - lastExternalStateAt > 12000) {
    showNextDemoState();
  }
}, 6500);
