#!/usr/bin/env python3
"""Copy new/changed output files from Claude Code sessions into a synced folder.

Layout produced (one folder per project/repo):

    <dest_root>/<repo>/              reports & writeups (pdf, docx, pptx, html, md in report dirs)
    <dest_root>/<repo>/figures/      images, plus PDFs/HTML that are clearly charts
    <dest_root>/<repo>/data/         xlsx / xls / csv / tsv (size-capped)

Usage
    sync_outputs.py hook              called by Claude Code hooks (reads hook JSON on stdin,
                                      hands off to a detached background worker, exits at once)
    sync_outputs.py backfill [DIR]    copy every qualifying file in DIR's project now
    sync_outputs.py dry-run [DIR]     show where each qualifying file would go
    sync_outputs.py status            show config, log location, known projects

Guarantees: never deletes anything, never blocks Claude Code (the hook process always
exits 0 within milliseconds; all work happens in a detached process), errors only go
to the log file. Set CLAUDE_OUTPUT_SYNC=0 to disable temporarily.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

HOME = Path.home()
STATE_DIR = HOME / ".claude" / "output-sync"
CONFIG_PATH = STATE_DIR / "config.json"
LOG_PATH = STATE_DIR / "sync.log"

MB = 1024 * 1024

DEFAULT_CONFIG = {
    # Where copies go. Point this at a folder Google Drive for Desktop syncs.
    "dest_root": str(HOME / "ClaudeOutputs"),
    # Subfolder (inside each repo folder) for each category. "" = repo folder itself.
    "folders": {"reports": "", "figures": "figures", "data": "data"},
    "extensions": {
        "figures": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".tif", ".tiff", ".eps", ".bmp"],
        "data": [".xlsx", ".xls", ".xlsm", ".csv", ".tsv"],
        # pdf/html are reports unless they look like a figure (see FIGURE_* below)
        "reports": [".pdf", ".html", ".htm", ".docx", ".doc", ".pptx", ".odt", ".rtf"],
        # markdown is copied only when it sits under one of report_dir_names
        "markdown": [".md"],
    },
    "max_mb": {"figures": 50, "data": 20, "reports": 100},
    # Directory names that mark PDF/HTML as figures.
    "figure_dir_names": ["figures", "figure", "figs", "fig", "plots", "plot", "charts", "chart",
                         "graphs", "images", "img"],
    # Directory names whose .md files count as writeups.
    "report_dir_names": ["reports", "report", "writeups", "writeup", "papers", "paper",
                         "drafts", "draft", "memos", "memo", "notes"],
    # Directories never scanned (any depth). Hidden dirs (starting with ".") are always skipped,
    # as are virtualenvs/conda envs (detected by pyvenv.cfg / conda-meta) and nested JS projects.
    "skip_dirs": ["node_modules", "__pycache__", "venv", "env", "site-packages", "dist", "build",
                  "htmlcov", "coverage", "target", "public", "static", "wandb", "mlruns",
                  "lightning_logs", "raw", "interim", "external"],
    # Extra glob patterns (matched against the repo-relative path, "/" separators) to ignore.
    "skip_globs": [],
    # When a project is first seen mid-session, files changed within this many minutes are
    # copied; older ones are just recorded (use `backfill` to copy those too).
    "first_seen_window_min": 120,
    "max_scan_entries": 200000,
}

FIGURE_NAME_RE = re.compile(r"(^|[_\-\s.])(fig|figs|figure|plot|chart|graph|heatmap)", re.I)
TEMP_NAME_RE = re.compile(r"^(~\$|\.~lock|\.)|(\.tmp|\.part|\.crdownload|~)$", re.I)


# ----------------------------------------------------------------------------- utilities

def log(msg: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > 1 * MB:
            os.replace(LOG_PATH, LOG_PATH.with_suffix(".log.1"))
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except Exception:
        pass


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    except FileNotFoundError:
        pass
    except Exception as e:
        log(f"config.json unreadable, using defaults: {e}")
    return cfg


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def norm(p: Path) -> str:
    s = str(p.resolve())
    return s.lower() if os.name == "nt" else s


def find_project_root(start: Path) -> Path | None:
    """Nearest ancestor containing .git; None if there is none."""
    p = start.resolve()
    for cand in (p, *p.parents):
        if (cand / ".git").exists():
            return cand
    return None


def too_broad(p: Path) -> bool:
    """Never scan the home directory, a drive root, or the destination tree itself."""
    p = p.resolve()
    return p == HOME.resolve() or p.parent == p or len(p.parts) <= 2


# ----------------------------------------------------------------------------- classification

def classify(path: Path, root: Path | None, cfg: dict) -> str | None:
    name = path.name
    if TEMP_NAME_RE.search(name):
        return None
    ext = path.suffix.lower()
    ex = cfg["extensions"]
    try:
        rel_parts = path.relative_to(root).parts[:-1] if root else path.parts[-3:-1]
    except ValueError:
        rel_parts = path.parts[-3:-1]
    dirs = {d.lower() for d in rel_parts}

    if ext in ex["figures"]:
        return "figures"
    if ext in ex["data"]:
        return "data"
    if ext in ex["markdown"]:
        return "reports" if dirs & set(cfg["report_dir_names"]) else None
    if ext in ex["reports"]:
        if ext in (".pdf", ".html", ".htm", ".svg"):
            if dirs & set(cfg["figure_dir_names"]) or FIGURE_NAME_RE.search(path.stem):
                return "figures"
            # A PDF/HTML saved next to an image of the same name is a figure export.
            for img in (".png", ".jpg", ".jpeg", ".svg"):
                if path.with_suffix(img).exists():
                    return "figures"
        return "reports"
    return None


def qualifies(path: Path, root: Path | None, cfg: dict, st=None) -> str | None:
    cat = classify(path, root, cfg)
    if not cat:
        return None
    if root:
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.name
        if any(fnmatch.fnmatch(rel, g) for g in cfg["skip_globs"]):
            return None
    try:
        st = st or path.stat()
    except OSError:
        return None
    if st.st_size == 0 or st.st_size > cfg["max_mb"].get(cat, 50) * MB:
        return None
    return cat


def skip_dir(d: Path, name: str, cfg: dict) -> bool:
    if name.startswith(".") or name.lower() in {s.lower() for s in cfg["skip_dirs"]}:
        return True
    if (d / "pyvenv.cfg").exists() or (d / "conda-meta").exists():
        return True
    if (d / "package.json").exists():  # nested JS app (e.g. a dashboard): source, not outputs
        return True
    return False


def scan(root: Path, cfg: dict):
    """Yield (path, stat, category) for qualifying files under root, with pruning."""
    dest = Path(cfg["dest_root"]).resolve()
    stack, seen = [root], 0
    while stack:
        d = stack.pop()
        try:
            it = os.scandir(d)
        except OSError:
            continue
        with it:
            for e in it:
                seen += 1
                if seen > cfg["max_scan_entries"]:
                    log(f"scan of {root} stopped at {seen} entries (max_scan_entries)")
                    return
                try:
                    if e.is_dir(follow_symlinks=False):
                        p = Path(e.path)
                        if not skip_dir(p, e.name, cfg) and p.resolve() != dest:
                            stack.append(p)
                    elif e.is_file(follow_symlinks=False):
                        p = Path(e.path)
                        st = e.stat()
                        cat = qualifies(p, root, cfg, st)
                        if cat:
                            yield p, st, cat
                except OSError:
                    continue


# ----------------------------------------------------------------------------- project state

class Project:
    def __init__(self, root: Path, cfg: dict, dest_name: str | None = None):
        self.root = root
        self.cfg = cfg
        self.key = hashlib.sha1(norm(root).encode()).hexdigest()[:12]
        self.state_path = STATE_DIR / "projects" / f"{self.key}.json"
        self.lock_path = STATE_DIR / "projects" / f"{self.key}.lock"
        self.pending_path = STATE_DIR / "projects" / f"{self.key}.pending"
        self.state = read_json(self.state_path, None)
        self.is_new = self.state is None
        if self.is_new:
            self.state = {"root": str(root), "dest_name": dest_name or self._claim_name(),
                          "files": {}, "owners": {}}

    def _claim_name(self) -> str:
        """Destination folder name = repo name; disambiguate if another root already uses it."""
        reg_path = STATE_DIR / "registry.json"
        reg = read_json(reg_path, {})
        base = re.sub(r'[<>:"/\\|?*]', "_", self.root.name) or "project"
        name, n = base, 1
        while name in reg and reg[name] != norm(self.root):
            n += 1
            name = f"{base} ({self.root.parent.name})" if n == 2 else f"{base} ({n})"
        reg[name] = norm(self.root)
        write_json(reg_path, reg)
        return name

    @property
    def dest_dir(self) -> Path:
        return Path(self.cfg["dest_root"]) / self.state["dest_name"]

    def rel(self, p: Path) -> str:
        try:
            return p.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return "@ext/" + p.resolve().as_posix()

    def dest_for(self, p: Path, cat: str) -> Path:
        rel = self.rel(p)
        rec = self.state["files"].get(rel, {})
        sub = self.cfg["folders"].get(cat, cat)
        if rec.get("dest") and rec.get("cat") == cat:
            return self.dest_dir / rec["dest"]
        owners = self.state["owners"]
        parts = [x for x in Path(rel.replace("@ext/", "")).parts[:-1]
                 if not any(c in x for c in ":/\\")]
        name = p.name
        # Flatten; on a name clash with a different source, prefix parent folder names.
        while True:
            key = (sub + "/" + name).lstrip("/")
            if owners.get(key.lower(), rel) == rel:
                owners[key.lower()] = rel
                return self.dest_dir / key
            if not parts:
                stem, suf = os.path.splitext(name)
                name = f"{stem}_{hashlib.sha1(rel.encode()).hexdigest()[:6]}{suf}"
                continue
            name = f"{parts.pop()}__{name}"

    def lock(self) -> bool:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
            except FileExistsError:
                try:
                    if time.time() - self.lock_path.stat().st_mtime > 600:  # stale
                        self.lock_path.unlink()
                        continue
                except OSError:
                    pass
                return False
        return False

    def unlock(self) -> None:
        try:
            self.lock_path.unlink()
        except OSError:
            pass

    def save(self) -> None:
        write_json(self.state_path, self.state)


def copy_one(proj: Project, p: Path, st, cat: str, rel: str) -> bool:
    dest = proj.dest_for(p, cat)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.{os.getpid()}.part")
    try:
        shutil.copy2(p, tmp)
        st2 = p.stat()
        if (st2.st_mtime_ns, st2.st_size) != (st.st_mtime_ns, st.st_size):
            tmp.unlink(missing_ok=True)  # still being written; next scan picks it up
            return False
        os.replace(tmp, dest)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        log(f"copy failed {p} -> {dest}: {e}")
        return False
    proj.state["files"][rel] = {"m": st.st_mtime_ns, "s": st.st_size, "cat": cat,
                                "dest": dest.relative_to(proj.dest_dir).as_posix()}
    log(f"copied {rel} -> {proj.state['dest_name']}/{proj.state['files'][rel]['dest']}")
    return True


def process(proj: Project, event: str, direct: list[Path], mode: str = "normal") -> int:
    """mode: normal | baseline (record only) | backfill (copy everything not yet copied)."""
    cfg, files = proj.cfg, proj.state["files"]
    copied = 0
    cutoff = time.time() - cfg["first_seen_window_min"] * 60
    if proj.is_new and mode == "normal":
        mode = "baseline" if event == "SessionStart" else "first_seen"

    candidates: dict[str, tuple] = {}
    for p in direct:
        try:
            st = p.stat()
        except OSError:
            continue
        cat = qualifies(p, proj.root, cfg, st)
        if cat:
            candidates[proj.rel(p)] = (p, st, cat, True)
    for p, st, cat in scan(proj.root, cfg):
        candidates.setdefault(proj.rel(p), (p, st, cat, False))

    for rel, (p, st, cat, is_direct) in candidates.items():
        rec = files.get(rel)
        changed = rec is None or rec.get("m") != st.st_mtime_ns or rec.get("s") != st.st_size \
            or rec.get("cat") != cat
        if mode == "backfill":
            changed = changed or not rec.get("dest")
        if not changed:
            continue
        record_only = (mode == "baseline" and not is_direct) or \
                      (mode == "first_seen" and not is_direct and st.st_mtime < cutoff)
        if record_only:
            files[rel] = {"m": st.st_mtime_ns, "s": st.st_size, "cat": cat, "dest": None}
            continue
        if copy_one(proj, p, st, cat, rel):
            copied += 1
    proj.is_new = False
    proj.save()
    return copied


# ----------------------------------------------------------------------------- entry points

def worker(payload: dict) -> None:
    cfg = load_config()
    cwd = Path(payload.get("cwd") or os.getcwd())
    direct = [Path(p) if os.path.isabs(p) else cwd / p for p in payload.get("paths", [])]
    root = find_project_root(cwd)
    if root is None:
        if too_broad(cwd):
            if not direct:
                return
            root = None
        else:
            root = cwd.resolve()
    if root is None:  # no project: copy direct writes only, into _misc
        root = STATE_DIR / "_misc_root"
        root.mkdir(parents=True, exist_ok=True)
        proj = Project(root, cfg, dest_name="_misc")
        for p in direct:
            try:
                st = p.stat()
            except OSError:
                continue
            cat = qualifies(p, None, cfg, st)
            if cat:
                copy_one(proj, p, st, cat, proj.rel(p))
        proj.save()
        return

    proj = Project(root, cfg)
    if not proj.lock():
        # Someone else is syncing this project: leave a note so they run one more pass.
        with open(proj.pending_path, "a", encoding="utf-8") as f:
            for p in direct:
                f.write(str(p) + "\n")
        return
    try:
        event = payload.get("event", "")
        for _ in range(5):
            process(proj, event, direct)
            if not proj.pending_path.exists():
                break
            try:
                extra = proj.pending_path.read_text(encoding="utf-8").splitlines()
                proj.pending_path.unlink()
            except OSError:
                extra = []
            direct = [Path(x) for x in extra if x.strip()]
            event = ""
            proj = Project(root, cfg)  # reload state
    finally:
        proj.unlock()


def spawn_worker(payload: dict) -> None:
    exe = Path(sys.executable)
    kwargs = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                  close_fds=True, cwd=str(STATE_DIR))
    if os.name == "nt":
        pyw = exe.with_name("pythonw.exe")
        if pyw.exists():
            exe = pyw
        kwargs["creationflags"] = 0x08000000 | 0x00000200 | 0x00000008  # NO_WINDOW|NEW_GROUP|DETACHED
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([str(exe), str(Path(__file__).resolve()), "worker", json.dumps(payload)],
                     **kwargs)


def hook_main() -> None:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        data = {}
    ti = data.get("tool_input") or {}
    paths = [ti[k] for k in ("file_path", "notebook_path") if isinstance(ti.get(k), str)]
    payload = {"event": data.get("hook_event_name", ""), "cwd": data.get("cwd") or os.getcwd(),
               "tool": data.get("tool_name", ""), "paths": paths}
    # Direct write of a file type we never copy (e.g. .py): nothing to do, skip the worker.
    if payload["tool"] in ("Write", "Edit", "MultiEdit", "NotebookEdit") and paths:
        cfg = load_config()
        if not any(classify(Path(p), None, cfg) for p in paths):
            return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    spawn_worker(payload)


def cli_target(argv: list[str]) -> Project:
    cfg = load_config()
    start = Path(argv[0]) if argv else Path.cwd()
    root = find_project_root(start) or start.resolve()
    if too_broad(root):
        sys.exit(f"Refusing to scan {root} (home directory or drive root). cd into a project.")
    return Project(root, cfg)


def main() -> None:
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "hook"
    if cmd == "hook":
        if os.environ.get("CLAUDE_OUTPUT_SYNC", "1") == "0":
            return
        try:
            hook_main()
        except Exception:
            log("hook error:\n" + traceback.format_exc())
        return  # always exit 0, print nothing
    if cmd == "worker":
        try:
            worker(json.loads(argv[1]))
        except Exception:
            log("worker error:\n" + traceback.format_exc())
        return
    if cmd == "backfill":
        proj = cli_target(argv[1:])
        if not proj.lock():
            sys.exit("A sync is running for this project; try again in a moment.")
        try:
            n = process(proj, "", [], mode="backfill")
        finally:
            proj.unlock()
        print(f"Copied {n} file(s) to {proj.dest_dir}")
        return
    if cmd == "dry-run":
        proj = cli_target(argv[1:])
        rows = sorted((cat, proj.rel(p)) for p, st, cat in scan(proj.root, proj.cfg))
        for cat, rel in rows:
            sub = proj.cfg["folders"].get(cat, cat)
            print(f"{(sub or '.') + '/':10} {rel}")
        print(f"\n{len(rows)} file(s) would sync to {proj.dest_dir}")
        return
    if cmd == "status":
        cfg = load_config()
        print(f"destination : {cfg['dest_root']}")
        print(f"config      : {CONFIG_PATH} ({'present' if CONFIG_PATH.exists() else 'defaults'})")
        print(f"log         : {LOG_PATH}")
        for name, root in sorted(read_json(STATE_DIR / 'registry.json', {}).items()):
            print(f"project     : {name:30} <- {root}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
