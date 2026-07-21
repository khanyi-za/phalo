"""Liveness + the last few job runs (the at-a-glance freshness signal)."""

from fastapi import APIRouter
from sqlalchemy import text

from phalo.db import connection

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, object]:
    async with connection() as conn:
        await conn.execute(text("SELECT 1"))
        rows = await conn.execute(
            text(
                "SELECT job, started_at, finished_at, status "
                "FROM phalo.job_runs ORDER BY started_at DESC LIMIT 5"
            )
        )
        recent = [
            {
                "job": r.job,
                "startedAt": r.started_at.isoformat(),
                "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
                "status": r.status,
            }
            for r in rows
        ]
    return {"status": "ok", "recentJobRuns": recent}
