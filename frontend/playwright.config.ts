/**
 * Браузерные E2E запускаются в Chromium. baseURL — локальный frontend, viewport — 1920×1080. webServer поднимает Vite, либо повторно использует существующий сервер вне CI. Скриншоты/trace сохраняются при ошибке.
 */
import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  use: {
    baseURL: "http://127.0.0.1:8017",
    viewport: { width: 1920, height: 1080 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "node e2e-server.mjs",
    url: "http://127.0.0.1:8017/health",
    reuseExistingServer: false,
  },
});
