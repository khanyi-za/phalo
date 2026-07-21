"""Internal-API surface: token gate + route shape (no DB required)."""

import os

os.environ.setdefault("PHALO_DATABASE_URL", "postgresql://x:x@localhost:5432/x")
os.environ.setdefault("PHALO_SERVICE_TOKEN", "test-token")

from fastapi.testclient import TestClient  # noqa: E402

from phalo.app import app  # noqa: E402


def client() -> TestClient:
    # Lifespan not started: scheduler/db stay untouched for these tests.
    return TestClient(app, raise_server_exceptions=False)


def test_jobs_requires_token() -> None:
    res = client().get("/jobs")
    assert res.status_code == 401


def test_jobs_lists_with_token() -> None:
    res = client().get("/jobs", headers={"X-Phalo-Token": "test-token"})
    assert res.status_code == 200
    names = [j["name"] for j in res.json()["jobs"]]
    assert "heartbeat" in names


def test_unknown_job_404s() -> None:
    res = client().post("/jobs/nope/run", headers={"X-Phalo-Token": "test-token"})
    assert res.status_code == 404
