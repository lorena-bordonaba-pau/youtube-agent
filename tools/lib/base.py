"""Shared scaffolding for the tools: sys.path bootstrap and Markdown helpers."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_ROOT = Path(__file__).resolve().parent.parent.parent


def load_env(path: Path | None = None) -> list[str]:
    """Load the project root's `.env` into the process environment.

    No dependency: `python-dotenv` is not in requirements and this is twenty
    lines. A variable already present in the real environment is **not
    overwritten**, so exporting it in your shell still wins over the file.

    Returns the names it loaded, never the values: no key should ever end up
    in a log or in a tool's output.
    """
    import os

    file = path or _ROOT / ".env"
    loaded = []
    if not file.exists():
        return loaded
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and not os.environ.get(key):
            os.environ[key] = value
            loaded.append(key)
    return loaded


# Runs on import: every tool does `from lib import base`.
load_env()


def md_table(rows: list[dict], columns: list[str] | None = None) -> str:
    """Render a list of dicts as a Markdown table."""
    if not rows:
        return "_No data._"
    cols = columns or list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        cells = [str(r.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def md_header(envelope: dict) -> str:
    """Header that keeps a figure's provenance visible in Markdown too."""
    return (f"# {envelope['tool']}\n\n"
            f"**Source:** `{envelope['source']}` — {envelope['notice']}  \n"
            f"**Generated:** {envelope['generated_at']}"
            f"{' (cache)' if envelope['cache_hit'] else ''}\n")
