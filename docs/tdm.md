# Moved: see [data.md](data.md)

Trade Data Monitor documentation (editions incl. `VN2`, API endpoint, standing
pulls, response format, licensing) is consolidated into **[data.md](data.md)** —
the master data reference — §2 (source properties) and §6 (licensing). Vendor
files remain in [tdm/](tdm/). Full original text in git history (through
commit `14646a5`).

Quick operational reminders: `python scripts/fetch_tdm.py` runs the standing
set; credentials in `.env` (`TDM_USERNAME`/`TDM_PASSWORD`); raw extracts stay
in git-ignored `data/raw/tdm/` — never commit (subscription license).
