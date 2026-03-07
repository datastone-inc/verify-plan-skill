#!/usr/bin/env python3
"""
Install the plan-implemented slash command.

Run this after cloning the repo into your Claude Code skills folder:

    python scripts/install_command.py

On all platforms this creates (or replaces) a symlink at:
    ~/.claude/commands/plan-implemented.md -> <this-repo>/commands/plan-implemented.md

On Windows, if symlink creation requires elevated privileges, it falls back to
copying the file instead.
"""

import os
import sys
import shutil
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / "commands" / "plan-implemented.md"

    if not src.exists():
        print(f"ERROR: command file not found at {src}", file=sys.stderr)
        sys.exit(1)

    commands_dir = Path.home() / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    dest = commands_dir / "plan-implemented.md"

    # Remove any existing file/symlink at the destination
    if dest.exists() or dest.is_symlink():
        dest.unlink()

    try:
        dest.symlink_to(src)
        print(f"Symlinked: {dest}")
        print(f"       -> {src}")
    except (OSError, NotImplementedError):
        # Windows without developer mode / elevated privileges
        shutil.copy2(src, dest)
        print(f"Copied (symlink unavailable): {dest}")

    print("\nDone. Restart Claude Code or start a new session to use /plan-implemented.")


if __name__ == "__main__":
    main()
