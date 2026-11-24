#!/usr/bin/env python3
"""Install (or remove) the Claude Code output-sync hook for the current user.

    python install.py                       install, destination ~/ClaudeOutputs
    python install.py --dest "G:/My Drive/ClaudeOutputs"
    python install.py --uninstall           remove the hooks (copied files are left alone)

What it does:
  * copies sync_outputs.py to ~/.claude/output-sync/
  * writes ~/.claude/output-sync/config.json (destination folder) if it doesn't exist yet
  * adds PostToolUse / Stop / SubagentStop / SessionStart hooks to ~/.claude/settings.json,
    after saving a timestamped backup of that file. Other settings are untouched.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
STATE_DIR = CLAUDE_DIR / "output-sync"
SETTINGS = CLAUDE_DIR / "settings.json"
MARK = "output-sync/sync_outputs.py"

EVENTS = {
    "PostToolUse": "Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell",
    "Stop": None,
    "SubagentStop": None,
    "SessionStart": None,
}


def is_ours(group: dict) -> bool:
    return any(MARK in (h.get("command") or "").replace("\\", "/") for h in group.get("hooks", []))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", help="folder to copy outputs into (default ~/ClaudeOutputs)")
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args()

    settings = {}
    if SETTINGS.exists():
        try:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"{SETTINGS} is not valid JSON ({e}); fix it first, nothing changed.")
        backup = SETTINGS.with_name(f"settings.json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(SETTINGS, backup)
        print(f"Backed up settings to {backup}")

    hooks = settings.setdefault("hooks", {})
    for ev in EVENTS:  # drop any previous copy of our hooks (idempotent)
        if ev in hooks:
            hooks[ev] = [g for g in hooks[ev] if not is_ours(g)]
            if not hooks[ev]:
                del hooks[ev]

    if not args.uninstall:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        script = STATE_DIR / "sync_outputs.py"
        shutil.copy2(Path(__file__).with_name("sync_outputs.py"), script)
        cfg_path = STATE_DIR / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        if args.dest or "dest_root" not in cfg:
            cfg["dest_root"] = str(Path(args.dest).expanduser() if args.dest else HOME / "ClaudeOutputs")
            cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        Path(cfg["dest_root"]).mkdir(parents=True, exist_ok=True)

        py = Path(sys.executable).as_posix()
        cmd = f'"{py}" "{script.as_posix()}" hook'
        for ev, matcher in EVENTS.items():
            group = {"hooks": [{"type": "command", "command": cmd, "timeout": 10}]}
            if matcher:
                group = {"matcher": matcher, **group}
            hooks.setdefault(ev, []).append(group)
        print(f"Installed hook script : {script}")
        print(f"Copies will go to     : {cfg['dest_root']}")
        print(f"Hook command          : {cmd}")
    if not hooks:
        settings.pop("hooks", None)

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print("Hooks removed from" if args.uninstall else "Hooks added to", SETTINGS)
    print("Restart open Claude Code sessions (or run /hooks) so they pick up the change.")


if __name__ == "__main__":
    main()
