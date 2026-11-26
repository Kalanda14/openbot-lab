"""Rules-first prop-firm test. The firm rules come FIRST (RULES below, 50K plans, from 2026 rule guides:
tradetanto.com comparison Sept 2026 + propfirmretiree + firm-guide searches; FEES ARE PARTLY GUESSED, marked '?').
Then setup B (only Nasdaq day-trade edge we found) is reshaped to fit each firm with rule-driven overlays:
  ke  = MNQ contracts in the evaluation, kf = MNQ in funded before 1st payout, kf2 = after 1st payout
  tp  = daily take-profit $ (flat for the day once open+closed P&L >= tp): fits consistency caps + winning-day rules
  sl  = daily stop $ (flat once P&L <= -sl): keeps one day from eating the trailing drawdown
Overlays are chosen on 2017-2021 starts only, then reported on 2022-2026 starts (never seen when choosing).
Control 'no-edge': same paths with each day's average drift removed (same shape, zero edge).
Wallet: $400 start; buys one account, rebuys after a fail if the wallet can pay; payouts go to the wallet.
Usage: python propsim.py FIRM  (needs paths_*.npz)  -> prop_FIRM.md
"""
import glob, itertools, sys, numpy as np

R = dict(  # dd = max loss; trail eod/intra; lock = floor stops at start+lock; cons = best day <= cons*profit
    APEX=dict(fee=47, monthly=0, act=129, target=3000, dd=2000, trail="eod", ftrail="eod", lock=100, econs=None,
              fcons=0.5, win=250, nwin=5, mind=5, buffer=2100, minpay=500, caps=[1500, 1500, 2000, 2500, 2500, 2500],
              frac=1.0, split=1.0, maxpay=6, bots="alerts only (semi-auto)"),
    TOPSTEP=dict(fee=49, monthly=1, act=149, data=29, target=3000, dd=2000, trail="eod", ftrail="eod", lock=0,
                 econs=0.5, fcons=None, win=150, nwin=5, mind=5, buffer=0, minpay=125, caps=[2000] * 99, frac=0.5,
                 split=0.9, floor_after_pay=True, bots="yes (API, $29/mo)"),
    TRADEIFY_DAILY=dict(fee=160, monthly=0, act=0, target=3000, dd=2000, trail="eod", ftrail="eod", lock=100,
                        econs=0.4, fcons=None, win=0, nwin=0, mind=1, buffer=2100, minpay=250, caps=[1000] * 99,
                        frac=1.0, split=0.9, dll=1000, bots="yes (own, non-HFT)", feeq=1),
    TRADEIFY_LIGHTNING=dict(fee=328, monthly=0, act=0, target=None, dd=2000, trail="eod", ftrail="eod", lock=100,
                            econs=None, fcons=[0.2, 0.25, 0.3], goal=3000, win=0, nwin=0, mind=1, buffer=0, minpay=0,
                            caps=[2000, 2000, 2000] + [2500] * 99, frac=1.0, split=0.9, dll=1250,
                            bots="yes (own, non-HFT)", feeq=1),
    MFF_RAPID=dict(fee=130, monthly=1, act=0, target=3000, dd=2000, trail="eod", ftrail="intra", lock=100, econs=0.5,
                   fcons=None, win=0, nwin=0, mind=1, buffer=2100, minpay=500, caps=[99999] * 99, frac=1.0, split=0.9,
                   bots="NO on Rapid", feeq=1),
    TPT_PRO=dict(fee=170, monthly=1, act=130, target=3000, dd=2000, trail="eod", ftrail="intra", lock=0, econs=0.5,
                 fcons=None, win=0, nwin=0, mind=1, buffer=2000, minpay=0, caps=[99999] * 99, frac=1.0, split=0.8,
                 bots="unclear", feeq=1),
    LUCID_FLEX=dict(fee=130, monthly=0, act=0, target=3000, dd=2000, trail="eod", ftrail="eod", lock=100, econs=0.5,
                    fcons=None, win=150, nwin=5, mind=5, buffer=0, minpay=500, caps=[2000] * 5, frac=0.5, split=0.9, maxpay=5,
                    bots="NO", feeq=1),
    BULENOX=dict(fee=115, monthly=1, act=148, target=3000, dd=2500, trail="eod", ftrail="eod", lock=100, econs=None,
                 fcons=0.4, win=0, nwin=0, mind=10, buffer=2600, minpay=1000, caps=[1500] * 3 + [99999] * 99,
                 frac=1.0, split=1.0, dll=1100, bots="unclear", feeq=1),
)
START, BUDGET, SLIP = 50000.0, 400.0, 0.25


