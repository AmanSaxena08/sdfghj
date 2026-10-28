import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development the React app runs on Vite and forwards /api calls to the FastAPI server,
// so the browser sees one origin just like in Docker (nginx) and on Vercel.
export default defineConfig({
  plugins: [react()],
  build: {
    // Libraries (React + Recharts, ~180 kB gzipped) ship as their own long-cached file,
    // separate from our own code, which changes more often.
    chunkSizeWarningLimit: 700,
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [{ name: 'vendor', test: /node_modules/ }],
        },
      },
    },
  },
  server: {
    port: 5200,
    proxy: {
      '/api': process.env.API_PROXY_TARGET ?? 'http://localhost:8010',
    },
  },
})
