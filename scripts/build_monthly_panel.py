"""Assemble the balanced monthly bilateral panel for the AI-compute HS6 codes.

Sources and hierarchy (per user direction + Atlas methodology, docs/tdm.md):
  1. UN Comtrade monthly (validated national submissions) is the backbone.
  2. TDM fills where Comtrade is silent: Taiwan (always), China 2025+, Vietnam 2024+
     (edition VN2, preliminary), and recent-month top-ups (KR/SG/FR/TR/TH).
  3. Discrepancies are treated Atlas-style (simplified Bustos-Yildirim): every corridor
     value is observed up to twice -- exporter's FOB report and importer's CIF report.
     CIF is deflated by CIF_FOB (1.10); when both sides exist the cell value is their
     mean and the mirror gap is recorded; otherwise the single available side is used.
     (Full BY would weight by reporter reliability; the recorded gaps enable that later.)

Panel: top-30 countries + ROW, per HS6 code, monthly from 2020-01. The balanced
endpoint is the last month at which every kept country has reported (or is covered by
TDM) on at least one side; within the balanced window, absent corridors are true zeros.
Cells between two non-reporting parties do not exist by construction (ROW-ROW is the
one structural hole; it is set to 0 and flagged).

Outputs:
  data/derived/panel_ai_compute_monthly.parquet   (long; git-ignored)
  results/panel_monthly/build_report.md           (committed summary + validation)
Run after fetch_comtrade_monthly.py and fetch_tdm.py.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.comtrade import CIF_FOB

CODES = ["847150", "847180", "847330"]
START = "2020-01"
# Top 30 by 2020-24 AI-compute involvement (see results/mfm), AUT excluded (reporting
# stopped 2022); everything else folds into ROW.
KEEP = ["CHN", "USA", "MEX", "TWN", "KOR", "VNM", "HKG", "MYS", "SGP", "THA",
        "NLD", "DEU", "CZE", "HUN", "JPN", "PHL", "IND", "IDN", "CAN", "GBR",
        "FRA", "ITA", "POL", "IRL", "ESP", "CHE", "BEL", "SWE", "DNK", "ISR"]
ROW = "ROW"
# Countries whose own reporting ends before the panel endpoint but whose kept-partner
# corridors are covered by mirror (partners' reports). Their ROW cells go dark beyond
# their horizon (0 + provenance flag). FRA: Comtrade ends 2025-12, TDM edition
# inaccessible on this account (probed empty even for 2024). PHL/IND/ITA/ESP/SWE:
# ~1-month slower than the rest; mirroring them moves the balanced endpoint from
# 2026-03 to 2026-04 at ~0.06% of monthly value going dark (see build report).
MIRROR_FALLBACK = {"FRA", "PHL", "IND", "ITA", "ESP", "SWE"}
CT_DIR = cfg.RAW_DIR / "comtrade_monthly"
TDM_DIR = cfg.RAW_DIR / "tdm"
OUT_PARQUET = cfg.DATA_DIR / "derived" / "panel_ai_compute_monthly.parquet"
REPORT_DIR = cfg.RESULTS_DIR / "panel_monthly"


def load_comtrade():
    """Comtrade monthly -> report records: one row per (reporter's view of a flow).
    The pulls carry only numeric M49 codes (includeDesc=False leaves ISO blank), so
    map code -> ISO3 via the Comtrade reference tables."""
    import comtradeapicall as ctc
    parts = []
    for f in sorted(CT_DIR.glob("*.parquet")):
        d = pd.read_parquet(f)
        if len(d):
            parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    df["period"] = df["period"].astype(str)
    df["cmdCode"] = df["cmdCode"].astype(str)
    df = df[df.cmdCode.isin(CODES) & (df.partnerCode != 0)]
    ref = ctc.getReference("partner")  # superset of reporters; has ISO3 per M49 code
    code2iso = {int(c): i for c, i in zip(ref["PartnerCode"], ref["PartnerCodeIsoAlpha3"])
                if isinstance(i, str) and len(i) == 3}
    code2iso[490] = "TWN"  # "Other Asia, nes" is Taiwan
    rec = pd.DataFrame({
        "reporter": df.reporterCode.map(code2iso), "partner": df.partnerCode.map(code2iso),
        "code": df.cmdCode, "period": df.period, "value": df.primaryValue.astype(float),
        "flow": df.flowCode, "source": "comtrade",
    })
    rec = rec[rec.reporter.notna()]
    rec["partner"] = rec.partner.fillna(ROW)
    return rec


def load_tdm():
    parts = []
    for f in sorted(TDM_DIR.glob("tdm_*.tsv")):
        d = pd.read_csv(f, sep="\t", encoding="utf-16",
                        dtype={"COMMODITY": str, "MONTH": str, "YEAR": str})
        if not len(d):
            continue
        parts.append(pd.DataFrame({
            "reporter": d.RPT_ISO, "partner": d.PTN_ISO, "code": d.COMMODITY,
            "period": d.YEAR + d.MONTH.str.zfill(2), "value": d.VALUE.astype(float),
            "flow": d.FLOW.map({"E": "X", "I": "M"}), "source": "tdm",
        }))
    return pd.concat(parts, ignore_index=True)


def normalize(rec):
    """Map to (exporter, importer, basis); bucket non-kept and non-country to ROW."""
    rec = rec[rec.value > 0].copy()
    valid = rec.partner.astype(str).str.fullmatch(r"[A-Z]{3}")
    rec.loc[~valid.fillna(False), "partner"] = ROW
    rec.loc[~rec.partner.isin(KEEP), "partner"] = ROW
    rec = rec[rec.reporter.isin(KEEP)]  # only kept countries' reports are usable
    exp = np.where(rec.flow == "X", rec.reporter, rec.partner)
    imp = np.where(rec.flow == "X", rec.partner, rec.reporter)
    out = pd.DataFrame({"exporter": exp, "importer": imp, "code": rec.code,
                        "period": rec.period, "value": rec.value,
                        "side": np.where(rec.flow == "X", "x", "m"),
                        "source": rec.source})
    out = out[out.exporter != out.importer]
    # duplicate reports of the same side of the same cell: comtrade beats tdm
    out = (out.sort_values("source")  # 'comtrade' < 'tdm'
              .groupby(["exporter", "importer", "code", "period", "side"], as_index=False)
              .first())
    # aggregate ROW buckets (many partners collapsed into one)
    return out


def reporter_horizons(records):
    """Last period each kept country has any report of its own (either side/source)."""
    isrep = ((records.side == "x") & records.exporter.isin(KEEP) |
             (records.side == "m") & records.importer.isin(KEEP))
    rep = np.where(records.side == "x", records.exporter, records.importer)
    h = (records[isrep].assign(rep=rep[isrep.values] if isinstance(isrep, pd.Series) else rep)
         .groupby("rep").period.max())
    return h


def main():
    ct = load_comtrade()
    tdm = load_tdm()
    print(f"comtrade records: {len(ct)}, tdm records: {len(tdm)}")
    rec = normalize(pd.concat([ct, tdm], ignore_index=True))
    # ROW partner rows were exploded per original partner -> sum them per cell/side
    rec = (rec.groupby(["exporter", "importer", "code", "period", "side"], as_index=False)
              .agg(value=("value", "sum"), source=("source", "first")))

    # reconcile x vs m per cell (Atlas-style simplified BY)
    piv = rec.pivot_table(index=["exporter", "importer", "code", "period"],
                          columns="side", values="value", aggfunc="sum").reset_index()
    src = rec.pivot_table(index=["exporter", "importer", "code", "period"],
                          columns="side", values="source", aggfunc="first").reset_index()
    piv = piv.merge(src, on=["exporter", "importer", "code", "period"],
                    suffixes=("", "_src"))
    for c in ["x", "m", "x_src", "m_src"]:
        if c not in piv:
            piv[c] = np.nan
    fob_m = piv["m"] / CIF_FOB
    both = piv["x"].notna() & piv["m"].notna()
    piv["value"] = np.where(both, (piv["x"] + fob_m) / 2, piv["x"].fillna(fob_m))
    piv["provenance"] = np.select(
        [both, piv["x"].notna()],
        ["both:" + piv["x_src"].fillna("") + "+" + piv["m_src"].fillna(""),
         "x_only:" + piv["x_src"].fillna("")],
        default="m_only:" + piv["m_src"].fillna(""))
    piv["mirror_gap"] = np.where(both, np.log(piv["x"] / fob_m), np.nan)

    # balanced endpoint: every kept country reporting (either side, any source),
    # except designated mirror-fallback countries
    horizons = reporter_horizons(rec)
    horizons = horizons.reindex(KEEP)
    endpoint = horizons.drop(list(MIRROR_FALLBACK)).min()
    print("reporter horizons (last reported period):")
    print(horizons.sort_values().to_string())
    print(f"balanced endpoint: {endpoint} (mirror-fallback: {sorted(MIRROR_FALLBACK)})")

    panel = piv[(piv.period >= START.replace("-", "")) & (piv.period <= endpoint)]
    panel = panel[["exporter", "importer", "code", "period", "value", "x", "m",
                   "provenance", "mirror_gap"]].rename(columns={"x": "value_x_fob",
                                                                "m": "value_m_cif"})
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT_PARQUET, index=False)

    write_report(panel, horizons, endpoint)
    print(f"panel -> {OUT_PARQUET}: {len(panel)} rows through {endpoint}")


def lag_analysis(panel, horizons, endpoint):
    """Document publication lags and the endpoint choice: what each laggard tier costs.

    A country whose reporting stops before the endpoint is 'mirror-fallback': its
    corridors with reporting partners survive via the partner's report; corridors
    where NEITHER party reports (laggard x laggard, laggard x ROW) go dark (0).
    Dark shares are measured against 2025+ value weights.
    """
    w = panel[panel.period >= "202501"]
    tot = w.value.sum()
    inv = lambda g: w.exporter.isin(g) | w.importer.isin(g)
    dark = lambda fb: w[(w.exporter.isin(fb) & w.importer.isin(fb)) |
                        (inv(fb) & ((w.exporter == ROW) | (w.importer == ROW)))
                        ].value.sum() / tot
    tiers = horizons.groupby(horizons).groups
    lines = ["", "## Publication lags and the endpoint choice", "",
             "National monthly submissions arrive with heterogeneous lags (~2-4 months; "
             "France has stopped monthly reporting since 2025-12 and its TDM edition is "
             "inaccessible). The balanced endpoint is the last month at which every "
             "kept country outside the mirror-fallback set has reported. Fallback "
             "countries stay covered on corridors where the partner reports; only "
             "laggard-laggard and laggard-ROW corridors go dark (set to 0, weighted "
             "share of 2025+ value shown below).", "",
             f"- Mirror-fallback set: {', '.join(sorted(MIRROR_FALLBACK))} -> "
             f"balanced endpoint {endpoint[:4]}-{endpoint[4:]}; dark-cell share "
             f"{dark(MIRROR_FALLBACK):.2%} of monthly value.",
             "- Cost of pushing further (dark share if all countries reporting before "
             "that month were mirrored):"]
    for h in sorted(set(horizons) - {horizons.max()}):
        fb = set(horizons[horizons <= h].index)
        nxt = min(x for x in set(horizons) if x > h)
        lines.append(f"  - endpoint {nxt[:4]}-{nxt[4:]}: fallback {len(fb)} countries "
                     f"({', '.join(sorted(fb)[:8])}{'...' if len(fb) > 8 else ''}), "
                     f"dark {dark(fb):.2%}")
    lines.append("- Re-running the fetch scripts + assembler rolls the endpoint forward "
                 "as laggards file; the fallback set should be revisited then.")
    return lines


def validate_vs_atlas(panel):
    """Aggregate kept-kept cells to annual and compare with the Atlas bilateral file."""
    atlas = pd.read_parquet(cfg.DATA_DIR / "derived" / "bilateral_ai_compute_2020_2024.parquet")
    atlas = atlas[atlas.exporter.isin(KEEP) & atlas.importer.isin(KEEP)]
    atlas = atlas.groupby(["exporter", "importer", "code", "year"], as_index=False
                          ).export_value.sum()
    p = panel[(panel.exporter != ROW) & (panel.importer != ROW)].copy()
    p["year"] = p.period.str[:4].astype(int)
    p = p[p.year <= 2024].groupby(["exporter", "importer", "code", "year"],
                                  as_index=False).value.sum()
    m = atlas.merge(p, on=["exporter", "importer", "code", "year"], how="inner")
    m = m[(m.export_value > 1e5) & (m.value > 1e5)]
    out = {}
    for code, g in m.groupby("code"):
        lr = np.log(g.value / g.export_value)
        out[code] = {"n_corridor_years": len(g),
                     "log_corr": float(np.corrcoef(np.log(g.value),
                                                   np.log(g.export_value))[0, 1]),
                     "median_ratio": float(np.exp(lr.median())),
                     "iqr_log_ratio": float(lr.quantile(0.75) - lr.quantile(0.25))}
    return out


def write_report(panel, horizons, endpoint):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    prov = panel.provenance.value_counts(normalize=True)
    val = validate_vs_atlas(panel)
    total_by_year = panel.assign(year=panel.period.str[:4]).groupby("year").value.sum() / 1e9
    gaps = panel.mirror_gap.dropna()
    lines = [
        "# Monthly bilateral AI-compute panel — build report", "",
        f"Codes {', '.join(CODES)}; {len(KEEP)} countries + ROW; {START} .. "
        f"{endpoint[:4]}-{endpoint[4:]} (balanced endpoint = slowest reporter).",
        "Sources: UN Comtrade monthly (backbone) + TDM (TWN always; CHN/VNM beyond "
        "Comtrade; KR/SG/FR/TR/TH top-ups). Reconciliation: simplified Bustos–Yildirim "
        f"— importer CIF deflated by {CIF_FOB}, mean of the two sides when both report.",
        "",
        f"- Rows: {len(panel):,}; total value {total_by_year.sum():.0f}B "
        f"(by year, $B: {', '.join(f'{y} {v:.0f}' for y, v in total_by_year.items())})",
        f"- Provenance shares: "
        + ", ".join(f"{k} {v:.1%}" for k, v in prov.items()),
        f"- Mirror gap log(x/m_fob), cells with both sides: median "
        f"{gaps.median():+.3f}, IQR {gaps.quantile(0.75)-gaps.quantile(0.25):.3f} "
        f"({len(gaps):,} cells)",
        "",
        "## Reporter horizons (last reported month)", "",
        "| country | last period |", "|---|---|",
    ]
    lines += [f"| {c} | {p[:4]}-{p[4:]} |" for c, p in horizons.sort_values().items()]
    lines += lag_analysis(panel, horizons, endpoint)
    lines += ["", "## Validation vs Atlas annual bilateral (2020–2024, kept-kept "
              "corridors > $0.1M)", "",
              "| code | corridor-years | log-corr | median panel/Atlas | IQR(log ratio) |",
              "|---|---|---|---|---|"]
    for code, v in val.items():
        lines.append(f"| {code} | {v['n_corridor_years']} | {v['log_corr']:.3f} | "
                     f"{v['median_ratio']:.2f} | {v['iqr_log_ratio']:.2f} |")
    lines += ["", "_Generated by `scripts/build_monthly_panel.py`; panel parquet in "
              "`data/derived/` (git-ignored)._"]
    (REPORT_DIR / "build_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"report -> {REPORT_DIR / 'build_report.md'}")


if __name__ == "__main__":
    main()
