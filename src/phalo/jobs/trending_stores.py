"""trending_stores — the first real ranking (foundation §5, PH-6 vocabulary).

Score per ACTIVE store over a trailing 7-day window:

    score = Σ exp(-age_days · λ) over views        (product_view + merchant_view,
                                                    λ = ln2/3.5 ⇒ ~3.5-day half-life)
          + 5  × follows gained in the window
          + 10 × paid orders placed in the window

Full refresh per window inside one transaction (idempotent); nuwa reads rows
fresher than 24h and otherwise falls back to its followerCount heuristic.
"""

from sqlalchemy import text

from phalo.db import connection
from phalo.jobs.registry import register

WINDOW = "7d"
DECAY_PER_DAY = 0.198  # ln(2) / 3.5

SCORE_SQL = text(
    """
    WITH view_events AS (
        SELECT
            COALESCE(e."storeId", p."storeId") AS store_id,
            EXP(-EXTRACT(EPOCH FROM (now() - e."createdAt")) / 86400.0 * :decay) AS w
        FROM public.analytics_events e
        LEFT JOIN public.products p ON p.id = e."productId"
        WHERE e."eventType" IN ('merchant_view', 'product_view')
          AND e."createdAt" > now() - interval '7 days'
    ),
    views AS (
        SELECT store_id, SUM(w) AS views_score
        FROM view_events
        WHERE store_id IS NOT NULL
        GROUP BY store_id
    ),
    follows AS (
        SELECT "storeId" AS store_id, COUNT(*)::float AS follow_count
        FROM public.store_followers
        WHERE "createdAt" > now() - interval '7 days'
        GROUP BY "storeId"
    ),
    paid_orders AS (
        SELECT "storeId" AS store_id, COUNT(*)::float AS order_count
        FROM public.orders
        WHERE "placedAt" > now() - interval '7 days'
          AND status NOT IN ('PENDING', 'CANCELLED')
        GROUP BY "storeId"
    )
    SELECT
        st.id AS store_id,
        COALESCE(v.views_score, 0)
          + 5  * COALESCE(f.follow_count, 0)
          + 10 * COALESCE(o.order_count, 0) AS score
    FROM public.stores st
    LEFT JOIN views v        ON v.store_id = st.id
    LEFT JOIN follows f      ON f.store_id = st.id
    LEFT JOIN paid_orders o  ON o.store_id = st.id
    WHERE st.status = 'ACTIVE'
    ORDER BY score DESC, st.id DESC
    """
)


@register("trending_stores", every_minutes=60)
async def trending_stores() -> dict[str, object]:
    async with connection() as conn:
        rows = (await conn.execute(SCORE_SQL, {"decay": DECAY_PER_DAY})).all()

        await conn.execute(
            text('DELETE FROM phalo.trending_stores WHERE "window" = :window'),
            {"window": WINDOW},
        )
        for rank, row in enumerate(rows, start=1):
            await conn.execute(
                text(
                    "INSERT INTO phalo.trending_stores "
                    '(store_id, "window", score, rank, computed_at) '
                    "VALUES (:store_id, :window, :score, :rank, now())"
                ),
                {
                    "store_id": row.store_id,
                    "window": WINDOW,
                    "score": float(row.score),
                    "rank": rank,
                },
            )

    return {"window": WINDOW, "stores_ranked": len(rows)}
