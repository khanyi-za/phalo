"""Alembic environment — synchronous engine (psycopg) against the shared
Postgres. Phalo migrations manage ONLY the `phalo` schema; nuwa's Prisma owns
public.* and must never be touched from here."""

from alembic import context
from sqlalchemy import create_engine, text

from phalo.config import get_settings


def run_migrations_online() -> None:
    engine = create_engine(get_settings().sync_database_url)

    with engine.connect() as connection:
        # The schema must exist before the version table can live in it.
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS phalo"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=None,
            version_table_schema="phalo",
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
