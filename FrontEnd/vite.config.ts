import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig, loadEnv} from 'vite';

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, '.', '');
  return {
    plugins: [react(), tailwindcss()],
    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      hmr: process.env.DISABLE_HMR !== 'true',
      proxy: {
        // kpi-service is published on host :8002 by docker-compose. The
        // front-end always calls /api/kpi/* so URLs stay env-agnostic; the
        // proxy rewrites the prefix away before forwarding.
        '/api/kpi': {
          target: env.VITE_KPI_API_URL || 'http://localhost:8002',
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/kpi/, ''),
        },
      },
    },
  };
});
