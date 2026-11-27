"""Shared evaluation for edge4 candidates. A sleeve = per-day return series (1x notional, gross) + per-day cost (fraction).
Train 2017-2021 (pick params), test 2022-2026 (untouched). Sharpe = annualised on all business days (zeros when flat)."""
import numpy as np, pandas as pd
LAB = "/Users/churchxelachurchxela/Projects/openbot-lab"
BOOK = pd.read_csv(f"{LAB}/edge4/book_daily.csv", index_col=0, parse_dates=True)
def nqgrid():
    z = np.load(f"{LAB}/edge4/nqgrid.npz", allow_pickle=True); return pd.DatetimeIndex(z["d"]), z["g"].astype(float), z["iid"]
K = lambda hh, mm: int((hh - 18) * 60 + mm) % 1440 - 1  # grid column holding last price before hh:mm ET (prev-evening hours >= 18)
def stats(gross, cost, active, nm=""):
    """gross, cost: pd.Series (daily, fraction); active: bool series (trade taken)."""
    out = {}
    net = gross - cost
    for per, sl in (("train", slice("2017", "2021")), ("test", slice("2022", "2026"))):
        g_, n_, a_ = gross[sl], net[sl], active[sl].astype(bool)
        tr = n_[a_]; yrs = len(n_) / 252
        sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
        bk = BOOK.reindex(n_.index)
        m = bk.notna().all(1)
        c = {k: np.corrcoef(n_[m], bk[k][m])[0, 1] for k in ("B", "ON", "TREND", "BOOK")}
        out[per] = dict(n=int(a_.sum()), tpy=a_.sum() / yrs, bp_g=g_[a_].mean() * 1e4, bp_n=tr.mean() * 1e4,
                        t=tr.mean() / tr.std() * np.sqrt(len(tr)) if len(tr) > 2 else np.nan, sh_g=sh(g_), sh_n=sh(n_), **{f"c{k}": v for k, v in c.items()})
    return out
def line(nm, o):
    f = lambda d: f"{d['n']} ({d['tpy']:.0f}/y) | {d['bp_g']:+.2f} | {d['bp_n']:+.2f} | {d['t']:+.2f} | {d['sh_g']:+.2f} | {d['sh_n']:+.2f} | {d['cB']:+.2f}/{d['cON']:+.2f}/{d['cTREND']:+.2f}"
    return f"| {nm} | {f(o['train'])} | {f(o['test'])} |"
HDR = ("| variant | TRAIN n | bp gross | bp net | t net | Sh gross | Sh net | corr B/ON/TR | TEST n | bp gross | bp net | t net | Sh gross | Sh net | corr B/ON/TR |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
