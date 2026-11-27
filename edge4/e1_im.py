"""Candidate 1: intraday momentum (Gao-Han-Li-Zhou 2018) on NQ (and ES RTH).
Signal r1 = return prev 16:00 -> 10:00 ET (incl. overnight) [or 09:30->10:00 RTH only]; trade sign(r1) 15:30 -> 16:00.
Cost: 1.25 NQ pt round trip (ES: 0.5 pt) per trade. Variants pre-listed below; all are reported."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
D, G, iid = nqgrid()
same = np.r_[False, iid[1:] == iid[:-1]]          # prev session same contract
p = lambda hh, mm: G[:, K(hh, mm)]
c16 = p(16, 0); pc16 = np.r_[np.nan, c16[:-1]]
pc16 = np.where(same, pc16, np.nan)
o930, p10, p1530, p15, p1545 = p(9, 30), p(10, 0), p(15, 30), p(15, 0), p(15, 45)
r1 = p10 / pc16 - 1; r1rth = p10 / o930 - 1; r12 = p1530 / p15 - 1
last = c16 / p1530 - 1; last15 = c16 / p1545 - 1
cost = 1.25 / p1530
S = lambda x: pd.Series(x, index=D)
out = [HDR]; nv = 0
def run(nm, sig, ret, cst=cost):
    global nv; nv += 1
    s = np.nan_to_num(np.sign(sig)); act = s != 0
    o = stats(S(s * np.nan_to_num(ret)), S(np.where(act, cst, 0)), S(act)); out.append(line(nm, o)); print(out[-1]); return o
run("NQ r(prev16->10) -> 15:30-16:00", r1, last)
run("NQ r(9:30->10) -> 15:30-16:00", r1rth, last)
run("NQ r(15:00-15:30) -> 15:30-16:00", r12, last)
run("NQ r1 & r12 agree -> 15:30-16:00", np.where(np.sign(r1) == np.sign(r12), r1, 0), last)
run("NQ r1 -> 15:45-16:00", r1, last15)
run("NQ r1 |r1|>train median -> 15:30-16:00", np.where(np.abs(r1) > np.nanmedian(np.abs(r1[D.year <= 2021])), r1, 0), last)
# ES RTH (es_rth.npz: 390 RTH 1m closes; c[:, j] = close of bar 09:30+j)
z = np.load(f"{LAB}/dbdata/es_rth.npz"); Des = pd.DatetimeIndex(z["d"]); c = z["c"].astype(float)
e930 = np.r_[np.nan, c[:-1, -1]]  # placeholder not used
er1 = c[:, 29] / c[:, 0] - 1; elast = c[:, 389] / c[:, 359] - 1; ecost = 0.5 / c[:, 359]
def runE(nm, sig, ret):
    global nv; nv += 1
    s = np.nan_to_num(np.sign(sig)); act = s != 0
    o = stats(pd.Series(s * np.nan_to_num(ret), Des), pd.Series(np.where(act, ecost, 0), Des), pd.Series(act, Des)); out.append(line(nm, o)); print(out[-1])
runE("ES r(9:31->10:00) -> 15:30-16:00", er1, elast)
out.append(f"\nvariants: {nv}")
open(f"{LAB}/edge4/e1_im.md", "w").write("\n".join(out))
