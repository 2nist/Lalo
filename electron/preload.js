const { contextBridge, ipcRenderer } = require('electron')

/**
 * Preload bridge (CommonJS to avoid ESM preload issues).
 */

contextBridge.exposeInMainWorld('electronAPI', {
  // Basic communication
  ping: () => ipcRenderer.invoke('ping'),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),

  // Persistent store (electron-store)
  store: {
    get: (key) => ipcRenderer.invoke('store:get', key),
    set: (key, value) => ipcRenderer.invoke('store:set', key, value),
    delete: (key) => ipcRenderer.invoke('store:delete', key),
    clear: () => ipcRenderer.invoke('store:clear'),
  },

  // Event listeners (one-way communication)
  on: (channel, callback) => {
    const subscription = (event, ...args) => callback(...args)
    ipcRenderer.on(channel, subscription)
    return () => {
      ipcRenderer.removeListener(channel, subscription)
    }
  },

  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel)
  },

  // Audio fetch (yt-dlp wrapper)
  audio: {
    fetch: (payload) => ipcRenderer.invoke('audio:fetch', payload),
  },
})
