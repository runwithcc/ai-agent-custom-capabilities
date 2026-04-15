import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { URL } from "node:url";
import { fileURLToPath } from "node:url";
import { ensureDir, readJson } from "./lib/files.js";
import { ingestHealthPayload } from "./lib/summary.js";

loadEnvFile();

const config = {
  port: Number(process.env.HEALTH_SYNC_PORT || 8780),
  bind: process.env.HEALTH_SYNC_BIND || "0.0.0.0",
  token: process.env.HEALTH_SYNC_TOKEN || "",
  timezone: process.env.HEALTH_SYNC_TIMEZONE || "Asia/Shanghai",
  dataDir: path.resolve(process.env.HEALTH_SYNC_DATA_DIR || "./data")
};

if (!config.token) {
  process.stderr.write("HEALTH_SYNC_TOKEN is required\n");
  process.exit(1);
}

ensureDir(config.dataDir);
ensureDir(path.join(config.dataDir, "raw"));
ensureDir(path.join(config.dataDir, "daily"));
ensureDir(path.join(config.dataDir, "exports", "daily"));

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);

  try {
    if (req.method === "GET" && url.pathname === "/healthz") {
      return writeJson(res, 200, { ok: true, service: "hermes-health-sync" });
    }

    if (req.method === "GET" && url.pathname === "/api/health/summary/latest") {
      const latest = readJson(path.join(config.dataDir, "exports", "daily-summary.json"), null);
      return writeJson(res, latest ? 200 : 404, latest || { ok: false, error: "summary_not_found" });
    }

    if (req.method === "GET" && url.pathname.startsWith("/api/health/daily/")) {
      const date = url.pathname.replace("/api/health/daily/", "");
      const doc = readJson(path.join(config.dataDir, "exports", "daily", `${date}.json`), null);
      return writeJson(res, doc ? 200 : 404, doc || { ok: false, error: "daily_not_found" });
    }

    if (req.method === "POST" && url.pathname === "/api/health/ingest") {
      authorize(req, config.token);
      const payload = await readJsonBody(req);
      const receivedAt = new Date().toISOString();
      const headers = normalizeHeaders(req.headers);
      const result = ingestHealthPayload({
        payload,
        headers,
        dataDir: config.dataDir,
        timezone: config.timezone,
        receivedAt
      });
      return writeJson(res, 202, {
        ok: true,
        receivedAt,
        rawFile: result.rawFile,
        updatedDates: result.updatedDates,
        latestSummaryPath: result.latestSummaryPath
      });
    }

    return writeJson(res, 404, { ok: false, error: "not_found" });
  } catch (error) {
    return writeJson(res, error.statusCode || 500, {
      ok: false,
      error: error.message || "internal_error"
    });
  }
});

server.listen(config.port, config.bind, () => {
  process.stdout.write(
    `[${new Date().toISOString()}] hermes-health-sync listening on ${config.bind}:${config.port}, data=${config.dataDir}\n`
  );
});

function loadEnvFile() {
  const envPath = path.resolve(path.join(path.dirname(fileURLToPath(import.meta.url)), "..", ".env"));
  if (!fs.existsSync(envPath)) {
    return;
  }
  const raw = fs.readFileSync(envPath, "utf8");
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }
    const index = trimmed.indexOf("=");
    if (index <= 0) {
      continue;
    }
    const key = trimmed.slice(0, index).trim();
    const value = trimmed.slice(index + 1).trim();
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

function authorize(req, expectedToken) {
  const authHeader = req.headers.authorization || "";
  const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : "";
  if (!token || token !== expectedToken) {
    const error = new Error("unauthorized");
    error.statusCode = 401;
    throw error;
  }
}

function normalizeHeaders(headers) {
  const next = {};
  for (const [key, value] of Object.entries(headers)) {
    next[key.toLowerCase()] = Array.isArray(value) ? value.join(",") : `${value || ""}`;
  }
  return next;
}

async function readJsonBody(req) {
  const chunks = [];
  let size = 0;

  for await (const chunk of req) {
    size += chunk.length;
    if (size > 25 * 1024 * 1024) {
      const error = new Error("payload_too_large");
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }

  const raw = Buffer.concat(chunks).toString("utf8").trim();
  if (!raw) {
    const error = new Error("empty_body");
    error.statusCode = 400;
    throw error;
  }

  try {
    return JSON.parse(raw);
  } catch {
    const error = new Error("invalid_json");
    error.statusCode = 400;
    throw error;
  }
}

function writeJson(res, statusCode, payload) {
  res.writeHead(statusCode, { "content-type": "application/json; charset=utf-8" });
  res.end(`${JSON.stringify(payload, null, 2)}\n`);
}
