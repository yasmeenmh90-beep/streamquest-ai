# Development history (archived)

This file preserves the README before its presentation refresh on 2 November 2026. Statements such as “no Git metadata” describe earlier development environments, not the current published repository. Follow the root README for current setup and revision guidance.

# StreamQuest AI
A host-controlled, five-round Twitch space adventure built with Codex. Real viewers vote with !a, !b and !c; decisions alter resources and community alignment. A separate read-only OBS overlay shows approved scenes.

## Two modes
- **Hosted browser demo:** playable prepared story; simulated votes; browser-local persistence and same-origin tab synchronization. No Twitch or runtime AI connection is claimed.
- **Local Python app:** backend-authoritative voting, SQLite persistence, host authentication, Twitch broadcaster OAuth and EventSub chat, optional AI-generated scenes, read-only overlay synchronized via polling. Requires your credentials. Real Twitch voting and the OBS approval flow at 1000 × 550 have user-reported manual verification; runtime AI remains unverified.

## Run locally (macOS / Linux)
Python 3.10+ and a Twitch account are needed for live chat.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export HOST_KEY='choose-your-own-long-password-at-least-16-characters'
export APP_BASE_URL='http://localhost:8080'
python3 -m backend.server
```
Open http://localhost:8080 and enter your HOST_KEY. Do not use 127.0.0.1 in the browser unless you also change APP_BASE_URL and the OAuth callback to match. The server binds loopback by default. No Node build is required.

For a reusable local configuration, copy `.env.example` to `.env`, edit the
placeholders privately, and export it before starting the server:

```bash
cp .env.example .env  # first setup only; do not overwrite an existing .env
# Edit .env locally; use a unique random HOST_KEY.
set -a
source .env
set +a
python -m backend.server
```

The server does not load `.env` automatically. Use shell-compatible values (quote
values containing spaces or shell punctuation). `.env.example` contains no real
credentials. `aiohttp` is the sole external Python dependency; SQLite is included
with Python. Node.js is needed only for the optional JS regression check; Google
Chrome/Chromium is needed for automated layout tests. No npm install or frontend
build is required.

## Connect Twitch
1. Register an application at https://dev.twitch.tv/console/apps. Register the exact redirect http://localhost:8080/auth/callback.
2. Stop the server and export TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in your terminal; never put them in frontend code.
3. Optionally set TWITCH_REDIRECT_URI if using a different permitted callback. Restart, log in, go to Connections and click Connect Twitch.
4. Authorize the broadcaster account whose chat you will use. This installed-bot configuration requests user:read:chat only, using the same broadcaster/user ID for EventSub.
5. Wait for Connected status, launch a story and open voting. Send !a / !b / !c in that channel from viewer accounts. Test this on an actual Twitch stream before recording the hackathon demo.
6. If Twitch authorization expires, refresh is attempted. Otherwise reconnect. Unexpected disconnection pauses voting; resume explicitly when chat is healthy. Events missed while disconnected cannot be recovered.

Official references: https://dev.twitch.tv/docs/chat/authenticating/ and https://dev.twitch.tv/docs/eventsub/handling-websocket-events/.

## AI storytelling
Export STORY_API_KEY and STORY_MODEL for a model supporting the configured OpenAI-compatible Chat Completions endpoint. Default endpoint: https://api.openai.com/v1/chat/completions; override STORY_API_URL if necessary. Runtime API usage may be separately billed. No key is included. API failure or invalid output keeps a prepared fallback. The host must approve every next scene, including the ending. The AI writes narrative only, never vote totals or resource values. Configure supported provider/model limits when choosing a model.

## OBS
In the local app open Stream overlay → Copy URL. Add that URL to an OBS Browser Source, width 1920, height 1080. The unguessable overlay token grants read-only story access. Keep the URL private. Hosted demo tab synchronization does not synchronize a separate OBS browser process; use the backend for OBS. Current overlay scenes have a dark background with transparent page surroundings.

## Rules and persistence
45-second rounds, five chapters. One vote per Twitch user per round; replacement is allowed until close. Duplicate event IDs are ignored. Ties choose the first tied choice in A/B/C order; no votes select A. State mutations are serialized. A close applies effects exactly once; versions prevent stale host commands. Restart pauses an active vote. SQLite stores story state and Twitch refresh credentials locally in data/; protect that directory and do not commit or distribute it. Host sessions are memory-only; log in again after restart. The server is intended for one trusted local streamer, not public multi-tenant use. Harden credential storage, authentication rate limiting, session lifetime and observability before public backend hosting.

## Verify
```bash
python3 -m unittest discover -s tests -v
node --check dist/app.js
```
Manual integration checklist: two real viewers; change a vote; late/invalid input; timer expiry; host approval; AI timeout/fallback; disconnect/resume; restart; OBS connection; all five rounds; unauthorized host action; exported recap.

## Layout
- dist/: dashboard, browser demo and OBS overlay
- backend/engine.py: deterministic state engine
- backend/server.py: aiohttp host, SQLite, Twitch OAuth/EventSub and narrative adapter
- tests/: engine and HTTP regression tests

## Hackathon submission
Create a public GitHub repository with all source and these instructions. Record a public YouTube demo under three minutes showing real Twitch operation and actual Codex development. Supply the genuine Codex build-thread session ID; none is invented here. This implementation was started 31 October 2026. Check current official rules at https://twitchcon-codex.devpost.com/rules.

## Expedition dashboard update
The colourful Cosmic Playground UI adds midnight-blue and violet navigation, a pastel planet and spaceship, cyan/pink resource cards, colour-coded voting choices, a five-chapter progress strip and a contextual Your next step prompt. Open How to play for a plain-language explanation of streamer, viewer and OBS roles.

### How the game works
You are the host. Open a vote; viewers type !a, !b or !c in your Twitch channel. When voting closes, the most popular choice changes ship resources and the story. Read the draft and approve it before it appears to viewers. Repeat for five chapters. The online demo lets you practice using the simulator instead of real viewers.

### Update an existing local installation
For a planned upgrade, install the matching backend and complete dist/ source, including story.js and assets/, then restart the server and hard-refresh the browser (Command + Shift + R). Keep your data directory and private environment configuration. A partial copy of index.html, style.css, and app.js can leave modules or cache policy out of sync. This submission review did not restart the running server.

## Dream Orbit styling
Compact story panel and controls, consistent SVG line icons, bundled pastel dreamscape and crescent illustrations, gentle star twinkling, entrance transitions and floating moon animation. Reduced-motion preferences disable animation. All artwork is bundled locally. UI update: replace dist/index.html, dist/style.css, dist/app.js and merge dist/assets/; do not replace your backend or data.

## Dashboard before host sign-in
The local app now opens with the styled dashboard and a host-key form at the top. Before authentication the dashboard shows an explicitly labeled sample session, not private session data. Host actions are disabled, and the backend continues to reject unauthorized commands and state access. After login the actual session loads; logout restores the sample preview. No backend changes are needed for this update.

## Compact preview navigation fix
All navigation pages now open before host sign-in: Mission control, How to play, Story chronicle, Stream overlay and Connections. Pages show sample or explanatory content until authenticated. Private overlay URLs, real history and connection details remain protected. Connecting Twitch and mission actions still require the host key. UI sizing is reduced further. If the display remains oversized on a Mac, reset browser zoom with Command+0. Copy all UI files and assets into dist, then hard-refresh with Command+Shift+R.

## Story continuity and integration verification
Earlier choices now create persistent facts and named endings. Repaired life support preserves oxygen on subsequent rounds; a rescued engineer restores energy; reinforced shields mitigate later damage; scanned coordinates and rescue signals change the finale. The dashboard and overlay display story-memory chips. Start a new adventure to collect continuity facts from chapter 1.

16 automated tests pass, including all 243 five-round decision paths and synthetic EventSub-to-vote-to-approval/overlay integration. Real Twitch viewer delivery, OBS, runtime AI and Codex session evidence are still pending. See docs/VERIFICATION_STATUS.md, docs/LIVE_DEMO_CHECKLIST.md and docs/CODEX_HANDOFF.md.

This full update changes backend/ and dist/. Stop the server; copy backend/, dist/, tests/ and docs/ into your existing project. Keep data/, .venv/ and your environment settings. Restart in the same terminal. Include dist/story.js and the assets folder.

## Choice Consequences Reveal
Closing a round saves a deterministic `result` snapshot in SQLite: selected choice,
all three vote counts and total, tie/default reason, actual resource deltas after
bonuses and 0–100 clamping, and only the newly gained memory facts. AI narration
cannot supply or modify these values. Both dashboard and OBS show this result
until `reveal_until` (seven seconds after backend close). Polling can delay its
first appearance by up to 800 ms; reconnecting shows only the remaining interval,
not a replay. Keep browser and backend clocks synchronized. Approval does not
remove the snapshot; OBS finishes the reveal before displaying an approved scene.
Without approval the existing scene stays visible. Old saves without a result
load normally and gain the feature on their next resolved round.

Ties explicitly report the tied letters and use the existing A/B/C ordering.
Zero votes explicitly report default A, never a community win. Round five can
correctly show “No new facts gained.” The browser demo uses locally calculated
sample results and labels them as samples.

The dedicated OBS layout supports Browser Sources at **1000 × 550** and
**1920 × 1080**. A live URL displays connection status and never falls back to
sample story content if the backend is unavailable. `?overlay=demo` explicitly
opens the sample preview. Reduced-motion disables the card entrance animation;
the seven-second display still applies. Twitch OAuth, EventSub, vote replacement,
and event deduplication retain their existing flow.

Run automated checks without reading credentials or using your saved database:

```bash
python3 -m unittest discover -s tests -v
node --check dist/app.js
node tests/test_reveal_ui.cjs
```

Tests use temporary databases. The HTTP tests need permission to bind a loopback
socket. In a restricted sandbox, run the socket-free checks separately:

```bash
python3 -m unittest discover -s tests -p test_engine.py -v
python3 -m unittest discover -s tests -p test_story.py -v
python3 -m unittest discover -s tests -p test_result_persistence.py -v
python3 -m unittest discover -s tests -p test_result_routes.py -v
node tests/test_reveal_ui.cjs
```

Manual browser/OBS verification (use a separate test database and a new test
session; do not reset an adventure you want to keep):

1. Open the dashboard and its live overlay. At both source sizes above, check the
   approved story, status/timer, and all three complete choice labels and counts.
2. Resolve a normal vote, a B/C tie, and a zero-vote round. Compare the card to
   `/api/state`'s `result`: exact counts, deltas, and newly gained memory.
3. Check the reveal ends seven seconds after close. Reload during and after it;
   it should neither restart nor replay. Delay approval: no draft may appear in
   OBS. Approve during the reveal: OBS finishes the card before the next scene.
4. Enable reduced motion in the OS/browser and repeat. Verify a static card with
   the same duration. Disconnect the backend: the overlay must identify its stale
   connection and never switch to sample content. Verify `?overlay=demo` is
   prominently marked SAMPLE PREVIEW.
5. With real Twitch viewers, verify replacement votes, timer closure, deduplication,
   reconnect/pause, and host approval. These require real-account verification;
   synthetic tests do not establish real Twitch delivery or OBS visual evidence.

### Review fixes and exact local verification
The follow-up review fixes live-overlay recovery labels even when session data
has not changed, avoids fetching host configuration for read-only overlays, and
makes zero-vote/tie draft introductions honest too. Short canvases put the three
choices in one row; longer scene text shrinks down to a readable 14 px when
needed. Provider narration still cannot set results. The Chrome layout tests
exercise long scenes, result cards, both canvas sizes, and reduced motion in an
isolated temporary browser profile. They skip with an explicit reason when
Chrome is absent or cannot launch:

```bash
python3 -m unittest discover -s tests -p test_overlay_layout.py -v
```

To verify locally without changing your saved adventure:

1. Stop any server currently using port 8080. In the project directory activate
   the existing virtual environment with `source .venv/bin/activate`. Use your
   existing backend environment configuration; do not print environment variables.
   `HOST_KEY` must already be configured (at least 16 characters).
2. Start an isolated session with this command. It creates a fresh database under
   a unique temporary directory and does not access `data/streamquest.db`:

   ```bash
   DATABASE_PATH="$(mktemp -d /tmp/streamquest-verify.XXXXXX)/state.db" APP_BASE_URL=http://localhost:8080 python3 -m backend.server
   ```

3. Open `http://localhost:8080`, hard-refresh, and unlock using your configured
   host key. In Connections, connect your Twitch broadcaster account for this
   temporary session. Existing environment credentials are reused; do not paste
   credentials into chat or source files. The new database has no saved OAuth
   authorization, so it requires a fresh Connect Twitch step.
