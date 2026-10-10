# Abstraction boundaries

Use for `false_unification`, `semantic_duplicate`, `policy_free_abstraction`,
and `unnecessary_compile_time_work`.

For shared code, substitute each actual caller's arguments and discard branches
that caller cannot take. Compare the remaining operations. Name the policies,
their owners, and a supported change that should affect only one. A finding needs
a concrete coupling cost: unrelated callers need new flags, shared validations
need exceptions, or a caller must know another operation's rules. Separate those
policies, then share only the common contract. A format option in a serializer
can be coherent; do not treat every parameter as evidence of a wrong abstraction.
This investigation follows [Sandi Metz's specialization technique](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction).

For a proposed extraction or merge, compare what the caller must know before and
after. Include error contracts, call order, state ownership and coordinated edits.
A short facade can hide substantial complexity. Splitting one operation into six
helpers may increase the information needed to change it. Use
[Ousterhout's interface-depth criterion](https://github.com/johnousterhout/aposd-vs-clean-code/blob/main/README.md#method-length),
not a function-length limit. Check history before merging duplicated compatibility
or migration paths.

For macros, inspect one expansion and its call sites. Separate code generation,
compile-time data inspection and ordinary runtime work. Can one ordinary function
hold the repeated implementation, leaving a small macro for required syntax?
Preserve variable hygiene, evaluation count, exceptions and phase behavior.
Use `mix xref trace path/to/caller.ex` in an isolated test copy to investigate
compile, export and runtime dependencies. Expansion and tracing execute code.
An AST-based DSL or genuine compile-time dependency is a valid exception. See
[Elixir's macro guide](https://elixir.hexdocs.pm/macro-anti-patterns.html).
