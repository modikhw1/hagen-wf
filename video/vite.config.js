import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import lokalaFiler from './vite-lokal.js'

export default defineConfig({
  plugins: [react(), lokalaFiler()],
  server: { port: 5181 },
})
