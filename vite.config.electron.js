import { defineConfig } from 'vite'
import path from 'path'

export default defineConfig({
  build: {
    lib: {
      entry: path.resolve(__dirname, 'electron/main.js'),
      formats: ['cjs'],
      fileName: () => 'main.cjs',
    },
    outDir: 'dist-electron',
    emptyOutDir: true,
    rollupOptions: {
      external: ['electron', 'electron-store'],
    },
  },
})
