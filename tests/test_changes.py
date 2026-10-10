import subprocess

import pytest

from slop_decisions.changes import changed_files


def git(root, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=check, capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.com")
    for name in ("staged.ex", "unstaged.ex", "deleted.ex", "renamed.ex", "empty.ex", "same.ex"):
        (tmp_path / name).write_text("def old, do: :ok\n")
    (tmp_path / ".gitignore").write_text("ignored.ex\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def test_changed_files_include_worktree_index_untracked_and_renames(repo):
    (repo / "staged.ex").write_text("def staged, do: :ok\n")
    git(repo, "add", "staged.ex")
    (repo / "unstaged.ex").write_text("def unstaged, do: :ok\n")
    (repo / "deleted.ex").unlink()
    git(repo, "mv", "renamed.ex", "new name.ex")
    (repo / "new\nline.exs").write_text("assert true\n")
    (repo / "ignored.ex").write_text("ignored\n")
    (repo / "README.md").write_text("not Elixir\n")
    (repo / "empty.ex").write_text("")
    result = changed_files(repo, "HEAD")
    assert result["files"] == ["new\nline.exs", "new name.ex", "staged.ex", "unstaged.ex"]
    assert result["skipped"] == [
        {"path": "deleted.ex", "reason": "deleted"},
        {"path": "empty.ex", "reason": "empty"},
        {"path": "renamed.ex", "reason": "deleted"},
    ]
    assert result["base"] == git(repo, "rev-parse", "HEAD").stdout.strip()


def test_base_uses_merge_base_and_includes_committed_branch_changes(repo):
    ancestor = git(repo, "rev-parse", "HEAD").stdout.strip()
    git(repo, "switch", "-qc", "feature")
    (repo / "feature.ex").write_text("def feature, do: :ok\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "feature")
    git(repo, "switch", "-q", "main")
    (repo / "upstream.ex").write_text("def upstream, do: :ok\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "upstream")
    git(repo, "switch", "-q", "feature")
    result = changed_files(repo, "main")
    assert result == {"base": ancestor, "files": ["feature.ex"], "skipped": []}


@pytest.mark.parametrize("ref", ["missing-ref", "--help", "", "HEAD:staged.ex"])
def test_invalid_refs_fail_with_useful_error(repo, ref):
    with pytest.raises(ValueError, match="commit"):
        changed_files(repo, ref)


def test_rejects_conflicts_instead_of_grading_conflict_markers(repo):
    git(repo, "switch", "-qc", "other")
    (repo / "same.ex").write_text("def other, do: :ok\n")
    git(repo, "commit", "-qam", "other")
    git(repo, "switch", "-q", "main")
    (repo / "same.ex").write_text("def main, do: :ok\n")
    git(repo, "commit", "-qam", "main")
    assert git(repo, "merge", "other", check=False).returncode == 1
    with pytest.raises(ValueError, match="conflict"):
        changed_files(repo, "HEAD")


def test_symlinks_cannot_send_source_from_outside_the_repo(repo, tmp_path_factory):
    external = tmp_path_factory.mktemp("external") / "secret.ex"
    external.write_text("private\n")
    (repo / "link.ex").symlink_to(external)
    with pytest.raises(ValueError, match="symlink"):
        changed_files(repo, "HEAD")


def test_requires_git_root_and_at_least_one_commit(tmp_path):
    with pytest.raises(ValueError, match="Git"):
        changed_files(tmp_path, "HEAD")
    git(tmp_path, "init", "-q")
    with pytest.raises(ValueError, match="commit"):
        changed_files(tmp_path, "HEAD")


def test_subdirectory_cannot_silently_drop_other_changes(repo):
    (repo / "lib").mkdir()
    with pytest.raises(ValueError, match="root"):
        changed_files(repo / "lib", "HEAD")


def test_git_filenames_preserve_carriage_returns(repo):
    name = "line\r\nbreak.ex"
    (repo / name).write_text("def run, do: :ok\n")
    assert changed_files(repo, "HEAD")["files"] == [name]
