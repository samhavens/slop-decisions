# Decisions integration checks

Verify the request contract before interpreting model scores.

1. Compare a live request with the official Decisions example. Save the request body, raw answer, request ID, model, token usage, and parsed result. Keep credentials out of logs.
2. Run positive and negative controls through direct HTTP, the official SDK, and the checker. Check answer-name mapping with different scores and reversed answer order.
3. On fixed source packets, vary one factor at a time: one versus two questions, prompt length, and full-file versus marked-function scope. Include both defective and repaired code. Keep expected labels out of requests.
4. If a defect is found, add a failing regression test before changing the implementation. Run the full test suite, lint, package build, and a live control after the fix.
5. Select twenty additional application/test files before reading their model results. Check all fourteen rules. Keep private code and results outside this repository. Review warnings against source and distinguish proved defects, test weaknesses, and unsupported warnings.

Keep the existing thresholds fixed. This audit does not calibrate them. Limit the expanded pass to 560 requests and the diagnostic pass to 80 requests; no automatic retries. Stop on repeated transport errors. Estimated API spend is below $2 at standard pricing. Run small protocol controls before the expanded pass.
