import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Temu 黑盒需 API 与 MCP 同机共享 UPLOAD_ROOT；本地页测默认代理到线上。
// 纯本地联调：VITE_API_PROXY=local npm run dev
const apiTarget =
  process.env.VITE_API_PROXY === 'local'
    ? process.env.VITE_API_TARGET || 'http://127.0.0.1:8000'
    : 'https://www.yoto.work/agent-platform'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5179,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
