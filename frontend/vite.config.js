import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 300,
    rollupOptions: {
      // Vue rarely changes, so keep it in its own file: an app update then doesn't re-download it.
      output: { manualChunks: { vue: ['vue'] } },
    },
  },
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
