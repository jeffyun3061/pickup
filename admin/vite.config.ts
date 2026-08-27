import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  // 프로덕션은 FastAPI가 /admin 으로 same-origin 서빙
  base: '/admin/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
});
