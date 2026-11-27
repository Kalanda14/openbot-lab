"""MONTH CHALLENGE (fake money): EUR400 -> EUR700 within 31 trading days. Plan from audit a8-a13 + edge4:
- start only when NQ vol20 >= 1.504%/day (24%/yr) OR NQ 60-day return >= 9.08% (start rule, a8b)
- Browne deadline sizing f=0.5 on trading days left, re-size band 50%, smooth cap = 100*(W-100)/300 (a12 'C')
- sleeves: B (NQ breakout), ON (NQ 15:55->03:30 after down day), TREND (BTC/ETH), GOLD night (GLD 15:55->09:30) x0.5
- stop the moment equity >= 700 (checked at every event), bust at <= 1.
Exposure per unit Browne leverage = k * w_s * volscale_s (constants from audit/lib.build calibration 2020-03..2021).
State lives in st["CH"] (paper/state.json). History of finished challenges in paper/challenges.csv."""
import math, os, datetime as dt
from statistics import NormalDist
import numpy as np

W0, G, DAYS, F, BAND = 400.0, 700.0, 31, 0.5, 0.5
K, SIG_TR = 0.9479, 0.005992
WGT = dict(B=0.376, ON=0.602, TREND=0.022)
NSTD = dict(B=0.008495, ON=0.006813, TREND=0.1415)
GOLD_X, GOLD_STD = 0.5, 0.0080   # gold risk = half of ON's
VOL_TH, RET_TH = 0.015045, 0.09077
ND = NormalDist()


def cap(W): return max(100 * min(max((W - 100) / 300, 0), 1), 1)


def browne(W, rem):
    x = min(max(W / G, 1e-6), 0.999999)
    lev = ND.pdf(ND.inv_cdf(x)) * G / (F * SIG_TR * math.sqrt(max(rem, 0.05)) * W)
    return min(lev, cap(W))


def volscale(st, s):
    h = [r for r in st.get("RAW", {}).get(s, []) if r != 0][-20:]
    if len(h) < 5: return 1.0
    return float(np.clip(NSTD[s] / np.std(h, ddof=1), 0, 3)) if np.std(h) > 0 else 1.0


def expo(st, s, jobs=False):
    if s == "GOLD": return GOLD_X * K * WGT["ON"] * volscale(st, "ON") * NSTD["ON"] / GOLD_STD
    return K * WGT[s] * volscale(st, s) * (2 if (s == "B" and jobs) else 1)


def raw(st, s, r):
    """keep raw sleeve returns for the vol scale"""
    h = st.setdefault("RAW", {}).setdefault(s, []); h.append(float(r)); del h[:-60]


def maybe_start(st, today, nq_close):
    """called once per day with NQ daily closes (list, oldest first)."""
    c = st.setdefault("CH", {"state": "waiting", "n": 0})
    if c["state"] in ("running",): return
    if len(nq_close) < 61: return
    lr = np.diff(np.log(nq_close))
    v20, r60 = float(np.std(lr[-20:], ddof=1)), nq_close[-1] / nq_close[-61] - 1
    c["rule"] = dict(date=str(today), vol20_yr=round(v20 * math.sqrt(252), 3), ret60=round(r60, 4))
    if v20 >= VOL_TH or r60 >= RET_TH:
        c.update(state="running", n=c.get("n", 0) + 1, start=str(today), W=W0, days_used=0, last_day=None, lev={}, log=[])


def rem(st, frac=0.0):
    c = st["CH"]; return DAYS - c["days_used"] - frac


def new_day(st, today):
    c = st.get("CH", {})
    if c.get("state") != "running" or c.get("last_day") == str(today): return
    if c["last_day"] is not None: c["days_used"] += 1
    c["last_day"] = str(today)
    if c["days_used"] >= DAYS: finish(st, "time up")


def lev_for(st, s, frac):
    """Browne leverage with 50% band: keep last leverage of this sleeve unless the new one differs by > 50%."""
    c = st.get("CH", {})
    if c.get("state") != "running": return None
    new = browne(c["W"], rem(st, frac)); old = c["lev"].get(s)
    if old and abs(new - old) <= BAND * old: return old
    c["lev"][s] = new; return new


def apply(st, s, unit_ret, frac, note="", jobs=False, lev=None):
    """unit_ret = sleeve return per 1x notional (after costs). Returns leverage used."""
    c = st.get("CH", {})
    if c.get("state") != "running": return None
    L = lev if lev is not None else lev_for(st, s, frac)
    e = expo(st, s, jobs); before = c["W"]
    c["W"] = max(before * (1 + L * e * unit_ret), 0.0)
    c["log"].append([dt.datetime.utcnow().strftime("%m-%d %H:%M"), s, round(L, 1), round(e, 3), round(unit_ret, 5), round(before, 2), round(c["W"], 2), note])
    del c["log"][:-40]
    if c["W"] >= G: finish(st, "TARGET HIT")
    elif c["W"] <= 1: finish(st, "bust")
    return L


def finish(st, why):
    c = st["CH"]; W = min(c["W"], G) if why == "TARGET HIT" else c["W"]
    new = not os.path.exists("paper/challenges.csv")
    with open("paper/challenges.csv", "a") as f:
        if new: f.write("n,start,end,days,result,equity\n")
        f.write(f"{c['n']},{c['start']},{c.get('last_day')},{c['days_used']},{why},{W:.2f}\n")
    st["CH"] = {"state": "waiting", "n": c["n"], "last": dict(result=why, equity=round(W, 2), start=c["start"])}


def board_lines(st):
    c = st.get("CH", {}); out = ["\n## Month challenge (fake EUR400 -> EUR700 in 31 trading days)\n"]
    if c.get("state") == "running":
        out.append(f"RUNNING #{c['n']} since {c['start']} | equity **EUR {c['W']:.2f}** | trading days used {c['days_used']}/{DAYS} | "
                   f"leverage now {browne(c['W'], rem(st)):.1f}x (cap {cap(c['W']):.0f})\n")
        out.append("| time UTC | sleeve | lev | expo | unit ret | before | after | note |\n|---|---|---|---|---|---|---|---|")
        for r in c["log"][-12:]: out.append("| " + " | ".join(map(str, r)) + " |")
    else:
        out.append(f"WAITING for start rule (NQ vol >= 24%/yr or 60-day return >= 9.1%). Last check: {c.get('rule')}")
        if c.get("last"): out.append(f"\nLast challenge: {c['last']}")
    if os.path.exists("paper/challenges.csv"): out.append("\nFinished:\n\n```\n" + open("paper/challenges.csv").read() + "```")
    return out
