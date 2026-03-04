# Electron + React + Vite Boilerplate

Production-ready template for building cross-platform desktop applications with modern web technologies.

## Features

- **⚡ Electron 28** - Latest Electron with security best practices
- **⚛️ React 18** - Modern React with hooks and concurrent features  
- **🚀 Vite 5** - Lightning-fast HMR and optimized builds
- **🎨 Tailwind CSS 3.4** - Utility-first CSS with JIT mode
- **📘 TypeScript** - Full TypeScript support (opt-in)
- **🔒 Security First** - Context isolation, sandboxed renderer, no node integration
- **💾 Persistent Storage** - electron-store for settings and data
- **📦 Multi-Platform Builds** - Windows (NSIS, Portable), macOS (DMG), Linux (AppImage)
- **🔧 Dev Tools** - Hot reload, React DevTools, debugging ready

## Quick Start

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run electron:dev
```

This starts both the Vite dev server (http://localhost:5173) and Electron with hot reload enabled.

### Build for Production

```bash
# Build renderer and electron
npm run build

# Package with electron-builder
npm run electron:build
```

Built artifacts will be in the `release/` directory.

## Project Structure

```
electron-react-vite-boilerplate/
├── electron/              # Electron main process
│   ├── main.js           # Main process entry (IPC handlers, window management)
│   └── preload.js        # Preload script (context bridge, security)
├── src/                  # React renderer process
│   ├── App.jsx           # Main React component
│   ├── main.jsx          # React entry point  
│   └── index.css         # Global styles (Tailwind)
├── public/               # Static assets
├── dist/                 # Renderer build output (Vite)
├── dist-electron/        # Main process build output
├── release/              # Final packaged apps
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration (renderer)
├── vite.config.electron.js  # Vite configuration (main process)
├── tailwind.config.js    # Tailwind CSS configuration
├── postcss.config.js     # PostCSS with Tailwind
└── tsconfig.json         # TypeScript configuration
```

## Security Architecture

This template follows Electron security best practices:

### Context Isolation

```javascript
// electron/main.js
webPreferences: {
  preload: path.join(__dirname, 'preload.js'),
  contextIsolation: true,      // ✓ Enabled
  nodeIntegration: false,       // ✓ Disabled
  sandbox: true,                // ✓ Enabled
}
```

### Preload Script (Context Bridge)

```javascript
// electron/preload.js
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  ping: () => ipcRenderer.invoke('ping'),
  // Only expose specific, safe APIs
})
```

### Renderer Process (React)

```javascript
// src/App.jsx
const result = await window.electronAPI.ping()
// No direct access to Node.js or Electron APIs
```

## IPC Communication

### Renderer → Main (Invoke)

**Renderer (React):**
```javascript
const result = await window.electronAPI.ping()
```

**Preload:**
```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  ping: () => ipcRenderer.invoke('ping'),
})
```

**Main Process:**
```javascript
ipcMain.handle('ping', () => {
  return 'pong'
})
```

### Main → Renderer (Events)

**Main Process:**
```javascript
mainWindow.webContents.send('update-available', updateInfo)
```

**Preload:**
```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  on: (channel, callback) => {
    ipcRenderer.on(channel, (event, ...args) => callback(...args))
  },
})
```

**Renderer (React):**
```javascript
useEffect(() => {
  const unsubscribe = window.electronAPI.on('update-available', (info) => {
    console.log('Update available:', info)
  })
  
  return () => unsubscribe()
}, [])
```

## Persistent Storage

Uses `electron-store` for simple key-value persistence:

```javascript
// Set value
await window.electronAPI.store.set('user-preferences', {
  theme: 'dark',
  language: 'en',
})

// Get value
const prefs = await window.electronAPI.store.get('user-preferences')

// Delete value
await window.electronAPI.store.delete('user-preferences')

