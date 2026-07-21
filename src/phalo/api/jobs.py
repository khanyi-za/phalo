"""Manual job triggers (service-token gated). Used for ops/admin re-runs and
by tests; the scheduler drives the routine cadence."""

from fastapi import APIRouter, Depends, HTTPException

from phalo.api.deps import require_service_token
from phalo.jobs.registry import all_jobs, get_job, run_job

router = APIRouter(dependencies=[Depends(require_service_token)])


@router.get("/jobs")
async def list_jobs() -> dict[str, object]:
    return {
        "jobs": [
            {"name": j.name, "everyMinutes": j.every_minutes} for j in all_jobs()
        ]
    }


@router.post("/jobs/{name}/run")
async def trigger_job(name: str) -> dict[str, object]:
    if get_job(name) is None:
        raise HTTPException(status_code=404, detail=f"Unknown job '{name}'")
    return await run_job(name)
