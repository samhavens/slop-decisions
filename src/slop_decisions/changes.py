"""Select current Elixir files changed since a Git merge base."""

import subprocess
from pathlib import Path


def git(root: Path, *args: str, error: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise ValueError("Git is required for --changed; install Git first") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Git timed out while selecting changed files") from exc
    if result.returncode:
        raise ValueError(error)
    return result.stdout.decode("utf-8")


def changed_files(root: Path, ref: str) -> dict:
    root = root.resolve()
    top = git(root, "rev-parse", "--show-toplevel", error="--changed requires a Git repository")
    if Path(top.strip()).resolve() != root:
        raise ValueError("set --root to the Git repository root for --changed")
    commit = git(
        root,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{ref}^{{commit}}",
        error="--changed needs a valid commit; fetch the base ref and check its name",
    ).strip()
    base = git(
        root,
        "merge-base",
        "HEAD",
        commit,
        error="no shared commit; fetch full history and make an initial commit before --changed",
    ).strip()
    conflicts = git(
        root,
        "diff",
        "--name-only",
        "--diff-filter=U",
        "-z",
        "--",
        error="could not inspect Git conflicts",
    )
    if conflicts:
        raise ValueError("resolve Git merge conflicts before running --changed")
    tracked = git(
        root,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--no-renames",
        "--name-only",
        "-z",
        base,
        "--",
        error="could not compare files with the base commit",
    )
    untracked = git(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        error="could not list new Git files",
    )
    files, skipped = [], []
    for name in sorted(set(tracked.split("\0") + untracked.split("\0")) - {""}):
        if Path(name).suffix not in {".ex", ".exs"}:
            continue
        path = root / name
        if path.is_symlink():
            raise ValueError(f"changed source is a symlink: {name}")
        if not path.exists():
            skipped.append({"path": name, "reason": "deleted"})
        elif not path.is_file():
            raise ValueError(f"changed source is not a regular file: {name}")
        elif path.stat().st_size == 0:
            skipped.append({"path": name, "reason": "empty"})
        else:
            files.append(name)
    return {"base": base, "files": files, "skipped": skipped}
