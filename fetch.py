"""Free Dukascopy ticks (Nasdaq 100 index, USATECHIDXUSD) -> 5-second mid-price bars, 9:30-11:00 New York.
Usage: python fetch.py 2024-11-01 2026-11-24   (skips days already saved)
"""
import lzma, os, struct, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pandas as pd, requests

NY = ZoneInfo(os.environ.get("TZ_MKT", "America/New_York"))
OH, OM = (int(x) for x in os.environ.get("OPEN", "09:30").split(":"))
OUT = os.environ.get("OUT", "data/bars")
MIN = int(os.environ.get("MINUTES", "90"))  # 390 = full day to 16:00
SYM = os.environ.get("SYM", "USATECHIDXUSD")
PMIN, PMAX = float(os.environ.get("PMIN", 3000)), float(os.environ.get("PMAX", 60000))
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"


def hour(dt):
    u = f"https://datafeed.dukascopy.com/datafeed/{SYM}/{dt.year}/{dt.month-1:02d}/{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
    for k in range(6):
        try:
            r = S.get(u, timeout=40)
            if r.status_code == 200:
                if not r.content: return []
                d = lzma.decompress(r.content)
                return [(dt + timedelta(milliseconds=t), (a + b) / 2, av + bv) for t, a, b, av, bv in struct.iter_unpack(">IIIff", d)]
            if r.status_code == 404: return []
        except Exception:
            pass
        time.sleep(5 * (k + 1))
    raise RuntimeError("failed " + u)


def day(d):
    out = f"{OUT}/{d}.csv.gz"
    if os.path.exists(out): return "have"
    o = datetime.combine(d, datetime.min.time(), NY).replace(hour=OH, minute=OM)
    a = o.astimezone(timezone.utc).replace(minute=0)
    try:
        ticks = [x for h in range(MIN // 60 + 2) for x in hour(a + timedelta(hours=h))]
    except RuntimeError as x:
        return f"SKIP (retry next run): {x}"
    if len(ticks) < 500:
        pd.DataFrame(columns=["t", "open", "high", "low", "close"]).to_csv(out, index=False); return "empty"
    ix = pd.DatetimeIndex([x[0] for x in ticks]).tz_convert(NY)
    s = pd.Series([x[1] for x in ticks], index=ix); vv = pd.Series([x[2] for x in ticks], index=ix)
    med = s.median()
    div = next(x for x in (1000, 100, 10, 1, 10000) if PMIN < med / x < PMAX)
    s = s / div
    keep = (s.index >= o) & (s.index < o + timedelta(minutes=MIN)); s, vv = s[keep], vv[keep]
    b = s.resample("5s").ohlc().dropna()
    if os.environ.get("VOL"):
        b["vol"] = vv.resample("5s").sum().reindex(b.index).fillna(0).round(2)
        b["n"] = vv.resample("5s").count().reindex(b.index).fillna(0).astype(int)
    if b.empty:
        pd.DataFrame(columns=["t", "open", "high", "low", "close"]).to_csv(out, index=False); return "empty"
    b.index = b.index.tz_localize(None); b.index.name = "t"
    b.round(3).to_csv(out)
    return f"{len(b)} bars px~{b.close.iloc[0]:.0f}"


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    a, z = (datetime.strptime(x, "%Y-%m-%d").date() for x in sys.argv[1:3])
    days = [a + timedelta(i) for i in range((z - a).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    with ThreadPoolExecutor(4) as ex:
        for d, r in zip(days, ex.map(day, days)):
            print(d, r, flush=True)