4. In Stream overlay, choose Copy URL. In OBS add a **Browser Source**, paste that
   URL privately, and set Width **1000**, Height **550**. Use the same URL at
   **1920 × 1080** as well. The source should say **LIVE MODE · Connected** and
   show the entire scene, status/timer, and three choices. Turn off OBS's
   “Shutdown source when not visible” while checking timing.
5. Launch adventure → Open voting. Have two distinct viewers both send `!b` in
   your channel. Close & resolve. On both dashboard and OBS confirm **B**, counts
   **A: 0 / B: 2 / C: 0**, total **2**, oxygen **−8**, energy **−5**, chaos **+15**,
   and newly gained **Signal decoded**. The reveal window ends seven seconds
   after backend close (the first appearance can lag by one polling interval).
6. Wait without approving: OBS must return to the old scene with “awaiting host
   approval.” The host can read the draft on the dashboard. Approve next chapter,
   then open voting. Have one viewer send `!b`, another `!c`. Close: confirm
   **Tie B / C**, selected **B**, **0 / 1 / 1**, deltas **−8 / −5 / +15**, and
   **Navigation mapped**. Approve during the reveal to confirm OBS finishes the
   result before showing the approved chapter.
7. Open the third vote and close without viewer commands. Confirm **No votes ·
   default A**, **0 / 0 / 0**, total **0**, deltas **+10 / −8 / −12**, and
   **Shields reinforced**. The draft must not claim a community choice. On the
   fifth round, no new memory fact is expected.
