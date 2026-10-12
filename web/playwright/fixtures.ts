import { mkdirSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test as base, expect } from "@playwright/experimental-ct-react";

// Set COVERAGE=1 to record V8 JS coverage for every component test
const COLLECT = process.env.COVERAGE === "1";
const RAW_DIR = fileURLToPath(new URL("../coverage/raw", import.meta.url));

// Re-exported so component specs only need one import
export const test = base.extend<{ collectCoverage: void }>({
  collectCoverage: [
    async ({ page }, use) => {
      if (!COLLECT) {
        await use();
        return;
      }
      await page.coverage.startJSCoverage({ resetOnNavigation: false });
      await use();
      const entries = await page.coverage.stopJSCoverage();
      mkdirSync(RAW_DIR, { recursive: true });
      writeFileSync(
        path.join(RAW_DIR, `${randomUUID()}.json`),
        JSON.stringify(entries),
      );
    },
    { auto: true },
  ],
});

export { expect };
