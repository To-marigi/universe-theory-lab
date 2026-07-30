"""v0.3.9 regression: frozen-branch resolution must work in a fresh clone.

`git clone` and `actions/checkout` create a local head only for the ref they
check out.  Before v0.3.9 the v0.3 baseline audit resolved the frozen branch
with a bare `git rev-parse`, which git does not fall back to a remote-tracking
ref for, so the audit passed only where that head had been created by hand.
CI run 30544994303 failed two tests for exactly this reason.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from universe_lab.final_theory.audit_v031 import (
    V03_ARTIFACT_FREEZE,
    V03_BRANCH,
    baseline_audit_v0_3_1,
    resolve_frozen_branch,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLONE_ONLY_BRANCH = "codex/frozen-branch-present-only-as-remote-tracking"


def _git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def clone_like_repository(tmp_path: Path) -> tuple[Path, str]:
    """A repository whose branch exists only as `refs/remotes/origin/<name>`.

    This is the ref layout every clone has for every branch it did not check
    out.  It is built directly instead of by cloning so the test stays fast and
    independent of network access.
    """

    root = tmp_path / "clone_like"
    root.mkdir()
    assert _git(root, "init", "--quiet").returncode == 0
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Regression Test")
    (root / "artifact.txt").write_text("frozen\n", encoding="utf-8", newline="\n")
    assert _git(root, "add", "artifact.txt").returncode == 0
    assert _git(root, "commit", "--quiet", "-m", "frozen commit").returncode == 0

    commit = _git(root, "rev-parse", "HEAD").stdout.strip()
    assert commit
    created = _git(
        root,
        "update-ref",
        f"refs/remotes/origin/{CLONE_ONLY_BRANCH}",
        commit,
    )
    assert created.returncode == 0
    return root, commit


def test_bare_rev_parse_cannot_see_a_remote_only_branch(
    clone_like_repository: tuple[Path, str],
) -> None:
    """Pin the git behaviour the regression depends on."""

    root, _ = clone_like_repository
    local = _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{CLONE_ONLY_BRANCH}")
    remote = _git(
        root,
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/remotes/origin/{CLONE_ONLY_BRANCH}",
    )
    bare = _git(root, "rev-parse", "--verify", "--quiet", CLONE_ONLY_BRANCH)
    assert local.returncode != 0
    assert remote.returncode == 0
    assert bare.returncode != 0


def test_resolver_finds_a_remote_only_branch(
    clone_like_repository: tuple[Path, str],
) -> None:
    """The v0.3.9 resolver succeeds where a bare rev-parse fails."""

    root, commit = clone_like_repository
    resolved = resolve_frozen_branch(root, CLONE_ONLY_BRANCH)
    assert resolved.returncode == 0
    assert resolved.stdout.strip() == commit


def test_resolver_reports_failure_for_an_absent_branch(tmp_path: Path) -> None:
    """A genuinely missing branch must still fail rather than resolve to junk."""

    root = tmp_path / "empty"
    root.mkdir()
    assert _git(root, "init", "--quiet").returncode == 0
    resolved = resolve_frozen_branch(root, "codex/branch-that-does-not-exist")
    assert resolved.returncode != 0
    assert resolved.stdout.strip() == ""


def test_local_head_still_takes_precedence(
    clone_like_repository: tuple[Path, str],
) -> None:
    """A checked-out working copy keeps its existing behaviour."""

    root, commit = clone_like_repository
    assert _git(root, "branch", CLONE_ONLY_BRANCH, commit).returncode == 0
    resolved = resolve_frozen_branch(root, CLONE_ONLY_BRANCH)
    assert resolved.returncode == 0
    assert resolved.stdout.strip() == commit


def test_repository_frozen_branch_still_resolves_to_the_freeze_commit() -> None:
    """The recorded audit value is unchanged by the new resolution path."""

    resolved = resolve_frozen_branch(REPOSITORY_ROOT, V03_BRANCH)
    assert resolved.returncode == 0
    assert resolved.stdout.strip() == V03_ARTIFACT_FREEZE

    audit = baseline_audit_v0_3_1(REPOSITORY_ROOT)
    assert audit["frozen_branch_target"] == V03_ARTIFACT_FREEZE
    assert audit["frozen_branch_targets_freeze"] is True