8. Reload the overlay during a reveal and after expiry: it shows only the
   remaining window and does not replay expired results. In Chrome DevTools →
   More tools → Rendering, emulate `prefers-reduced-motion: reduce`; repeat a
   reveal and confirm no entrance movement. Resize the source to each target
   size and verify every line and choice stays in view.
9. To test reconnect without restarting the session, open the overlay in Chrome,
   set DevTools Network to Offline, then back to No throttling. Its status must
   change from disconnected back to **Connected**, even if no votes changed.
   `http://localhost:8080/?overlay=demo` must instead say **SAMPLE PREVIEW**.
10. Stop the temporary server with Ctrl+C. Restart your normal server with
    `python3 -m backend.server` in its usual configured environment to return to
    your saved adventure. No reset or deletion is needed.

Automated checks use temporary databases and synthetic events. They do not
establish delivery from real Twitch accounts or successful rendering in OBS.

### OBS refresh after the responsive overlay fix (revision 20261101-obs2)

The shipped broadcast view never uses “Your story preview.” Seeing that text in
OBS indicates an older UI or the dashboard URL rather than the current overlay.
The updated entry page versions CSS, JS, and the story module; the Python server
sends `Cache-Control: no-store`. The live overlay displays
**LIVE MODE · Connected · 20261101-obs2** so its revision can be checked directly.
All three choices stay together on short canvases. Scene text shrinks first;
if content still exceeds the viewport, the complete scene or result layout scales
to fit without truncating text. Host approval and Twitch handlers are unchanged.

