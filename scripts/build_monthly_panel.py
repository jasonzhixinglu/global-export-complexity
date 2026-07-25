"""Assemble the balanced monthly bilateral panel for the supply-chain HS6 codes.

Covers all 60 codes (Fed AI-compute 3 + OECD semiconductor 57, stages 1-8;
see src/gec/classifications.py) from 2017-01. The legacy 3-code panel
(panel_ai_compute_monthly.parquet, 2020+) is left untouched on disk so existing
estimations keep their sample; new work should read panel_semi_monthly.parquet
and filter codes/periods as needed.

Sources and hierarchy (per user direction + Atlas methodology, docs/data.md):
  1. UN Comtrade monthly (validated national submissions) is the backbone.
  2. TDM fills where Comtrade is silent: Taiwan (always), China 2025+, Vietnam 2024+
     (edition VN2, preliminary), and recent-month top-ups (KR/SG/FR/TR/TH).
  3. Reconciliation follows the Growth Lab mirroring pipeline (Bustos, Yildirim et
     al., "Tackling Discrepancies in Trade Data", GL WP 251 / Scientific Data 2026),
     implemented faithfully at annual country-pair level and applied to code-months:
       Step 2  CIF->FOB: gravity regression ln(CIF/FOB) ~ ln(dist) + contiguity +
               exporter FE + importer FE (CEPII GeoDist), fit per year on the
               importer reports that carry BOTH bases for the same flow (~4-5k
               observations/year in the aggregate pull); predicted ratios
               constrained non-negative and capped at 1.20 (their cap).
       Step 3  Reliability: pair discrepancy D = |X - M_fob|/(X + M_fob) (D = 1 for
               single-sided pairs); OLS D = a_j + a_k over the trade network;
               negative a clipped to 0; base country chosen by R^2 search;
               reliability = 1 - a, re-estimated per year.
       Step 4  Pair weights: softmax over (rel_exp, rel_imp); reporters in the
               bottom decile of reliability are disregarded in favor of the
               reliable side; single-sided flows taken at full weight.
       Step 5  Product level: reliability weights reconcile the PAIR TOTALS only;
               code-month values follow the EXPORTER's reported composition,
               rescaled by the pair-year factor (reconciled total / exporter
               total); the importer side is used only where the exporter does
               not report. Verified against Atlas directly: their published
               value is a single reconciled number per flow (export and
               reverse-import perspectives identical to <0.1% in 100% of
               corridors tested) that tracks the exporter report at HS6 level
               (IQR of log ratio ~0.13 vs ~0.8 for code-level blending) --
               importer product-level classification noise is what their XXXX
               residual code absorbs, so it must not be blended into code cells.
     Steps 2-3 are estimated on ANNUAL ALL-PRODUCT bilateral totals over the full
     reporting network (scripts/fetch_comtrade_totals.py), which is the level BY
     specify ("to avoid concordance issues ... we use data only at the aggregate
     importer-exporter level"); the resulting pair weights are then applied to our
     code-month cells (their Step 5).
     Remaining deviations from the published pipeline (documented, deliberate):
       - No ANS (Areas-Not-Specified) subtraction: our cells are bilateral and
         unknown-partner trade lands in ROW rather than double-counting a partner.
       - No product-level rescale to reconciled country totals and no XXXX
         residual code: both require all-product coverage per pair, while our
         basket is 60 codes.
       - No LT vintage harmonisation: codes are taken as reported. This is the
         one substantive difference and it is measured, not assumed -- see
         results/panel_monthly/atlas_discrepancy_audit.md.
       - ROW is an aggregate, not a reporter: ROW cells are single-sided by
         construction and take the counterparty's report with an importer-average
         CIF ratio.

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

from gec.classifications import SEMICONDUCTOR_OECD as _OECD
CODES = ["847150", "847180", "847330"] + sorted(
    {c for g, d in _OECD.items() if g != "Photosensitive devices" for c in d})
START = "2017-01"
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
OUT_PARQUET = cfg.DATA_DIR / "derived" / "panel_semi_monthly.parquet"
ATLAS_CACHE = cfg.DATA_DIR / "derived" / "bilateral_semi_2017_2024.parquet"
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
    """Map to (exporter, importer, basis); bucket non-kept and non-country to ROW.

    Order matters: Comtrade/TDM duplicates are resolved at the ORIGINAL partner
    level, and only then are non-kept partners collapsed into ROW and summed.
    (Deduping after the ROW collapse would keep one partner's value and discard
    every other non-kept partner in the same cell.)"""
    rec = rec[rec.value > 0].copy()
    rec = rec[rec.reporter.isin(KEEP)]  # only kept countries' reports are usable
    valid = rec.partner.astype(str).str.fullmatch(r"[A-Z]{3}")
    rec.loc[~valid.fillna(False), "partner"] = "__NONISO__"
    # same reporter/partner/code/period/flow from both sources: Comtrade wins
    rec = (rec.sort_values("source")   # 'comtrade' < 'tdm'
              .groupby(["reporter", "partner", "code", "period", "flow"], as_index=False)
              .first())
    rec.loc[~rec.partner.isin(KEEP), "partner"] = ROW
    exp = np.where(rec.flow == "X", rec.reporter, rec.partner)
    imp = np.where(rec.flow == "X", rec.partner, rec.reporter)
    out = pd.DataFrame({"exporter": exp, "importer": imp, "code": rec.code,
                        "period": rec.period, "value": rec.value,
                        "side": np.where(rec.flow == "X", "x", "m"),
                        "source": rec.source})
    out = out[out.exporter != out.importer]
    # now sum the collapsed ROW buckets (many partners -> one cell)
    return (out.groupby(["exporter", "importer", "code", "period", "side"], as_index=False)
               .agg(value=("value", "sum"), source=("source", "first")))


def load_cepii():
    """CEPII GeoDist: (iso_o, iso_d) -> distance, contiguity (all countries)."""
    d = pd.read_excel(cfg.RAW_DIR / "dist_cepii.xls",
                      usecols=["iso_o", "iso_d", "dist", "contig"])
    d = d[d.iso_o != d.iso_d]
    return d.groupby(["iso_o", "iso_d"])[["dist", "contig"]].first()


def load_totals():
    """Annual ALL-PRODUCT bilateral totals (BY estimate Steps 2-3 at this level).

    Returns (py, dual):
      py   -- exporter/importer/year with x (exporter-reported) and m (importer CIF)
      dual -- importer reports carrying BOTH cifvalue and fobvalue: the direct
              freight observations BY's CIF-to-FOB regression is fit on.
    """
    import comtradeapicall as ctc
    files = sorted((cfg.RAW_DIR / "comtrade_totals").glob("*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    ref = ctc.getReference("partner")
    c2i = {int(c): i for c, i in zip(ref["PartnerCode"], ref["PartnerCodeIsoAlpha3"])
           if isinstance(i, str) and len(i) == 3}
    c2i[490] = "TWN"
    df["rep"] = df.reporterCode.map(c2i)
    df["ptn"] = df.partnerCode.map(c2i)
    df = df[df.rep.notna() & df.ptn.notna() & (df.rep != df.ptn) & (df.partnerCode != 0)]
    df["year"] = df.period.astype(str).str[:4]
    x = df[df.flowCode == "X"].rename(columns={"rep": "exporter", "ptn": "importer"})
    m = df[df.flowCode == "M"].rename(columns={"rep": "importer", "ptn": "exporter"})
    py = (x.groupby(["exporter", "importer", "year"]).primaryValue.sum().rename("x")
          .to_frame().join(
              m.groupby(["exporter", "importer", "year"]).primaryValue.sum().rename("m"),
              how="outer").reset_index())
    dual = m[(m.cifvalue.fillna(0) > 0) & (m.fobvalue.fillna(0) > 0)][
        ["exporter", "importer", "year", "cifvalue", "fobvalue"]].copy()
    return py, dual


def cif_fob_ratios(dual, geo, pairs):
    """BY Step 2, faithful: ln(CIF/FOB) = a + t1 ln(dist) + t2 contiguity
    + exporter FE + importer FE, fit per year on importer reports that carry BOTH
    bases; predicted ratios applied to all pairs, constrained non-negative and
    capped at 1.20 (their cap). Countries absent from the estimation sample take
    the sample-average effect (FE = 0).

    Returns dict (exporter, importer, year) -> ratio and an importer-average
    fallback for cells whose counterparty is the ROW aggregate.
    """
    dual = dual.merge(geo, left_on=["exporter", "importer"], right_index=True, how="left")
    dual = dual[dual.dist.notna()].copy()
    # Estimation-sample hygiene: raw dual-basis rows contain impossible ratios
    # (max observed 1.3e5 -- fob mis-keyed or partial). Keep economically
    # plausible freight ratios on non-trivial flows.
    dual["ratio"] = dual.cifvalue / dual.fobvalue
    dual = dual[(dual.ratio > 0.9) & (dual.ratio < 3.0) & (dual.fobvalue > 1e5)]
    out, imp_fallback = {}, {}
    for year, est in dual.groupby("year"):
        y = np.log(est.ratio)
        ok = np.isfinite(y)
        est, y = est[ok], y[ok]
        if len(est) < 100:
            continue
        Xe = pd.get_dummies(est.exporter, prefix="e", dtype=float)
        Xi = pd.get_dummies(est.importer, prefix="i", dtype=float)
        X = pd.concat([pd.Series(np.log(est.dist.values), index=est.index, name="lndist"),
                       est.contig.astype(float).rename("contig"), Xe, Xi], axis=1)
        X.insert(0, "const", 1.0)
        beta, *_ = np.linalg.lstsq(X.values, y.values, rcond=None)
        coef = pd.Series(beta, index=X.columns)
        # Only ~36 countries report both bases, so most of our reporters have no
        # estimated fixed effect. Centre the FEs into the constant so an unseen
        # country takes the AVERAGE country effect rather than the arbitrary
        # zero level (leaving FE=0 biased predictions up by ~exp(0.24)).
        for pre in ("e_", "i_"):
            fe = [c for c in coef.index if c.startswith(pre)]
            if fe:
                mu = coef[fe].mean()
                coef[fe] -= mu
                coef["const"] += mu
        pr = pairs.merge(geo, left_on=["exporter", "importer"], right_index=True, how="left")
        pr = pr[pr.dist.notna()]
        Pe = pd.get_dummies(pr.exporter, prefix="e", dtype=float).reindex(
            columns=Xe.columns, fill_value=0.0)
        Pi = pd.get_dummies(pr.importer, prefix="i", dtype=float).reindex(
            columns=Xi.columns, fill_value=0.0)
        P = pd.concat([pd.Series(np.log(pr.dist.values), index=pr.index, name="lndist"),
                       pr.contig.astype(float).rename("contig"), Pe, Pi], axis=1)
        P.insert(0, "const", 1.0)
        pred = np.clip(np.exp(P.values @ coef.values.astype(float)), 1.0, 1.2)
        for (e, i), r in zip(zip(pr.exporter, pr.importer), pred):
            out[(e, i, year)] = float(r)
        for i, sub in pd.DataFrame({"i": pr.importer.values, "r": pred}).groupby("i"):
            imp_fallback[(i, year)] = float(sub.r.mean())
    return out, imp_fallback


def reliability_scores(py, ratios, imp_fallback):
    """BY Step 3, per year, over the FULL trade network (all reporting countries,
    all-product totals): D = |X - M_fob| / (X + M_fob), with D = 1 when only one
    side reports; OLS D = alpha_exporter + alpha_importer; negative alphas clipped
    to zero; base country chosen by highest R^2; reliability = 1 - alpha.

    The base-country search solves the same normal equations A = B'B with one row
    and column dropped, so all N candidate baselines cost one matrix build.
    """
    rel, diag = {}, {}
    for year, g in py.groupby("year"):
        r = np.array([ratios.get((e, i, year),
                                 imp_fallback.get((i, year), CIF_FOB))
                      for e, i in zip(g.exporter, g.importer)])
        m_fob = g.m.values / r
        x = g.x.values
        both = np.isfinite(x) & np.isfinite(m_fob)
        with np.errstate(invalid="ignore"):
            D = np.where(both, np.abs(x - m_fob) / (x + m_fob), 1.0)
        D = np.nan_to_num(D, nan=1.0)
        countries = sorted(set(g.exporter) | set(g.importer))
        cidx = {c: n for n, c in enumerate(countries)}
        n, nc = len(g), len(countries)
        ei = np.array([cidx[c] for c in g.exporter])
        ii = np.array([cidx[c] for c in g.importer])
        B = np.zeros((n, nc))
        B[np.arange(n), ei] += 1.0
        B[np.arange(n), ii] += 1.0
        A, BtD = B.T @ B, B.T @ D
        tss = ((D - D.mean()) ** 2).sum()
        best = None
        for base in range(nc):
            keep = np.arange(nc) != base
            try:
                a = np.linalg.solve(A[np.ix_(keep, keep)], BtD[keep])
            except np.linalg.LinAlgError:
                continue
            alpha = np.zeros(nc)
            alpha[keep] = np.maximum(a, 0.0)        # their non-negativity rule
            r2 = 1 - ((D - B @ alpha) ** 2).sum() / tss
            if best is None or r2 > best[0]:
                best = (r2, alpha, countries[base])
        for c, k in cidx.items():
            rel[(c, year)] = float(np.clip(1.0 - best[1][k], 0.0, 1.0))
        diag[year] = {"r2": best[0], "base": best[2], "n_edges": n, "n_countries": nc}
    return rel, diag


def pair_weights(rel, years):
    """BY Step 4: softmax over (reliability_exporter, reliability_importer) giving
    the weight on the importer report; reporters below the 10th percentile of the
    reliability distribution are disregarded in favour of the reliable partner.
    Computed for every country pair on demand via the returned closure."""
    thr = {y: float(np.percentile([v for (c, yy), v in rel.items() if yy == y], 10))
           for y in years if any(yy == y for (c, yy) in rel)}

    def w(e, i, year):
        re_, ri = rel.get((e, year)), rel.get((i, year))
        t = thr.get(year)
        if re_ is None or ri is None or t is None:
            return np.nan
        lo_e, lo_i = re_ < t, ri < t
        if lo_e and not lo_i:
            return 1.0                  # unreliable exporter: use the importer report
        if lo_i and not lo_e:
            return 0.0                  # unreliable importer: use the exporter report
        return float(np.exp(ri) / (np.exp(re_) + np.exp(ri)))
    return w


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

    # reconcile x vs m per cell (Growth Lab mirroring, faithful implementation)
    piv = rec.pivot_table(index=["exporter", "importer", "code", "period"],
                          columns="side", values="value", aggfunc="sum").reset_index()
    src = rec.pivot_table(index=["exporter", "importer", "code", "period"],
                          columns="side", values="source", aggfunc="first").reset_index()
    piv = piv.merge(src, on=["exporter", "importer", "code", "period"],
                    suffixes=("", "_src"))
    for c in ["x", "m", "x_src", "m_src"]:
        if c not in piv:
            piv[c] = np.nan

    geo = load_cepii()
    tot_py, dual = load_totals()
    pairs = tot_py[["exporter", "importer"]].drop_duplicates()
    ratios, imp_fallback = cif_fob_ratios(dual, geo, pairs)          # BY Step 2
    rel, rel_diag = reliability_scores(tot_py, ratios, imp_fallback)  # BY Step 3
    print("reliability regression by year:")
    for y, d in sorted(rel_diag.items()):
        print(f"  {y}: R^2 {d['r2']:.3f}, base {d['base']}, "
              f"{d['n_edges']} edges, {d['n_countries']} countries")
    wfun = pair_weights(rel, sorted(rel_diag))                        # BY Step 4
    # BY Step 5: reconcile pair-year TOTALS with the reliability weights, then
    # carry the exporter's code-level composition, rescaled to the reconciled
    # total. s_e = T / X_tot multiplies exporter-reported cells; s_i = T / M_fob_tot
    # multiplies importer-reported cells (used only where the exporter is silent).
    tk = list(zip(tot_py.exporter, tot_py.importer, tot_py.year))
    rt = np.array([ratios.get(k, imp_fallback.get((k[1], k[2]), CIF_FOB)) for k in tk])
    wt = np.array([wfun(*k) for k in tk])
    Xt, Mt_fob = tot_py.x.values, tot_py.m.values / rt
    have_x, have_m = np.isfinite(Xt), np.isfinite(Mt_fob)
    w_eff_t = np.where(np.isnan(wt), 0.5, wt)
    T = np.where(have_x & have_m, (1 - w_eff_t) * Xt + w_eff_t * Mt_fob,
                 np.where(have_x, Xt, Mt_fob))
    MIN_TOT = 1e6            # below this the scale factor is noise; fall back to 1
    s_e = {k: float(T[n] / Xt[n]) for n, k in enumerate(tk)
           if have_x[n] and Xt[n] > MIN_TOT}
    s_i = {k: float(T[n] / Mt_fob[n]) for n, k in enumerate(tk)
           if have_m[n] and Mt_fob[n] > MIN_TOT}
    yr = piv.period.str[:4]
    keys = list(zip(piv.exporter, piv.importer, yr))
    r_pair = np.array([ratios.get(k, imp_fallback.get((k[1], k[2]), CIF_FOB))
                       for k in keys])
    fob_m = piv["m"] / r_pair
    se = np.array([s_e.get(k, 1.0) for k in keys])
    si = np.array([s_i.get(k, 1.0) for k in keys])
    piv["value"] = np.where(piv["x"].notna(), piv["x"] * se, fob_m * si)
    both = piv["x"].notna() & piv["m"].notna()
    print(f"pair-total rescale factors: s_e median {np.median(list(s_e.values())):.3f} "
          f"IQR [{np.quantile(list(s_e.values()), .25):.3f}, "
          f"{np.quantile(list(s_e.values()), .75):.3f}]; "
          f"cells on exporter composition {piv['x'].notna().mean():.1%}")
    piv["provenance"] = np.select(
        [both, piv["x"].notna()],
        ["both:" + piv["x_src"].fillna("") + "+" + piv["m_src"].fillna(""),
         "x_only:" + piv["x_src"].fillna("")],
        default="m_only:" + piv["m_src"].fillna(""))
    piv["mirror_gap"] = np.where(both, np.log(piv["x"] / fob_m), np.nan)
    rel_summary = pd.Series(rel).rename_axis(["country", "year"]).unstack()
    print("reliability scores, kept countries (2024):")
    print(rel_summary.reindex(KEEP)["2024"].sort_values(ascending=False)
          .round(3).to_string())
    globals()["_REL"] = rel_summary

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


def atlas_bilateral():
    """Kept-kept Atlas corridors for all 60 codes, 2017-2024 (cached extract from
    the HS12 bulk CSVs)."""
    if ATLAS_CACHE.exists():
        return pd.read_parquet(ATLAS_CACHE)
    parts = []
    for path in [cfg.RAW_DIR / "hs12_country_country_product_year_6_2012_2019.csv",
                 cfg.RAW_DIR / "hs12_country_country_product_year_6_2020_2024.csv"]:
        for chunk in pd.read_csv(path, usecols=["country_iso3_code", "partner_iso3_code",
                                                "product_hs12_code", "year", "export_value"],
                                 dtype={"product_hs12_code": str}, chunksize=3_000_000):
            sel = chunk[chunk.product_hs12_code.isin(CODES) & (chunk.year >= 2017)
                        & chunk.country_iso3_code.isin(KEEP)
                        & chunk.partner_iso3_code.isin(KEEP)]
            if len(sel):
                parts.append(sel.rename(columns={
                    "country_iso3_code": "exporter", "partner_iso3_code": "importer",
                    "product_hs12_code": "code"}))
    atlas = pd.concat(parts, ignore_index=True)
    ATLAS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    atlas.to_parquet(ATLAS_CACHE, index=False)
    return atlas


def validate_vs_atlas(panel):
    """Aggregate kept-kept cells to annual and compare with the Atlas bilateral file."""
    atlas = atlas_bilateral()
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
        wt = g.export_value / g.export_value.sum()
        out[code] = {"n_corridor_years": len(g),
                     "log_corr": float(np.corrcoef(np.log(g.value),
                                                   np.log(g.export_value))[0, 1]),
                     "median_ratio": float(np.exp(lr.median())),
                     "iqr_log_ratio": float(lr.quantile(0.75) - lr.quantile(0.25)),
                     # level-based (value-weighted) measures: logs overstate the
                     # role of small linkages; these are dominated by the large
                     # corridors the analysis actually rides on
                     "aggregate_ratio": float(g.value.sum() / g.export_value.sum()),
                     "wtd_within25": float(((lr.abs() < np.log(1.25)) * wt).sum()),
                     "wtd_mape": float((np.abs(g.value - g.export_value)
                                        / g.export_value * wt).sum())}
    lr = np.log(m.value / m.export_value)
    wt = m.export_value / m.export_value.sum()
    out["ALL"] = {"n_corridor_years": len(m),
                  "log_corr": float(np.corrcoef(np.log(m.value),
                                                np.log(m.export_value))[0, 1]),
                  "median_ratio": float(np.exp(lr.median())),
                  "iqr_log_ratio": float(lr.quantile(0.75) - lr.quantile(0.25)),
                  "aggregate_ratio": float(m.value.sum() / m.export_value.sum()),
                  "wtd_within25": float(((lr.abs() < np.log(1.25)) * wt).sum()),
                  "wtd_mape": float((np.abs(m.value - m.export_value)
                                     / m.export_value * wt).sum())}
    return out


def write_report(panel, horizons, endpoint):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    prov = panel.provenance.value_counts(normalize=True)
    val = validate_vs_atlas(panel)
    total_by_year = panel.assign(year=panel.period.str[:4]).groupby("year").value.sum() / 1e9
    gaps = panel.mirror_gap.dropna()
    lines = [
        "# Monthly bilateral supply-chain panel — build report", "",
        f"{len(CODES)} HS6 codes (stages 1-8, docs/data.md); {len(KEEP)} countries + ROW; {START} .. "
        f"{endpoint[:4]}-{endpoint[4:]} (balanced endpoint = slowest reporter).",
        "Sources: UN Comtrade monthly (backbone) + TDM (TWN always; CHN/VNM beyond "
        "Comtrade). Reconciliation: Growth Lab mirroring (Bustos-Yildirim et al., GL "
        "WP 251) — gravity-estimated CIF/FOB ratios (capped 1.20), network-estimated "
        "annual reliability scores, softmax pair weights with bottom-decile "
        "disregard; see script docstring for the faithful-implementation notes.",
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
    lines += ["", "## Validation vs Atlas annual bilateral (2017–2024, kept-kept "
              "corridors > $0.1M)", "",
              "Log-based columns treat every corridor equally (they overstate small "
              "linkages); the value-weighted columns are dominated by the large "
              "corridors the analysis actually rides on.", "",
              "| code | corridor-years | log-corr | median ratio | IQR(log) | "
              "aggregate ratio | value-wtd within ±25% | value-wtd MAPE |",
              "|---|---|---|---|---|---|---|---|"]
    for code, v in val.items():
        lines.append(f"| {'**ALL**' if code == 'ALL' else code} | "
                     f"{v['n_corridor_years']} | {v['log_corr']:.3f} | "
                     f"{v['median_ratio']:.2f} | {v['iqr_log_ratio']:.2f} | "
                     f"{v['aggregate_ratio']:.2f} | {v['wtd_within25']:.0%} | "
                     f"{v['wtd_mape']:.0%} |")
    lines += ["", "_Generated by `scripts/build_monthly_panel.py`; panel parquet in "
              "`data/derived/` (git-ignored)._"]
    (REPORT_DIR / "build_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"report -> {REPORT_DIR / 'build_report.md'}")


if __name__ == "__main__":
    main()
