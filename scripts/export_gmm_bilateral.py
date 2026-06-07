"""Encode bilateral (origin -> destination) PCI distributions as Gaussian mixtures.

Universe: the top-N displayed countries (cfg.N_TOP) + a single ROW bloc, so corridors are
(N+1)^2.  Bilateral value is one-directional (A->B export = B<-A import), so we store the
export direction; the import view of a corridor is the same number read the other way.

Each corridor's distribution over PCI is a Gaussian mixture (adaptive K by fidelity to the raw
data, fixed across years, warm-started year-to-year) -- same method as the country distributions
(docs/analysis.md s3.3).  Concentrated single-product corridors smear (fine in W1, large in KS;
see the error discussion); we accept that uniform treatment.

Writes dashboard/public/data/gmm_bilateral.json.
Run:  python scripts/export_gmm_bilateral.py [year_range ...]   (default 2020_2024)
"""
from __future__ import annotations
import gzip, json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import data as gdata

warnings.filterwarnings("ignore")
OUT = cfg.ROOT / "dashboard" / "public" / "data"
DERIVED = cfg.DATA_DIR / "derived"
RNG = np.random.default_rng(0)
XG = np.linspace(cfg.PCI_LO, cfg.PCI_HI, 600)
KCANDS = (2, 3, 5, 8)
NDRAW = 3000
MIN_PROD = 12          # below this a corridor is too sparse to fit a mixture; skipped
ROW = "ROW"


def mix_shape(par, x):
    pi = par[:, 0] / par[:, 0].sum()
    return (pi[:, None] * norm.pdf((x[None, :] - par[:, 1][:, None]) / par[:, 2][:, None]) / par[:, 2][:, None]).sum(0)


def ks_to_truth(par, pci, w):
    o = np.argsort(pci); c = np.cumsum(w[o]); c = c / c[-1]
    emp = np.interp(XG, pci[o], c, left=0, right=1)
    pi = par[:, 0] / par[:, 0].sum()
    mcdf = (pi[:, None] * norm.cdf((XG[None, :] - par[:, 1][:, None]) / par[:, 2][:, None])).sum(0)
    return float(np.abs(mcdf - emp).max())


def fit_k(pci, w, K, warm=None, ninit=2):
    p = w / w.sum(); n = min(NDRAW, max(400, 8 * len(pci)))
    d = RNG.choice(pci, n, p=p)
    kw = dict(n_components=K, random_state=0, max_iter=200, reg_covar=1e-4)
    if warm is not None and len(warm) == K:
        g = GaussianMixture(n_init=1, means_init=warm[:, 1:2],
                            weights_init=warm[:, 0] / warm[:, 0].sum(),
                            precisions_init=(1 / warm[:, 2] ** 2).reshape(K, 1, 1), **kw)
    else:
        g = GaussianMixture(n_init=ninit, **kw)
    g.fit(d.reshape(-1, 1))
    par = np.column_stack([g.weights_, g.means_.ravel(), np.sqrt(g.covariances_.ravel())])
    return par[np.argsort(par[:, 1])]