// Clear all
await window.electronAPI.store.clear()
```

Data is stored in:
- **Windows:** `%APPDATA%/<app-name>/config.json`
- **macOS:** `~/Library/Application Support/<app-name>/config.json`
- **Linux:** `~/.config/<app-name>/config.json`

## Building for Production

### Windows (NSIS Installer + Portable)

```bash
npm run electron:build
```

Creates:
- `release/Electron React Vite App Setup.exe` (installer)
- `release/Electron React Vite App Portable.exe` (portable)

### macOS (DMG)

```bash
npm run electron:build
```

Creates: `release/Electron React Vite App.dmg`

### Linux (AppImage)

```bash
npm run electron:build
```

Creates: `release/Electron React Vite App.AppImage`

## Customization

### Change App Name

Update `package.json`:

```json
{
  "name": "your-app-name",
  "productName": "Your App Name",
  "build": {
    "appId": "com.yourcompany.yourapp",
    "productName": "Your App Name"
  }
}
```

### Add Icons

Place icons in `build/` directory:
- `build/icon.ico` (Windows)
- `build/icon.icns` (macOS)
- `build/icon.png` (Linux, 512x512)

### Configure Window

Edit `electron/main.js`:

```javascript
mainWindow = new BrowserWindow({
  width: 1200,
  height: 800,

## Section Verification (MIR)

You can validate section boundary quality of imported songs with a local CLI:

```bash
npm run verify:sections -- --song datasets/mcgill/mcgill_jcrd_salami_Billboard/school_s_out_alice_cooper.json --strategy auto-json
```

With an external reference file:

```bash
npm run verify:sections -- --song datasets/mcgill/mcgill_jcrd_salami_Billboard/school_s_out_alice_cooper.json --strategy auto-json --reference path/to/reference.json --tolerance 0.5
```

Generate a reference template from dataset timestamps:

```bash
npm run verify:sections -- --mode template --song datasets/mcgill/mcgill_jcrd_salami_Billboard/school_s_out_alice_cooper.json
```

Reference format:

```json
{
  "sections": [
    { "label": "Verse", "start_s": 12.0, "end_s": 35.4 },
    { "label": "Chorus", "start_ms": 35400, "end_ms": 58200 }
  ]
}
```

The script reports:
- Boundary precision / recall / F1 with a tolerance window.
- Duration-weighted label agreement (exact label match).

### SALAMI-first workflow

Fetch/update the SALAMI public annotations:

```bash
npm run dataset:fetch:salami
```

Build normalized SALAMI references and McGill->SALAMI title/artist matches:

```bash
npm run dataset:build:salami-refs
```

Outputs:
- `data/normalized/salami/salami_song_index.json`
- `data/normalized/salami/salami_references.json`
- `data/normalized/salami/mcgill_to_salami_matches.json`

Verify against a specific SALAMI song id/annotator:

```bash
npm run verify:sections -- --song datasets/mcgill/mcgill_jcrd_salami_Billboard/school_s_out_alice_cooper.json --strategy auto-json --salami-refs data/normalized/salami/salami_references.json --salami-song-id 20 --salami-annotator primary
```
  minWidth: 800,
  minHeight: 600,
  frame: true,          // Show window frame
  transparent: false,   // Transparent window
  resizable: true,      // Allow resizing
  // ... more options
})
```

## TypeScript Usage

The template supports TypeScript out of the box. To use TypeScript:

1. Rename `.jsx` → `.tsx` and `.js` → `.ts`
2. Add type definitions:

```typescript
// src/App.tsx
import { useState, useEffect } from 'react'

interface SystemInfo {
  platform: string
  arch: string
  electronVersion: string
  chromeVersion: string
}

function App() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  // ...
}
```

## Scripts Reference

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server only |
| `npm run electron:dev` | Start Vite + Electron (hot reload) |
| `npm run build` | Build renderer + main process |
| `npm run electron:build` | Build + package with electron-builder |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Check TypeScript types |

## Troubleshooting

### Electron window is blank

Make sure Vite dev server is running on `http://localhost:5173`:

```bash
npm run dev  # In terminal 1
# Wait for server to start
npm run electron:dev  # In terminal 2
```

### Build fails

Clear build caches:

```bash
rm -rf dist dist-electron release node_modules
npm install
npm run build
```

### "require is not defined" error

This means you're trying to use Node.js APIs in the renderer. Use IPC instead:

❌ **Wrong:**
```javascript
const fs = require('fs')  // Not allowed in renderer
```

✓ **Correct:**
```javascript
// Add to preload.js
contextBridge.exposeInMainWorld('fileAPI', {
  readFile: (path) => ipcRenderer.invoke('read-file', path),
})

// Add to main.js
ipcMain.handle('read-file', (event, filePath) => {
  return fs.promises.readFile(filePath, 'utf-8')
})

// Use in renderer
const content = await window.fileAPI.readFile('/path/to/file')
```

## Examples

### Add a New IPC Channel

**1. Define handler in `electron/main.js`:**

```javascript
ipcMain.handle('get-user-data', async (event, userId) => {
  // Fetch from database, API, etc.
  return { id: userId, name: 'John Doe' }
})
```

**2. Expose in `electron/preload.js`:**

```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  getUserData: (userId) => ipcRenderer.invoke('get-user-data', userId),
  // ... existing methods
})
```

**3. Use in React components:**

```javascript
const userData = await window.electronAPI.getUserData(123)
```

### Add Tailwind Custom Theme

Edit `tailwind.config.js`:

```javascript
export default {
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#8B5CF6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
}
```

## Credits

Extracted from [CRAFT CPQ](https://github.com/2nist/craft_tools_hub) architecture as part of the repository refactoring initiative.

## License

MIT License - see [LICENSE](LICENSE) file

## Related Projects

- [@2nist/music-theory](https://github.com/2nist/music-theory) - Music theory utilities
- [@2nist/max-dict-helpers](https://github.com/2nist/max-dict-helpers) - Max for Live helpers
- [chordify-agent](https://github.com/2nist/chordify-agent) - MIDI chord recognition
- [reaper-bridge](https://github.com/2nist/reaper-bridge) - REAPER automation

## Support

For issues, questions, or contributions, please visit:
https://github.com/2nist/electron-react-vite-boilerplate
