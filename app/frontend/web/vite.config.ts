import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    port: parseInt(process.env.PORT || '8080'),
    host: '0.0.0.0',
    allowedHosts: [
      'mergemind-ui-epjxxjzzfq-uc.a.run.app',
      'mergemind-ui-812918665937.us-central1.run.app',
      'localhost',
      '127.0.0.1'
    ]
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})