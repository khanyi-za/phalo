"""APScheduler wiring — one in-process AsyncIOScheduler started from the
FastAPI lifespan. Single Railway service runs both the API and the jobs;
nothing here is load-bearing for user traffic (PH-4: Phalo down = stale
rankings, never an outage)."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from phalo.jobs.registry import all_jobs, run_job

logger = logging.getLogger("phalo.scheduler")


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    for job in all_jobs():
        if job.every_minutes is None:
            continue
        scheduler.add_job(
            run_job,
            "interval",
            minutes=job.every_minutes,
            args=[job.name],
            id=job.name,
            max_instances=1,
            coalesce=True,
        )
        logger.info("scheduled job %s every %s min", job.name, job.every_minutes)
    return scheduler
