import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { ensureDir, listJsonFiles, readJson, writeJsonAtomic } from "./files.js";

const START_KEYS = ["startDate", "start_date", "dateFrom", "date_from", "from", "start", "timestamp", "time", "date"];
const END_KEYS = ["endDate", "end_date", "dateTo", "date_to", "to", "end"];
const NAME_KEYS = ["identifier", "type", "metric", "name", "key"];
const UNIT_KEYS = ["unit", "units"];
const VALUE_FIELDS = [
  ["value", ""],
  ["qty", ""],
  ["count", ""],
  ["total", "_total"],
  ["sum", "_total"],
  ["average", "_avg"],
  ["avg", "_avg"],
  ["min", "_min"],
  ["max", "_max"],
  ["duration", "_duration"],
  ["durationMinutes", "_duration_minutes"],
  ["distance", "_distance"],
  ["energy", "_energy"],
  ["calories", "_energy"],
  ["minutes", "_minutes"]
];

export function ingestHealthPayload({ payload, headers, dataDir, timezone, receivedAt }) {
  const rawFile = writeRawEnvelope({ payload, headers, dataDir, receivedAt });
  return ingestStoredEnvelope({
    payload,
    headers,
    rawFile,
    dataDir,
    timezone,
    receivedAt,
    buildSummary: true
  });
}

export function rebuildFromRawArchives({ dataDir, timezone }) {
  const rawFiles = listRawFiles(dataDir);
  clearDerivedOutputs(dataDir);

  let lastReceivedAt = new Date().toISOString();
  let lastUpdatedDates = [];

  for (const rawFile of rawFiles) {
    const envelope = readJson(rawFile, null);
    if (!envelope?.payload) {
      continue;
    }
    lastReceivedAt = envelope.receivedAt || lastReceivedAt;
    const result = ingestStoredEnvelope({
      payload: envelope.payload,
      headers: envelope.headers || {},
      rawFile,
      dataDir,
      timezone,
      receivedAt: lastReceivedAt,
      buildSummary: false
    });
    lastUpdatedDates = result.updatedDates;
  }

  const latestSummary = buildLatestSummary({
    dataDir,
    updatedDates: lastUpdatedDates,
    receivedAt: lastReceivedAt,
    timezone
  });

  return {
    rawFileCount: rawFiles.length,
    latestSummaryPath: path.join(dataDir, "exports", "daily-summary.json"),
    latestSummary
  };
}

function ingestStoredEnvelope({ payload, headers, rawFile, dataDir, timezone, receivedAt, buildSummary }) {
  const extracted = extractObservations({ payload, receivedAt, timezone });
  const grouped = groupByDay(extracted, timezone, receivedAt);
  const updatedDates = [];

  for (const [date, dayData] of grouped.entries()) {
    const dailyPath = path.join(dataDir, "daily", `${date}.json`);
    const previous = readJson(dailyPath, createEmptyDay(date));
    const next = mergeDay({
      previous,
      rawFile,
      receivedAt,
      timezone,
      headers,
      observations: dayData.observations,
      workouts: dayData.workouts
    });
    writeJsonAtomic(dailyPath, next);
    writeJsonAtomic(path.join(dataDir, "exports", "daily", `${date}.json`), next);
    updatedDates.push(date);
  }

  const latestSummary = buildSummary ? buildLatestSummary({ dataDir, updatedDates, receivedAt, timezone }) : null;
  return {
    rawFile,
    updatedDates,
    latestSummaryPath: path.join(dataDir, "exports", "daily-summary.json"),
    latestSummary
  };
}

function writeRawEnvelope({ payload, headers, dataDir, receivedAt }) {
  const receivedDate = receivedAt.slice(0, 10);
  const rawDir = path.join(dataDir, "raw", receivedDate);
  ensureDir(rawDir);
  const id = crypto.randomBytes(4).toString("hex");
  const rawFile = path.join(rawDir, `${receivedAt.replaceAll(":", "-")}-${id}.json`);
  writeJsonAtomic(rawFile, {
    receivedAt,
    headers,
    payload
  });
  return rawFile;
}

function createEmptyDay(date) {
  return {
    date,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    rawFiles: [],
    ingestSessions: [],
    metrics: {},
    workouts: {
      count: 0,
      totalDurationMinutes: 0,
      totalEnergyKcal: 0,
      items: []
    }
  };
}

