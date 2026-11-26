"""PAPER BOT (fake money) for the stacked book. Free public data only. State lives in paper/ (committed by Actions).
Book (fixed from backtest, vol target 10%): equity weights B 0.626, ON 0.388, TREND 0.036 (x notional), CARRY 3x.
 B      : Nasdaq noise-area breakout on NQ=F (Yahoo 5m), checks at :00/:30 10:00-15:30 NY, flat 15:55; jobs Friday 2x.
          sigma(k) = 14-day mean |close(k)/open - 1| at the same 5m bar. Cost 0.7 pt per round trip.
 ON     : long NQ=F from 15:55 close to next 9:30 open. Cost 0.5 bp.
 TREND  : BTC+ETH 55-day breakout, exit close < highest close since entry - 3*ATR(20), 0.1%/side (Binance daily).
 CARRY  : long Binance spot, short Hyperliquid perp (BTC+ETH): HL funding + spot-perp drift - cash (3.8%/yr).
Usage: python paper.py intraday   (every 30 min on weekdays)   |   python paper.py daily   (00:15 UTC)
Writes paper/state.json, paper/ledger.csv (date, sleeve, ret), paper/README.md (scoreboard).
"""
import json, os, sys, time, datetime as dt
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, requests

NY = ZoneInfo("America/New_York"); P = "paper"; os.makedirs(P, exist_ok=True)
W = dict(B=0.626, ON=0.388, TREND=0.036, CARRY=3.0); CASH = 0.038
UA = {"User-Agent": "Mozilla/5.0"}
st = json.load(open(f"{P}/state.json")) if os.path.exists(f"{P}/state.json") else {}
now = dt.datetime.now(NY)


def ledger(date, sleeve, ret, note=""):
    new = not os.path.exists(f"{P}/ledger.csv")
    with open(f"{P}/ledger.csv", "a") as f:
        if new: f.write("date,sleeve,ret,note\n")
        f.write(f"{date},{sleeve},{ret:.6f},{note}\n")


