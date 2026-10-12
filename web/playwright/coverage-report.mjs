// Merges the V8 coverage collected by playwright/fixtures.ts into an HTML report.
// Usage: COVERAGE=1 npm run test:ct && npm run coverage
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import MCR from "monocart-coverage-reports";

const webRoot = fileURLToPath(new URL("..", import.meta.url));
const rawDir = path.join(webRoot, "coverage/raw");
const assetsDir = path.join(webRoot, "playwright/.cache/assets");

const entries = readdirSync(rawDir)
  .filter((file) => file.endsWith(".json"))
  .flatMap((file) => JSON.parse(readFileSync(path.join(rawDir, file), "utf8")));

const mcr = MCR({
  name: "Component test coverage",
  outputDir: path.join(webRoot, "coverage/report"),
  reports: ["html", "console-summary"],
  // Only the app source; drop the Playwright harness and node_modules
  sourceFilter: "**/src/**",
  // The dev server that served the maps is gone, so read them from the build output
  sourceMapResolver: (url, defaultResolver) => {
    const mapFile = path.join(assetsDir, path.basename(url));
    return existsSync(mapFile)
      ? JSON.parse(readFileSync(mapFile, "utf8"))
      : defaultResolver(url);
  },
});

await mcr.add(entries);
await mcr.generate();
