# The daily briefing routine — canonical spec

This file is the source of truth for what the scheduled daily-briefing task
is supposed to do. The task itself runs from a prompt stored in claude.ai's
Triggers / Scheduled tasks settings for this environment — **that stored
prompt has to be updated by hand to match this file**; nothing in this repo
pushes to it automatically, and no tool available to Claude in a session can
reach it either. When this file changes, go update the trigger.

The block below is the full prompt, ready to paste into the trigger
configuration as-is.

## Current prompt (as of 2026-09-14, rot watch)

```
Generate a briefing to help me catch up, then record it and yesterday's
decisions in the repo. The repo toby-a11y/daily-breifing is checked out in
your working directory; commit and push to it at the end.

Carry forward rather than rebuilding from scratch. Two sources, in this
order:

- The Punch List artifact
  (https://claude.ai/code/artifact/8f773d70-1369-4e9b-85c9-c1e8b070c653)
  is the LIVE carry-forward source — it is updated every run and holds
  Toby's own statuses and notes. Read it first (Artifact action:"read").
- The Open Loops board
  (https://claude.ai/code/artifact/7f776cfe-f735-4d98-be0b-281e3b64ac08,
  Artifact tool, action read_db, collection "loops") is a SECONDARY
  source and is not guaranteed current. Before using it, check the
  newest `updatedAt` across the records you read. If that is more than
  2 days older than today, treat the board as historical only: say so
  in one line in the briefing, and do not present its contents as the
  current state of anything. As of 2026-09-14 the board had not been
  written to since 2026-09-04.

If neither can be read, use the newest Gmail thread with subject:WORKLIST
instead.

BRIEFING

1. Schedule. Today's meetings and events with times, attendees, and prep
   needed. Anything with a same-day deadline attached (a delivery, an
   install, a switch) goes at the top, not buried in the list.
1.1 Kari's projects. Read her latest daily recap. Track progress against
    what is already on the Punch List rather than re-deriving it from raw
    email. If her last recap is more than 2 days old, say so and how many
    days — and reconstruct from her call logs, sent mail and HubSpot
    activity instead, rather than reporting nothing.

2. Important emails. Unread threads needing attention, grouped by urgency.
   When a thread references a quote or deal, pull its status from HubSpot
   directly instead of noting "lives in HubSpot" — and check the deal's
   ASSOCIATED ACTIVITY TIMELINE (recent EMAIL/CALL/MEETING engagements,
   sorted newest first), not just its stage property. A deal's stage is not
   reliable proof of what has or hasn't happened: stages go stale when
   someone sends a follow-up without moving the pipeline forward, but the
   engagement log doesn't have that failure mode. See decisions/SCHEMA.md's
   "Standing rule: check deal activity, not deal stage" for the exact
   lookup pattern. If a customer named in the Punch List, the board or an
   email has no HubSpot deal at all, say so explicitly rather than
   skipping them — that absence is itself worth knowing.
   Check QuickBooks for any payment that closes something already open.

3. Messages requiring response. Direct messages or mentions needing a
   reply.
4. Action items. Pending tasks or follow-ups. Roll recurring automated
   alerts (price monitor, deploy failures, Zapier) into whatever Punch List
   item already covers that system rather than listing them fresh each
   time — but only up to the roll-up ceiling in section 5: once a signal
   reaches `escalate`, it comes OUT of the roll-up and stands on its own.

5. Rot watch. Things that decay get escalated here instead of being
   re-described every morning. Full spec in ROT.md. Three steps:

   a. Seed today's ledger:  bin/rot-check.py --carry
      This copies yesterday's signals forward with `last_change`
      UNCHANGED. That is deliberate — a new day does not mean anything
      moved.

   b. Edit health/YYYY-MM-DD.json: move a signal's `last_change` forward
      ONLY where you can point at primary-source evidence that the thing
      actually changed (a reply sent, an invoice paid, a board write, an
      alert cleared), and record that evidence in the `evidence` field.
      Re-reading a stale source is not a change. Add signals for anything
      new that can rot; retire ones that are genuinely finished by setting
      "retired": "YYYY-MM-DD" with a reason. Use the same `id` as the
      matching Punch List item.

   c. Run bin/rot-check.py and obey what it returns — the state decides
      the treatment, not your judgment on the day:
        warn     — one line in its own section; may stay rolled up
        escalate — promote OUT of any roll-up into its own numbered action
                   item, name the owner, state the age in days
        blocker  — lead the briefing with it, above the schedule, and ask
                   plainly: fix it, reassign it, or consciously retire it
      A signal with no owner cannot resolve; say so and ask for one.
      Include the rot-check output as a "Rot watch" section when anything
      is above `warn`, and say nothing when nothing is.

Keep it concise and scannable. Skip a section with nothing notable rather
than saying "nothing to report."

REPO

The repo's trunk is the `main` branch. Every run must build on it and
land on it — do NOT start a fresh branch from whatever the working copy
happens to be checked out at, and never create a new root commit.

Before writing anything:

    git fetch origin
    git checkout -B <this session's branch> origin/main
    bin/sync-branch.sh --check

If `origin/main` does not exist, stop and say so in the briefing output
rather than starting a new lineage. `bin/sync-branch.sh --check` confirms
the checkout actually landed on the trunk and prints the drift if it did
not — cheap, and it is the check that five drifted runs did not have.

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
- health/YYYY-MM-DD.json: the staleness ledger from section 5. Always
  write this one, every run — it is what makes rot visible across days
  instead of being re-derived and forgotten each morning. See ROT.md.

Commit everything with the message "briefing YYYY-MM-DD" and land it on
the trunk:

    git push origin HEAD:main

This puts the commit on `main` directly, whatever the session's own
branch is called, so the history stays in one lineage. If the push is
rejected because `main` moved underneath you, run `git fetch origin &&
git rebase origin/main` once and push again. If it still fails, say so
in the briefing output in one line and stop — do not retry further, and
do not work around it by pushing to a side branch.

Then confirm it actually landed:

    bin/sync-branch.sh --verify

That asserts HEAD is an ancestor of `origin/main` AND that today's
briefing and health ledger are really present on the trunk, which a
successful-looking push to a side branch is not. Say in one line whether
today's files are on `main`. A run that writes five files but leaves them
off the trunk has not delivered.

PUNCH LIST

After the repo commit above, also update the Punch List artifact at
https://claude.ai/code/artifact/8f773d70-1369-4e9b-85c9-c1e8b070c653
(full spec in PUNCH_LIST.md — item schema, status model, link formulas).
Read its current live state first; never rebuild from scratch. Apply the
carry-forward merge exactly as PUNCH_LIST.md defines it: drop items marked
done, leave every remaining open/doing item's status and note untouched,
add new items for anything in today's briefing that has no matching
stable id yet, and run the HubSpot resolving process plus populate links
for those new items only. If the read or publish fails, say so in the
briefing output in one line and move on — it must not block the repo
commit above, which is the routine's real deliverable.

Do not send any email. Do not write to the Open Loops board (the
read-only source in the first paragraph above) — the Punch List artifact
is a separate page, and writing to it is the point of this section.
```

