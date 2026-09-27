#!/usr/bin/env python3
"""PreToolUse hook: ask before a command spends money or quota.

`Bash(python3 tools/*)` is allowed wholesale, which is right for the 1-3 unit
reads but also lets an image generation spend fal.ai credits, or a search burn
100 of the 10,000 daily units, without anyone saying yes. This hook turns
exactly those calls back into a question. It never blocks: the creator decides.

It never fails either. Anything unexpected ends in exit 0 with no output,
which leaves the normal permission flow untouched.
"""
import json
import re
import sys

# (pattern the command must match, flag that makes it free, why it costs)
SPENDERS = [
    (r"tools/generate_image\.py", "--dry-run", "spends fal.ai credits"),
    (r"tools/refine_image\.py", "--dry-run", "spends fal.ai credits"),
    (r"tools/yt_search\.py", None, "costs 100 YouTube API units per query"),
    (r"tools/kw_research\.py", "--no-competition",
     "costs 100 YouTube API units per keyword (search.list)"),
]


def reason_for(command: str) -> str | None:
    for pattern, free_flag, why in SPENDERS:
        if re.search(pattern, command) and not (free_flag and free_flag in command):
            return why
    return None


def main() -> None:
    try:
        event = json.load(sys.stdin)
        command = event.get("tool_input", {}).get("command", "")
    except Exception:  # noqa: BLE001 — a hook must not break the session
        return
    why = reason_for(command)
    if not why:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": f"This command {why}. Run it?",
    }}))


if __name__ == "__main__":
    main()
