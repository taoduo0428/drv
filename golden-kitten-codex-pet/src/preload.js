const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('goldenKittenPet', {
  getConfig: () => ipcRenderer.invoke('pet:get-config'),
  getWindowPosition: () => ipcRenderer.invoke('pet:get-window-position'),
  setWindowPosition: (position) => ipcRenderer.invoke('pet:set-window-position', position),
  hide: () => ipcRenderer.invoke('pet:hide'),
  openCodex: () => ipcRenderer.invoke('pet:open-codex'),
  cycleSize: () => ipcRenderer.invoke('pet:cycle-size'),
  resetWindow: () => ipcRenderer.invoke('pet:reset-window'),
  openStateFile: () => ipcRenderer.invoke('pet:open-state-file'),
  onState: (callback) => {
    const listener = (_event, payload) => callback(payload);
    ipcRenderer.on('pet-state', listener);
    return () => ipcRenderer.removeListener('pet-state', listener);
  }
});
