"""Book with ON replaced by ON_eu_down (real CME: 15:55 -> 03:30 only after a down day, 0.5bp cost; dated next day like ON).
Same vol-managed risk-parity build + intraday wipe as m300b (ON worst = 1.5 x min(ret,0)). Month-1 +EUR300 and 3-mo odds."""
import numpy as np, pandas as pd, goal80 as g, hybrid4 as H, m300b as M, m300c as C
D = pd.read_csv("dbdata/eudrift.csv", index_col=0, parse_dates=True)
new = ((D.eu - 0.5e-4).where(D.down.astype(bool), 0)).shift(1).reindex(g.S.index).fillna(0)
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
def build(on):
    S = g.S[["B", "TREND"]].assign(ON=on.values)
    w = 1 / S[:"2021"].std(); w = w / w.sum(); sc = {}
    for c in S:
        nz = S[c].where(S[c] != 0); vol = nz.rolling(20, min_periods=5).std().ffill().shift(1)
        sc[c] = (nz[:"2021"].std() / vol).clip(0, 3).fillna(1).values
    R = sum(w[c] * sc[c] * S[c].values for c in S)
    WR = w["B"] * sc["B"] * M.bw + w["ON"] * sc["ON"] * 1.5 * np.minimum(S.ON.values, 0) + w["TREND"] * sc["TREND"] * 2 * np.minimum(S.TREND.values, 0)
    n = (S.index < "2022").sum(); print(f"  weights {dict(w.round(3))} | book Sharpe train {sh(R[:n]):.2f} test {sh(R[n:]):.2f}")
    k = g.R.std() / R[:n].std(); return R * k, WR * k
for nm, on in (("old ON (free data)", g.S.ON), ("ON_eu_down (real CME)", new)):
    print(nm); R, WR = build(on); fwd = R - R.mean() + 1.2 * R.std() / np.sqrt(252)
    for f in (0.5, 0.75):
        a = M.run(R, WR, H.PA, 300, 100, 0, f, 0.0); b = M.run(fwd, WR, H.PA26, 300, 100, 0, f, 0.0)
        print(f"  1 mo f {f}: backtest hit {a[0]:.0%} (<100 {a[3]:.0%}, halves {a[1]:.0%}/{a[2]:.0%}) | cautious hit {b[0]:.0%} (<100 {b[3]:.0%})", flush=True)
    a = C.run(R, WR, 63, 0); b = C.run(fwd, WR, 63, 0)
    print(f"  3 mo f 0.5: backtest hit {a[0]:.0%} loss {a[1]:.0%} | cautious hit {b[0]:.0%} loss {b[1]:.0%}", flush=True)
