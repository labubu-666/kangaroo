import { defineConfig, devices } from "@playwright/experimental-ct-react";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  testDir: "src",
  testMatch: "**/*.ct.spec.tsx",
  timeout: 10 * 1000,
  fullyParallel: true,
  reporter: "list",
  use: {
    ctPort: 3100,
    ctViteConfig: {
      plugins: [react(), tailwindcss()],
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
