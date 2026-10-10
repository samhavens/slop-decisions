# Public source provenance

The seed manifest points to exact revisions in these projects:

| Project | Cases | Source license |
| --- | --- | --- |
| [Tesla](https://github.com/elixir-tesla/tesla) | Stream failures and mutation-sensitive tests | MIT |
| [Logflare](https://github.com/Logflare/logflare) | Egress telemetry and duplicate setup | [Apache-2.0](https://github.com/Logflare/logflare/blob/740bce56caadd3aed007043ac0558ef5fd24ba7b/LICENSE.md) |
| [Bandit](https://github.com/mtrudel/bandit) | Accumulated body length | MIT |
| [Boundary](https://github.com/sasa1977/boundary) | Export-policy simplification | MIT |
| [ex_slop](https://github.com/elixir-vibe/ex_slop) | Identity-wrapper regression fixtures | MIT |

Third-party source is downloaded into an ignored local cache. It is not included
in the Python package or relicensed under this repository's MIT license. Preserve
upstream license notices if you redistribute the fetched files. The manifest
records repository, full commit SHA, path, and SHA256 for every file.

The case selection and initial rubrics were reconstructed from a research
discussion about semantic Elixir checks. The original attachment was unavailable;
this is an independently reconstructed implementation, not a verbatim import.
Each label links to the public PR and exact source span. Review text, private
conversation content, commit messages, and grading witnesses are excluded from
model input. Test names used as an upstream regression oracle are also removed
from extracted ex_slop fixtures.
