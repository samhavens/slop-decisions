# Select a change review

Use the supplied diff or comparison ref. For local changes without a ref, compare
the working tree with `HEAD`. When a base ref is supplied, compare the working
tree with `git merge-base HEAD <base-ref>`. Include branch commits, staged and
unstaged edits, and non-ignored untracked files. Do not silently choose a different
base when a ref is unavailable or the working tree has unresolved conflicts.

Use `git status --short`, `git diff --no-ext-diff --no-textconv --no-renames`, and
`git ls-files --others --exclude-standard`. Pass the selected base to `git diff`;
a bare `git diff` omits staged changes. Read new files separately and deleted
files at the base. In a repository without a usable `HEAD`, report the limitation
and review the available files under the user's requested scope.

Start with changed source and tests, then follow callers, fixtures, owners, and
test/CI selection to establish each finding. Inspect lock/configuration changes
when they can alter collection, validation, or which checks run. A changed line
alone does not authorize a wider cleanup.
