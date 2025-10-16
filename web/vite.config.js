import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import dotenv from 'dotenv';
import path from 'path';

// Load .env file from two levels up
dotenv.config({ path: path.resolve(__dirname, '../.env') });

export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_API_BASE': JSON.stringify(process.env.VITE_API_BASE || 'http://localhost:3001'),
    'import.meta.env.PASS_THRESHOLD': parseInt(process.env.PASS_THRESHOLD || 12),
  },
  server: {
    proxy: {
      // Proxy API requests
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      // Proxy static PDFs
      '/pdfs': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
});
