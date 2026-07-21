# Moved: see [data.md](data.md)

UN Comtrade documentation (API, keys, pull modes, availability polling, caveats)
is consolidated into **[data.md](data.md)** — the master data reference — §2
(source properties) and §5 (refresh cadence). The full original text of this
file is in git history (through commit `14646a5`).

Quick operational reminders: free key from comtradedeveloper.un.org (100k
rows/call, 500/day; `.env`); availability check without a key:
`python scripts/fetch_comtrade.py --year 2025 --reporters CHN,USA --check`;
monthly bilateral pull: `python scripts/fetch_comtrade_monthly.py`.
