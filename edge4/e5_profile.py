"""Diagnostic: NQ mean return per 30-min slot over the 23h session (train vs test), all days and after a down day
(16:00 < prev 16:00). Used to look for any window with stable drift outside the ON window (15:55->03:30)."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
D, G, iid = nqgrid()
c16 = G[:, K(16, 0)]; dn = np.r_[False, c16[1:] < c16[:-1]]; dn = np.r_[False, dn[:-1]]  # yesterday was a down day
tr = D.year <= 2021; out = ["| slot start ET | all train bp | all test bp | t train | t test | after-down train | after-down test |", "|---|---|---|---|---|---|---|"]
for k in range(0, 1380, 30):
    if k + 29 >= 1380: break
    a = G[:, k + 29] / np.where(k == 0, np.nan, G[:, max(k - 1, 0)]) - 1 if k > 0 else G[:, 29] / G[:, 0] - 1
    a = np.where(np.abs(a) < 0.05, a, np.nan)
    f = lambda m: (np.nanmean(a[m]) * 1e4, np.nanmean(a[m]) / np.nanstd(a[m]) * np.sqrt(np.isfinite(a[m]).sum()))
    (m1, t1), (m2, t2), (m3, _), (m4, _) = f(tr), f(~tr), f(tr & dn), f(~tr & dn)
    hh = (18 * 60 + k) // 60 % 24; mm = k % 60
    out.append(f"| {hh:02d}:{mm:02d} | {m1:+.2f} | {m2:+.2f} | {t1:+.1f} | {t2:+.1f} | {m3:+.2f} | {m4:+.2f} |")
print("\n".join(out)); open(f"{LAB}/edge4/e5_profile.md", "w").write("\n".join(out))
