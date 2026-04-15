# Hermes Health Sync

Small REST ingest service for Apple Health exports coming from Health Auto Export.

## What it does

- accepts authenticated `POST /api/health/ingest`
- stores every raw upload without loss
- rolls uploads into one daily archive file per calendar day
- writes a lightweight `daily-summary.json` for Hermes to read

## Local run

```bash
cp .env.example .env
npm start
```

## Environment

- `HEALTH_SYNC_PORT`: HTTP port, default `8780`
- `HEALTH_SYNC_BIND`: bind address, default `0.0.0.0`
- `HEALTH_SYNC_TOKEN`: bearer token required for ingest
- `HEALTH_SYNC_TIMEZONE`: summary timezone, default `Asia/Shanghai`
- `HEALTH_SYNC_DATA_DIR`: storage root, default `./data`

## Endpoints

- `GET /healthz`
- `POST /api/health/ingest`
- `GET /api/health/summary/latest`
- `GET /api/health/daily/YYYY-MM-DD`

## Storage layout

```text
data/
  raw/YYYY-MM-DD/*.json
  daily/YYYY-MM-DD.json
  exports/daily/YYYY-MM-DD.json
  exports/daily-summary.json
```

The raw files are the source of truth. Daily files are append-only summaries meant for Hermes and later weekly/monthly analytics.