1. In the terminal running the server, press **Ctrl+C**. From this project folder,
   in your usual configured shell, run:

   ```bash
   source .venv/bin/activate
   python3 -m backend.server
   ```

   Reuse your existing environment (`HOST_KEY`, Twitch settings, and any
   `DATABASE_PATH` override). The app does not load `.env` automatically. Keep the
   same database; no reset, new database, or Twitch reauthorization is needed.
   Restart pauses an active vote and requires unlocking the dashboard again.
2. Open `http://localhost:8080`, press **Command+Shift+R**, unlock the dashboard,
   and use **Stream overlay → Copy URL**. The URL must contain your private
   `?overlay=…` token; do not use the plain dashboard URL or `overlay=demo`.
3. In OBS, open the Browser Source **Properties**. Turn **Local file** off,
   paste the copied URL, set **Width 1000 / Height 550**, and click
   **Refresh cache of current page**, then **OK**. If the old view persists,
   append `&v=20261101-obs2` to the URL and refresh again. Verify the revision
   label above. If missing, check the server/project folder and port being used.
4. Right-click the source → **Transform → Reset Transform** to remove an old
   crop/scale. Position/scale it as needed after checking the source itself.
   Repeat with Browser Source **Width 1920 / Height 1080**. Changing the OBS
   output canvas alone does not change the Browser Source viewport.
