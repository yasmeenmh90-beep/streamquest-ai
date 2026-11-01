# Real Twitch + OBS verification

Automated local tests use synthetic EventSub fixtures. They are not evidence of an actual Twitch stream. Complete the following on the streamer's Mac and record what actually happens.

1. Start the updated backend with HOST_KEY, APP_BASE_URL, TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET configured. Use the same data directory to retain authorization. Never show keys in recordings.
2. Open localhost:8080, unlock, Connections → Connect Twitch, authorize the broadcaster account. Wait for Connected to <channel>.
3. In OBS, add a Browser Source. Copy the local app's Stream overlay URL; set 1920 x 1080. Do not use the private hosted static demo for OBS synchronization.
4. Start a Twitch stream using your normal OBS setup. Ask two real viewers to open the channel chat.
5. Launch an adventure and open voting. Viewer 1 sends !a then !b; viewer 2 sends !b. Expect A=0, B=2, C=0. Invalid commands must not count.
6. Let the 45-second timer expire. Expect exactly one resolution, B selected, resource change, signal-decoded memory, and a pending draft. Viewers must still see the previous approved scene.
7. Approve the next scene. Confirm the OBS overlay advances and recalls the decoded signal.
8. In chapter 2 choose A (help engineer). In chapter 3, verify a later energy bonus and remembered engineer. Continue through five chapters and record the named ending.
9. Verify pause/resume. Briefly interrupt networking when safe to do so; expect voting to pause and connection status to change. Reconnect and resume explicitly.
10. Capture evidence: actual chat messages, changing totals, OBS overlay on Twitch, approval boundary, story-memory callback and ending. Note any failures accurately.

## Demo video plan (under 3 minutes)
0:00-0:20 problem and idea; 0:20-1:20 real Twitch voting; 1:20-1:55 approval + memory consequences; 1:55-2:20 ending + overlay; 2:20-2:55 genuine Codex development footage, tests and repository.

## Evidence recorded so far

The user reports passing manual OBS checks at 1000 × 550 on revision
20261101-obs2: real Twitch totals match the dashboard, the result card appears,
the old scene remains pending approval, Approve advances to Chapter 3, and all
three choices are visible. This does not confirm every scenario listed above
or a public broadcast recording. Manual 1920 × 1080 remains unverified.

The user separately reports all 27 Python tests passing locally with no skips,
including HTTP and automated layout checks at both sizes. See
[VERIFICATION_STATUS.md](VERIFICATION_STATUS.md) for exact scope and remaining gaps.
