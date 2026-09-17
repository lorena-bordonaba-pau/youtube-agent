#!/usr/bin/env python3
"""Re-authorise Google access. INTERACTIVE: it opens a browser.

No other tool in the harness opens a browser. If a tool exits with code 2,
this is the command to run by hand.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import auth
from lib.contract import EXIT_OK, ToolError, fail

if __name__ == "__main__":
    try:
        creds = auth.get_credentials(interactive=True)
    except ToolError as e:
        fail(e, "auth_setup")
    print(f"Authorisation complete. Token saved to {auth.TOKEN_FILE}")
    print(f"Scopes granted: {len(auth.SCOPES)}")
    sys.exit(EXIT_OK)
