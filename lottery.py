"""Month-1 +$1,000 via MANY cheap prop evals at different firms, each at aggressive size (losses capped at fees).
Wallet $430. Each account: eval MNQ / funded MNQ / tp chosen per firm (aggressive). Payouts in 21 trading days.
Firms (cheapest real 2026 prices): Apex Intraday $25+$99, Topstep Consistency $25 (+$149, alerts no API), MFF Rapid $125,
Take Profit Trader Classic $102/mo (activation $0 w/ NOFEE40; day-one payouts above $52k; alerts/manual),
FundedNext Flex $75, Lucid Daily $116, Bulenox Momentum $79. Test starts 2022-26."""
import itertools, numpy as np, fundsim as F, propsim as P, month1fund as M
A = M.A
CH = {"APXI": ("Apex Intraday 50K", 25), "TSC": ("Topstep 50K Consistency", 25), "MFF": ("MFF Rapid 50K", 125),
      "TPT": ("Take Profit Trader Classic", 102), "FNF": ("FundedNext Flex 50K", 75), "LUD": ("Lucid Daily 50K (EOD)", 116),
      "BUL": ("Bulenox Momentum 50K", 79)}
def acct(key, ke, kf, tp):
    nm, fee = CH[key]; r = dict(A[nm]); r["fee"] = fee; r.pop("data", None)
    return r, tuple(P.day_table(F.m, F.lo, k, tp, None, r.get("dll")) for k in (ke, kf, kf))
def run(books, s, D=21):
    w = F.BUDGET; acc = []
    for r, T in books:
        if w >= r["fee"]: w -= r["fee"]; acc.append([r, T, P.new_acct(r)])
    for i in range(s, s + D):
        for x in acc:
            if x[2] is None: continue
            x[2], w = P.step(x[2], x[0], x[1], i, w)
    return w - F.BUDGET
SIZES = [(25, 8, 1500), (16, 8, None), (40, 8, 1500)]
out = []
for keys in (["TSC"], ["APXI", "TSC"], ["APXI", "TSC", "BUL", "FNF"], ["APXI", "TSC", "BUL"], ["APXI", "TSC", "FNF", "MFF"], ["APXI", "TSC", "TPT"]):
    for sz in SIZES:
        books = [acct(k, *sz) for k in keys]
        x = np.array([run(books, s) for s in range(F.half, F.n - 30, 2)])
        line = f"> {'+'.join(keys)} size {sz}: P(+$1,000) {np.mean(x >= 1000):.0%} | P(+$430) {np.mean(x >= 430):.0%} | P(money back) {np.mean(x >= 0):.0%} | avg {x.mean():+.0f}"
        print(line, flush=True); out.append(line)
open("lottery.md", "w").write("\n".join(out) + "\n")
