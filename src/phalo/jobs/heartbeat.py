"""Heartbeat — the Phase 1 loop-prover. Reads one cheap fact from nuwa's
domain tables (read access works) and reports it (write access works via the
job_runs row the registry maintains). Replaced as the canary once real
ranking jobs land in Phase 2."""

from sqlalchemy import text

from phalo.db import connection
from phalo.jobs.registry import register


@register("heartbeat", every_minutes=60)
async def heartbeat() -> dict[str, object]:
    async with connection() as conn:
        events = await conn.execute(text('SELECT count(*) FROM public.analytics_events'))
        stores = await conn.execute(
            text("SELECT count(*) FROM public.stores WHERE status = 'ACTIVE'")
        )
    return {
        "analytics_events": events.scalar_one(),
        "active_stores": stores.scalar_one(),
    }
