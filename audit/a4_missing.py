"""Days present in real CME data but missing from the m2 day index (g.S from stack4_daily.csv): where, and how the book did."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
from lib import *
bk = build(); X = ext_index(); bx = build(X, trend="stack4+crypto", ref=bk); ix = bk["ix"]
miss = X[(X >= ix[0]) & ~X.isin(ix)]
print("missing days by year:", pd.Series(1, index=miss).groupby(miss.year).sum().to_dict())
print("month list:", sorted(set(str(d)[:7] for d in miss)))
R = pd.Series(sum(bx["P"].values()), index=X); W = pd.Series(sum(v for v in [bx["P"]["B"]*0]), index=X)
m = R[miss]; k = R[(X >= ix[0]) & X.isin(ix)]
print(f"book on missing days: mean {m.mean()*1e4:.1f} bp, std {m.std()*1e4:.1f}, Sharpe {m.mean()/m.std()*np.sqrt(252):.2f}; on kept days mean {k.mean()*1e4:.1f} bp std {k.std()*1e4:.1f} Sharpe {k.mean()/k.std()*np.sqrt(252):.2f}")
for c in ("B", "ON", "TREND"):
    s = pd.Series(bx["P"][c], index=X); print(c, f"missing-days mean {s[miss].mean()*1e4:.1f}bp  kept {s[k.index].mean()*1e4:.1f}bp")
