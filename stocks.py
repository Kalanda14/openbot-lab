"""Per-stock daily features + 5-min ORB trade (Zarattini, Barbon & Aziz 2024 rules) from free Dukascopy 1-min BID candles.
Usage: python stocks.py SYMBOL 2017-01-01 2026-11-24  -> stk_SYMBOL.csv
Per day: first-5-min volume, daily OHLC, 14-day ATR (prior days), and the ORB trade for the side given by the
first 5-min candle colour: stop-entry at the 5-min high (long) / low (short) after 9:35, stop = 10% of ATR,
exit at 15:59 close. Result in % of entry price (before costs) + worst open %.
"""
import lzma, struct, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, requests

NY = ZoneInfo("America/New_York")
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"


def get(sym, d):
    u = f"https://datafeed.dukascopy.com/datafeed/{sym}/{d.year}/{d.month-1:02d}/{d.day:02d}/BID_candles_min_1.bi5"
    for k in range(5):
        try:
            r = S.get(u, timeout=40)
            if r.status_code == 404 or (r.status_code == 200 and not r.content): return None
            if r.status_code == 200:
                rows = np.array(list(struct.iter_unpack(">IIIIIf", lzma.decompress(r.content))), dtype=float)
                return rows
        except Exception:
            pass
        time.sleep(3 * (k + 1))
    return None


def session(sym, d):
    rows = get(sym, d)
    if rows is None or len(rows) == 0: return None
    o930 = datetime.combine(d, datetime.min.time(), NY).replace(hour=9, minute=30).astimezone(timezone.utc)
    s0 = int((o930 - datetime.combine(d, datetime.min.time(), timezone.utc)).total_seconds())
    m = rows[(rows[:, 0] >= s0) & (rows[:, 0] < s0 + 390 * 60)]
    m = m[m[:, 5] > 0]
    if len(m) < 300: return None
    t = ((m[:, 0] - s0) // 60).astype(int)
    O, C, L, H, V = (m[:, i] / 1000 if i < 5 else m[:, i] for i in (1, 2, 3, 4, 5))
    return t, O, C, L, H, V


if __name__ == "__main__":
    sym, a, z = sys.argv[1], *(datetime.strptime(x, "%Y-%m-%d").date() for x in sys.argv[2:4])
    days = [a + timedelta(i) for i in range((z - a).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    with ThreadPoolExecutor(4) as ex:
        sess = list(ex.map(lambda d: session(sym, d), days))
    out, rng = [], []
    for d, s in zip(days, sess):
        if s is None: continue
        t, O, C, L, H, V = s
        f5 = t < 5
        if f5.sum() < 3: continue
        o5, c5, h5, l5, v5 = O[f5][0], C[f5][-1], H[f5].max(), L[f5].min(), V[f5].sum()
        dO, dH, dL, dC = O[0], H.max(), L.min(), C[-1]
        r = dict(d=d, o5=o5, c5=c5, h5=h5, l5=l5, v5=v5, dO=dO, dH=dH, dL=dL, dC=dC, atr=np.mean(rng[-14:]) if len(rng) >= 14 else np.nan,
                 ret=np.nan, worst=np.nan, side=0)
        if not np.isnan(r["atr"]) and c5 != o5:
            side = 1 if c5 > o5 else -1; lvl = h5 if side == 1 else l5; stopd = 0.1 * r["atr"]
            after = ~f5; e = None
            for j in np.where(after)[0]:
                if e is None:
                    if (side == 1 and H[j] >= lvl) or (side == -1 and L[j] <= lvl):
                        e = max(O[j], lvl) if side == 1 else min(O[j], lvl); stop = e - side * stopd; worst = 0.0
                        if (side == 1 and L[j] <= stop) or (side == -1 and H[j] >= stop):
                            r.update(ret=-stopd / e, worst=-stopd / e, side=side); break
                    continue
                adv = (L[j] - e) if side == 1 else (e - H[j]); worst = min(worst, adv / e)
                if (side == 1 and L[j] <= stop) or (side == -1 and H[j] >= stop):
                    r.update(ret=-stopd / e, worst=-stopd / e, side=side); break
            else:
                if e is not None: r.update(ret=(C[-1] - e) * side / e, worst=min(worst, 0), side=side)
            if e is not None and r["side"] == 0: r.update(ret=(C[-1] - e) * side / e, worst=min(worst, 0), side=side)
        rng.append(dH - dL)
        out.append(r)
    pd.DataFrame(out).to_csv(f"stk_{sym}.csv", index=False)
    print(sym, len(out), "days", flush=True)
