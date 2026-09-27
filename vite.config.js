import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// host: true exposes the dev server on your local network,
// so you can open the preview on your phone (same Wi-Fi).
export default defineConfig({
  plugins: [react()],
  server: { host: true },
})