function mergeDay({ previous, rawFile, receivedAt, timezone, headers, observations, workouts }) {
  const next = {
    ...previous,
    updatedAt: receivedAt,
    rawFiles: dedupeStrings([...(previous.rawFiles || []), rawFile]),
    ingestSessions: dedupeStrings([
      ...(previous.ingestSessions || []),
      headers["session-id"] || `${receivedAt}:${headers["automation-id"] || "manual"}`
    ]),
    timezone
  };

  next.metrics = { ...(previous.metrics || {}) };

  for (const observation of observations) {
    const key = observation.metricKey;
    const current = next.metrics[key] || {
      unit: observation.unit || "",
      count: 0,
      sum: 0,
      min: null,
      max: null,
      last: null,
      lastAt: null,
      samples: [],
      seenIds: []
    };
    const seenIds = new Set(current.seenIds || []);
    if (observation.id && seenIds.has(observation.id)) {
      continue;
    }

    current.unit = current.unit || observation.unit || "";
    current.count += 1;
    current.sum += observation.value;
    current.min = current.min === null ? observation.value : Math.min(current.min, observation.value);
    current.max = current.max === null ? observation.value : Math.max(current.max, observation.value);
    current.last = observation.value;
    current.lastAt = observation.at;
    current.seenIds = observation.id ? [...(current.seenIds || []), observation.id] : current.seenIds || [];
    current.samples = [...(current.samples || []), observation].slice(-20);
    next.metrics[key] = current;
  }

  const workoutBucket = {
    count: previous.workouts?.count || 0,
    totalDurationMinutes: previous.workouts?.totalDurationMinutes || 0,
    totalEnergyKcal: previous.workouts?.totalEnergyKcal || 0,
    items: [...(previous.workouts?.items || [])],
    seenIds: [...(previous.workouts?.seenIds || [])]
  };
  const seenWorkoutIds = new Set(workoutBucket.seenIds);

  for (const workout of workouts) {
    if (workout.id && seenWorkoutIds.has(workout.id)) {
      continue;
    }
    if (workout.id) {
      seenWorkoutIds.add(workout.id);
      workoutBucket.seenIds.push(workout.id);
    }
    workoutBucket.count += 1;
    workoutBucket.totalDurationMinutes += workout.durationMinutes || 0;
    workoutBucket.totalEnergyKcal += workout.totalEnergyKcal || 0;
    workoutBucket.items.push(workout);
  }
  workoutBucket.items = workoutBucket.items
    .sort((left, right) => `${left.startAt || ""}`.localeCompare(`${right.startAt || ""}`))
    .slice(-30);
  next.workouts = workoutBucket;
  return next;
}

function buildLatestSummary({ dataDir, updatedDates, receivedAt, timezone }) {
  const dailyDir = path.join(dataDir, "daily");
  const files = listJsonFiles(dailyDir);
  const docs = files.map((filePath) => readJson(filePath, null)).filter(Boolean);
  if (!docs.length) {
    return null;
  }

  docs.sort((left, right) => left.date.localeCompare(right.date));
  const latestDate = [...docs.map((doc) => doc.date), ...updatedDates].sort().at(-1);
  const latestDoc = docs.find((doc) => doc.date === latestDate) || docs.at(-1);
  const window7 = docs.filter((doc) => doc.date <= latestDoc.date).slice(-7);
  const window30 = docs.filter((doc) => doc.date <= latestDoc.date).slice(-30);

  const latestSummary = {
    generatedAt: receivedAt,
    timezone,
    latestDate: latestDoc.date,
    latest: compactDay(latestDoc),
    trend7d: summarizeWindow(window7),
    trend30d: summarizeWindow(window30),
    availableDailyFiles: docs.map((doc) => path.join(dataDir, "exports", "daily", `${doc.date}.json`))
  };

  writeJsonAtomic(path.join(dataDir, "exports", "daily-summary.json"), latestSummary);
  return latestSummary;
}

function compactDay(dayDoc) {
  const summary = {
    date: dayDoc.date,
    rawFiles: dayDoc.rawFiles,
    workouts: {
      count: dayDoc.workouts?.count || 0,
      totalDurationMinutes: round(dayDoc.workouts?.totalDurationMinutes || 0),
      totalEnergyKcal: round(dayDoc.workouts?.totalEnergyKcal || 0),
      items: (dayDoc.workouts?.items || []).slice(-10)
    },
    metrics: {}
  };

  for (const [key, metric] of Object.entries(dayDoc.metrics || {})) {
    summary.metrics[key] = {
      unit: metric.unit || "",
      count: metric.count || 0,
      total: round(metric.sum || 0),
      average: metric.count ? round(metric.sum / metric.count) : null,
      min: metric.min,
      max: metric.max,
      last: metric.last,
      lastAt: metric.lastAt
    };
  }
  return summary;
}

