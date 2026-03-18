import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    server: {
      proxy: {
          "/api": {
              target: "http://localhost:8000",
              changeOrigin: true,
          },
          "/health": {
              target: "http://localhost:8000",
              changeOrigin: true,
          },
          "/docs": {                          // ← добавить
              target: "http://localhost:8000",
              changeOrigin: true,
          },
          "/openapi.json": {                  // ← добавить — без этого docs не загрузит схему
              target: "http://localhost:8000",
              changeOrigin: true,
          },
          "/redoc": {                         // ← опционально
              target: "http://localhost:8000",
              changeOrigin: true,
          },
      }
    }
})