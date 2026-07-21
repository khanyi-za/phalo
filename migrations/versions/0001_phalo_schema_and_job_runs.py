"""phalo schema + job_runs (Phase 1 foundation)

Revision ID: 0001
Revises:
Create Date: 2026-06-12
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema creation is idempotent here AND in env.py (env.py needs it for
    # the version table before any migration runs).
    op.execute("CREATE SCHEMA IF NOT EXISTS phalo")
    op.execute(
        """
        CREATE TABLE phalo.job_runs (
            id          bigserial PRIMARY KEY,
            job         text        NOT NULL,
            started_at  timestamptz NOT NULL DEFAULT now(),
            finished_at timestamptz,
            status      text        NOT NULL DEFAULT 'RUNNING',
            detail      jsonb
        )
        """
    )
    op.execute("CREATE INDEX job_runs_job_started_idx ON phalo.job_runs (job, started_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE phalo.job_runs")
