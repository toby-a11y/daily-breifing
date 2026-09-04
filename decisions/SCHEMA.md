# decisions/*.jsonl — schema

Append-only. One JSON object per line. Never edit or delete an existing line —
only ever append new ones. Files are named `decisions/YYYY-MM-DD.jsonl`
(America/Chicago date of the write, not necessarily the date being discussed).

Two sources feed this log, distinguished by `"source"`:

## `source: "decisionlog_email"` (implicit — see below)

The original source. Toby sends himself a self-email with subject
`DECISIONLOG YYYY-MM-DD | <who> | <topic>`, body is a JSON object. The daily
briefing run pulls every such message (`subject:DECISIONLOG in:anywhere
newer_than:3d`) not already logged and appends it verbatim, plus:

- `message_id` — the Gmail message id
- `subject` — the email subject line

These lines predate the `"source"` field, so **its absence means
`decisionlog_email`** — don't require the field, infer it. Fields beyond that
vary per message but commonly include `date`, `item`, `who`, `topic`,
`choice`, `why`, `draft`, `draft_to`.

**Deriving the email link for these lines:** Gmail thread URLs follow
`https://mail.google.com/mail/u/0/#all/<message_id>` — since every
`decisionlog_email` line carries `message_id`, the link is always derivable,
even though it isn't stored as its own field. An automated consumer should
build it with that formula rather than expect a `links` field here.

## `source: "session"`

Added when Toby and Claude work through items together in a live session
(e.g. the daily Punch List artifact). Explicit going forward — always set
`"source":"session"`.

Fields:

| field | type | meaning |
|---|---|---|
| `date` | string `YYYY-MM-DD` | date of the action, America/Chicago |
| `ts` | string, ISO 8601 UTC | timestamp of the action |
| `source` | `"session"` | always this literal for session-sourced lines |
| `item_id` | string | stable id matching the Punch List artifact's item `id` where applicable, else `null` |
| `item` | string | short title of the task/decision |
| `who` | string | person the item is about/for (customer, teammate, or `"Toby"`) |
| `topic` | string | one of: `quote`, `call`, `decision`, `ops`, `watch`, `other` |
| `action` | string | what happened: `status_change`, `note`, `decision`, `draft_created`, `email_sent`, `infra` |
| `status` | string or null | for `status_change`: `open` / `doing` / `done` |
| `choice` | string or null | the decision made, if any |
| `why` | string or null | reasoning, if worth capturing |
| `links` | array of `{label, url}` | **email links, populated directly** — unlike `decisionlog_email` lines, these are stored explicitly since a session item may reference an existing thread without generating a new message of its own |

## Automation note

A consumer that wants "every logged item with its email link" can do, per line:

```
url = line.links[0].url                                          if source == "session" and links
url = f"https://mail.google.com/mail/u/0/#all/{line.message_id}"  if source == "decisionlog_email" (or source absent)
```
