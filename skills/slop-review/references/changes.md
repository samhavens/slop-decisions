# Select a change review

Use the supplied diff or comparison ref. For local changes without a ref, compare
with `HEAD`. For a branch/ref, compare the working tree with its merge base with
`HEAD`. Include branch commits, staged and unstaged edits, and non-ignored
untracked files.

Use `git status --short`, `git diff --no-ext-diff --no-textconv --no-renames`, and
`git ls-files --others --exclude-standard`. Read new files separately and deleted
files at the base. Report missing bases or conflicts; do not substitute a base.

Start with the changed code and tests, then follow their owners, callers,
fixtures and test/CI selection to establish each finding.
