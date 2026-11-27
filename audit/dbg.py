import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
from lib import *
bk = build(); X = ext_index(); bx = build(X, trend="crypto", ref=bk); ix = bk["ix"]
pos = X.get_indexer(ix); print("missing g.S days in ext", (pos < 0).sum(), "ext days in 2020-03+", (X >= ix[0]).sum(), len(ix))
for c in ("B", "ON", "TREND"):
    a = bk["P"][c]; b = bx["P"][c][pos]; print(c, np.abs(a - b).max(), np.corrcoef(a, b)[0, 1], a.std(), b.std())
print(bk["w"], bx["w"], bk["k"], bx["k"])
extra = X[(X >= ix[0]) & ~X.isin(ix)]; print("extra ext days", len(extra), list(extra[:10]))
Rx = pd.Series(sum(bx["P"].values()), index=X) / bx["k"]; Ro = pd.Series(sum(bk["P"].values()), index=ix) / bk["k"]
print("R tr std ext", Rx[bx["tr"]].std(), "orig", Ro[bk["tr"]].std())
a = pd.DataFrame({c: pd.Series(bx["P"][c], index=X)[bx["tr"]] / bx["k"] for c in ("B", "ON", "TREND")})
print(a.abs().max(), a.std()); print(a.loc[a.abs().max(1).nlargest(5).index])
print("crypto raw on missing days", pd.Series(bx["S"]["TREND"], index=X)[extra].abs().nlargest(3))
