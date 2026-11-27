"""Candidate 3: crypto intraday seasonality, Binance spot 1h klines BTCUSDT/ETHUSDT (data.binance.vision).
Fee 0.1% round trip per trade (spec). Train 2017-08..2021, test 2022..2026-10.
(a) hour-of-day profile (diagnostic). (b) window search: every contiguous UTC window of 1..12 h, long or short, chosen
by TRAIN net Sharpe on BTC+ETH average -> test that one window (selection count reported). (c) pre-registered fixed
hypotheses: weekend long (Fri 00 -> Mon 00 UTC), funding hours (hold 23-01, 07-09, 15-17 UTC), US cash open hour
13:30-15:00 UTC proxy 13-15 h, late-US/Asia-open 21-23 h."""
import sys, glob, zipfile, io; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
def load(sym):
    fs = sorted(glob.glob(f"{LAB}/edge4/bnb/{sym}-1h-*.zip")); L = []
    for f in fs:
        with zipfile.ZipFile(f) as z: L.append(pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 1, 4]))
    d = pd.concat(L); d.columns = ["t", "o", "c"]; t = d.t.astype("int64"); t = np.where(t > 1e14, t // 1000, t)
    d.index = pd.to_datetime(t, unit="ms"); return d[~d.index.duplicated()].sort_index()
P = {s: load(s) for s in ("BTCUSDT", "ETHUSDT")}
r = {s: np.log(d.c).diff().reindex(pd.date_range(d.index[0], d.index[-1], freq="h")).fillna(0) for s, d in P.items()}
out = []
out.append("## (a) hour-of-day mean log return, bp (hour = bar start UTC)\n| hour | BTC train | BTC test | ETH train | ETH test |\n|---|---|---|---|---|")
for h in range(24):
    v = []
    for s in r: x = r[s]; m = x.index.hour == h; v += [x[m & (x.index.year <= 2021)].mean() * 1e4, x[m & (x.index.year >= 2022)].mean() * 1e4]
    out.append(f"| {h:02d} | " + " | ".join(f"{a:+.2f}" for a in v) + " |")
FEE = 10e-4
def day_series(s, hours, sign=1, wkday=None):
    """hold `hours` (set of bar-start hours) each day; one round trip per contiguous block per day. Returns daily gross, cost, active."""
    x = r[s]; m = x.index.hour.isin(hours)
    if wkday is not None: m &= np.isin(x.index.weekday, wkday)
    g = (x * m * sign).groupby(x.index.normalize()).sum()
    blocks = (m & ~np.r_[False, m[:-1]]); nb = pd.Series(blocks, x.index).groupby(x.index.normalize()).sum()
    return np.expm1(g), nb * FEE, nb > 0
def tot(s, hours, sign=1, wkday=None):
    g, c, a = day_series(s, hours, sign, wkday); return stats(g, c, a)
# (b) window search on train
cand = []
for h0 in range(24):
    for L_ in range(1, 13):
        hrs = [(h0 + k) % 24 for k in range(L_)]
        for sg in (1, -1):
            sh = []
            for s in r:
                g, c, a = day_series(s, hrs, sg); n = (g - c)[:"2021"]; sh.append(n.mean() / n.std() * np.sqrt(365))
            cand.append((np.mean(sh), h0, L_, sg))
cand.sort(reverse=True); nsearch = len(cand)
out.append(f"\n## (b) window search: {nsearch} windows x sign searched on train (BTC+ETH avg net Sharpe, 365-day annualisation)\nTop 5 train: " +
           "; ".join(f"start {h0:02d}h len {L_}h {'long' if sg > 0 else 'short'} train Sh {v:.2f}" for v, h0, L_, sg in cand[:5]))
out.append(HDR.replace("corr B/ON/TR", "corr B/ON/TR (equity-day aligned)"))
for v, h0, L_, sg in cand[:3]:
    for s in r:
        out.append(line(f"{s} {h0:02d}h+{L_}h {'L' if sg > 0 else 'S'} (search rank)", tot(s, [(h0 + k) % 24 for k in range(L_)], sg)))
# (c) fixed hypotheses
fx = [("weekend long Sat+Sun all hours", list(range(24)), 1, [5, 6]),
      ("funding hours long 23,00,07,08,15,16", [23, 0, 7, 8, 15, 16], 1, None),
      ("US open 13-15h long", [13, 14], 1, None), ("US open 13-15h short", [13, 14], -1, None),
      ("21-23h long", [21, 22], 1, None)]
for nm, hrs, sg, wk in fx:
    for s in r: out.append(line(f"{s} {nm}", tot(s, hrs, sg, wk)))
nv = 3 * 2 + len(fx) * 2
out.append(f"\nvariants reported: {nv} (+ {nsearch} windows searched in-sample for (b))")
print("\n".join(out)); open(f"{LAB}/edge4/e3_crypto.md", "w").write("\n".join(out))
