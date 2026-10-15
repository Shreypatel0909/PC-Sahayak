import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development the Python API runs separately (uvicorn api.main:app --port 8000);
// Vite forwards /api calls to it so the browser only ever talks to one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
});
