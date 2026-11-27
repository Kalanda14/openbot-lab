"""m3: three new sleeves added to the m2 base book (real CME B, roll-safe base ON, TREND; vol-managed, risk parity on 2020-21).
RULES FIXED BEFORE RESULTS (no tuning):
 V1 CRYPTO-ON (analog of Boyarchenko-Larsen-Whelan overnight drift after down days): on every NQ day d (nqD roll==0) with
    r55<0, long 0.5 BTC + 0.5 ETH Binance perp from the 16:00 ET 15m bar open to the 03:30 ET bar open on the next NQ day.
    Cost 0.05%/side (0.10% round trip), minus perp funding paid inside the window. Dated to the exit day (like ON).
 V2 control: same window every NQ day (no down-day condition). Not a candidate, only shows if the condition matters.
 V3 ES-B: B on real CME ES (dbdata/paths_es.npz, ends 2026-06-30), jobs 2x, as a 4th risk-parity sleeve.
 V4 TOM (Lakonishok-Smidt 1988, McConnell-Xu 2008 FAJ, Etula et al 2020 RFS): long NQ from 15:55 ET of trading day -2
    to 15:55 of trading day +3 (returns of days -1,+1,+2,+3). Daily 15:55->15:55 returns only when instrument_id equals
    the previous day's (roll day = flat for that day + extra 0.5bp). Cost 1bp round trip.
Sleeve train = 2017-21 (crypto 2020-21), test 2022-26. Book weights/vol scaling exactly as m2 common.build (train 2020-21)."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/m2")
from common import *
TB = "/Users/churchxelachurchxela/Projects/trendbot/data/"

def build2(extra):
    pt = paths("real"); S = {"B": pt["M"][:, -1] * JOBS, "ON": C.ONS["base"].shift(1).reindex(idx).fillna(0).values,
                             "TREND": g.S.TREND.values}
    S.update(extra); sc = {c: vscale(S[c]) for c in S}
    rp = 1 / pd.DataFrame(S)[:NTR].std(); rp = rp / rp.sum()
    P = {c: rp[c] * sc[c] * S[c] for c in S}; R = sum(P.values()); k = g.R.std() / R[:NTR].std()
    return R * k, {c: v * k for c, v in P.items()}, dict(rp.round(3))

# ---------- crypto ON ----------
D = pd.read_pickle("dbdata/nqD.pkl"); D = D[D.roll == 0]
def crypto(cond=True):
    out = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        k = pd.read_csv(TB + f"{sym}_15m.csv", parse_dates=["time"]).set_index("time")
        k.index = k.index.tz_localize("UTC").tz_convert("America/New_York"); op = k.open
        f = pd.read_csv(TB + f"{sym}_funding.csv"); f.t = pd.to_datetime(f.t).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
        fc = f.set_index("t").r.cumsum()
        r = {}
        for d, row in D.iterrows():
            if cond and not row.r55 < 0: continue
            a = pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=16)
            e = pd.Timestamp(row.nx).tz_localize("America/New_York") + pd.Timedelta(hours=3, minutes=30)
            if a not in op.index or e not in op.index: continue
            fund = fc.asof(e) - fc.asof(a) if a > fc.index[0] else 0.0
            r[pd.Timestamp(row.nx)] = op[e] / op[a] - 1 - 0.001 - fund
        out[sym] = pd.Series(r)
    x = (0.5 * out["BTCUSDT"] + 0.5 * out["ETHUSDT"]).dropna()
    return x

# ---------- ES B ----------
def esb():
    z = np.load("dbdata/paths_es.npz", allow_pickle=True)
    s = pd.Series(z["mtm"][:, -1] / z["px"], index=pd.to_datetime(z["d"]))
    jb = np.array([(t.weekday() == 4 and t.day <= 7) for t in s.index]) + 1
    return s * jb

# ---------- TOM ----------
def tom():
    N = pd.read_pickle("dbdata/nq.pkl"); b = N[(N.index.hour == 15) & (N.index.minute == 54)]
    b.index = pd.to_datetime(b.index.date); b = b[~b.index.duplicated()]
    r = b.close.pct_change(); same = b.instrument_id == b.instrument_id.shift(1)
    dts = b.index; mo = dts.to_period("M"); pos = pd.Series(range(len(dts)), index=dts)
    first = pd.Series(dts).groupby(mo).transform("min").values; last = pd.Series(dts).groupby(mo).transform("max").values
    rank_f = pd.Series(dts).groupby(mo).cumcount().values + 1  # 1 = first day of month
    rank_l = pd.Series(dts).groupby(mo).cumcount(ascending=False).values  # 0 = last day of month
    inw = (rank_f <= 3) | (rank_l == 0)
    x = pd.Series(np.where(inw, np.where(same, r, -0.5e-4), 0.0), index=dts)
    entry = inw & (rank_l == 0)  # window starts on last day (entry at day -2 close)
    x = x - np.where(entry, 1e-4, 0)
    return x[x.index >= "2017-02-01"], int((inw & ~same).sum())

def stats(nm, s, bookR0, extra_key=None):
    tr, te = s[(s.index < "2022")], s[(s.index >= "2022")]
    return f"{nm}: sleeve Sharpe train {sh(tr):.2f} (n {(tr!=0).sum()}, {tr.index[0].date()}..) / test {sh(te):.2f} (n {(te!=0).sum()}), mean/bet test {te[te!=0].mean()*1e4:.1f}bp"

R0, P0, w0 = build2({}); b0 = pd.Series(R0, index=idx)
print(f"BASE book: train {sh(R0[:NTR]):.2f} test {sh(R0[NTR:]):.2f} Browne {browne(sh(R0[NTR:])):.1%} w {w0}")
res = {}
cr = crypto(True); cr2 = crypto(False); es = esb(); tm, nroll = tom()
print("TOM roll days inside window:", nroll)
for nm, s in [("V1 crypto-ON down-day", cr), ("V2 crypto-ON all days (control)", cr2), ("V3 ES-B", es), ("V4 TOM NQ", tm)]:
    print(stats(nm, s, b0))
    v = s.reindex(idx).fillna(0).values
    R1, P1, w1 = build2({"X": v})
    te = idx >= "2022"; c = np.corrcoef(v[te], R0[te])[0, 1]; con = np.corrcoef(v[te], P0["ON"][te])[0, 1]
    print(f"   corr test with base book {c:.2f}, with ON {con:.2f}, with B {np.corrcoef(v[te], P0['B'][te])[0,1]:.2f} | book train {sh(R1[:NTR]):.2f} test {sh(R1[NTR:]):.2f} "
          f"24-26 {sh(R1[idx>='2024']):.2f} (base 24-26 {sh(R0[idx>='2024']):.2f}) Browne {browne(sh(R1[NTR:])):.1%} w {w1}")
    if nm.startswith("V3"):
        m = idx < "2026-07-01"
        print(f"   to 2026-06 only: base test {sh(R0[NTR:][m[NTR:]]):.2f} -> {sh(R1[NTR:][m[NTR:]]):.2f}")
    for y in range(2017, 2027):
        z = s[s.index.year == y]
        if len(z) > 5: print(f"     {y} {sh(z):+.2f}", end="")
    print()
