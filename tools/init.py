#!/usr/bin/env python3
"""Harness status at session start. Run from the SessionStart hook.

Prints what the agent needs to know BEFORE its first reply: whether there are
credentials, whether the voice profile is populated, when the channel was last
measured. Without this, it finds out halfway through an answer.

It never fails: if something goes wrong it reports it as a notice. A hook that
crashes blocks the session from starting.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import auth, cache  # noqa: E402
from lib.contract import (BASE_DIR, CONFIG_DIR, DATA_DIR,  # noqa: E402
                          MEMORY_DIR)

SNAPSHOTS = DATA_DIR / "history" / "snapshots.jsonl"


def dias_desde(date: str) -> int | None:
    try:
        return (datetime.now() - datetime.strptime(date, "%Y-%m-%d")).days
    except Exception:  # noqa: BLE001
        return None


def main() -> None:
    lines = ["=== YouTube coach harness ==="]
    warnings = []

    # Credentials
    try:
        est = auth.status()
        lines.append(f"Credentials: {'OK' if est['ok'] else 'NO'} — {est['reason']}")
        if not est["ok"]:
            warnings.append(est.get("hint", ""))
    except Exception as e:  # noqa: BLE001
        lines.append(f"Credentials: could not verify ({e})")

    # Last channel snapshot
    if SNAPSHOTS.exists():
        try:
            rows = [l for l in SNAPSHOTS.read_text(encoding="utf-8").splitlines()
                     if l.strip()]
            last = json.loads(rows[-1])
            d = dias_desde(last["date"])
            freshness = "hoy" if d == 0 else f"hace {d} days"
            lines.append(
                f"Last snapshot: {last['date']} ({freshness}) — "
                f"{last['subs']} subs, {last['views']} views/"
                f"{last['window_days']}d · {len(rows)} snapshots en total")
            if d is not None and d > 14:
                warnings.append("Channel data is more than 2 weeks old: "
                              "run `python3 tools/yt_report.py` before "
                              "afirmar cifras.")
        except Exception as e:  # noqa: BLE001
            lines.append(f"Last snapshot: unreadable ({e})")
    else:
        lines.append("Last snapshot: none yet")
        warnings.append("No baseline yet. Run `python3 tools/yt_report.py` "
                      "to get your own data.")

    # Voice profile — the scripting skill depends on it
    voz = MEMORY_DIR / "voice_profile.md"
    if voz.exists():
        body = voz.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        words = len(body.split())
        # The placeholder explains how to fill it and runs ~160 words, so
        # counting length alone would give a false "populated". The explicit
        # marker wins.
        populated = "NOT POPULATED" not in body.upper() and "SIN POBLAR" not in body.upper() and words > 150
        lines.append(f"Voice profile: {'populated' if populated else 'EMPTY'} "
                      f"({words} words)")
        if not populated:
            warnings.append("The voice profile is empty. The scripting skill must build "
                          "it from real transcripts before writing, not invent "
                          "it.")
    else:
        lines.append("Voice profile: does not exist")

    # Real CTR from Studio — without it the rubrics stay unvalidated
    ctr = DATA_DIR / "history" / "studio_ctr.json"
    if ctr.exists():
        try:
            n = len(json.loads(ctr.read_text(encoding="utf-8"))["videos"])
            lines.append(f"Studio CTR: {n} videos ingested")
        except Exception:  # noqa: BLE001
            lines.append("Studio CTR: file unreadable")
    else:
        lines.append("Studio CTR: not ingested — the scoring rubrics remain "
                      "UNVALIDATED against real CTR")

    # Initial configuration — the step people skip and the one that hurts
    # most. A harness with no identity filled in gives textbook advice, which
    # is exactly what this project exists not to do.
    unconfigured = []
    contract = BASE_DIR / "CLAUDE.md"
    if contract.exists() and "[CHANNEL TOPIC]" in contract.read_text(encoding="utf-8"):
        unconfigured.append("section 1 of CLAUDE.md (channel identity)")
    channel_cfg = CONFIG_DIR / "config.json"
    if channel_cfg.exists():
        try:
            if not json.loads(channel_cfg.read_text(encoding="utf-8")).get("channel_context"):
                unconfigured.append("`channel_context` in config/config.json")
        except Exception:  # noqa: BLE001
            unconfigured.append("config/config.json (unreadable)")
    if unconfigured:
        lines.append("Configuration: NOT PERSONALISED")
        warnings.append(
            "INSTALLATION NOT PERSONALISED. Still to fill in: "
            + "; ".join(unconfigured)
            + ". Until that is done the agent does not know what your channel "
              "is about and will give generic advice. See step 4 of the README.")
    else:
        lines.append("Configuration: personalised")

    # Image provider — the visual branch needs a live one
    prov_cfg = CONFIG_DIR / "image_providers.json"
    if prov_cfg.exists():
        try:
            pc = json.loads(prov_cfg.read_text(encoding="utf-8"))
            provider = pc.get("provider")
            if provider == "fal":
                has_key = bool(os.environ.get(
                    pc["fal"].get("key_env", "FAL_KEY"), "").strip())
                lines.append(f"Image: fal.ai provider — "
                              f"{'key OK' if has_key else 'NO KEY'}")
                if not has_key:
                    warnings.append(
                        "No FAL_KEY: the visual branch only works in "
                        "--dry-run. Put FAL_KEY in your .env (see .env.example) "
                        "and start a new session.")
                no_slug = [k for k in ("generate", "edit")
                            if not pc["fal"]["models"].get(k)]
                if no_slug:
                    warnings.append(
                        f"Unresolved model slugs: {', '.join(no_slug)}. "
                        "The gpt-image-2 fallback will be used; to use another model, "
                        "write its slug in config/image_providers.json.")
            else:
                lines.append(f"Image: provider {provider} (via MCP) — "
                              "the tool returns the call, it does not generate")
        except Exception:  # noqa: BLE001
            lines.append("Image: configuration unreadable")

    # Cache
    try:
        c = cache.status()
        lines.append(f"Cache: {c['entries']} entries {c['families'] or ''}")
    except Exception:  # noqa: BLE001
        pass

    if warnings:
        lines.append("\nWarnings:")
        lines += [f"  - {a}" for a in warnings if a]

    lines.append(f"\nContract: {BASE_DIR / 'CLAUDE.md'} · "
                  f"Tools: {BASE_DIR / 'TOOLS.md'} · "
                  f"Limits: {BASE_DIR / 'LIMITS.md'}")
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — a hook must never break the session
        print(f"[init] Could not build the status line: {e}")
