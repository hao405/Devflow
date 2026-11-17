import asyncio
import subprocess
import uuid
from pathlib import Path
from types import SimpleNamespace

from app.core.config import settings
from app.services import code_analysis


def test_sync_checkout_uses_cached_checkout_when_update_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "repo_checkout_dir", str(tmp_path))
    repo = SimpleNamespace(
        id=uuid.uuid4(),
        full_name="owner/repo",
        clone_url="https://github.com/owner/repo.git",
        default_branch="main",
    )
    checkout = code_analysis._repo_checkout_path(repo)
    (checkout / ".git").mkdir(parents=True)

    def fail_run(args, cwd=None):
        raise subprocess.CalledProcessError(128, ["git", *args], stderr="network failed")

    monkeypatch.setattr(code_analysis, "_run_git", fail_run)

    assert code_analysis._sync_checkout(repo, None) == checkout


def test_sync_checkout_uses_configured_local_repo_without_updating(tmp_path, monkeypatch) -> None:
    local_repo = tmp_path / "local-repo"
    local_repo.mkdir()
    repo = SimpleNamespace(
        id=uuid.uuid4(),
        full_name="owner/repo",
        clone_url="https://github.com/owner/repo.git",
        default_branch="main",
        local_path=str(local_repo),
        checkout_mode="local",
    )

    monkeypatch.setattr(code_analysis, "_is_git_work_tree", lambda path: path == local_repo.resolve())

    def fail_run(args, cwd=None):
        raise AssertionError("local repository indexing should not fetch, checkout, or pull")

    monkeypatch.setattr(code_analysis, "_run_git", fail_run)

    assert code_analysis._sync_checkout(repo, None) == local_repo.resolve()


def test_sync_checkout_moves_managed_repo_outside_persistent_root_into_volume(tmp_path, monkeypatch) -> None:
    checkout_root = tmp_path / "persistent-repos"
    external_checkout = tmp_path / "host-mount" / "onyx"
    external_checkout.mkdir(parents=True)
    (external_checkout / ".git").mkdir()
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "repo_checkout_dir", str(checkout_root))
    repo = SimpleNamespace(
        id=uuid.uuid4(),
        full_name="owner/repo",
        clone_url="https://github.com/owner/repo.git",
        default_branch="main",
        local_path=str(external_checkout),
        checkout_mode="managed",
    )
    persistent_checkout = code_analysis._repo_checkout_path(repo)
    persistent_checkout.mkdir(parents=True)
    (persistent_checkout / ".git").mkdir()
    updated_checkouts: list[str] = []

    monkeypatch.setattr(code_analysis.shutil, "which", lambda name: "git")
    monkeypatch.setattr(code_analysis, "_is_git_work_tree", lambda path: (path / ".git").exists())
    monkeypatch.setattr(
        code_analysis,
        "_run_git",
        lambda args, cwd=None: updated_checkouts.append(str(Path(cwd).resolve())) if cwd else None,
    )

    assert code_analysis._sync_checkout(repo, None) == persistent_checkout
    assert repo.local_path == str(persistent_checkout)
    assert updated_checkouts
    assert set(updated_checkouts) == {str(persistent_checkout)}


def test_repository_checkout_uses_configured_github_token_when_repo_token_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(settings, "github_token", "environment-token")
    repo = SimpleNamespace(github_token_encrypted=None)

    assert code_analysis._repository_token(repo) == "environment-token"


def test_sync_code_analysis_skips_when_another_index_is_running(monkeypatch) -> None:
    repo = SimpleNamespace(
        id=uuid.uuid4(),
        full_name="owner/repo",
        clone_url="https://github.com/owner/repo.git",
        owner="owner",
        name="repo",
        default_branch="main",
        local_path=None,
        checkout_mode="managed",
        github_token_encrypted=None,
    )
    monkeypatch.setattr(code_analysis, "_try_code_analysis_lock", lambda db, repo_id: False, raising=False)
    monkeypatch.setattr(settings, "github_token", None)

    def fail_checkout(*args, **kwargs):
        raise AssertionError("a duplicate code-index task must exit before touching the checkout")

    monkeypatch.setattr(code_analysis, "_sync_checkout", fail_checkout)

    assert asyncio.run(code_analysis.sync_repository_code_analysis(object(), repo)) == 0


def test_sync_checkout_rejects_non_empty_configured_download_target(tmp_path, monkeypatch) -> None:
    target = tmp_path / "repo"
    target.mkdir()
    (target / "README.md").write_text("# occupied\n", encoding="utf-8")
    repo = SimpleNamespace(
        id=uuid.uuid4(),
        full_name="owner/repo",
        clone_url="https://github.com/owner/repo.git",
        default_branch="main",
        local_path=str(target),
        checkout_mode="managed",
    )

    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(code_analysis.shutil, "which", lambda name: "git")
    monkeypatch.setattr(code_analysis, "_is_git_work_tree", lambda path: False)

    try:
        code_analysis._sync_checkout(repo, None)
    except RuntimeError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("expected configured non-empty download target to be rejected")
