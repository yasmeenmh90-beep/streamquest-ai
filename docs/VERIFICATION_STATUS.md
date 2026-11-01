# Verification status — 1 November 2026

## User-provided local automated result

In the user's normal Mac terminal:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Reported result: **Ran 27 tests in 13.330s — OK, no skips**. This includes
all six previously blocked HTTP tests and both headless Chrome overlay layout
tests. Layout coverage includes 1000 × 550 and 1920 × 1080, long scenes, result
cards, and reduced motion. These are automated Chrome checks, not manual OBS
observations. The coding environment did not independently reproduce this run.

The earlier restricted coding-environment run had 19 passes, six socket-bind
setup errors, and a skipped layout class. The user's Mac result resolves those
local execution blockers. A separate Node UI suite passed in the coding
environment, including the saved 7000 ms expiry boundary and early approval.
That Node run is separate from the 27 Python tests.

## User-reported manual results

OBS at **1000 × 550**, revision **20261101-obs2**:

- Real Twitch totals match the dashboard.
- The Choice Consequences Reveal card appears.
- After the reveal, the old chapter stays visible with “awaiting host approval.”
- Approve advances OBS to Chapter 3.
- All three choices and the revision label are visible.

Earlier manual testing confirmed B=1, oxygen −8, energy −5, chaos +15,
Signal decoded on the dashboard, and Chapter 2 appearing in OBS after approval.

## Remaining evidence gaps

Manual OBS at 1920 × 1080; measured seven-second visible duration; approval
during reveal; reload during/after reveal; tie/zero-vote presentation; reduced
motion; reconnect; long generated-scene fit; full five-chapter OBS run; runtime
AI provider; public broadcast/demo video and genuine Codex session/build evidence.
Do not infer these from automated tests or the confirmed 1000 × 550 observations.

See README.md for setup and submission readiness. No running server or saved
adventure was modified by the review; no repository was pushed.