function summarizeWindow(docs) {
  const metrics = {};
  let workoutCount = 0;
  let workoutMinutes = 0;

  for (const doc of docs) {
    workoutCount += doc.workouts?.count || 0;
    workoutMinutes += doc.workouts?.totalDurationMinutes || 0;
    for (const [key, metric] of Object.entries(doc.metrics || {})) {
      const current = metrics[key] || {
        count: 0,
        sum: 0,
        min: null,
        max: null,
        last: null,
        unit: metric.unit || ""
      };
      current.count += metric.count || 0;
      current.sum += metric.sum || 0;
      current.min = current.min === null ? metric.min : Math.min(current.min, metric.min ?? current.min);
      current.max = current.max === null ? metric.max : Math.max(current.max, metric.max ?? current.max);
      current.last = metric.last ?? current.last;
      current.unit = current.unit || metric.unit || "";
      metrics[key] = current;
    }
  }

  const compactMetrics = {};
  for (const [key, metric] of Object.entries(metrics)) {
    compactMetrics[key] = {
      unit: metric.unit,
      total: round(metric.sum || 0),
      average: metric.count ? round(metric.sum / metric.count) : null,
      min: metric.min,
      max: metric.max,
      last: metric.last,
      sampleCount: metric.count
    };
  }

  return {
    days: docs.map((doc) => doc.date),
    workouts: {
      count: workoutCount,
      totalDurationMinutes: round(workoutMinutes)
    },
    metrics: compactMetrics
  };
}

function extractObservations({ payload, receivedAt, timezone }) {
  const official = extractOfficialPayload({ payload, receivedAt, timezone });
  if (official) {
    return official;
  }

  const observations = [];
  const workouts = [];
  walk(payload, [], (node, nodePath) => {
    if (!node || typeof node !== "object" || Array.isArray(node)) {
      return;
    }

    const workout = extractWorkout(node, nodePath, receivedAt, timezone);
    if (workout) {
      workouts.push(workout);
    }

    const startAt = readDateValue(node, START_KEYS) || receivedAt;
    for (const [field, suffix] of VALUE_FIELDS) {
      const rawValue = node[field];
      if (typeof rawValue !== "number" || Number.isNaN(rawValue)) {
        continue;
      }
      const baseName = resolveMetricBaseName(node, nodePath);
      const metricKey = canonicalMetricKey(`${baseName}${suffix}`);
      observations.push({
        id: buildObservationId({
          metricKey,
          at: startAt,
          value: rawValue,
          source: node.source || nodePath.join(".")
        }),
        metricKey,
        value: rawValue,
        unit: resolveObservationUnit(field, node),
        at: startAt,
        path: nodePath.join("."),
        source: node.source || ""
      });
    }
  });

  return { observations, workouts };
}

