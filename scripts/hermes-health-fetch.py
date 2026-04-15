#!/usr/bin/env python3
import json
import os
import sys
from urllib.request import ProxyHandler, build_opener


DEFAULT_URL = os.environ.get("HERMES_HEALTH_SUMMARY_URL", "http://100.98.2.78:8780/api/health/summary/latest")
OPENER = build_opener(ProxyHandler({}))


def fetch_json(url: str) -> dict:
    with OPENER.open(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def render_markdown(summary: dict) -> str:
    latest = summary.get("latest", {})
    metrics = latest.get("metrics", {})
    workouts = latest.get("workouts", {})
    trend7 = summary.get("trend7d", {})
    trend30 = summary.get("trend30d", {})

    preferred_keys = [
        "sleep_duration",
        "resting_heart_rate",
        "hrv",
        "heart_rate",
        "steps",
        "active_energy",
        "vo2_max",
        "respiratory_rate",
        "blood_oxygen",
    ]

    lines = [
        "# Hermes Health Context",
        "",
        f"- generated_at: {summary.get('generatedAt', '')}",
        f"- latest_date: {summary.get('latestDate', '')}",
        f"- workouts_today: {workouts.get('count', 0)}",
        f"- workout_minutes_today: {workouts.get('totalDurationMinutes', 0)}",
        f"- workout_energy_kcal_today: {workouts.get('totalEnergyKcal', 0)}",
        "",
        "## Latest Metrics",
    ]

    for key in preferred_keys:
        metric = metrics.get(key)
        if not metric:
            continue
        lines.append(format_metric_line(key, metric))

    lines.extend(["", "## Trend 7d"])
    for key in preferred_keys:
        metric = trend7.get("metrics", {}).get(key)
        if not metric:
            continue
        lines.append(format_metric_line(key, metric, include_samples=True))

    lines.extend(["", "## Trend 30d"])
    for key in preferred_keys:
        metric = trend30.get("metrics", {}).get(key)
        if not metric:
            continue
        lines.append(format_metric_line(key, metric, include_samples=True))

    lines.extend(["", "## Daily Files"])
    for item in summary.get("availableDailyFiles", [])[-14:]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def format_metric_line(key: str, metric: dict, include_samples: bool = False) -> str:
    parts = [f"- {key}:"]
    if metric.get("total") is not None:
        parts.append(f"total={metric.get('total')} {metric.get('unit','')}".rstrip())
    if metric.get("average") is not None:
        parts.append(f"avg={metric.get('average')} {metric.get('unit','')}".rstrip())
    parts.append(f"min={metric.get('min')}")
    parts.append(f"max={metric.get('max')}")
    parts.append(f"last={metric.get('last')}")
    if include_samples:
        parts.append(f"samples={metric.get('sampleCount')}")
    return " ".join(parts)


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    summary = fetch_json(url)
    if not isinstance(summary, dict) or not summary.get("latestDate"):
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1
    sys.stdout.write(render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
