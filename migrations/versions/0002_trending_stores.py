"""trending_stores ranking table (Phase 2)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-12
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # "window" is a reserved word in PostgreSQL — quoted here and in every query.
    op.execute(
        """
        CREATE TABLE phalo.trending_stores (
            store_id    text             NOT NULL,
            "window"    text             NOT NULL,
            score       double precision NOT NULL,
            rank        integer          NOT NULL,
            computed_at timestamptz      NOT NULL DEFAULT now(),
            PRIMARY KEY (store_id, "window")
        )
        """
    )
    op.execute(
        'CREATE INDEX trending_stores_window_rank_idx ON phalo.trending_stores ("window", rank)'
    )


def downgrade() -> None:
    op.execute("DROP TABLE phalo.trending_stores")