function extractOfficialPayload({ payload, receivedAt, timezone }) {
  const root = payload?.data && typeof payload.data === "object" ? payload.data : payload;
  const metricSeries = Array.isArray(root?.metrics) ? root.metrics : null;
  const workoutSeries = Array.isArray(root?.workouts) ? root.workouts : null;

  if (!metricSeries && !workoutSeries) {
    return null;
  }

  const observations = [];
  const workouts = [];

  for (const metric of metricSeries || []) {
    const metricName = `${metric?.name || ""}`.trim();
    const metricUnit = `${metric?.units || metric?.unit || ""}`.trim();
    const metricData = Array.isArray(metric?.data) ? metric.data : [];
    if (!metricName || !metricData.length) {
      continue;
    }

    if (metricName === "sleep_analysis") {
      for (const point of metricData) {
        const at = parseDate(point.date || point.sleepEnd || point.sleepStart) || receivedAt;
        const source = point.source || "";
        for (const [field, metricKey] of [
          ["totalSleep", "sleep_duration"],
          ["core", "sleep_core"],
          ["deep", "sleep_deep"],
          ["rem", "sleep_rem"],
          ["awake", "sleep_awake"],
          ["inBed", "sleep_in_bed"]
        ]) {
          const value = point[field];
          if (typeof value !== "number" || Number.isNaN(value)) {
            continue;
          }
          observations.push({
            id: buildObservationId({ metricKey, at, value, source }),
            metricKey,
            value,
            unit: "hr",
            at,
            source,
            path: `data.metrics.${metricName}.${field}`
          });
        }
      }
      continue;
    }

    const metricKey = canonicalMetricKey(metricName);
    for (const point of metricData) {
      const value = firstNumber(point.qty, point.value, point.Avg, point.avg, point.average, point.Min, point.min, point.Max, point.max);
      if (typeof value !== "number" || Number.isNaN(value)) {
        continue;
      }
      const at = parseDate(point.date || point.startDate || point.endDate) || receivedAt;
      const source = point.source || "";
      observations.push({
        id: buildObservationId({ metricKey, at, value, source }),
        metricKey,
        value,
        unit: metricUnit,
        at,
        source,
        path: `data.metrics.${metricName}`
      });
    }
  }

  for (const workout of workoutSeries || []) {
    const startAt = parseDate(workout.start || workout.startDate) || receivedAt;
    const endAt = parseDate(workout.end || workout.endDate) || startAt;
    const energy = normalizeEnergyKcal(
      firstNumber(workout.activeEnergyBurned?.qty, workout.totalEnergyBurned?.qty, workout.activeEnergyBurned, workout.totalEnergyBurned),
      workout.activeEnergyBurned?.units || workout.totalEnergyBurned?.units || ""
    );
    const distanceKm = normalizeDistanceKm(
      firstNumber(workout.totalDistance?.qty, workout.distance?.qty, workout.totalDistance, workout.distance),
      workout.totalDistance?.units || workout.distance?.units || ""
    );

    workouts.push({
      id: workout.id || buildWorkoutId(workout.name || workout.workoutActivityType || "workout", startAt, endAt),
      day: toLocalDate(startAt, timezone),
      sourcePath: "data.workouts",
      startAt,
      endAt,
      activityType: workout.name || workout.workoutActivityType || workout.activityType || "unknown",
      durationMinutes: normalizeDurationMinutes({ duration: workout.duration, durationMinutes: workout.durationMinutes }),
      totalEnergyKcal: energy,
      distanceKm
    });
  }

  return { observations, workouts };
}

function extractWorkout(node, nodePath, receivedAt, timezone) {
  const looksLikeWorkout =
    typeof node.workoutActivityType === "string" ||
    typeof node.activityType === "string" ||
    ((typeof node.duration === "number" || typeof node.durationMinutes === "number") &&
      (typeof node.distance === "number" ||
        typeof node.totalEnergyBurned === "number" ||
        typeof node.energy === "number" ||
        typeof node.calories === "number"));

  if (!looksLikeWorkout) {
    return null;
  }

  const startAt = readDateValue(node, START_KEYS) || receivedAt;
  const endAt = readDateValue(node, END_KEYS) || startAt;
  const durationMinutes = normalizeDurationMinutes(node);
  const totalEnergyKcal = firstNumber(node.totalEnergyBurned, node.energy, node.calories);
  const distanceKm = normalizeDistanceKm(node.distance, readUnit(node));

  return {
    id: node.id || buildWorkoutId(node.workoutActivityType || node.activityType || node.type || "unknown", startAt, endAt),
    day: toLocalDate(startAt, timezone),
    sourcePath: nodePath.join("."),
    startAt,
    endAt,
    activityType: node.workoutActivityType || node.activityType || node.type || "unknown",
    durationMinutes,
    totalEnergyKcal,
    distanceKm
  };
}

function groupByDay(extracted, timezone, receivedAt) {
  const grouped = new Map();

  for (const observation of extracted.observations) {
    const day = toLocalDate(observation.at || receivedAt, timezone);
    ensureDay(grouped, day).observations.push(observation);
  }

  for (const workout of extracted.workouts) {
    ensureDay(grouped, workout.day || toLocalDate(receivedAt, timezone)).workouts.push(workout);
  }

  if (!grouped.size) {
    grouped.set(toLocalDate(receivedAt, timezone), { observations: [], workouts: [] });
  }

  return grouped;
}

function ensureDay(grouped, day) {
  if (!grouped.has(day)) {
    grouped.set(day, { observations: [], workouts: [] });
  }
  return grouped.get(day);
}

function walk(value, pathParts, visitor) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => walk(item, [...pathParts, String(index)], visitor));
    return;
  }
  if (!value || typeof value !== "object") {
    return;
  }
  visitor(value, pathParts);
  for (const [key, next] of Object.entries(value)) {
    walk(next, [...pathParts, key], visitor);
  }
}

