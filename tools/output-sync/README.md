# Claude Code output sync

A user-level Claude Code hook that copies new or changed output files from any project into a folder
that Google Drive for Desktop syncs, sorted by type:

```
ClaudeOutputs\<repo>\            reports & writeups: .pdf .docx .pptx .html, .md under reports/ writeups/ papers/ drafts/ notes/
ClaudeOutputs\<repo>\figures\    images (.png .jpg .svg …), plus PDFs/HTML that are clearly charts*
ClaudeOutputs\<repo>\data\       .xlsx .xls .csv .tsv (≤ 20 MB)
```

\* A PDF or HTML file counts as a figure when it sits in a `figures/`/`plots/`/`charts/`… folder, has
fig/plot/chart/graph/heatmap in its name, or has an image of the same name next to it (for example
`market_share.pdf` + `market_share.png`). Otherwise it's a report.

## Install (Windows, from this folder)

```
python install.py
```

To send copies straight into Google Drive's streamed drive instead:
`python install.py --dest "G:/My Drive/ClaudeOutputs"`. With the default `C:\Users\<you>\ClaudeOutputs`,
add that folder in Google Drive for Desktop → Preferences → **My Computer → Add folder**. It then shows
up under **Computers** in Drive on the web and on your phone.

Restart any open Claude Code sessions afterwards. `python install.py --uninstall` removes the hooks.
Before changing `~/.claude/settings.json`, the installer saves a timestamped backup of it.

## How it works

* Hooks: `PostToolUse` (Write/Edit/NotebookEdit/Bash/PowerShell), `Stop`, `SubagentStop`, `SessionStart`.
* The hook process exits in ~50 ms, prints nothing and never fails. The real work runs in a detached,
  windowless background process, so Claude Code never waits on it.
* Each run scans the project (the nearest folder with `.git`, otherwise the session folder) for qualifying
  files whose size or modification time changed. That catches files written by scripts as well as by
  Claude directly. It never scans your home directory or a drive root.
* The first time it sees a project, existing files are only recorded, so old outputs don't flood the
  folder. To copy those too: `python ~/.claude/output-sync/sync_outputs.py backfill <project folder>`.
* It never deletes anything. A changed source overwrites its copy (Drive keeps version history). If two
  files share a name, the second gets its parent folder name as a prefix (`figures__adding_up.png`).
* Skipped: hidden folders (`.git`, `.venv` …), virtualenvs/conda envs, nested JS apps (folders with
  `package.json`), `node_modules`, `build`, `dist`, `public`, `static`, `raw`, `interim`, `external`,
  `__pycache__`, empty or oversized files, and Office temp files (`~$…`).

## Tuning

Edit `~/.claude/output-sync/config.json`. Any key from `DEFAULT_CONFIG` in `sync_outputs.py` can be
overridden, for example:

```json
{
  "dest_root": "C:/Users/Jase/ClaudeOutputs",
  "folders": {"reports": "writeups"},
  "skip_dirs": ["node_modules", "venv", "raw", "derived", "legacy"],
  "max_mb": {"data": 50}
}
```

Other commands: `sync_outputs.py dry-run <dir>` shows where each file would go, and `sync_outputs.py status`
shows the config and known projects. The log is `~/.claude/output-sync/sync.log`. Set
`CLAUDE_OUTPUT_SYNC=0` to pause syncing.
