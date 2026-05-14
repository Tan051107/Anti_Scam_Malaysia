import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://54.160.109.226',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
