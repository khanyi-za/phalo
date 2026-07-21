"""FastAPI app factory. One process serves the internal API and runs the
APScheduler job loop (started/stopped via lifespan)."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

import phalo.jobs  # noqa: F401 — importing registers every job
from phalo.api.health import router as health_router
from phalo.api.jobs import router as jobs_router
from phalo.db import dispose_engine
from phalo.jobs.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = build_scheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await dispose_engine()


app = FastAPI(
    title="Phalo",
    description="YIIVA smart engine — internal API. Not browser-facing.",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(jobs_router)