## Repository layout and branching

`main` is the trunk and the only branch that matters. It holds every
briefing, board snapshot, decisions file and worklist the routine has
ever written. Each scheduled run gets its own throwaway session branch
from the harness; that branch is a workspace, not a destination — the
commit lands on `main` via `git push origin HEAD:main`.

**Why this is spelled out.** Until 2026-09-14 the prompt said only
"commit and push", and the harness hands each session a fresh branch
name. Every run therefore pushed to a brand-new branch that nobody ever
merged. By 9/14 the repo had ten branches, no `main` at all, and a
default branch (`claude/relaxed-goodall-3yl6eu`) still holding only the
2026-09-04 briefing — so a fresh clone showed ten-day-old data and each
morning's run started from whatever stale point it happened to land on.
Two runs on 9/04 had even created **unrelated root commits** (`e68f2ef`
and `a15054d`, nine minutes apart), splitting the history into two
disconnected trees whose files were later copied across by hand without
ever merging.

The 2026-09-14 consolidation merged all ten branches into `main`,
including the second root via `--allow-unrelated-histories`. Every prior
branch tip is now an ancestor of `main`. Two blobs are deliberately not
in `main`'s tree, both verified non-lossy: an array-wrapped copy of
`board/2026-09-04.json` (same 87 records as the canonical JSONL) and a
79-line `decisions/2026-09-04.jsonl` that is a strict subset of the
92-line version kept. The old branches were left in place as a safety
net; they can be deleted once `main` has been eyeballed.

