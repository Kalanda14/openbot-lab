"""bt7: B variants, rules fixed before results. 1-min bars from data/full (needs vol column for VWAP).
 v30   original B (30-min checks)
 vwap  paper's version: long exits when close < max(UB, VWAP), short exits when close > min(LB, VWAP)
 opt   same trades as v30 but buying an at-the-money option that expires at the session close:
       premium/exit value by Black-Scholes, vol = 1.2 x last-14-day realized daily vol (implied usually > realized),
       0.5% of premium cost each side. Daily output = sum over trades of (exit value / premium - 1).
 also: session close price (for overnight return).
Env: COSTPCT, MINUTES, OPEN, DAILY.
"""
import glob, os, math, numpy as np, pandas as pd

CPCT = float(os.environ.get("COSTPCT", "0"))
N = int(os.environ.get("MINUTES", "390"))
OH, OM = (int(x) for x in os.environ.get("OPEN", "09:30").split(":"))


def load():
    out = []
    for f in sorted(glob.glob("data/full/*.csv.gz")):
        b = pd.read_csv(f, index_col=0, parse_dates=True)
        if len(b) > N * 12 * 0.6:
            agg = dict(open="first", high="max", low="min", close="last")
            if "vol" in b: agg["vol"] = "sum"
            m = b.resample("1min").agg(agg).dropna(subset=["close"])
            m.index = m.index.hour * 60 + m.index.minute - (OH * 60 + OM)
            m = m.reindex(range(N)); m[["open", "high", "low", "close"]] = m[["open", "high", "low", "close"]].ffill().bfill()
            if "vol" in m: m["vol"] = m.vol.fillna(0)
            out.append((b.index[0].normalize(), m))
    return out


def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs(S, K, T, v, call):
    if T <= 1e-9: return max(S - K, 0) if call else max(K - S, 0)
    d1 = (math.log(S / K) + 0.5 * v * v * T) / (v * math.sqrt(T)); d2 = d1 - v * math.sqrt(T)
    return S * ncdf(d1) - K * ncdf(d2) if call else K * ncdf(-d2) - S * ncdf(-d1)


def day(m, o, pc, sg, rt, mode, dvol):
    C, H, L = m.close.values, m.high.values, m.low.values
    tp = (H + L + C) / 3
    vw = None
    if mode == "vwap":
        v = m.vol.values if "vol" in m else np.ones(N)
        v = np.where(v > 0, v, 1e-9); vw = np.cumsum(tp * v) / np.cumsum(v)
    ub, lb = max(o, pc) * (1 + sg), min(o, pc) * (1 - sg)
    pos, e, real, worst, ke, orets = 0, 0.0, 0.0, 0.0, 0, 0.0
    iv = 1.2 * dvol  # daily vol fraction
    def close_opt(k):
        T = (N - 1 - k) / N; T0 = (N - 1 - ke) / N
        prem = bs(e, e, T0, iv, pos == 1); val = bs(C[k], e, T, iv, pos == 1)
        return (val * 0.995) / (prem * 1.005) - 1 if prem > 0 else 0.0
    for k in range(30, N):
        if pos:
            adv = (L[k] - e) if pos == 1 else (e - H[k]); worst = min(worst, real + adv - rt)
            if k % 30 == 0:
                lvl_l = max(ub[k], vw[k]) if vw is not None else ub[k]
                lvl_s = min(lb[k], vw[k]) if vw is not None else lb[k]
                if (pos == 1 and C[k] < lvl_l) or (pos == -1 and C[k] > lvl_s):
                    real += (C[k] - e) * pos - rt; orets += close_opt(k); pos = 0
        if not pos and k % 30 == 0 and k < N - 1:
            if C[k] > ub[k]: pos, e, ke = 1, C[k], k
            elif C[k] < lb[k]: pos, e, ke = -1, C[k], k
    if pos: real += (C[N - 1] - e) * pos - rt; orets += close_opt(N - 1)
    return real / o * 100, min(worst, real) / o * 100, orets


if __name__ == "__main__":
    days = load(); hist, rows, rets = [], [], []
    for i, (d, m) in enumerate(days):
        o = m.open.iloc[0]; mv = (m.close / o - 1).abs().values
        if i >= 15:
            pc = days[i - 1][1].close.iloc[-1]
            sg = np.mean(np.vstack(hist[-14:]), axis=0)
            rt = o * CPCT / 100 if CPCT else 1.12
            dvol = np.std(rets[-14:]) if len(rets) >= 14 else 0.012
            r = dict(d=d, px=o, cl=m.close.iloc[-1], prevcl=pc)
            r["p_v30"], r["w_v30"], r["opt"] = day(m, o, pc, sg, rt, "v30", dvol)
            r["p_vwap"], r["w_vwap"], _ = day(m, o, pc, sg, rt, "vwap", dvol)
            rows.append(r)
        if i >= 1: rets.append(m.close.iloc[-1] / days[i - 1][1].close.iloc[-1] - 1)
        hist.append(mv)
    df = pd.DataFrame(rows).set_index("d"); df.to_csv(os.environ.get("DAILY", "bt7.csv"))
    sh = lambda y: y.mean() / y.std() * np.sqrt(252) if y.std() > 0 else 0
    for c in ("p_v30", "p_vwap"):
        print(f"{c}: %/yr {df[c].mean()*252:+.1f} Sharpe {sh(df[c]):+.2f}")
    print(f"opt: avg return on premium per day {df.opt.mean():+.3f}, trade-day win {(df.opt[df.opt!=0]>0).mean():.0%}")
