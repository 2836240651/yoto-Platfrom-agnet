/**
 * Minimal preload — thin shell has no Node bridge into page JS.
 * Kept for future safe APIs (e.g. app version) without nodeIntegration.
 */
const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('yotoDesktop', {
  shell: true,
  kind: 'workspace-thin',
})