5. Keep the source visible and disable **Shutdown source when not visible**
   during verification. On the next Chapter 1 round, send `!b` from one viewer
   and close voting. Expect **B: 1**, **oxygen −8**, **energy −5**, **chaos +15**,
   and **Signal decoded** on both dashboard and OBS. The result expires seven
   seconds after backend close; 800 ms polling can shorten its visible time.
   Wait without approving: the previous scene and all three choices return with
   **awaiting host approval**. Approve: Chapter 2 appears. If approving during
   the reveal, the result stays until its original expiry, then Chapter 2 appears.

### Verification status — 2026-11-01

**User-reported manual OBS verification, 1000 × 550, revision 20261101-obs2:**

- Real Twitch vote totals match the dashboard.
- The Choice Consequences Reveal card appears in OBS.
- After the reveal, the old chapter stays visible with “awaiting host approval.”
- Clicking Approve changes OBS to Chapter 3.
- All three choices are fully visible; the live revision label is displayed.

These are the user's observations, not automated browser results. Earlier manual
checks also confirmed B=1, oxygen −8, energy −5, chaos +15, Signal decoded on the
dashboard, and Chapter 2 in OBS after approval. Exact seven-second visible timing
has not been measured manually. The result window is seven seconds from backend
close; polling can shorten the visible interval.

**Automated rerun using the project's virtual environment:**

```bash
.venv/bin/python -m unittest discover -s tests -p test_server.py -v
.venv/bin/python -m unittest discover -s tests -p test_live_flow.py -v
.venv/bin/python -m unittest discover -s tests -v
node tests/test_reveal_ui.cjs
```

**Latest user-provided local automated result:** in the user's normal Mac
terminal, `.venv/bin/python -m unittest discover -s tests -v` reported
**Ran 27 tests in 13.330s — OK, no skips**. This includes the previously blocked
six HTTP tests and both overlay layout tests. The layout tests cover
**1000 × 550 and 1920 × 1080**, long scenes, result cards, and reduced motion in
headless Chrome. This result is reported by the user; the coding environment did
not independently reproduce it. Automated Chrome layout success is distinct from
manual testing in OBS, which is confirmed only at **1000 × 550**.

The earlier restricted-environment run had 19 Python passes, six HTTP setup
errors from denied socket binds, and a skipped Chrome layout class. The local
Mac result resolves those execution blockers for local verification. Coverage
includes voting rules, all 243 story paths, persistence, HTTP permissions,
cache headers, result accuracy, and draft redaction. The separately run Node UI
suite passed in the coding environment, including the 7000 ms timestamp boundary,
early approval, and recovery. That Node result is separate from the 27 Python
tests and is not a measurement of visible OBS duration.

HTTP fixtures now clear inherited environment configuration, restore it during
cleanup, use unique temporary databases and ephemeral loopback ports, and
register client cleanup before startup so setup failures close client sessions.
All existing assertions remain; no HTTP test was skipped or replaced. The
verification work did not stop or modify the user's running server or saved
adventures.

**Still unverified manually:** 1920 × 1080; exact seven-second visible duration;
approval during the reveal; reload during/after reveal; tie and zero-vote result
presentation; reduced motion; disconnect/reconnect; long generated-scene fit;
and a complete five-chapter OBS run. The HTTP commands above can run alongside the app; they use temporary databases and ephemeral
ports and do not require stopping the running app. The earlier restart and
isolated-session instructions are optional procedures, not actions performed by
this verification run.

### Submission readiness

Review checks: `.venv/bin/python -m pip check` reports no broken requirements;
`node tests/test_reveal_ui.cjs` passes. Ignore rules were tested in a disposable
Git repository: 21 representative private paths are excluded and eight required
submission paths (including `.env.example`) remain included. A credential-format
scan of reviewed submission text found no remaining matches; it is not a complete
credential or Git-history audit.

- Source dependencies and setup are documented above. Keep `.venv`, populated
  `.env` files, `data/`, databases and their sidecars, OAuth token files, private
  keys, logs, and archives out of submissions; `.gitignore` covers these paths.
  `.env.example` is intentionally included with safe placeholders.
- Credential-like values were removed from `.env.example` during review. Treat
  the removed host password and provider/client secrets as exposed if valid:
  rotate them privately before publishing. Changing the file or adding ignore
  rules cannot remove secrets from earlier copies or Git history.
- This workspace currently has no `.git` metadata, so tracked files, remotes,
  and history could not be audited. Before publishing, initialize/review the
  repository, inspect the staged file list, and scan any imported history for
  secrets. Ignore rules do not untrack previously committed files. Do not submit
  a raw folder archive containing private files.
