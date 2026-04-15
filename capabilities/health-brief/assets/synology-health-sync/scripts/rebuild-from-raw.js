import path from "node:path";
import { fileURLToPath } from "node:url";
import { rebuildFromRawArchives } from "../src/lib/summary.js";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const serviceRoot = path.resolve(scriptDir, "..");
const dataDir = path.resolve(process.env.HEALTH_SYNC_DATA_DIR || path.join(serviceRoot, "data"));
const timezone = process.env.HEALTH_SYNC_TIMEZONE || "Asia/Shanghai";

const result = rebuildFromRawArchives({ dataDir, timezone });
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
