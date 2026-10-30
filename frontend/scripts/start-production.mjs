import { cpSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const output = join(root, ".next", "standalone");
if (!existsSync(join(output, "server.js"))) {
  throw new Error("Production build not found. Run npm run build first.");
}
const require = createRequire(import.meta.url);
const { loadEnvConfig } = require("@next/env");
loadEnvConfig(root);

// Next's standalone bundle deliberately omits static/public assets. Copy them
// for local production, as the Dockerfile also does when building its image.
cpSync(join(root, ".next", "static"), join(output, ".next", "static"), {
  recursive: true,
});
if (existsSync(join(root, "public"))) {
  cpSync(join(root, "public"), join(output, "public"), { recursive: true });
}
process.env.HOSTNAME ||= "127.0.0.1";
process.env.PORT ||= "3000";
await import(pathToFileURL(join(output, "server.js")).href);
