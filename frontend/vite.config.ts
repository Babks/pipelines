/**
 * Конфигурация инструмента разработки. react() включает JSX/React-плагин. strictPort запрещает молчаливый переход с 5173. proxy работает у dev-сервера; /api удаляется регулярным выражением. test — конфигурация Vitest с jsdom и setup-файлом.
 */
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["src/__tests__/setup.ts"],
    include: ["src/__tests__/**/*.test.{ts,tsx}"],
    css: false,
  },
});
