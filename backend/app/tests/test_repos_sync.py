import asyncio
import uuid
from types import SimpleNamespace

from app.schemas.repos import RepoSyncRequest
from app.services.repos_sync import sync_repository


class _FakeResult:
    def scalar_one(self) -> bool:
        return False


class _FakeSession:
    def __init__(self) -> None:
        self.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        self.rollback_called = False

    def get_bind(self):
        return self.bind

    def execute(self, statement, params):
        assert "pg_try_advisory_xact_lock" in str(statement)
        assert "lock_key" in params
        return _FakeResult()

    def rollback(self) -> None:
        self.rollback_called = True


def test_sync_repository_skips_duplicate_sync_without_waiting_for_database_rows() -> None:
    db = _FakeSession()
    repo = SimpleNamespace(
        id=uuid.uuid4(),
        provider="github",
        github_token_encrypted=None,
        api_base_url=None,
    )

    payload = RepoSyncRequest(sync_issues=False, sync_pull_requests=False, sync_workflow_runs=False)
    result = asyncio.run(sync_repository(db, repo, payload))

    assert result.status == "already_running"
    assert result.synced == {"issues": 0, "pull_requests": 0, "workflow_runs": 0}
    assert db.rollback_called is True