def load():
    import os
    fs = sorted(glob.glob(os.environ.get("PATHS", "pathsd/**/paths_*.npz"), recursive=True))
    z = [np.load(f) for f in fs]
    d = np.concatenate([x["d"] for x in z]); px = np.concatenate([x["px"] for x in z])
    m = np.concatenate([x["mtm"] for x in z]).astype(float); lo = np.concatenate([x["low"] for x in z]).astype(float)
    o = np.argsort(d); d, px, m, lo = d[o], px[o], m[o], lo[o]
    sc = (px[-1] / px)[:, None] * 2.0  # $ per MNQ at today's Nasdaq price
    return d, m * sc, lo * sc


def day_table(m, lo, k, tp, sl, dll):
    """$ result, worst open $, best open $ per day for k MNQ with daily tp/sl (first touch wins)."""
    M, L = m * k, lo * k
    stop = min(x for x in (sl, dll, 1e12) if x)
    n = M.shape[1]
    hs = np.where((L <= -stop).any(1), (L <= -stop).argmax(1), n)
    ht = np.where((M >= tp).any(1), (M >= tp).argmax(1), n) if tp else np.full(len(M), n)
    end = np.minimum(np.minimum(hs, ht), n - 1)
    pnl = M[np.arange(len(M)), end]
    pnl = np.where(hs < ht, -stop - SLIP * 2 * k, pnl)
    pnl = np.where((hs >= n) & (ht >= n), M[:, -1], pnl)
    mask = np.arange(n)[None, :] <= end[:, None]
    worst = np.minimum(np.where(mask, L, 0).min(1), pnl)
    best = np.maximum(np.where(mask, M, 0).max(1), pnl)
    return pnl, worst, best


def new_acct(r): return dict(ph="eval" if r["target"] else "fund", bal=START, pk=START, d=0, best=0.0, np=0, sd=0,
                             nw=0, pb=0.0, pbase=START)


def step(a, r, T, i, w):
    """One trading day for account a. Returns (account or None if failed/ended, wallet)."""
    if r["monthly"] and a["ph"] == "eval" and a["d"] and a["d"] % 21 == 0:
        if w < r["fee"]: return None, w
        w -= r["fee"]
    if a["ph"] == "eval" and r.get("elim") and a["d"] >= r["elim"]: return None, w  # eval time limit (trading days)
    tb = T[0] if a["ph"] == "eval" else (T[2] if a["np"] else T[1])
    p, wo, be = tb[0][i], tb[1][i], tb[2][i]
    a["d"] += 1
    tr = r["trail"] if a["ph"] == "eval" else r["ftrail"]
    fixed = r.get("floor_after_pay") and a["np"]
    floor = START if fixed else min(a["pk"] - r["dd"], START + r["lock"])
    if a["bal"] + wo <= floor: return None, w  # intraday breach
    if tr == "intra":
        a["pk"] = max(a["pk"], a["bal"] + be)
        floor = START if fixed else min(a["pk"] - r["dd"], START + r["lock"])
    a["bal"] += p
    if a["bal"] <= floor: return None, w
    a["pk"] = max(a["pk"], a["bal"])
    if a["ph"] == "eval":
        a["best"] = max(a["best"], p); pr = a["bal"] - START
        if pr >= r["target"] and (not r["econs"] or a["best"] <= r["econs"] * pr):
            if w < r["act"]: return None, w
            w -= r["act"]; a = new_acct(r); a["ph"] = "fund"
        return a, w
    a["sd"] += 1; a["nw"] += (p >= r["win"]) if r["nwin"] else 0; a["pb"] = max(a["pb"], p)
    since = a["bal"] - a["pbase"]
    fc = r["fcons"]; fc = fc[min(a["np"], len(fc) - 1)] if isinstance(fc, list) else fc
    ok = a["sd"] >= r["mind"] and a["nw"] >= r["nwin"] and (not fc or a["pb"] <= fc * max(since, 1))
    if r.get("goal") is not None and a["np"] == 0: ok = ok and a["bal"] - START >= r["goal"]
    if not ok: return a, w
    avail = (a["bal"] - START) * r["frac"] if r.get("floor_after_pay") else (a["bal"] - START - r["buffer"]) * r["frac"]
    x = min(avail, r["caps"][min(a["np"], len(r["caps"]) - 1)])
    if r.get("cap2x"): x = min(x, 2 * max(since, 0))
    if x < max(r["minpay"], 1): return a, w
    a["bal"] -= x; w += x * r["split"]; a["np"] += 1; a["sd"] = a["nw"] = 0; a["pb"] = 0.0; a["pbase"] = a["bal"]
    if r.get("maxpay") and a["np"] >= r["maxpay"]: return None, w
    return a, w


