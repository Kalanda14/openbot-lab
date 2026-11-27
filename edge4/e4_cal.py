"""Candidates 4+5 on real NQ 1m (front contract, roll sessions excluded for overnight legs).
4 tug-of-war: overnight return (prev 16:00 -> 09:30) sign predicts RTH (09:30 -> 16:00) reversal.
5 calendar: pre-holiday day, opex week, quad-witching week, week after opex.
Costs: 1.25 NQ pt per round trip; holds crossing 17:00 ET also pay 1.2 bp swap per night."""
import sys, json; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
D, G, iid = nqgrid(); same = np.r_[False, iid[1:] == iid[:-1]]
p = lambda hh, mm: G[:, K(hh, mm)]
c16 = p(16, 0); pc16 = np.where(same, np.r_[np.nan, c16[:-1]], np.nan); o930 = p(9, 30)
on = o930 / pc16 - 1; rth = c16 / o930 - 1; cc = c16 / pc16 - 1
S = lambda x: pd.Series(x, index=D)
j = json.load(open(f"{LAB}/edge4/yf/GSPC.json"))["chart"]["result"][0]
nyse = pd.DatetimeIndex(pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert("America/New_York").tz_localize(None).normalize())
nyse = nyse[nyse <= D[-1]]
out = [HDR]; nv = 0
def run(nm, sig, ret, cost):
    global nv; nv += 1
    s = np.nan_to_num(sig); a = (s != 0) & np.isfinite(ret)
    o = stats(S(np.where(a, s * np.nan_to_num(ret), 0)), S(np.where(a, cost, 0)), S(a)); out.append(line(nm, o)); print(out[-1]); return o
cR = 1.25 / o930; cO = 1.25 / pc16 + 1.2e-4
run("tug: -sign(ON) -> RTH", -np.sign(on), rth, cR)
med = np.nanmedian(np.abs(on[D.year <= 2021]))
run("tug: -sign(ON) -> RTH, |ON|>train median", np.where(np.abs(on) > med, -np.sign(on), 0), rth, cR)
run("tug: +sign(ON) -> RTH (momentum control)", np.sign(on), rth, cR)
# pre-holiday: NYSE day whose next weekday is not a NYSE day (and not Friday->Mon normal weekend)
nx = nyse + pd.offsets.BDay(1); pre = nyse[~nx.isin(nyse) & (nx <= nyse[-1])]
isP = D.isin(pre); out.append(f"pre-holiday days found: {isP.sum()} ({isP.sum() / 9.9:.1f}/y)")
run("pre-holiday long close->close", isP * 1.0, cc, cO)
run("pre-holiday long RTH 09:30-16:00", isP * 1.0, rth, cR)
# opex: third Friday of month; opex week = Mon-Fri of that week; quad = Mar/Jun/Sep/Dec
tf = pd.DatetimeIndex([d for d in pd.date_range("2016-12-01", "2026-12-31", freq="WOM-3FRI")])
wk = lambda x: (x - pd.to_timedelta(x.weekday, unit="D"))
ow = wk(D).isin(wk(tf)); q = wk(D).isin(wk(tf[tf.month.isin([3, 6, 9, 12])])); aft = wk(D).isin(wk(tf) + pd.Timedelta(days=7))
run("opex week long close->close", ow * 1.0, cc, cO)
run("quad-witch week long close->close", q * 1.0, cc, cO)
run("week after opex short close->close", -1.0 * aft, cc, cO)
run("control: every day long close->close", np.ones(len(D)), cc, cO)
out.append(f"\nvariants: {nv} (incl. 2 controls)")
open(f"{LAB}/edge4/e4_cal.md", "w").write("\n".join(out))
