"""Registry semantics that don't need a database."""

import pytest

from phalo.jobs.registry import Job, all_jobs, get_job, register


def test_heartbeat_is_registered() -> None:
    import phalo.jobs  # noqa: F401 — side-effect import registers jobs

    job = get_job("heartbeat")
    assert isinstance(job, Job)
    assert job.every_minutes == 60


def test_duplicate_registration_rejected() -> None:
    import phalo.jobs  # noqa: F401

    with pytest.raises(ValueError):
        register("heartbeat")(lambda: None)  # type: ignore[arg-type]


def test_all_jobs_lists_registered() -> None:
    import phalo.jobs  # noqa: F401

    names = [j.name for j in all_jobs()]
    assert "heartbeat" in names
