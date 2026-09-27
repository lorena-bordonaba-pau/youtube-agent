#!/usr/bin/env python3
"""PreToolUse hook for youtube-strategist: it may only write inside memory/.

The strategist needs Write/Edit to keep `memory/channel_positioning.md` up to
date, and nothing else. Tools, skills, config and this contract are not its
business, so a write anywhere else is blocked (exit 2) and the reason goes
back to the agent.
"""
import json
import os
import sys
from pathlib import Path


def main() -> None:
    try:
        event = json.load(sys.stdin)
        target = event.get("tool_input", {}).get("file_path", "")
    except Exception:  # noqa: BLE001 — malformed input: stay out of the way
        return
    if not target:
        return
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    memory = (root / "memory").resolve()
    path = Path(target)
    if not path.is_absolute():
        path = root / path
    if path.resolve().is_relative_to(memory):
        return
    print(f"youtube-strategist may only write inside {memory}; "
          f"refused: {target}. Hand anything else back to the main agent.",
          file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
