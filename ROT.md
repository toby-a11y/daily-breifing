# Quiet rot — what it is, and how this repo stops it

"Quiet rot" is the failure mode this routine kept producing: **things decayed, the
briefing noticed every single morning, and nothing ever changed as a result.**

Look at the Sep 4–13 briefings and the pattern is unmistakable. Each one re-derived
"the board hasn't been written in N days" from scratch, wrote it into a prose
paragraph, and moved on. N grew from 1 to 9. Same for Kari's recap (1 → 10 days),
the two erroring Zaps (1 → 10), the BFG NDA one-liner (1 → 7), David Morris's
drawing (1 → 9), and Aaron's ridge-vent comment (open since Aug 25). The routine was
never unobservant. It was *only* observant.

Three specific mechanisms produced that, and each has a countermeasure here:

| Mechanism | Countermeasure |
|---|---|
| **Age lived only in prose.** Every run recomputed "N days" from raw sources and wrote it into a sentence. Nothing persisted, so nothing could be compared, sorted, or alarmed on. | `health/YYYY-MM-DD.json` — a machine-readable staleness record written every run. |
| **No threshold.** Day 1 and day 10 of the same problem got the same treatment: one line in a list. Nothing about the report changed as the thing got worse. | `bin/rot-check.py` — fixed thresholds that escalate a signal through four states as it ages. |
| **Roll-up became a void.** "Roll recurring alerts into whatever board item already covers that system" was a good rule for reducing noise — until the board itself went stale. Then rolling up meant rolling into nothing. | The **roll-up ceiling** below: an item may be rolled up only while it is `ok` or `warn`. At `escalate` it must be promoted out. |

There is a fourth, mechanically separate failure — **branch drift** — handled by
`bin/sync-branch.sh` and documented at the bottom.

## The signal ledger

Every run writes `health/YYYY-MM-DD.json`. One entry per thing that can rot:

```json
{
  "date": "2026-09-13",
  "generated_at": "2026-09-13T19:16:00-05:00",
  "signals": [
    {
      "id": "open-loops-board",
      "label": "Open Loops board writes",
      "kind": "source",
      "last_change": "2026-09-04",
      "evidence": "91 records; read byte-identical to the 09-10 and 09-11 snapshots",
      "owner": "Toby",
      "thresholds": {"warn": 3, "escalate": 7, "blocker": 14}
    }
  ]
}
```

| field | meaning |
|---|---|
| `id` | stable kebab-case slug. **Must match the Punch List item `id`** where one exists, so the two systems agree on what a thing is. |
| `label` | short human name |
| `kind` | `source` (an input that feeds the briefing), `alert` (an automated system complaining), `promise` (something owed to a person), `infra` |
| `last_change` | `YYYY-MM-DD` of the last time this thing actually moved. **Not** the date it was last observed — the date it last changed. This is the whole point: observation is not progress. |
| `evidence` | how `last_change` was established, so the next run can verify rather than trust |
| `owner` | who can actually end it. `null` is itself a finding — an unowned signal can never resolve. |
| `thresholds` | `{warn, escalate, blocker}` in days |

`last_change` is the load-bearing field. The rule that makes the whole thing work:
**a signal's `last_change` may only move forward when the underlying thing changed.**
Re-reading a stale board, re-noticing a silent recap, or re-listing an unacked alert
does not touch it. If a run cannot establish that something moved, it carries the
previous `last_change` forward verbatim.

## The escalation ladder

`bin/rot-check.py` computes `age = today − last_change` and assigns a state. The
state, not the run's judgment, decides how the briefing treats it:

| State | Age | What the briefing must do |
|---|---|---|
| `ok` | `< warn` | Say nothing. Silence is correct here. |
| `warn` | `>= warn` | One line, in the section it belongs to. May be rolled up. |
| `escalate` | `>= escalate` | **Promoted out of any roll-up** into its own numbered action item, with the owner named and the age stated in days. May not be folded into another item. |
| `blocker` | `>= blocker` | Leads the briefing, above the schedule, with an explicit ask: *fix it, reassign it, or consciously kill it.* |

The ladder exists so that **the report changes shape as a thing gets worse**, which
is exactly what the prose version never did. A signal that has been sitting for ten
days should not look like a signal that started yesterday.

### The roll-up ceiling

The `ROUTINE.md` prompt still says to roll recurring automated alerts into the board
item that covers that system — that rule is good and stays. It now has a ceiling:
**roll-up is permitted only at `ok` and `warn`.** Once a signal reaches `escalate`
it comes out of the roll-up and stands on its own. This is what stops "two Zaps have
been erroring since Sep 3" from riding quietly inside a bullet for ten days.

### Killing a signal is a legitimate outcome

A `blocker` has three valid resolutions and "keep reporting it" is not one of them.
Fix it, hand it to a named owner with a date, or **consciously retire it** — record
`"retired": "YYYY-MM-DD"` with a one-line reason and stop carrying it. Deciding
something doesn't matter is a real decision; letting it rot because nobody ever
decided is the thing this file exists to prevent.

## Running it

```sh
bin/rot-check.py                      # newest health/ file
bin/rot-check.py --date 2026-09-13    # a specific day
bin/rot-check.py --carry              # seed today's file from the newest one
```

`--carry` copies the previous run's signals forward with `last_change` untouched,
which is the correct default: **a new day does not by itself mean anything moved.**
The run then edits only the entries it can prove changed, and adds any new ones.

Exit codes: `0` nothing above `warn`, `1` at least one `escalate`, `2` at least one
`blocker`. The routine does not fail on these — the repo commit is still the real
deliverable — but a non-zero code means the notification has something in it.

## Branch drift

Mechanically separate from rot, and it is **already fixed at the policy level** — the
2026-09-14 consolidation pinned the trunk to `origin/main` and made every run branch
from it and land with `git push origin HEAD:main`. See `ROUTINE.md`, REPO section.
That policy is canonical; nothing here second-guesses it.

What was still missing is that the policy lived only as prose in a prompt, and prose
in a prompt is what produced five drifted runs (Sep 7, 8, 9, 11, 13) in the first
place. `bin/sync-branch.sh` executes the same rules as a tested command:

```sh
bin/sync-branch.sh          # fetch; fast-forward onto origin/main when safe
bin/sync-branch.sh --check  # report only, change nothing
bin/sync-branch.sh --verify # after pushing: did today's work actually land on main?
```

Behaviour against `origin/main`:

- current, or **ahead** (unpushed work) → reports and exits clean
- **strictly behind** (HEAD is an ancestor of the trunk) → fast-forwards; safe, nothing can be lost
- **diverged** (real local commits the trunk lacks) → **stops and reports.** It never
  forces, rebases, or discards. Divergence wants a human.
- `origin/main` missing → stops, per `ROUTINE.md`

`--verify` is the half that catches the actual historical failure. A run that pushed
to its own branch instead of the trunk *looks* successful — the commit exists, the
push succeeded, nothing errors — and delivers nothing. `--verify` asserts HEAD is an
ancestor of `origin/main` **and** that today's briefing and health ledger are really
present on the trunk. Run it after pushing, and believe it over the push output.
