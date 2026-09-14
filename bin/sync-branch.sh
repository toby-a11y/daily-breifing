#!/usr/bin/env bash
# Execute the trunk discipline in ROUTINE.md's REPO section as a tested command
# instead of improvised prose. Trunk is origin/main — that rule is canonical and
# this script does not second-guess it.
#
#   bin/sync-branch.sh            fetch; fast-forward onto origin/main when safe
#   bin/sync-branch.sh --check    report only, change nothing
#   bin/sync-branch.sh --verify   after pushing: did today's work actually land on main?
#
# Exit: 0 fine · 2 diverged / did not land (needs a human) · 3 no trunk
set -euo pipefail

MODE="${1:-sync}"
cd "$(git rev-parse --show-toplevel)"

fetch() {
  for attempt in 1 2 3 4; do
    git fetch origin --prune --quiet 2>/dev/null && return 0
    [ "$attempt" = 4 ] && return 1
    sleep $((2 ** attempt))
  done
}

fetch || { echo "!! fetch failed after 4 attempts"; exit 3; }

if ! git rev-parse --verify --quiet origin/main >/dev/null; then
  echo "!! origin/main does not exist — per ROUTINE.md, stop and say so in the briefing."
  exit 3
fi

TRUNK=$(git rev-parse origin/main)
HEAD_SHA=$(git rev-parse HEAD)
CUR=$(git rev-parse --abbrev-ref HEAD)

# --verify: the post-push ancestry check the REPO section asks for. A run that
# pushed to its own branch instead of main looks successful but delivers nothing,
# which is exactly how this repo reached ten branches and no trunk.
if [ "$MODE" = "--verify" ]; then
  TODAY=$(TZ=America/Chicago date +%F)
  echo "→ verifying $TODAY landed on origin/main"
  if ! git merge-base --is-ancestor "$HEAD_SHA" "$TRUNK"; then
    echo "!! HEAD (${HEAD_SHA:0:7}) is NOT an ancestor of origin/main — the work did NOT land."
    echo "   Re-push with: git push origin HEAD:main"
    exit 2
  fi
  # Check what this run actually produced, not what a run is supposed to produce:
  # every today-dated file present in the working tree must also be on the trunk.
  # A non-briefing commit has none, and correctly passes on ancestry alone.
  MISSING=""; CHECKED=0
  for f in "briefings/$TODAY.md" "health/$TODAY.json" "board/$TODAY.json" \
           "decisions/$TODAY.jsonl" "worklists/$TODAY.txt"; do
    [ -f "$f" ] || continue
    CHECKED=$((CHECKED + 1))
    git cat-file -e "origin/main:$f" 2>/dev/null || MISSING="$MISSING $f"
  done
  if [ -n "$MISSING" ]; then
    echo "!! on trunk, but these local files are NOT on origin/main:$MISSING"
    echo "   Commit them and re-push with: git push origin HEAD:main"
    exit 2
  fi
  if [ "$CHECKED" = 0 ]; then
    echo "✓ on trunk (no $TODAY-dated deliverables in the working tree to check)"
  else
    echo "✓ on trunk, and all $CHECKED today-dated file(s) are present on origin/main"
  fi
  exit 0
fi

echo "→ trunk:   origin/main (${TRUNK:0:7})"
echo "→ current: $CUR (${HEAD_SHA:0:7})"

if [ "$HEAD_SHA" = "$TRUNK" ]; then
  echo "✓ current with trunk"
  exit 0
fi

if git merge-base --is-ancestor "$TRUNK" "$HEAD_SHA"; then
  echo "✓ ahead of trunk by $(git rev-list --count "$TRUNK..$HEAD_SHA") commit(s) — unpushed work, push with: git push origin HEAD:main"
  exit 0
fi

if git merge-base --is-ancestor "$HEAD_SHA" "$TRUNK"; then
  BEHIND=$(git rev-list --count "$HEAD_SHA..$TRUNK")
  echo "!! DRIFT: behind trunk by $BEHIND commit(s)"
  git log --oneline "$HEAD_SHA..$TRUNK" | head -15 | sed 's/^/     /'
  if [ "$MODE" = "--check" ]; then
    echo "   (--check: not fast-forwarding)"
    exit 0
  fi
  echo "→ fast-forwarding (safe: HEAD is a strict ancestor, nothing can be lost)"
  git merge --ff-only origin/main --quiet
  echo "✓ synced to $(git rev-parse --short HEAD)"
  exit 0
fi

# Diverged: real local commits the trunk lacks. Never force, rebase or discard.
echo "!! DIVERGED from trunk — NOT changing anything."
echo "   local-only:"; git log --oneline "$TRUNK..$HEAD_SHA" | sed 's/^/     /'
echo "   trunk-only:"; git log --oneline "$HEAD_SHA..$TRUNK" | head -15 | sed 's/^/     /'
echo "   Per ROUTINE.md: git rebase origin/main, then push again."
exit 2
