import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const isProd = mode === 'production'
  
  return {
    plugins: [vue()],
    base: '/',
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: 'http://backend:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, options) => {
            proxy.on('proxyReq', (proxyReq, req, res) => {
              // 传递所有原始请求的 headers
              if (req.headers['authorization']) {
                proxyReq.setHeader('Authorization', req.headers['authorization']);
              }
              if (req.headers['content-type'] && req.headers['content-type'].includes('multipart/form-data')) {
                proxyReq.setHeader('Content-Type', req.headers['content-type']);
              }
            });
            proxy.on('proxyRes', (proxyRes, req, res) => {
              if (req.url && req.url.includes('/chat/stream')) {
                proxyRes.headers['X-Accel-Buffering'] = 'no';
                proxyRes.headers['Cache-Control'] = 'no-cache';
                proxyRes.headers['Connection'] = 'keep-alive';
                proxyRes.headers['Content-Type'] = 'text/event-stream';
                proxyRes.headers['Transfer-Encoding'] = 'chunked';
              }
            });
          }
        },
        '/auth': {
          target: 'http://backend:8000',
          changeOrigin: true,
          configure: (proxy, options) => {
            proxy.on('proxyReq', (proxyReq, req, res) => {
              if (req.headers['authorization']) {
                proxyReq.setHeader('Authorization', req.headers['authorization']);
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
