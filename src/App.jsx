import { useState, useEffect } from 'react'

function App() {
  const [version, setVersion] = useState('')
  const [systemInfo, setSystemInfo] = useState(null)
  const [pingResult, setPingResult] = useState('')
  const [storeValue, setStoreValue] = useState('')

  useEffect(() => {
    // Get app version
    window.electronAPI.getAppVersion().then(v => setVersion(v))
    
    // Get system info
    window.electronAPI.getSystemInfo().then(info => setSystemInfo(info))
  }, [])

  const handlePing = async () => {
    const result = await window.electronAPI.ping()
    setPingResult(result)
  }

  const handleStoreTest = async () => {
    // Set a value
    await window.electronAPI.store.set('test-key', 'Hello from Electron Store!')
    
    // Get the value
    const value = await window.electronAPI.store.get('test-key')
    setStoreValue(value)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-pink-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-5xl font-bold text-white mb-8">
          Electron + React + Vite
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Version Card */}
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-white mb-4">App Version</h2>
            <p className="text-3xl font-mono text-emerald-400">{version || 'Loading...'}</p>
          </div>

          {/* IPC Test Card */}
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-white mb-4">IPC Test</h2>
            <button
              onClick={handlePing}
              className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition-colors"
            >
              Send Ping
            </button>
            {pingResult && (
              <p className="mt-4 text-xl text-emerald-400">Response: {pingResult}</p>
            )}
          </div>

          {/* Store Test Card */}
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-white mb-4">Electron Store</h2>
            <button
              onClick={handleStoreTest}
              className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-2 px-4 rounded transition-colors"
            >
              Test Store
            </button>
            {storeValue && (
              <p className="mt-4 text-sm text-emerald-400 break-words">{storeValue}</p>
            )}
          </div>

          {/* System Info Card */}
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-white mb-4">System Info</h2>
            {systemInfo ? (
              <div className="text-left text-sm text-gray-300 space-y-1">
                <p><span className="text-blue-400">Platform:</span> {systemInfo.platform}</p>
                <p><span className="text-blue-400">Arch:</span> {systemInfo.arch}</p>
                <p><span className="text-blue-400">Electron:</span> {systemInfo.electronVersion}</p>
                <p><span className="text-blue-400">Chrome:</span> {systemInfo.chromeVersion}</p>
              </div>
            ) : (
              <p className="text-gray-400">Loading...</p>
            )}
          </div>
        </div>

        {/* Features List */}
        <div className="mt-8 bg-white/10 backdrop-blur-lg rounded-lg p-6 shadow-xl">
          <h2 className="text-2xl font-semibold text-white mb-4">Included Features</h2>
          <ul className="text-left text-gray-300 space-y-2">
            <li className="flex items-center">
              <span className="text-emerald-400 mr-2">✓</span>
              Electron 28 + React 18 + Vite 5
            </li>
            <li className="flex items-center">
              <span className="text-emerald-400 mr-2">✓</span>
              Tailwind CSS 3.4 with JIT mode
            </li>
            <li className="flex items-center">
              <span className="text-emerald-400 mr-2">✓</span>
              TypeScript support
            </li>
            <li className="flex items-center">
              <span className="text-emerald-400 mr-2">✓</span>
              Context Bridge security (preload pattern)
            </li>
            <li className="flex items-center">
              <span className="text-emerald-400 mr-2">✓</span>
              Electron Store for persistence
            </li>
            <li className="flex items-center">
              <span className="text-emerald-400 mr-2">✓</span>
              Hot reload in development
            </li>
            <li className="flex items-center">
              <span className="text-emerald-400 mr-2">✓</span>
              Production builds (NSIS, Portable, DMG, AppImage)
            </li>
          </ul>
        </div>

        {/* Documentation Link */}
        <div className="mt-8 text-center">
          <p className="text-gray-400">
            Built with ❤️ by <span className="text-white font-semibold">2nist</span>
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Extracted from CRAFT CPQ architecture
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
