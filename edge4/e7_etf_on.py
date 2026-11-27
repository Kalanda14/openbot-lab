"""Own idea: overnight (close->open) drift in other asset classes via Yahoo ETFs (dividend-adjusted with adjclose factor):
GLD (gold 'night effect'), SLV, TLT, IEF, USO, EWJ, EWG. All nights and after-down-day. Cost 2.5 bp per night
(CFD spread + financing). ETF opens are 09:30 ET prints -> overnight = 16:00 -> 09:30 ET, overlaps our ON window."""
import sys, json; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
def yf(s):
    j = json.load(open(f"{LAB}/edge4/yf/{s}.json"))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    idx = pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert("America/New_York").tz_localize(None).normalize()
    df = pd.DataFrame({"o": q["open"], "c": q["close"], "a": j["indicators"]["adjclose"][0]["adjclose"]}, index=idx).dropna()
    df = df[~df.index.duplicated(keep="last")]; f = df.a / df.c; df["o"] *= f; df["c"] = df.a; return df
out = [HDR]; nv = 0; R = {}
for s in ("GLD", "SLV", "TLT", "IEF", "USO", "EWJ", "EWG"):
    df = yf(s); on = (df.o / df.c.shift(1) - 1).where(lambda x: x.abs() < 0.15); down = df.c.shift(1) < df.c.shift(2)
    for nm, a in (("all nights", on.notna()), ("after down day", down & on.notna())):
        nv += 1; g = on.where(a, 0).fillna(0); o = stats(g, pd.Series(np.where(a, 2.5e-4, 0), g.index), a)
        R[(s, nm)] = g; out.append(line(f"{s} ON {nm}", o)); print(out[-1])
open(f"{LAB}/edge4/e7_etf_on.md", "w").write("\n".join(out + [f"\nvariants: {nv}"]))
