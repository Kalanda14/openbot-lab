"""Candidate 2: overnight drift (close->next open) on other cash indices (Yahoo daily), all nights and 'after a down day'
(close t-1 < close t-2, same rule as our NQ ON). Cost: 2.5 bp per night (CFD spread ~1 bp + overnight financing ~1.2-1.5 bp).
Also reported: intraday (open->close) for reference and the 'tug of war' reversal (overnight up -> intraday?)."""
import sys, json; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
def yf(s):
    j = json.load(open(f"{LAB}/edge4/yf/{s}.json"))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    tz = j["meta"]["exchangeTimezoneName"]
    idx = pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert(tz).tz_localize(None).normalize()
    df = pd.DataFrame({"o": q["open"], "c": q["close"]}, index=idx).dropna(); df = df[~df.index.duplicated(keep="last")]
    df = df[(df.o > 0) & (df.c > 0)]; return df
out = [HDR]; nv = 0; R = {}
for s in ("GDAXI", "STOXX50E", "FCHI", "FTSE", "N225", "HSI", "AXJO", "GSPC", "NDX", "RUT"):
    df = yf(s); on = df.o / df.c.shift(1) - 1; down = (df.c.shift(1) < df.c.shift(2))
    flat = (df.o == df.c.shift(1)).mean()
    on = on.where(on.abs() < 0.15)
    for nm, a in (("all nights", on.notna()), ("after down day", down & on.notna())):
        nv += 1; g = on.where(a, 0).fillna(0); o = stats(g, pd.Series(np.where(a, 2.5e-4, 0), g.index), a)
        R[(s, nm)] = (g, a); out.append(line(f"{s} ON {nm} (open==prevclose {flat:.0%})", o)); print(out[-1])
open(f"{LAB}/edge4/e2_onidx.md", "w").write("\n".join(out + [f"\nvariants: {nv}"]))
pd.to_pickle(R, f"{LAB}/edge4/e2_series.pkl")