def choose_k(pci, w, tol=0.005):
    cands = [K for K in KCANDS if K <= max(2, len(pci) // 6)]
    ks = {K: ks_to_truth(fit_k(pci, w, K, ninit=1), pci, w) for K in cands}
    best = min(ks.values())
    for K in cands:
        if ks[K] <= best + tol:
            return K
    return min(ks, key=ks.get)


def load_bilateral_blocs(year_ranges, top, years, chunksize=2_000_000):
    """Chunked read mapping every country/partner to its ISO (if in `top`) or ROW, aggregating
    to (origin_bloc, dest_bloc, HS4 product, year).  Bounded memory: collapse to N+1 blocs per chunk."""
    topset = set(top)
    parts = []
    for yr_range in year_ranges:
        path = cfg.bilateral_path(yr_range)
        if not path.exists():
            raise FileNotFoundError(f"{path} - run download_data.py --bilateral {yr_range}")
        n = 0
        for chunk in pd.read_csv(path, usecols=gdata.BILATERAL_USECOLS,
                                 dtype={"country_iso3_code": str, "partner_iso3_code": str,
                                        "product_hs92_code": str}, chunksize=chunksize):
            chunk["year"] = chunk["year"].astype(int)
            chunk = chunk[chunk["year"].isin(years)]
            if chunk.empty:
                continue
            chunk["export_value"] = pd.to_numeric(chunk["export_value"], errors="coerce")
            chunk = chunk.dropna(subset=["export_value"])
            chunk = chunk[chunk["export_value"] > 0]
            chunk["o"] = np.where(chunk.country_iso3_code.isin(topset), chunk.country_iso3_code, ROW)
            chunk["d"] = np.where(chunk.partner_iso3_code.isin(topset), chunk.partner_iso3_code, ROW)
            chunk["p4"] = chunk.product_hs92_code.str.zfill(6).str[:4]
            parts.append(chunk.groupby(["o", "d", "p4", "year"], as_index=False)["export_value"].sum())
            n += len(chunk)
        print(f"  read {yr_range}: {n:,} rows", flush=True)
    out = pd.concat(parts, ignore_index=True)
    return out.groupby(["o", "d", "p4", "year"], as_index=False)["export_value"].sum()


def main():
    year_ranges = tuple(sys.argv[1:]) or ("2020_2024",)
    s = np.load(DERIVED / "surfaces.npz", allow_pickle=True)
    top = [str(c) for c in s["countries"]]                 # the displayed top-N universe
    rng_years = {"2020_2024": range(2020, 2025), "2010_2019": range(2010, 2020),
                 "2000_2009": range(2000, 2010), "1995_1999": range(1995, 2000)}
    years = sorted(set().union(*[set(rng_years[r]) for r in year_ranges]))
    print(f"bilateral GMM: top-{len(top)} + ROW, years {years[0]}-{years[-1]} from {year_ranges}", flush=True)

    # Per-year-range bloc parquet caches, so the multi-GB read is resumable: a kill only loses
    # the range in progress; finished ranges (and the earlier 2020_2024 run) are reused.
    DERIVED.mkdir(parents=True, exist_ok=True)
    rcaches = {r: DERIVED / f"bilateral_blocs_top{len(top)}_{r}.parquet" for r in year_ranges}
    pci_by = None
    parts = []
    for yr_range in year_ranges:
        rc = rcaches[yr_range]
        if rc.exists():
            print(f"loading cached range {yr_range}: {rc.name}", flush=True)
            parts.append(pd.read_parquet(rc))
            continue
        if pci_by is None:
            base = gdata.load_clean(years=years)
            pci_by = (base.assign(p4=base.product_hs92_code.str.zfill(4))
                      .groupby(["year", "p4"])["pci"].first())
        ry = sorted(set(years) & set(rng_years[yr_range]))
        print(f"reading bilateral {yr_range} (chunked) ...", flush=True)
        blr = load_bilateral_blocs([yr_range], top, ry)
        blr["pci"] = blr.set_index(["year", "p4"]).index.map(pci_by)
        blr = blr.dropna(subset=["pci"])
        blr = blr[blr.pci.between(cfg.PCI_LO, cfg.PCI_HI)]
        blr.to_parquet(rc)
        print(f"cached -> {rc.name}", flush=True)
        parts.append(blr)
    bl = pd.concat(parts, ignore_index=True) if len(parts) > 1 else parts[0]
    print(f"corridors present: {bl.groupby(['o','d']).ngroups:,}", flush=True)

    # exact marginals over ALL corridors (incl. skipped thin ones) for the adding-up check:
    # origin marginal = total exports; destination marginal = total imports (inclusive of ROW).
    me = bl.groupby(["o", "year"])["export_value"].sum()
    mi = bl.groupby(["d", "year"])["export_value"].sum()
    margExp = {o: {str(int(y)): round(float(me[(o, y)]) / 1e9, 3) for (oo, y) in me.index if oo == o}
               for o in me.index.get_level_values(0).unique()}
    margImp = {d: {str(int(y)): round(float(mi[(d, y)]) / 1e9, 3) for (dd, y) in mi.index if dd == d}
               for d in mi.index.get_level_values(0).unique()}

    blocs = top + [ROW]
    # checkpoint so a long fit resumes mid-way instead of restarting
    ckpt = DERIVED / f"gmm_bilateral_ckpt_{'_'.join(year_ranges)}.json"
    if ckpt.exists():
        st = json.loads(ckpt.read_text())
        mix, kmap, corrB = st["mix"], st["kmap"], st["corrB"]
        ks_list, done = st["ks_list"], set(st["done"])
        ncell, ncomp, skipped = st["ncell"], st["ncomp"], st["skipped"]
        print(f"resuming from checkpoint: {ncell} corridors already done", flush=True)
    else:
        mix = {}; kmap = {}; corrB = {}
        ks_list = []; done = set(); ncell = ncomp = skipped = 0

    def save_ckpt():
        ckpt.write_text(json.dumps({"mix": mix, "kmap": kmap, "corrB": corrB, "ks_list": ks_list,
                                    "done": sorted(done), "ncell": ncell, "ncomp": ncomp, "skipped": skipped}))

    for (o, d), gall in bl.groupby(["o", "d"]):
        key = f"{o}|{d}"
        if o == d or key in done:    # no domestic flows / already fitted
            continue
        by_year = {}
        for yr, g in gall.groupby("year"):
            if len(g) >= MIN_PROD:
                by_year[int(yr)] = (g.pci.to_numpy(float), g.export_value.to_numpy(float))
        if len(by_year) < 2:
            skipped += 1; done.add(key)
            continue
        K = choose_k(*by_year[max(by_year)])
        prev = None
        for yr in sorted(by_year):
            pci, w = by_year[yr]
            par = fit_k(pci, w, K, warm=prev); prev = par
            mix.setdefault(o, {}).setdefault(d, {})[str(yr)] = [
                [round(float(par[k, 0]), 4), round(float(par[k, 1]), 3), round(float(par[k, 2]), 3)]
                for k in range(K)]
            corrB.setdefault(o, {}).setdefault(d, {})[str(yr)] = round(float(w.sum()) / 1e9, 3)
            ncomp += K
            ks_list.append(ks_to_truth(np.array(mix[o][d][str(yr)]), pci, w))
        kmap.setdefault(o, {})[d] = K
        ncell += 1; done.add(key)
        if ncell % 300 == 0:
            save_ckpt(); print(f"  fitted {ncell} corridors ... (checkpointed)", flush=True)

    payload = {"flow": "export", "blocs": blocs, "years": years,
               "blur": {"low": 0.05, "med": 0.10, "high": 0.18},
               "K": kmap, "mix": mix, "corridorB": corrB,
               "margExpB": margExp, "margImpB": margImp}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gmm_bilateral.json").write_text(json.dumps(payload))
    ckpt.unlink(missing_ok=True)
    raw = (OUT / "gmm_bilateral.json").stat().st_size
    gz = len(gzip.compress((OUT / "gmm_bilateral.json").read_bytes(), 6))
    ks = np.array(ks_list)
    print(f"\ncorridors encoded: {ncell}  (skipped {skipped} too-sparse)  components: {ncomp}")
    print(f"KS vs raw truth: p50 {100*np.median(ks):.1f}%  p95 {100*np.percentile(ks,95):.1f}%")
    print(f"gmm_bilateral.json: raw {raw/1e6:.2f} MB  gz {gz/1e6:.2f} MB")


if __name__ == "__main__":
    main()