def run(r, T, s, days, nmax=1, reserve=0.0):
    """Wallet change after `days`. Keeps up to nmax accounts (same trades copied); an extra account is bought only
    when the wallet still holds `reserve` after paying for it."""
    w, acc = BUDGET, []
    first = r["fee"] + (r["act"] if r["target"] is None else 0)
    for i in range(s, s + days):
        while len(acc) < nmax and w >= first + (reserve if acc else 0):
            w -= r["fee"]; acc.append(new_acct(r))
        if not acc and w < first: break
        if r.get("data") and (i - s) % 21 == 0 and acc: w -= r["data"]
        nxt = []
        for a in acc:
            a, w = step(a, r, T, i, w)
            if a is not None: nxt.append(a)
        acc = nxt
    return w - BUDGET


def stats(x): return np.mean(x > 0), np.mean(x >= 1000), np.mean(x >= 10000), x.mean()


if __name__ == "__main__":
    firm = sys.argv[1]; r = R[firm]
    d, m, lo = load(); n = len(d)
    mu = m[:, -1].mean(); ramp = np.linspace(0, 1, m.shape[1])[None, :]
    m0, lo0 = m - mu * ramp, lo - mu * ramp
    half = int(np.searchsorted(d, "2022-01-01"))
    H = (126, 252)
    tr = [range(20, half - h, 6) for h in H]; te = [range(half, n - h, 3) for h in H]
    dll = r.get("dll")
    grid = [(ke, kf, kf, tp, sl) for ke, kf, tp, sl in itertools.product((5, 8, 12, 16), (1, 2, 3, 5, 8),
                                                                          (None, 300, 500, 800, 1500), (None, 400, 700, 1000))]
    cache = {}
    def tab(mm, ll, k, tp, sl, key):
        kk = (key, k, tp, sl)
        if kk not in cache: cache[kk] = day_table(mm, ll, k, tp, sl, dll)
        return cache[kk]
    res = []
    for ke, kf, kf2, tp, sl in grid:
        if kf2 > kf: continue
        T = (tab(m, lo, ke, tp, sl, 0), tab(m, lo, kf, tp, sl, 0), tab(m, lo, kf2, tp, sl, 0))
        a = np.array([run(r, T, s, 126) for s in tr[0]])
        res.append((np.mean(a >= 1000), a.mean(), (ke, kf, kf2, tp, sl)))
    res.sort(key=lambda x: (x[0], x[1]), reverse=True)
    L = [f"# {firm} (bots: {r['bots']})\n", "Picked on 2017-21 starts by P(+$1k in 6 mo). Cells: P(profit) / P(+$1k) / "
         "P(+$10k) / avg $.\n", "| ke kf kf2 tp sl | horizon | TRAIN 2017-21 | TEST 2022-26 | NO-EDGE test |", "|---|---|---|---|---|"]
    base = [(0, 0, (10, 2, 2, None, None))]
    for _, _, (ke, kf, kf2, tp, sl) in res[:3] + base:
        for hi, h in enumerate(H):
            T = (tab(m, lo, ke, tp, sl, 0), tab(m, lo, kf, tp, sl, 0), tab(m, lo, kf2, tp, sl, 0))
            T0 = (tab(m0, lo0, ke, tp, sl, 1), tab(m0, lo0, kf, tp, sl, 1), tab(m0, lo0, kf2, tp, sl, 1))
            c = [stats(np.array([run(r, X, s, h) for s in rg])) for X, rg in ((T, tr[hi]), (T, te[hi]), (T0, te[hi]))]
            f = lambda z: f"{z[0]:.0%} / {z[1]:.0%} / {z[2]:.0%} / ${z[3]:+.0f}"
            L.append(f"| {ke} {kf} {kf2} {tp} {sl} | {h//21} mo | {f(c[0])} | {f(c[1])} | {f(c[2])} |")
    L.append("\n(last block = plain B, 10 MNQ eval -> 2 funded, no tp/sl: the old plan, for comparison)")
    open(f"prop_{firm}.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
