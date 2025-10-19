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
      process.env.CUSTOM_DOMAIN || 'localhost',
      process.env.CUSTOM_DOMAIN ? `www.${process.env.CUSTOM_DOMAIN}` : 'www.localhost',
      process.env.CLOUD_RUN_URL ? new URL(process.env.CLOUD_RUN_URL).hostname : undefined,
      'localhost',
      '127.0.0.1',
      'all' // Allow all hosts in production
    ].filter(Boolean)
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})