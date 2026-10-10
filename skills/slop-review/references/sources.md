# Why these patterns count as slop

Selection starts with reported residue from agent coding sessions and concrete
cleanup patches. These sources support the choice of patterns; they do not make
every similar test bad or establish which model wrote it.

| Source | Evidence used | Limit |
| --- | --- | --- |
| [OpenClaw #155040](https://github.com/openclaw/openclaw/pull/155040) | The removed `channel.message-adapter.test.ts` substitutes declared flags for live-behavior proof. Production patches remove test-supplied cache parameters and an inspection getter. | Some forwarding assertions can protect a real adapter contract. The PR reports nine preservation gaps repaired during pruning; deletion alone was not success. |
| [OpenClaw #156316](https://github.com/openclaw/openclaw/pull/156316) and its [pinned test-audit skill](https://github.com/openclaw/openclaw/blob/80930af448ebabc84174146b56bc106d37fab3b4/.agents/skills/test-audit/SKILL.md) | The author explicitly connects repetitive tests to agents. Guidance adds circular expectations, mock-produced facts, false negatives and named retained coverage. | The policy-subsystem examples are reported skill-trial observations, not executions reproduced here. We borrow the distinctions, not the campaign workflow. |
| [async_wallpaper #65](https://github.com/codenameakshay/async_wallpaper/pull/65) | `test/models_test.dart` removes constructor read-backs and copied enum inventories while retaining default, copy and outcome behavior. Production cleanup removes test-only helpers. | Claude Code assisted the cleanup; this does not establish authorship of every removed test. |
| [klass-hero #1611](https://github.com/MaxPayne89/klass-hero/pull/1611) | `program_provider_resolver.ex` removes a blanket rescue returning `:program_not_found` after unexpected exceptions. | The patch supports failure masking. Its title does not establish model authorship. |
| [BoothIQ's Elixir account](https://getboothiq.com/blog/150k-lines-vibe-coded-elixir-good-bad-ugly) | Firsthand reports of excess defensive guards, repeated implementations and misdirected test-environment repairs. | No corresponding patches are supplied. Our examples are adaptations, not mined production fixtures. |
| [Saša Jurić's Elixir review](https://www.linkedin.com/posts/sasajuric_i-recently-reviewed-some-ai-assisted-code-activity-7435287708752658432-JwE0) | Firsthand reports of overlapping, private-implementation and never-executed tests in AI-assisted code. | No public patch is provided in the post. |
| Claude Code [#7074](https://github.com/anthropics/claude-code/issues/7074) and [#32376](https://github.com/anthropics/claude-code/issues/32376) | Users report weakened assertions and a narrowed verification gate; the latter includes a diff excerpt. | These are user reports, not a controlled model evaluation. |

The Elixir examples in this skill and its evals are authored adaptations unless
explicitly marked otherwise. They test the distinctions, not the original
projects. None of these reports establishes how often a current model produces
slop. Human-written code can have the same problems.
