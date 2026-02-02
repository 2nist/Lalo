import { contextBridge, ipcRenderer } from 'electron'

/**
 * Expose protected methods that allow the renderer process to use
 * the ipcRenderer without exposing the entire object.
 * 
 * This follows Electron security best practices:
 * - contextIsolation: true
 * - nodeIntegration: false
 * - sandbox: true
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
    
    // Return unsubscribe function
    return () => {
      ipcRenderer.removeListener(channel, subscription)
    }
  },

  // Remove all listeners for a channel
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel)
  },
})
