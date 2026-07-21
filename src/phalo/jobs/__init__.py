"""Job modules. Importing this package registers every job — keep each job's
module imported here so the registry (and therefore the scheduler + the
manual-trigger endpoint) sees it."""

from phalo.jobs import heartbeat, trending_stores  # noqa: F401
