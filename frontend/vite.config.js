import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3050, // must match the backend's CORS allow_origins entry
    strictPort: true,
    host: true, // bind on all interfaces (IPv4 + IPv6) -- some environments
                // otherwise default to IPv6-only loopback, which makes
                // http://127.0.0.1:3050 unreachable even though localhost works
  },
})
