# Phalo — YIIVA's Smart Engine

Python sister service to **nuwa** (the NestJS API). Phalo owns YIIVA's
computed intelligence — rankings, analytics aggregates, and (later) search
relevance and ML-adjacent features — as **scheduled batch jobs over the
shared Postgres**, plus a minimal internal API.

**Design doc (source of truth):** `../nuwa/docs/phalo-engine/phalo-foundation.md`
(+ `phalo-search.md` for the search-quality track). The locked principles:

- Phalo is **never in the user request path**. nuwa serves everything, with
  freshness-checked fallbacks — Phalo down means stale rankings, not an outage.
- Phalo **reads** nuwa's `public.*` tables and **writes only** to the `phalo`
  schema (Alembic-managed here; Prisma never touches it, and vice versa).
- Nothing here is browser-facing. The internal API is service-token gated.

## Stack

Python 3.12 · FastAPI · APScheduler (in-process) · SQLAlchemy Core + asyncpg ·
Alembic · uv

## Running locally

```bash
uv sync                      # install deps (creates .venv)
cp .env.example .env         # fill PHALO_DATABASE_URL + PHALO_SERVICE_TOKEN
uv run alembic upgrade head  # creates the phalo schema + tables
uv run uvicorn phalo.app:app --port 8000 --reload
```

- `GET /health` — liveness + last 5 job runs
- `GET /jobs` · `POST /jobs/{name}/run` — require the `X-Phalo-Token` header

Tests: `uv run pytest` · Lint: `uv run ruff check src tests`

## Database access

Locally Phalo can use the same connection string as nuwa. In deployed
environments create the dedicated role (run as the DB superuser):

```sql
CREATE ROLE phalo_rw LOGIN PASSWORD '...';
GRANT CONNECT ON DATABASE <db> TO phalo_rw;
GRANT USAGE ON SCHEMA public TO phalo_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO phalo_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO phalo_rw;
-- phalo owns its schema outright
CREATE SCHEMA IF NOT EXISTS phalo AUTHORIZATION phalo_rw;
-- nuwa's role needs read access to serve phalo-derived data
GRANT USAGE ON SCHEMA phalo TO <nuwa_role>;
ALTER DEFAULT PRIVILEGES FOR ROLE phalo_rw IN SCHEMA phalo
  GRANT SELECT ON TABLES TO <nuwa_role>;
```

## Jobs

Jobs are async functions registered in `src/phalo/jobs/` via
`@register(name, every_minutes=...)`. Every run writes a `phalo.job_runs`
row (status, timing, stats) — the freshness/observability primitive.

| Job | Cadence | Phase |
|---|---|---|
| `heartbeat` | hourly | 1 — proves the read/write loop |
| `trending_stores` | hourly | 2 (next) |
| `store_stats_daily` | nightly + intraday | 3 |
| `product_popularity`, `trending_searches` | hourly | 4 |

## Deploy (Railway)

One service. `Procfile` runs migrations then the server. Env vars:
`PHALO_DATABASE_URL` (the shared Postgres, phalo role),
`PHALO_SERVICE_TOKEN`, `PHALO_ENVIRONMENT=production`.