- Still needed for submission: the actual public repository URL, demo video,
  genuine Codex session/build evidence, and confirmation of the applicable event
  requirements. None were created, published, or pushed by this review.

### Initial commit preparation

The first-commit review identified 24 publishable files: backend and frontend
source, both SVG assets, tests, documentation, requirements, `.gitignore`, and
the sanitized `.env.example`. A value-redacting credential scan found no matches
in that set. Exclusion checks passed for 23 representative private paths,
including populated `.env` variants, OAuth/token exports, SQLite databases and
sidecars, `.venv`, recordings, captures, and archives. Recordings and additional
archive formats are now explicitly ignored. Keep any new private exports out
of the repository and review future staged files before committing.

Creating this workspace's `.git` directory was denied with “Operation not
permitted” in the coding environment. No project repository, initial commit,
remote, or push was created. The exclusion review used disposable temporary
Git metadata only; it did not stage or commit project files. The earlier
credential-rotation advice still applies to previously populated templates.

## Dreamy OBS overlay — revision 20261102-dream1

The OBS-only skin now matches the dashboard's lavender, purple, pink and teal
palette, using the existing dreamscape and moon SVGs, stars, soft gradients and
rounded cards. The story has a readable title and narration; three side-by-side
choice cards show A/B/C, chat commands, actual counts, rounded percentages and
vote bars. Countdown/status, chapter and resource values remain visible. The
result uses the existing authoritative counts, deltas and full new memory facts
with a restrained entrance animation and reduced-motion support. Host dashboard
markup/styles and all backend/Twitch/authentication logic are unchanged.

Narration starts at a viewport-appropriate size and shrinks only as needed to
14 logical pixels; a final whole-layout fitting pass handles overflow without
ellipsis, line clamps, scroll-only content or discarded facts. Existing backend
narration limits (110 words / 1400 characters for provider text) are unchanged.
The layout refits after font loading and resizing. Extreme content can require
additional scaling; readability and fit need confirmation on the new OBS skin.

**This revision's verification:** Node syntax and UI checks pass, including
actual counts/percentages, reveal expiry, early approval, escaping and draft
privacy. The Python run has 19 passes, six HTTP setup errors from denied socket
binds, and one skipped Chrome layout class because headless Chrome cannot launch
in this environment. Socket-free route/cache checks pass with the new revision.
Browser tests now additionally check choice text/counts and resource/effect
bounds, plus pending, voting and paused layouts at both target sizes. They could
not execute here. The user's previous 27-test local success and manual OBS
1000 × 550 evidence apply to **20261101-obs2**, not this restyle. Neither target
size is claimed visually verified for **20261102-dream1** yet.

To verify in a normal Mac terminal without accessing saved adventures:

```bash
.venv/bin/python -m unittest discover -s tests -v
node tests/test_reveal_ui.cjs
```

To load this revision in OBS:

1. In the terminal running the app, press **Ctrl+C**. Keep its existing exported
   environment and database configuration, then run from this project directory:

   ```bash
   .venv/bin/python -m backend.server
   ```

   This restarts the same saved session; an active vote pauses on restart. Host
   login is required again. Do not delete/reset the database or create a new one.
2. Open `http://localhost:8080`, press **Command+Shift+R**, unlock, and choose
   **Stream overlay → Copy URL**. Keep this authenticated read-only URL private.
3. OBS → Browser Source → **Properties**: turn **Local file** off, paste the
   copied URL, append **`&v=20261102-dream1`**, set **Width 1000 / Height 550**,
   then click **Refresh cache of current page → OK**. Confirm the connection
   badge shows **20261102-dream1**. Use the overlay URL, not the dashboard URL.
4. Check any previous crop via **Transform → Reset Transform**, then position
   the source as desired. Repeat with Browser Source **Width 1920 / Height 1080**;
   the OBS output canvas size alone does not set this viewport.
5. Keep the source visible and disable **Shutdown source when not visible**
   during checks. Verify long narration, all three choices/counts/percentages,
   resource values, result facts and deltas at both sizes. Close a vote, wait for
   the reveal to expire, then approve. The old chapter must stay until approval;
   approval during reveal must not shorten the saved seven-second result window.
   Polling can delay first appearance by up to one normal 800 ms interval.

No server restart, data deletion, commit or push was performed by this restyle.
