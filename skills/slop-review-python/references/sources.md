# Sources and evidence limits

Adapt the focused skill from
[`samhavens/slop-decisions` at `37ef42f`](https://github.com/samhavens/slop-decisions/tree/37ef42f9447a4356a907fe3ea3f5847532db1042/skills/slop-review).
Keep its 13 rule names, predicates, severities, and source links. The
[upstream provenance table](https://github.com/samhavens/slop-decisions/blob/37ef42f9447a4356a907fe3ea3f5847532db1042/skills/slop-review/references/sources.md)
distinguishes cleanup patches, firsthand reports, and their limitations.

The original sources include OpenClaw test audits and preservation work,
async_wallpaper constructor-test cleanup, an Elixir failure-masking patch, and
reports of defensive scaffolding and weakened verification. They motivate the
patterns. They do not establish the authorship of any reviewed code or the
frequency with which a current model produces it.

The Python examples in this skill are authored adaptations, not newly mined
Python production incidents. The repository's Python cases are synthetic
development examples. Neither those examples nor the upstream Elixir evaluations
establish Python detection precision or recall. Report only the checks actually
performed; do not transfer upstream scores to this port.

## Python runtime and framework contracts

Use the version installed in the reviewed project. These primary references
explain the distinctions used in this port:

| Reference | Contract to inspect |
| --- | --- |
| [Python typing](https://docs.python.org/3.11/library/typing.html) | Function and variable annotations do not themselves enforce runtime validity. |
| [unittest.mock and AsyncMock](https://docs.python.org/3.11/library/unittest.mock.html) | Patch lookup, mock return values, and separate call/await evidence. |
| [Dataclasses](https://docs.python.org/3.11/library/dataclasses.html) | Generated initialization, post-initialization hooks, and default factories. |
| [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) | Autouse setup, fixture scope, teardown, and dependencies. |
| [pytest skip and xfail](https://docs.pytest.org/en/stable/how-to/skipping.html) | Collection, execution, expected failure, and strictness. |
| [SQLAlchemy session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) | Identity maps, flush, transaction ownership, and commit. |
| [Django transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) | Transaction boundaries and commit callbacks in Django projects. |

Keep framework-specific claims conditional on the framework being present and
its supported version. Do not treat these links as a requirement to install a
framework or make external calls during each review.
