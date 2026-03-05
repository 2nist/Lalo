import { app, BrowserWindow, ipcMain } from 'electron'
import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'
import Store from 'electron-store'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Initialize electron-store for persistent settings
const store = new Store()

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  // Load the app
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// App lifecycle
app.whenReady().then(() => {
  registerIpcHandlers()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC Handlers
function registerIpcHandlers() {
  // Basic ping/pong
  ipcMain.handle('ping', () => {
    return 'pong'
  })

  // Get app version
  ipcMain.handle('get-app-version', () => {
    return app.getVersion()
  })

  // Store operations
  ipcMain.handle('store:get', (event, key) => {
    return store.get(key)
  })

  ipcMain.handle('store:set', (event, key, value) => {
    store.set(key, value)
    return { success: true }
  })

  ipcMain.handle('store:delete', (event, key) => {
    store.delete(key)
    return { success: true }
  })

  ipcMain.handle('store:clear', () => {
    store.clear()
    return { success: true }
  })

  // Example: Get system info
  ipcMain.handle('get-system-info', () => {
    return {
      platform: process.platform,
      arch: process.arch,
      version: process.version,
      electronVersion: process.versions.electron,
      chromeVersion: process.versions.chrome,
    }
  })

  // Audio fetch via yt-dlp wrapper
  ipcMain.handle('audio:fetch', async (event, payload) => {
    const { url, slug, outDir, format } = payload || {}
    if (!url || !slug) {
      throw new Error('audio:fetch requires url and slug')
    }
    const scriptPath = path.join(__dirname, '../scripts/experiments/downloadAudio.js')
    const args = [scriptPath, '--url', url, '--slug', slug]
    if (outDir) args.push('--out-dir', outDir)
    if (format) args.push('--format', format)

    const nodeBin =
      process.env.NPM_NODE_EXEC_PATH ||
      process.env.npm_node_execpath ||
      process.env.NODE_BINARY ||
      'node'

    return await new Promise((resolve, reject) => {
      let stdout = ''
      let stderr = ''
      let proc
      try {
        proc = spawn(nodeBin, args, {
          cwd: path.join(__dirname, '..'),
          stdio: ['ignore', 'pipe', 'pipe'],
          shell: false,
        })
      } catch (err) {
        reject(new Error(`audio:fetch spawn failed: ${err instanceof Error ? err.message : String(err)}`))
        return
      }

      proc.stdout.on('data', (d) => { stdout += d.toString() })
      proc.stderr.on('data', (d) => { stderr += d.toString() })
      proc.on('error', (err) => {
        reject(new Error(`audio:fetch error: ${err instanceof Error ? err.message : String(err)}`))
      })
      proc.on('close', (code, signal) => {
        if (code === 0) resolve({ ok: true, stdout })
        else reject(new Error(stderr || `audio:fetch failed (code ${code}${signal ? `, signal ${signal}` : ''}) using ${nodeBin}`))
      })
    })
  })
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
})