function resolveMetricBaseName(node, nodePath) {
  for (const key of NAME_KEYS) {
    const value = node[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  const filtered = nodePath.filter((segment) => !/^\d+$/.test(segment));
  return filtered.at(-1) || "measurement";
}

function canonicalMetricKey(value) {
  const normalized = slugify(value);
  const aliases = [
    ["step_count", "steps"],
    ["step", "steps"],
    ["sleep_analysis", "sleep_duration"],
    ["sleep", "sleep_duration"],
    ["resting_heart", "resting_heart_rate"],
    ["blood_oxygen_saturation", "blood_oxygen"],
    ["heart_rate_variability", "hrv"],
    ["heart_variability", "hrv"],
    ["hrv", "hrv"],
    ["heart_rate", "heart_rate"],
    ["active_energy", "active_energy"],
    ["vo2", "vo2_max"],
    ["weight", "body_weight"],
    ["body_mass", "body_weight"],
    ["walking_running_distance", "walking_running_distance"],
    ["exercise_time", "exercise_minutes"],
    ["blood_oxygen", "blood_oxygen"],
    ["respiratory_rate", "respiratory_rate"]
  ];
  const match = aliases.find(([needle]) => normalized.includes(needle));
  return match ? match[1] : normalized;
}

function slugify(value) {
  return `${value}`
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .toLowerCase();
}

function readDateValue(node, keys) {
  for (const key of keys) {
    const value = node[key];
    const date = parseDate(value);
    if (date) {
      return date;
    }
  }
  return null;
}

function parseDate(value) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toISOString();
}

function readUnit(node) {
  for (const key of UNIT_KEYS) {
    const value = node[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  return "";
}

function resolveObservationUnit(field, node) {
  if (field === "duration" || field === "durationMinutes" || field === "minutes") {
    return "minutes";
  }
  if (field === "energy" || field === "calories") {
    return "kcal";
  }
  return readUnit(node);
}

function normalizeDurationMinutes(node) {
  if (typeof node.durationMinutes === "number") {
    return node.durationMinutes;
  }
  if (typeof node.duration === "number") {
    return node.duration > 1000 ? round(node.duration / 60) : node.duration;
  }
  return 0;
}

function normalizeDistanceKm(distance, unit) {
  if (typeof distance !== "number" || Number.isNaN(distance)) {
    return 0;
  }
  const normalizedUnit = `${unit || ""}`.toLowerCase();
  if (normalizedUnit.includes("km")) {
    return distance;
  }
  if (normalizedUnit.includes("m")) {
    return round(distance / 1000);
  }
  return distance;
}

function toLocalDate(value, timezone) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date(value));
}

function dedupeStrings(values) {
  return [...new Set(values.filter(Boolean))];
}

function buildObservationId({ metricKey, at, value, source }) {
  return `${metricKey}|${at}|${round(value)}|${source || ""}`;
}

function buildWorkoutId(activityType, startAt, endAt) {
  return `${activityType}|${startAt}|${endAt}`;
}

function listRawFiles(dataDir) {
  const rawRoot = path.join(dataDir, "raw");
  if (!fs.existsSync(rawRoot)) {
    return [];
  }
  const dayDirs = fs.readdirSync(rawRoot).map((name) => path.join(rawRoot, name)).filter((candidate) => fs.statSync(candidate).isDirectory());
  return dayDirs.flatMap((dirPath) => listJsonFiles(dirPath)).sort();
}

function clearDerivedOutputs(dataDir) {
  const targets = [path.join(dataDir, "daily"), path.join(dataDir, "exports", "daily")];
  for (const dirPath of targets) {
    ensureDir(dirPath);
    for (const filePath of listJsonFiles(dirPath)) {
      fs.rmSync(filePath, { force: true });
    }
  }
  fs.rmSync(path.join(dataDir, "exports", "daily-summary.json"), { force: true });
}

function round(value) {
  return Math.round(value * 100) / 100;
}

function firstNumber(...values) {
  for (const value of values) {
    if (typeof value === "number" && !Number.isNaN(value)) {
      return value;
    }
  }
  return 0;
}

function normalizeEnergyKcal(value, unit) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }
  const normalizedUnit = `${unit || ""}`.toLowerCase();
  if (normalizedUnit.includes("kj")) {
    return round(value / 4.184);
  }
  return value;
}
