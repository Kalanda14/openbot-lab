"""Order-flow tests on REAL CME NQ trades (Databento 'trades', side = aggressor: B buy, A sell). Apr-Nov 2026.
Rules fixed BEFORE looking at results. Train = Apr-Jul 2026, Test = Aug-Nov 2026. Cost 1.12 pt per round trip.
Per minute 9:30-16:00 NY: buy vol, sell vol, big buy/sell vol (trade size >= 10 NQ), close price.
 OF1 flow30 : every 30 min (10:00..15:30) go WITH sign of (buy-sell) of the last 30 min, hold 30 min
 OF2 big30  : same with big trades only
 OF3 absorb : last 30 min price moved one way but flow the other way -> trade WITH flow, hold 30 min
 OF4 open   : sign of flow 9:30-10:00 -> hold 10:00-15:59
 OF5 B+flow : setup B, but only take a breakout when day flow since 9:30 has the same sign
 OF6 flow5  : every 5 min, with sign of last-5-min flow imbalance if |imb| > 20%, hold 5 min
Usage: python ofb.py build   (dbdata/nq_trades_*.dbn.zst -> dbdata/of_min.pkl)
       python ofb.py test
"""
import glob, sys, numpy as np, pandas as pd
RT, N = 1.12, 390


def build():
    import databento as db
    out = []
    for f in sorted(glob.glob("dbdata/nq_trades_*.dbn.zst")):
        st = db.DBNStore.from_file(f)
        for ch in st.to_df(count=5_000_000):
            ch = ch[["price", "size", "side"]]
            ch.index = ch.index.tz_convert("America/New_York")
            ch = ch.between_time("09:30", "15:59:59")
            if ch.empty: continue
            b = ch["side"].eq("B"); a = ch["side"].eq("A"); big = ch["size"] >= 10
            g = pd.DataFrame(dict(buy=ch["size"].where(b, 0), sell=ch["size"].where(a, 0),
                                  bbuy=ch["size"].where(b & big, 0), bsell=ch["size"].where(a & big, 0),
                                  px=ch["price"])).resample("1min")
            out.append(pd.concat([g[["buy", "sell", "bbuy", "bsell"]].sum(), g["px"].last().rename("close")], axis=1))
            print(f, ch.index[-1], flush=True)
    m = pd.concat(out); m = m.groupby(level=0).agg(dict(buy="sum", sell="sum", bbuy="sum", bsell="sum", close="last"))
    m.dropna(subset=["close"]).to_pickle("dbdata/of_min.pkl")


def days():
    m = pd.read_pickle("dbdata/of_min.pkl")
    m[["buy", "sell", "bbuy", "bsell"]] = m[["buy", "sell", "bbuy", "bsell"]].astype("int64")  # sizes are uint32
    for d, g in m.groupby(m.index.date):
        if len(g) < N * 0.9: continue
        g = g.copy(); g.index = g.index.hour * 60 + g.index.minute - 570
        g = g.reindex(range(N)); g[["buy", "sell", "bbuy", "bsell"]] = g[["buy", "sell", "bbuy", "bsell"]].fillna(0)
        g["close"] = g["close"].ffill().bfill()
        yield pd.Timestamp(d), g


def test():
    rows, hist, prev = [], [], None
    for d, g in days():
        C = g.close.values; fl = (g.buy - g.sell).values; bf = (g.bbuy - g.bsell).values; vol = (g.buy + g.sell).values
        r = dict(d=d)
        p1 = p2 = p3 = 0.0
        for k in range(30, 360, 30):
            f30, b30, mv = fl[k - 30:k].sum(), bf[k - 30:k].sum(), C[k - 1] - C[k - 31] if k >= 31 else C[k - 1] - C[0]
            fwd = C[k + 29] - C[k - 1]
            p1 += np.sign(f30) * fwd - RT * (f30 != 0)
            p2 += np.sign(b30) * fwd - RT * (b30 != 0)
            if np.sign(mv) * np.sign(f30) < 0: p3 += np.sign(f30) * fwd - RT
        r["OF1"], r["OF2"], r["OF3"] = p1, p2, p3
        r["OF4"] = np.sign(fl[:30].sum()) * (C[-1] - C[29]) - RT
        p6 = 0.0
        for k in range(5, N - 5, 5):
            v = vol[k - 5:k].sum(); imb = fl[k - 5:k].sum() / v if v else 0
            if abs(imb) > 0.2: p6 += np.sign(imb) * (C[k + 4] - C[k - 1]) - RT
        r["OF6"] = p6
        # B and B+flow (same rules as paths.py, entries/exits at :00/:30 closes)
        o = C[0]
        if len(hist) >= 14 and prev is not None:
            pc = prev if abs(prev / o - 1) < 0.03 else o
            sg = np.mean(np.vstack(hist[-14:]), axis=0); ub, lb = max(o, pc) * (1 + sg), min(o, pc) * (1 - sg)
            for nm, filt in (("B", False), ("OF5", True)):
                pos, e, pn = 0, 0.0, 0.0
                for k in range(30, N, 30):
                    c = C[k] if k < N else C[-1]
                    if pos and ((pos == 1 and c < ub[k]) or (pos == -1 and c > lb[k])): pn += (c - e) * pos - RT; pos = 0
                    if not pos and k < N - 1:
                        cf = fl[:k].sum()
                        if c > ub[k] and (not filt or cf > 0): pos, e = 1, c
                        elif c < lb[k] and (not filt or cf < 0): pos, e = -1, c
                if pos: pn += (C[-1] - e) * pos - RT
                r[nm] = pn
        hist.append(np.abs(C / o - 1)); prev = C[-1]
        rows.append(r)
    df = pd.DataFrame(rows).set_index("d")
    tr, te = df[:"2026-07-31"], df["2026-08-01":]
    sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
    tt = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if x.std() > 0 else 0
    L = [f"days train {len(tr)} / test {len(te)}; pts per day per 1 NQ-equivalent (MNQ $ = 2x)\n",
         "| setup | TRAIN pts/day | Sharpe | t | TEST pts/day | Sharpe | t |", "|---|---|---|---|---|---|---|"]
    for c in ("OF1", "OF2", "OF3", "OF4", "OF5", "OF6", "B"):
        a, b = tr[c].dropna(), te[c].dropna()
        L.append(f"| {c} | {a.mean():+.2f} | {sh(a):+.2f} | {tt(a):+.1f} | {b.mean():+.2f} | {sh(b):+.2f} | {tt(b):+.1f} |")
    open("of_results.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    build() if sys.argv[1] == "build" else test()
