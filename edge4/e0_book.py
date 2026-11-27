"""Export the book's daily sleeve returns (B, ON, TREND) on the real CME ext index 2017-2026 via audit/lib.build."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
from lib import *
bk = build(); X = ext_index()
b = build(X, bsrc="real", trend="stack4+crypto", ref=bk)
df = pd.DataFrame({k: b["S"][k] for k in ("B", "ON", "TREND")}, index=X)
df["BOOK"] = sum(b["P"][k] for k in ("B", "ON", "TREND"))
df.to_csv(f"{LAB}/edge4/book_daily.csv")
print(df.describe()); print((df != 0).mean())
for c in df: s = df[c]; print(c, "ann Sharpe all-days", round(s.mean() / s.std() * np.sqrt(252), 2),
                   "2017-21", round(s[:"2021"].mean() / s[:"2021"].std() * 252**.5, 2), "2022-26", round(s["2022":].mean() / s["2022":].std() * 252**.5, 2))
print(df.corr().round(2))