**Known gap: there is no `briefings/2026-09-12.md`.** It is absent from
every branch, so that run either never fired or failed before writing.
It is not recoverable from the repo.

**`briefings/2026-09-04.second-run.md`** is the other 9/04 briefing,
from the second root. Two runs that day produced two genuinely different
briefings for the same date — not a draft and a revision — so both are
kept. This is the only date with a `.second-run` file, and the naming is
deliberately awkward so it stays a one-off rather than a pattern.

## Changelog

- **2026-09-14 (rot watch)** — Added section 5, "Rot watch", and
  `health/YYYY-MM-DD.json` to the repo deliverables. Cause: the structural
  fixes earlier the same day stopped the routine *reading* stale sources, but
  not the older failure underneath it — things owed to people aged for weeks
  while every briefing faithfully re-described them and nothing changed. The
  board reached 10 days, Kari's recap 11, the erroring Zaps 11, the BFG
  one-line reply 8, Jinyi's ship date 20. Age lived only in prose, so nothing
  could be compared or alarmed on, and the roll-up rule quietly buried alerts
  once the board they rolled into went stale. Now: age persists in a ledger,
  fixed thresholds escalate a signal through ok → warn → escalate → blocker,
  and crossing a threshold changes what the briefing is *obliged* to do —
  including promoting an item out of a roll-up and, at blocker, leading the
  briefing. `last_change` may only move on evidence that the thing actually
  moved; observation is not progress. Retiring a signal on purpose is an
  allowed outcome, letting it rot is not. Also added `bin/sync-branch.sh`,
  which executes the trunk rules as a tested command rather than prose, and
  whose `--verify` catches the specific failure where a run pushes
  successfully to a side branch and delivers nothing. Full spec in ROT.md.

- **2026-09-14 (structural fixes)** — Three causes fixed after the 9/14
  run found the repo fragmented across ten branches. (1) The REPO
  section now pins the trunk: fetch and branch from `origin/main` before
  writing, `git push origin HEAD:main` to land, one rebase-and-retry on
  rejection, then an explicit ancestry check so a run can't silently
  leave its files off the trunk. (2) The carry-forward source is now the
  Punch List artifact, with the Open Loops board demoted to secondary
  plus a staleness check — the board had not been written to since
  2026-09-04 while the prompt still treated it as the freshest input,
  which would have had every run rebuilding from ten-day-old state. (3)
  Repository layout and branching documented above, including the
  duplicate-root incident and the missing 9/12 briefing. **The stored
  trigger prompt must be updated by hand to match — see the top of this
  file.**

- **2026-09-04 (punch-list wiring)** — Added a PUNCH LIST section to the
  prompt: the routine now reads and updates the Punch List artifact every
  run, via the carry-forward merge defined in `PUNCH_LIST.md` (drop done
  items, preserve open/doing items' status and notes untouched, add new
  items with links and the HubSpot resolving process applied only to
  those). Also clarified that "do not write to the board" means the
  read-only Open Loops board specifically, not the Punch List artifact —
  the two are different pages and the constraint was ambiguous once the
  routine started writing to one of them. Failure to read/publish the
  artifact is non-blocking; the repo commit is still the routine's real
  deliverable.
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

## The Punch List artifact

Now built and updated by this routine every run (see the PUNCH LIST
section of the prompt above) — no longer a live-session-only pattern.
Full spec — item schema, the three-state check-off model, how it
persists, the daily carry-forward merge, and how its live links get
built — is in `PUNCH_LIST.md`.
