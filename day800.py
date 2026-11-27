"""DAY-800 bot (fake money): every trading day a fresh EUR400 tries to reach EUR800 by 15:55 NY.
Attempt = overnight NQ (15:55 -> 03:30, only after a down day) + next day's B breakout. Browne deadline sizing f=0.3,
no cap except broker 400:1 notional. Stops at 800, bust at <= 1. Backtest (audit/a14_day800.py, CFD swap-free costs):
P(800) 27-32%, P(end < 100) 33-36%, the rest ends near 400 (no trade that day). Results: paper/day800.csv."""
import math, os, datetime as dt
from statistics import NormalDist
import challenge as CH

W0, G, F, NCAP = 400.0, 800.0, 0.3, 400.0
ND = NormalDist()


def lev(W, rem, expo):
    x = min(max(W / G, 1e-6), 0.999999)
    L = ND.pdf(ND.inv_cdf(x)) * G / (F * CH.SIG_TR * math.sqrt(max(rem, 0.02)) * W)
    return min(L, NCAP / max(expo, 1e-9))


def start(st, date):
    """called at 15:55: close the old attempt, open a new one."""
    d = st.get("D8")
    if d and d.get("state") == "running": end(st, "day over")
    st["D8"] = dict(state="running", date=str(date), W=W0, log=[])


def size(st, s, rem, jobs=False):
    d = st.get("D8", {})
    if d.get("state") != "running": return None
    e = CH.expo(st, s, jobs); return lev(d["W"], rem, e)


def apply(st, s, unit_ret, L, note="", jobs=False):
    d = st.get("D8", {})
    if d.get("state") != "running" or not L: return
    e = CH.expo(st, s, jobs); b = d["W"]; d["W"] = max(b * (1 + L * e * unit_ret), 0.0)
    d["log"].append([dt.datetime.utcnow().strftime("%m-%d %H:%M"), s, round(L * e, 1), round(unit_ret, 5), round(b, 2), round(d["W"], 2), note])
    if d["W"] >= G: end(st, "DOUBLED")
    elif d["W"] <= 1: end(st, "bust")


def end(st, why):
    d = st["D8"]; W = G if why == "DOUBLED" else d["W"]
    new = not os.path.exists("paper/day800.csv")
    with open("paper/day800.csv", "a") as f:
        if new: f.write("started,result,equity\n")
        f.write(f"{d['date']},{why},{W:.2f}\n")
    d["state"] = "done"; d["result"] = why; d["W"] = W


def board_lines(st):
    d = st.get("D8", {}); out = ["\n## Day-800 bot (fake EUR400 -> EUR800 in one day, high risk)\n"]
    if d: out.append(f"attempt from {d.get('date')} | state {d.get('state')} {d.get('result', '')} | equity **EUR {d.get('W', 0):.2f}**\n")
    if d.get("log"):
        out.append("| time UTC | sleeve | notional x | unit ret | before | after | note |\n|---|---|---|---|---|---|---|")
        for r in d["log"][-10:]: out.append("| " + " | ".join(map(str, r)) + " |")
    if os.path.exists("paper/day800.csv"):
        import pandas as pd
        t = pd.read_csv("paper/day800.csv")
        out.append(f"\n{len(t)} days: doubled {(t.result == 'DOUBLED').mean():.0%}, ended below 100 {(t.equity < 100).mean():.0%}, "
                   f"no-trade/flat {((t.equity >= 100) & (t.result != 'DOUBLED')).mean():.0%}\n\n```\n" + t.tail(10).to_string(index=False) + "\n```")
    return out
