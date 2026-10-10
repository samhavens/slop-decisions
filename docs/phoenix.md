# Phoenix and Ecto checks

The three checks follow behavior across templates, callbacks, and database calls.
Use them in Codex:

```text
$slop-review Check my changes for client_state_round_trip, liveview_reconnect_state_loss, and per_record_database_read.
```

| Check | Report | Allow |
| --- | --- | --- |
| UI round trip | Showing static content waits for a server event that only changes visibility. | Loading authorized content, starting work, or changing meaningful URL state. |
| Reconnect state loss | A remount loses required wizard answers that recovery cannot restore. | Built-in form recovery, a persisted draft, or an intentional reset of disposable state. |
| Per-record reads | Query count grows with the number of rows because each row causes a separate lookup. | A list preload, already-loaded associations, or a fixed set of batched queries. |

For the review steps and framework sources, read the
[Phoenix and Ecto boundaries](../skills/slop-review/references/phoenix.md).
The [authored review cases](../evals/phoenix/README.md) include valid lookalikes
and missing-context examples.

Static checks can catch some candidates first. The
[OeditusCredo extension](https://github.com/Oeditus/oeditus_credo) includes
`NPlusOneQuery` for patterns such as `Enum.map` with repository calls. Trace
helpers and query behavior before treating a candidate as a defect.
