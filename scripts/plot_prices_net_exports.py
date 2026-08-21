"""Charts for the price / terms-of-trade / net-export tables.

Three charts, each in two speeds, all straight from the data rather than from a
model -- the pack's non-model view of how the chain changed:

  net_exports_*        net exports ($B), aggregate over the 60-code basket
  terms_of_trade_*     terms of trade, 2021 average = 100
  price_indices_*      the two unit-value legs of that ratio, side by side

Speeds: `12m` is a trailing 12-month total (net exports) or a 12-month unit-value
window (prices) -- smooth, and a quarter or two slow. `3m_sa` is the 3-month
version, seasonally adjusted, and for net exports annualised so the two are read on
the same axis. The fast line turns first and wobbles more; that is the trade.

ONE cast of countries appears on every chart, so a reader follows the same names -- and
the same colours -- from page to page. The cast is gec.config.CHAIN_MAJORS filtered by
the two tests in priceable(): usable quantity coverage, and a terms-of-trade series that
does not move more than MAX_SD in a typical month. A country failing either is dropped
from ALL THREE charts rather than appearing on some and not others; the net-export chart
loses information that way (Malaysia and Singapore are large net exporters), so their
figures belong in the caption instead.
China and Hong Kong appear as the CHK bloc on every chart, built from extra-bloc flows
rather than by adding the two countries together (their mutual trade is an internal
transfer, and a large one). CHN and HKG keep their own rows in the tables.

Inputs: results/tables/{net_exports,terms_of_trade,price_coverage}.csv
Output: results/figures/prices/*.{pdf,png}
Run after scripts/compute_prices_net_exports.py.
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.palette import COUNTRY, COUNTRY_FALLBACK

TABLES = cfg.RESULTS_DIR / "tables"
OUT = cfg.RESULTS_DIR / "figures" / "prices"

# same surface/ink as network_stats.py so the pack looks like one document
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "grid.alpha": 0.9, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10,
})

MAJORS = cfg.CHAIN_MAJORS
MIN_COVERAGE = 0.5          # a price series needs half its value carrying a quantity
MAX_SD = 0.035              # ...and must not move more than 3.5% in a typical month
BREAKS = {"202307": "2023-07", "202504": "2025-04"}
# (suffix, terms-of-trade freq, label for the chart title). A seasonally adjusted
# 3-month version of all three charts was built and dropped: net exports survived it
# fine, but at a 3-month window the price indices are dominated by basket churn
# (Korea's terms of trade swung 135 -> 66 -> 160 inside a year on codes entering and
# leaving the window), so the charts stay on the 12-month view for comparability.
# The m3_sa rows remain in terms_of_trade.csv and the *_sa columns in
# net_exports.csv for anyone who wants to look again.
SPEEDS = [("12m", "roll12", "12-month")]


def _col(iso):
    return COUNTRY.get(iso, COUNTRY_FALLBACK)


def _x(periods):
    return pd.PeriodIndex(periods, freq="M").to_timestamp()


def priceable(tot):
    """Majors a price chart can honestly carry, on two disclosed tests.

    Coverage: at least half the reported value on both flows yields a unit value.

    Stability: the terms-of-trade series moves less than MAX_SD in a typical month.
    A 12-month window shares eleven months between consecutive points, so a series
    swinging several percent a month is telling us about its basket, not its prices.
    The alternative -- filtering the offending months out of the data -- would drop
    precisely the volatile tail and bias every remaining country's index toward calm,
    so the exclusion happens here, at country level, where it is visible and reversible.
    """
    c = pd.read_csv(TABLES / "price_coverage.csv")
    w = c[c.stage == "ALL"].pivot_table(index="iso", columns="flow", values="coverage")
    ok = set(w[(w.X >= MIN_COVERAGE) & (w.M >= MIN_COVERAGE)].index)
    keep, dropped = [], []
    for iso in MAJORS:
        x = tot[(tot.freq == "roll12") & (tot.iso == iso)].sort_values("period")
        sd = np.log(x.tot).diff().std() if len(x) > 12 else np.nan
        why = ("coverage" if iso not in ok else
               "volatility" if not (sd < MAX_SD) else None)
        (dropped if why else keep).append((iso, sd, why))
    for iso, sd, why in dropped:
        print(f"  excluded {iso}: {why} (monthly sd {sd:.1%})")
    return [i for i, _, _ in keep], dropped


def _mark(ax, index):
    """Same two reference lines the model charts carry (H100 ramp, tariffs). Labels
    sit inside the axes so they cannot collide with the figure title."""
    for per, lab in BREAKS.items():
        t = pd.Period(per, "M").to_timestamp()
        if index.min() <= t <= index.max():
            ax.axvline(t, color=MUTED, lw=0.8, ls=":", zorder=0)
            ax.annotate(lab, (t, 0.015), xycoords=("data", "axes fraction"),
                        fontsize=7.5, color=MUTED, ha="center", va="bottom")


def _draw(ax, w, series, dx=8):
    """One line per country, each labelled at its own last month (series end on
    different months once incomplete months are dropped), labels pushed apart."""
    ends = []
    for iso in series:
        if iso not in w:
            continue
        s = w[iso].dropna()
        if s.empty:
            continue
        ax.plot(s.index, s.values, lw=1.9, color=_col(iso), label=iso, zorder=3)
        ends.append((iso, s.index[-1], s.iloc[-1]))
    ax.figure.canvas.draw()
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * 0.042
    placed = None
    for iso, x, y in sorted(ends, key=lambda e: e[2]):
        y = y if placed is None else max(y, placed + gap)
        placed = y
        ax.annotate(iso, (x, y), xytext=(dx, 0), textcoords="offset points",
                    fontsize=8.5, color=_col(iso), va="center", ha="left",
                    fontweight="bold", annotation_clip=False)


def net_exports(ne, series):
    # CHK arrives as its own row (extra-bloc flows only), so nothing is summed here.
    g = ne.sort_values(["iso", "period"]).copy()
    g["12m"] = g.net_12m
    g["3m_sa"] = 12 * g.net_sa3m          # annualised onto the 12-month axis
    for suffix, _, speed in SPEEDS:
        w = g.pivot(index="period", columns="iso", values=suffix).dropna(how="all")
        w.index = _x(w.index)
        fig, ax = plt.subplots(figsize=(9, 4.4))
        _mark(ax, w.index)
        ax.axhline(0, color="#c3c2b7", lw=1.0, zorder=1)
        _draw(ax, w / 1e9, series)
        ax.set_ylabel("net exports ($B/year)")
        ax.set_xlim(w.index.min(), w.index.max() + pd.Timedelta(days=210))
        ax.set_title(f"Net exports of the 60-code chain basket — {speed}",
                     fontsize=11, color=INK)
        ax.legend(fontsize=8, frameon=False, ncol=5, loc="lower left")
        fig.tight_layout()
        _save(fig, f"net_exports_{suffix}")


def terms_of_trade(tot, series):
    for suffix, freq, speed in SPEEDS:
        w = tot[tot.freq == freq].pivot(index="period", columns="iso", values="tot_2021")
        w.index = _x(w.index)
        fig, ax = plt.subplots(figsize=(9, 4.4))
        _mark(ax, w.index)
        ax.axhline(100, color="#c3c2b7", lw=1.0, zorder=1)
        _draw(ax, w, series)
        ax.set_ylabel("terms of trade (2021 average = 100)")
        ax.set_xlim(w.index.min(), w.index.max() + pd.Timedelta(days=210))
        ax.set_title(f"Terms of trade on the chain basket — {speed}",
                     fontsize=11, color=INK)
        ax.legend(fontsize=8, frameon=False, ncol=6, loc="lower left")
        fig.tight_layout()
        _save(fig, f"terms_of_trade_{suffix}")


def price_legs(tot, series):
    for suffix, freq, speed in SPEEDS:
        r = tot[tot.freq == freq]
        px = r.pivot(index="period", columns="iso", values="px_2021")
        pm = r.pivot(index="period", columns="iso", values="pm_2021")
        px.index, pm.index = _x(px.index), _x(pm.index)
        hi = max(px[series].max().max(), pm[series].max().max()) * 1.10
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True)
        for ax, w, name in ((axes[0], px, "export prices"), (axes[1], pm, "import prices")):
            _mark(ax, w.index)
            ax.axhline(100, color="#c3c2b7", lw=1.0, zorder=1)
            ax.set_title(name, fontsize=10, color=INK)
            ax.set_xlim(w.index.min(), w.index.max() + pd.Timedelta(days=200))
            ax.set_ylim(40, hi)
            _draw(ax, w, series, dx=5)
        axes[0].set_ylabel("unit-value index (2021 average = 100)")
        axes[0].legend(fontsize=8, frameon=False, ncol=3, loc="upper left")
        fig.suptitle(f"The two legs of the ratio — unit-value indices, {speed}",
                     color=INK, fontsize=11)
        fig.tight_layout()
        _save(fig, f"price_indices_{suffix}")


def _save(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=150, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / stem}.pdf/.png")


def main():
    ne = pd.read_csv(TABLES / "net_exports.csv", dtype={"period": str})
    tot = pd.read_csv(TABLES / "terms_of_trade.csv", dtype={"period": str})
    series, dropped = priceable(tot)
    print(f"price charts show {series} of {MAJORS}")
    net_exports(ne, series)
    terms_of_trade(tot, series)
    price_legs(tot, series)


if __name__ == "__main__":
    main()
