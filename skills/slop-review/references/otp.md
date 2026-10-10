# Process and configuration boundaries

For `scattered_process_interface`, find the owner and all external reads, updates
and message constructors. Try one private layout change. Which modules must change
together? Move knowledge of that layout behind named operations in the owner.
Do not flag a documented public protocol or an intentional general-purpose state
primitive. A process may be justified while its interface is still scattered.

For `oversized_process_capture`, follow free variables into spawned functions and
message payloads. Identify which fields the receiver uses. Extracting a small
value before spawning can avoid retaining the original structure. Establish size
or lifetime before claiming a useful reduction. Do not estimate bytes copied from
source alone: BEAM sharing, reference-counted binaries and retained sub-binaries
matter. Full-payload consumers are valid.
See [Elixir process anti-patterns](https://elixir.hexdocs.pm/process-anti-patterns.html)
and [Erlang process costs](https://www.erlang.org/doc/system/eff_guide_processes.html).

For `global_configuration_coupling`, write a two-consumer sequence: configure A,
configure B, call A, call B. Trace the actual reads. If constructing B changes A's
endpoint or behavior, name the supported independence that was lost. Settings
passed into each process or function preserve separate instances. Intentional
application-wide policy and globally selected equivalent adapters can be valid.
Async tests that write the same application setting also need isolation. See
[Elixir library configuration](https://elixir.hexdocs.pm/design-anti-patterns.html#using-application-configuration-for-libraries).
