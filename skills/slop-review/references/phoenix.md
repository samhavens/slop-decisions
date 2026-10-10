# Phoenix and Ecto boundaries

For `client_state_round_trip`, trace the click to its event handler and all uses
of the changed state. A local visibility toggle is a candidate only when no
server behavior needs it. Data loading, authorization, persisted or shared state,
and URL navigation can justify a server event. `JS.push(...) |> JS.hide(...)`
does not wait for the server before hiding. Preserve focus and dismissal behavior
when suggesting a local modal. See [LiveView JS](https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.JS.html).

For `liveview_reconnect_state_loss`, identify a concrete interruption and the
state that must survive it. Trace remount and recovery through the rendered form,
URL, hooks, and storage. A stable form `id` with `phx-change` already enables
automatic recovery; inspect what its handler restores. Wizard answers removed
from the DOM may need another recovery source. Do not require a custom reconnect
hook or assume every brief interruption destroys all state. Propose a browser
disconnect/remount test when the client behavior is uncertain. See
[form recovery](https://hexdocs.pm/phoenix_live_view/form-bindings.html#recovery-following-crashes-or-disconnects).

For `per_record_database_read`, count the reads for one collection, including
reads hidden in helpers or components. Compare two collection sizes when practical.
Distinguish one query per record from one query per association for the whole list.
Check whether associations are already loaded. Preserve tenant filters, ordering,
pagination, and per-parent limits in a proposed batch. A join can multiply result
rows; fewer queries do not prove lower latency. See
[Ecto preload choices](https://hexdocs.pm/ecto/Ecto.Query.html#preload/3).
