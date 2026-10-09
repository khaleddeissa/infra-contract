"""Terminal branding inspired by the README's hexagon, nodes, braces, and checkmark."""

from __future__ import annotations

import os
import sys

LOGO = (
    "        o\n"
    "      / | \\\n"
    "    o---+---o\n"
    "    |  {v}  |   infra-contract\n"
    "    o---+---o\n"
    "      \\ | /\n"
    "        o"
)
COMMUNITY_MESSAGE = (
    f"{LOGO}\n\n"
    "Thanks for using infra-contract!\n"
    "If it helps you, a GitHub star or feedback would be much appreciated.\n"
    "Star: https://github.com/khaleddeissa/infra-contract\n"
    "Feedback: https://github.com/khaleddeissa/infra-contract/issues"
)
_shown = False


def show_community_message() -> None:
    """Print once on terminal stderr; INFRA_CONTRACT_NO_BANNER=1 silences it."""
    global _shown
    if _shown or os.environ.get("INFRA_CONTRACT_NO_BANNER") == "1":
        return
    if sys.stderr is None or not sys.stderr.isatty():
        return
    try:
        print(COMMUNITY_MESSAGE, file=sys.stderr)
    except OSError:
        return
    _shown = True
