"""Job registry + run bookkeeping.

Every job is an async callable registered under a name. `run_job` wraps the
execution with a `phalo.job_runs` row (the observability primitive — admin
panels read it for "rankings last computed N min ago"). Jobs must be
idempotent: full-refresh writes per window inside one transaction.
"""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy import text

from phalo.db import connection

logger = logging.getLogger("phalo.jobs")

# A job receives nothing and returns a JSON-serialisable stats dict
# (row counts, windows — whatever is useful in job_runs.detail).
JobFn = Callable[[], Awaitable[dict[str, object]]]


@dataclass(frozen=True)
class Job:
    name: str
    fn: JobFn
    # Interval in minutes for the scheduler; None = manual-trigger only.
    every_minutes: int | None


_registry: dict[str, Job] = {}


def register(name: str, every_minutes: int | None = None) -> Callable[[JobFn], JobFn]:
    def decorator(fn: JobFn) -> JobFn:
        if name in _registry:
            raise ValueError(f"Job '{name}' is already registered")
        _registry[name] = Job(name=name, fn=fn, every_minutes=every_minutes)
        return fn

    return decorator


def all_jobs() -> list[Job]:
    return list(_registry.values())


def get_job(name: str) -> Job | None:
    return _registry.get(name)


async def run_job(name: str) -> dict[str, object]:
    """Execute a job with job_runs bookkeeping. Returns the run summary."""
    job = get_job(name)
    if job is None:
        raise KeyError(f"Unknown job '{name}'")

    async with connection() as conn:
        row = await conn.execute(
            text(
                "INSERT INTO phalo.job_runs (job, started_at, status) "
                "VALUES (:job, now(), 'RUNNING') RETURNING id"
            ),
            {"job": name},
        )
        run_id = row.scalar_one()

    started = time.monotonic()
    try:
        detail = await job.fn()
        status = "SUCCESS"
    except Exception as exc:  # noqa: BLE001 — the job boundary is where we catch
        detail = {"error": f"{type(exc).__name__}: {exc}"}
        status = "FAILED"
        logger.exception("job %s failed", name)

    elapsed_ms = int((time.monotonic() - started) * 1000)
    detail = {**detail, "elapsed_ms": elapsed_ms}

    async with connection() as conn:
        await conn.execute(
            text(
                "UPDATE phalo.job_runs "
                "SET finished_at = now(), status = :status, detail = :detail "
                "WHERE id = :id"
            ),
            {"status": status, "detail": json.dumps(detail), "id": run_id},
        )

    return {"job": name, "status": status, "detail": detail}
