# The daily briefing routine — canonical spec

This file is the source of truth for what the scheduled daily-briefing task
is supposed to do. The task itself runs from a prompt stored in claude.ai's
Triggers / Scheduled tasks settings for this environment — **that stored
prompt has to be updated by hand to match this file**; nothing in this repo
pushes to it automatically, and no tool available to Claude in a session can
reach it either. When this file changes, go update the trigger.

The block below is the full prompt, ready to paste into the trigger
configuration as-is.

## Current prompt (as of 2026-09-04)

```
Generate a briefing to help me catch up, then record it and yesterday's
decisions in the repo. The repo toby-a11y/daily-breifing is checked out in
your working directory; commit and push to it at the end.

Pull from the Open Loops board first
(https://claude.ai/code/artifact/7f776cfe-f735-4d98-be0b-281e3b64ac08,
Artifact tool, action read_db, collection "loops") rather than rebuilding
from scratch. It already holds the open items with history. If the board
cannot be read, use the newest Gmail thread with subject:WORKLIST instead.

BRIEFING

1. Schedule. Today's meetings and events with times, attendees, and prep
   needed. Anything with a same-day deadline attached (a delivery, an
   install, a switch) goes at the top, not buried in the list.
1.1 Kari's projects. Read her latest daily recap. Track progress against
    what is already on the board rather than re-deriving it from raw email.

2. Important emails. Unread threads needing attention, grouped by urgency.
   When a thread references a quote or deal, pull its status from HubSpot
   directly instead of noting "lives in HubSpot" — and check the deal's
   ASSOCIATED ACTIVITY TIMELINE (recent EMAIL/CALL/MEETING engagements,
   sorted newest first), not just its stage property. A deal's stage is not
   reliable proof of what has or hasn't happened: stages go stale when
   someone sends a follow-up without moving the pipeline forward, but the
   engagement log doesn't have that failure mode. See decisions/SCHEMA.md's
   "Standing rule: check deal activity, not deal stage" for the exact
   lookup pattern. If a customer named in the board or email has no
   HubSpot deal at all, say so explicitly rather than skipping them — that
   absence is itself worth knowing.
   Check QuickBooks for any payment that closes something already open.

3. Messages requiring response. Direct messages or mentions needing a
   reply.
4. Action items. Pending tasks or follow-ups. Roll recurring automated
   alerts (price monitor, deploy failures, Zapier) into whatever board item
   already covers that system rather than listing them fresh each time.

Keep it concise and scannable. Skip a section with nothing notable rather
than saying "nothing to report."

REPO

Use today's date in America/Chicago as YYYY-MM-DD.

- briefings/YYYY-MM-DD.md: the full briefing above, verbatim.
- decisions/YYYY-MM-DD.jsonl: every Gmail message with subject:DECISIONLOG
  in:anywhere newer_than:3d whose message id is not already present in any
  file under decisions/. One line per message: the JSON body from the
  email, plus "message_id" and "subject" fields. Skip the file if there are
  none. Never edit or delete an existing line in decisions/; it is
  append-only. See decisions/SCHEMA.md for the full field reference.
- worklists/YYYY-MM-DD.txt: the body of the newest Gmail message with
  subject:WORKLIST, if one exists from the last 3 days.
- board/YYYY-MM-DD.json: the raw board read from above, if it succeeded.

Commit everything with the message "briefing YYYY-MM-DD" and push. If the
push fails, say so in the briefing output in one line; do not retry more
than once.

Do not send any email. Do not write to the board.
```

## Changelog

- **2026-09-04** — Added the HubSpot deal-activity-over-stage rule to
  section 2, and the "no deal found is worth saying" instruction. Cause:
  the Heather Parker deal's `Prospect` stage read as "quote never sent,"
  but HubSpot's own email log showed Kari had sent it days earlier — the
  stage was just never advanced. A live working session that day (see
  `decisions/2026-09-04.jsonl`, `source:"session"` lines with
  `action:"hubspot_audit"`) then re-checked every customer-facing item on
  the Punch List artifact against deal activity and found the same gap
  pattern elsewhere. Full rule and lookup pattern documented in
  `decisions/SCHEMA.md`.

## Related, not (yet) part of the automated routine

The **Punch List artifact** (an interactive per-day checklist built from
the briefing, with status/notes that save back to the page, and a
`decisions/*.jsonl` `source:"session"` trail of what got decided while
working it) is a live-session pattern, not something the unattended daily
run creates itself. Full spec — item schema, the three-state check-off
model, how it persists, and how its live links get built — is in
`PUNCH_LIST.md`. If that should become part of the automated routine too,
this file and the trigger prompt both need to say so explicitly — right
now the routine only produces the four files above.
