# Phalo — Claude project notes

Read this on session start. It's the durable context for working in this repo.

## What this is

**Phalo** is YIIVA's smart engine — the Python sister service to `../nuwa`
(NestJS API). It computes rankings, analytics aggregates, and later search
intelligence, as **batch jobs over the shared Postgres**. The full design is
locked in `../nuwa/docs/phalo-engine/phalo-foundation.md` and
`phalo-search.md` — **read those before adding features**; decisions there
(PH-1…PH-5, S1–S4) are binding until explicitly revisited.

Non-negotiables:
- **Never in the user request path.** nuwa serves users and falls back to
  heuristics when phalo tables are stale/missing. Don't build endpoints that
  user surfaces would call directly.
- **Write only to the `phalo` schema** (Alembic-owned). Read `public.*`
  freely but never write it — that's Prisma's (nuwa's) territory.
- **Jobs are idempotent** — full-refresh per window inside one transaction.
  Every job run writes a `phalo.job_runs` row via the registry wrapper.

## Layout

```
src/phalo/
  config.py        pydantic-settings (PHALO_* env, fail-fast)
  db.py            async engine (SQLAlchemy Core + asyncpg); `connection()` ctx
  app.py           FastAPI factory; lifespan starts the APScheduler loop
  api/             internal surface: /health (open), /jobs* (X-Phalo-Token)
  jobs/
    registry.py    @register(name, every_minutes) + run_job (job_runs rows)
    scheduler.py   APScheduler interval wiring from the registry
    heartbeat.py   Phase 1 canary job
    __init__.py    ← import every job module here or it won't register
migrations/        Alembic, scoped to the phalo schema (version table inside it)
tests/             pytest; DB-free tests use env defaults + TestClient
```

## Conventions

- **Explicit SQL** (SQLAlchemy `text()`), no ORM models — nuwa's Prisma schema
  is the source of truth for `public.*`; mirror nothing.
- New job = new module with `@register` + import in `jobs/__init__.py` + (if
  it writes a new table) an Alembic migration in `migrations/versions/`.
- Job stats go in the returned dict — they land in `job_runs.detail`.
- Money stays integer cents; timestamps timestamptz.

## Commands

```bash
uv sync                          # deps
uv run alembic upgrade head      # migrate (phalo schema)
uv run uvicorn phalo.app:app --port 8000 --reload
uv run pytest                    # tests
uv run ruff check src tests      # lint
```

Local `.env` points at the same Postgres as nuwa (`ayana` DB). nuwa dev server
usually occupies :3000; athena :3001; run phalo on :8000.

## Session protocol

`CHANGELOG.md` does not exist yet — session state for the YIIVA project lives
in `../nuwa/STATUS.md` (cross-repo handoffs reference phalo from there). Keep
this file updated when conventions or architecture change.
