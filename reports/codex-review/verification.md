# Codex review verification

Ship a self-contained Codex skill that reviews changed Elixir code with all 14
rules in the current session. Keep provider-based checks and evaluations as
explicit experiments. Do not use model scores as a required merge gate.

Before implementation, add tests that fail without the skill. Verify that the
distributed rule reference matches the canonical rules, that every referenced
file ships, and that the skill can run without the Python package or API keys.

Use an independent reviewer on a small repository with known defects and valid
lookalikes. Give the reviewer the installed skill and source only. Require it to
trace validators before reporting invalid input handling, distinguish weak tests
from broken production code, and cite evidence for actual defects. Check changed
code selection, including uncommitted work. This is a behavioral smoke test, not
a detector accuracy estimate.

Run the existing test suite, lint, formatting, build, and skill validation. Read
all edited files again. Verify the documented installation in Codex and that the
README leads with the review workflow. Keep the pattern table and links to the
local, OpenAI, and OpenRouter experiment setup. No paid checker runs are needed.