def nq5():
    for k in range(4):
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/NQ=F", params=dict(interval="5m", range="60d"), headers=UA, timeout=30)
        if r.ok: break
        time.sleep(10)
    j = r.json()["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    d = pd.DataFrame(dict(o=q["open"], c=q["close"]), index=pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert(NY)).dropna()
    return d


def intraday():
    if now.weekday() > 4: return
    d = nq5(); rth = d.between_time("09:30", "15:55")
    today = rth[rth.index.date == now.date()]
    if today.empty: return
    days = sorted(set(rth.index.date))
    past = [x for x in days if x < now.date()][-14:]
    o = float(today.o.iloc[0]); s = st.setdefault("B", {})
    if s.get("date") != str(now.date()):
        prev = [x for x in days if x < now.date()]
        pc = float(rth[rth.index.date == prev[-1]].c.iloc[-1]) if prev else o
        if abs(pc / o - 1) > 0.08: pc = o  # only a contract-roll glitch, not a real gap
        s.clear(); s.update(date=str(now.date()), open=o, pc=pc, pos=0, e=0.0, pnl=0.0, done=False, trades=[])
        if "ON" in st and st["ON"].get("entry"):  # close overnight at today's open
            on = st.pop("ON"); r = o / on["entry"] - 1 - 0.00005
            ledger(now.date(), "ON", r * W["ON"], f"raw {r:+.4%}")
    if s["done"]: return
    mins = now.hour * 60 + now.minute - 570
    jobs = now.weekday() == 4 and now.day <= 7; rt = 0.7
    if mins >= 385:  # 15:55 -> flat B, open overnight
        c = float(today.c.iloc[-1])
        if s["pos"]: s["pnl"] += (c - s["e"]) * s["pos"] - rt; s["trades"].append([str(now.time())[:5], "flat", c]); s["pos"] = 0
        r = s["pnl"] / s["open"] * (2 if jobs else 1)
        ledger(now.date(), "B", r * W["B"], f"raw {r:+.4%} trades {len(s['trades'])}"); s["done"] = True
        st["ON"] = dict(entry=c, date=str(now.date()))
        return
    k = (mins // 30) * 30
    if k < 30 or s.get("last_k") == k or mins - k > 25: return
    s["last_k"] = k
    bar = today[today.index <= today.index[0] + pd.Timedelta(minutes=k)]
    c = float(bar.c.iloc[-1])
    hist = []
    for x in past:
        g = rth[rth.index.date == x]
        at = g[g.index <= g.index[0] + pd.Timedelta(minutes=k)]
        if len(at): hist.append(abs(at.c.iloc[-1] / g.o.iloc[0] - 1))
    sg = float(np.mean(hist)) if hist else 0.01
    ub, lb = max(o, s["pc"]) * (1 + sg), min(o, s["pc"]) * (1 - sg)
    if s["pos"] and ((s["pos"] == 1 and c < ub) or (s["pos"] == -1 and c > lb)):
        s["pnl"] += (c - s["e"]) * s["pos"] - rt; s["pos"] = 0; s["trades"].append([f"{9 + (30 + k) // 60}:{(30 + k) % 60:02d}", "exit", c])
    if not s["pos"]:
        if c > ub: s["pos"], s["e"] = 1, c; s["trades"].append([f"{9 + (30 + k) // 60}:{(30 + k) % 60:02d}", "long", c])
        elif c < lb: s["pos"], s["e"] = -1, c; s["trades"].append([f"{9 + (30 + k) // 60}:{(30 + k) % 60:02d}", "short", c])


def kl(sym, n=120):
    r = requests.get("https://api.binance.com/api/v3/klines", params=dict(symbol=sym, interval="1d", limit=n), timeout=30).json()
    d = pd.DataFrame(r).iloc[:, :5].astype(float); d.index = pd.to_datetime(d[0], unit="ms"); d.columns = ["t", "o", "h", "l", "c"]
    return d.iloc[:-1]  # completed days only


def hl(body):
    return requests.post("https://api.hyperliquid.xyz/info", json=body, timeout=30).json()


def daily():
    y = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).date()
    if st.get("daily_done") == str(y): return
    tr, car = [], []
    for sym, coin in (("BTCUSDT", "BTC"), ("ETHUSDT", "ETH")):
        d = kl(sym); c, h, l = d.c, d.h, d.l
        atr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1).rolling(20).mean()
        hi55 = c.rolling(55).max().shift(1)
        t = st.setdefault("TREND", {}).setdefault(sym, dict(pos=0, best=0.0))
        ret = t["pos"] * (c.iloc[-1] / c.iloc[-2] - 1)  # position held over yesterday
        newpos = t["pos"]
        if t["pos"] == 0 and c.iloc[-1] > hi55.iloc[-1]: newpos, t["best"] = 1, c.iloc[-1]
        elif t["pos"] == 1:
            t["best"] = max(t["best"], c.iloc[-1])
            if c.iloc[-1] < t["best"] - 3 * atr.iloc[-1]: newpos = 0
        ret -= abs(newpos - t["pos"]) * 0.001; t["pos"] = newpos; tr.append(ret)
        t0 = int(dt.datetime.combine(y, dt.time(), dt.timezone.utc).timestamp() * 1000)
        fr = sum(float(x["fundingRate"]) for x in hl({"type": "fundingHistory", "coin": coin, "startTime": t0, "endTime": t0 + 86400000}))
        cd = hl({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d", "startTime": t0 - 86400000, "endTime": t0 + 86400000}})
        hc = {int(x["t"]): float(x["c"]) for x in cd}
        a, b = hc.get(t0 - 86400000), hc.get(t0)  # closes of the day before and of yesterday
        drift = (c.iloc[-1] / c.iloc[-2] - 1) - (b / a - 1) if a and b else 0.0
        car.append(fr + drift - CASH / 365)
    ledger(y, "TREND", float(np.mean(tr)) * W["TREND"], f"pos BTC {st['TREND']['BTCUSDT']['pos']} ETH {st['TREND']['ETHUSDT']['pos']}")
    ledger(y, "CARRY", float(np.mean(car)) * W["CARRY"], f"raw {np.mean(car):+.5%}")
    st["daily_done"] = str(y)


def board():
    if not os.path.exists(f"{P}/ledger.csv"): return
    L = pd.read_csv(f"{P}/ledger.csv", parse_dates=["date"])
    by = L.pivot_table(index="date", columns="sleeve", values="ret", aggfunc="sum").fillna(0)
    book = by.sum(axis=1); eq = (1 + book).cumprod()
    sh = book.mean() / book.std() * np.sqrt(252) if len(book) > 5 and book.std() > 0 else float("nan")
    lines = ["# Paper bot scoreboard (fake money, started 2026-11-27)\n",
             f"days: {len(book)} | book return: {eq.iloc[-1] - 1:+.2%} | Sharpe so far: {sh:+.2f} (needs months to mean anything)\n",
             "| sleeve | total return contribution | days |", "|---|---|---|"]
    for c in by: lines.append(f"| {c} | {by[c].sum():+.3%} | {(by[c] != 0).sum()} |")
    lines.append("\nlast 10 ledger rows:\n\n```\n" + L.tail(10).to_string(index=False) + "\n```")
    open(f"{P}/README.md", "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    {"intraday": intraday, "daily": daily}[sys.argv[1]]()
    json.dump(st, open(f"{P}/state.json", "w"), indent=1, default=str)
    board()
