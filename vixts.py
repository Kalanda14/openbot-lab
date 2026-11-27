"""VIX term-structure tilt (cutoff = 67th pct of VIX/VIX3M in 2020-21 only, signal lagged 1 day):
ON and TREND x k when in top tercile, on top of vol-managed (L20). Book re-scaled to same train vol. Then month-1 +EUR300 odds."""
import numpy as np, pandas as pd, goal80 as g, hybrid4 as H, m300b as M
S = g.S[["B", "ON", "TREND"]]
ld = lambda f: pd.read_csv(f, index_col=0, parse_dates=True)["CLOSE"].astype(float)
ts = (ld("ext/VIX.csv") / ld("ext/VIX3M.csv")).shift(1).reindex(S.index, method="ffill")
hi = (ts > ts[:"2021"].quantile(0.67)).values
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
n_tr = (S.index < "2022").sum()
def book(k_on, k_tr):
    R = M.w["B"] * M.sc["B"] * S.B.values + M.w["ON"] * M.sc["ON"] * S.ON.values * np.where(hi, k_on, 1) + M.w["TREND"] * M.sc["TREND"] * S.TREND.values * np.where(hi, k_tr, 1)
    WR = M.w["B"] * M.sc["B"] * M.bw + M.w["ON"] * M.sc["ON"] * np.minimum(S.ON.values, 0) * np.where(hi, k_on, 1) + M.w["TREND"] * M.sc["TREND"] * 2 * np.minimum(S.TREND.values, 0) * np.where(hi, k_tr, 1)
    k = g.R.std() / R[:n_tr].std(); return R * k, WR * k
if __name__ == "__main__":
    for k_on, k_tr in ((1, 1), (2, 1), (1, 2), (2, 2), (3, 2)):
        R, WR = book(k_on, k_tr)
        fwd = R - R.mean() + 1.2 * R.std() / np.sqrt(252)
        line = f"ON x{k_on} TREND x{k_tr}: Sharpe train {sh(R[:n_tr]):.2f} test {sh(R[n_tr:]):.2f}"
        if (k_on, k_tr) in ((1, 1), (2, 2)):
            a = M.run(R, WR, H.PA, 300, 100, 0, 0.5, 0.0); b = M.run(fwd, WR, H.PA26, 300, 100, 0, 0.5, 0.0)
            line += f" | +300 in 1 mo: backtest {a[0]:.0%} (<100 {a[3]:.0%}, halves {a[1]:.0%}/{a[2]:.0%}) cautious {b[0]:.0%}"
        print(line, flush=True)
