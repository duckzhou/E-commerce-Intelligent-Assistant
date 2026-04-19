import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const isProd = mode === 'production'
  
  return {
    plugins: [vue()],
    base: '/',
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, options) => {
            proxy.on('proxyReq', (proxyReq, req, res) => {
              if (req.headers['content-type'] && req.headers['content-type'].includes('multipart/form-data')) {
                proxyReq.setHeader('Content-Type', req.headers['content-type']);
              }
            });
            proxy.on('proxyRes', (proxyRes, req, res) => {
              if (req.url && req.url.includes('/chat/stream')) {
                proxyRes.headers['X-Accel-Buffering'] = 'no';
                proxyRes.headers['Cache-Control'] = 'no-cache';
                proxyRes.headers['Connection'] = 'keep-alive';
              }
            });
          }
        }
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      minify: 'esbuild'
    }
  }
})
