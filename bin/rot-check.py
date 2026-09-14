#!/usr/bin/env python3
"""Turn the staleness ledger into an escalation, so decay changes the report's shape.

See ROT.md. The point is narrow: age must live in a file, not in a sentence, and
crossing a threshold must change what the briefing is obliged to do about it.

    bin/rot-check.py                    # newest health/ file
    bin/rot-check.py --date 2026-09-13  # a specific day
    bin/rot-check.py --carry            # seed today from the newest file
    bin/rot-check.py --json             # machine-readable

Exit: 0 nothing above warn · 1 some escalate · 2 some blocker
"""
import argparse, datetime as dt, json, pathlib, sys
from zoneinfo import ZoneInfo

# Every date in this routine is America/Chicago (ROUTINE.md). Using the host's
# local date would silently shift ages by a day whenever the box runs UTC, which
# it does — an off-by-one that lands exactly on the threshold boundaries.
TZ = ZoneInfo("America/Chicago")


def today_chicago():
    return dt.datetime.now(TZ).date()


ROOT = pathlib.Path(__file__).resolve().parent.parent
HEALTH = ROOT / "health"
STATES = ["ok", "warn", "escalate", "blocker"]
DEFAULT_THRESHOLDS = {"warn": 3, "escalate": 7, "blocker": 14}

# What the briefing is REQUIRED to do at each state. Printed with the report so the
# obligation travels with the finding instead of living only in ROT.md.
DUTY = {
    "ok":       "say nothing",
    "warn":     "one line in its section; may stay rolled up",
    "escalate": "PROMOTE out of any roll-up into its own action item, owner named, age in days",
    "blocker":  "LEAD the briefing: fix it, reassign it, or consciously retire it",
}


def load(path):
    with open(path) as f:
        return json.load(f)


def newest_health():
    files = sorted(HEALTH.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json"))
    return files[-1] if files else None


def classify(age_days, thresholds):
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    for state in ("blocker", "escalate", "warn"):
        if age_days >= t[state]:
            return state
    return "ok"


def evaluate(doc, today):
    rows = []
    for sig in doc.get("signals", []):
        if sig.get("retired"):
            continue
        last = dt.date.fromisoformat(sig["last_change"])
        age = (today - last).days
        rows.append({
            "id": sig["id"],
            "label": sig.get("label", sig["id"]),
            "kind": sig.get("kind", "source"),
            "owner": sig.get("owner"),
            "age_days": age,
            "last_change": sig["last_change"],
            "state": classify(age, sig.get("thresholds")),
            "evidence": sig.get("evidence", ""),
        })
    rows.sort(key=lambda r: (-STATES.index(r["state"]), -r["age_days"]))
    return rows


def render(rows, today):
    out = [f"## Rot watch — {today.isoformat()}", ""]
    worst = max((STATES.index(r["state"]) for r in rows), default=0)

    if worst == 0:
        out += ["Nothing above `warn`. No rot section in the briefing today.", ""]
        return "\n".join(out)

    for state in ("blocker", "escalate", "warn"):
        group = [r for r in rows if r["state"] == state]
        if not group:
            continue
        out += [f"**{state.upper()}** — {DUTY[state]}", ""]
        for r in group:
            owner = r["owner"] or "**NO OWNER** (cannot resolve — assign one)"
            out.append(f"- `{r['id']}` — {r['label']} — **{r['age_days']}d** "
                       f"(since {r['last_change']}) · owner: {owner}")
            if r["evidence"]:
                out.append(f"  - {r['evidence']}")
        out.append("")

    ok = [r for r in rows if r["state"] == "ok"]
    if ok:
        out.append(f"_{len(ok)} signal(s) below threshold, deliberately not reported: "
                   + ", ".join(f"`{r['id']}`" for r in ok) + "._")
    return "\n".join(out)


def carry(today):
    """Seed today's ledger from the newest one. last_change is NEVER advanced here:
    a new day does not mean anything moved. The run edits only what it can prove."""
    src = newest_health()
    if src is None:
        print("no existing health/ file to carry from", file=sys.stderr)
        return 3
    dst = HEALTH / f"{today.isoformat()}.json"
    if dst.exists():
        print(f"{dst.relative_to(ROOT)} already exists — not overwriting")
        return 0
    doc = load(src)
    doc["date"] = today.isoformat()
    doc["generated_at"] = None
    doc["carried_from"] = src.stem
    HEALTH.mkdir(exist_ok=True)
    dst.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"carried {len(doc.get('signals', []))} signal(s) "
          f"{src.stem} → {dst.stem} (last_change untouched)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--carry", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else today_chicago()

    if args.carry:
        return carry(today)

    path = HEALTH / f"{today.isoformat()}.json" if args.date else newest_health()
    if path is None or not path.exists():
        print(f"no health ledger found ({path})", file=sys.stderr)
        return 3

    doc = load(path)
    # Age against the real today, not the file's date, so a stale ledger still ages.
    rows = evaluate(doc, today_chicago())

    if args.json:
        print(json.dumps({"date": doc["date"], "signals": rows}, indent=2))
    else:
        print(render(rows, today_chicago()))

    worst = max((STATES.index(r["state"]) for r in rows), default=0)
    return {0: 0, 1: 0, 2: 1, 3: 2}[worst]


if __name__ == "__main__":
    sys.exit(main())
