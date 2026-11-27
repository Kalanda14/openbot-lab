"""Polymarket liquidity-rewards paper test - replay simulator.

Replays pmlp/data (written by collect.py). At every snapshot of a market we (re)post a two-sided quote:
  bid YES at fair - d, ask YES at fair + d (an ask without YES inventory = a NO bid at 1-ask), size = MULT x min_size,
held until the next snapshot (gap capped at MAXGAP; longer gaps = we assume no quote, no reward, no fills).

Pre-registered policies (do not tune after looking at results):
  mid1   fair = size-cutoff-adjusted mid of the OTHER orders, d = 1 cent
  midv2  fair = same,                                          d = max_spread / 2
  last1  fair = mean of the last 5 observed trades (YES-equivalent, < 6 h old), else mid1 fair; d = 1 cent

Rewards (docs.polymarket.com/market-makers/liquidity-rewards): the book incl. our quote gives the adjusted mid;
each order within v cents of it and >= min size scores ((v-s)/v)^2 * size; Q_one = YES bids (NO asks are mirrored
into them), Q_two = YES asks; Q_min = max(min, max/3) if mid in [0.10,0.90] else min. Our share of each sampled
minute = ours / (ours + others). Others are only visible as an aggregate book, so:
  base: others = Q_min(aggregate)     pess: others = Q_one + Q_two  (upper bound on the sum of their Q_min)
Pool per minute = rate_per_day / 1440 (exact if some LP qualifies in every minute of the UTC day, which we would).

Fills: every real taker trade (data-api, taker side) in the interval that reaches our price fills us first, for
min(remaining, trade size). One requote per snapshot restores full size. Inventory cap: |YES-NO| <= 2 x size,
the side that would grow it is not quoted. YES+NO pairs merge into $1 (gasless). Positions are marked at the
last observed mid, or at 1/0 if the market resolved. Gas: 0 per order by default (CLOB orders are off-chain
EIP-712 signatures; settlement/merge go through the gasless relayer); --gas sets a per-order cost for sensitivity.

usage: python pmlp/sim.py [--mult 1] [--gas 0] [--maxgap 1200] [--top 10]
"""
import json, os, glob, math, argparse, datetime as dt, collections

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
ap = argparse.ArgumentParser()
ap.add_argument("--mult", type=float, default=1.0); ap.add_argument("--gas", type=float, default=0.0)
ap.add_argument("--maxgap", type=int, default=1200); ap.add_argument("--top", type=int, default=10)
A = ap.parse_args()


def jl(pat):
    out = []
    for p in sorted(glob.glob(os.path.join(D, pat))):
        for l in open(p):
            try: out.append(json.loads(l))
            except Exception: pass
    return out


meta = {m["c"]: m for m in jl("meta.jsonl")}
res = {r["c"]: r for r in jl("resolved.jsonl") if r.get("closed")}
books, trades = collections.defaultdict(list), collections.defaultdict(list)
for b in jl("books/*.jsonl"): books[b["c"]].append(b)
for t in jl("trades/*.jsonl"):
    yes_p = t["p"] if t["o"] == 0 else 1 - t["p"]
    buy = (t["s"] == "B") == (t["o"] == 0)  # taker buys YES-equivalent
    trades[t["c"]].append((t["t"], buy, yes_p, t["z"]))
for c in books: books[c].sort(key=lambda b: b["t"])
for c in trades: trades[c].sort()


def pick(budget):
    """Ex-ante market choice for a capital budget: rank by the FIRST snapshot only (pool x naive share / capital)."""
    sc = []
    for c, s in books.items():
        b = s[0]; v, mn = b["v"], b["n"] * A.mult
        mid = adj_mid([tuple(x) for x in b["b"]], [tuple(x) for x in b["a"]], b["n"])
        if mid is None or v <= 1: continue
        q1, q2 = qside(b["b"], mid, v, b["n"]), qside(b["a"], mid, v, b["n"])
        ours = ((v - 1) / v) ** 2 * mn
        sc.append((b["r"] * ours / (ours + qmin(q1, q2, mid)) / mn, c, mn))
    out, used = set(), 0.0
    for _, c, cap in sorted(sc, reverse=True):
        if used + cap <= budget: out.add(c); used += cap
    return out


def adj_mid(bids, asks, mn):
    b = [p for p, s in bids if s >= mn]; a = [p for p, s in asks if s >= mn]
    return (max(b) + min(a)) / 2 if b and a else None


def S(p, mid, v): s = abs(p - mid) * 100; return ((v - s) / v) ** 2 if s < v else 0.0
def qside(side, mid, v, mn): return sum(S(p, mid, v) * s for p, s in side if s >= mn)
def qmin(q1, q2, mid): return max(min(q1, q2), max(q1, q2) / 3) if 0.10 <= mid <= 0.90 else min(q1, q2)


def run(policy, only=None):
    day = collections.defaultdict(lambda: {"rew": 0.0, "rew_p": 0.0, "orders": 0})
    per_mkt, fills_all, cap_t = {}, [], collections.defaultdict(float)
    for c, snaps in books.items():
        if only is not None and c not in only: continue
        size_seen = {}
        yes = no = cash = 0.0; rew = rew_p = 0.0; nf = 0; last_mid = None; alone = 0; qmins = 0
        tr = trades.get(c, []); ti = 0
        for i, b in enumerate(snaps[:-1]):
            dtsec = snaps[i + 1]["t"] - b["t"]
            if dtsec <= 0 or dtsec > A.maxgap: continue
            v, mn, k, rate = b["v"], b["n"], b["k"], b["r"]; size = A.mult * mn
            ob, oa = [tuple(x) for x in b["b"]], [tuple(x) for x in b["a"]]
            m0 = adj_mid(ob, oa, mn)
            if m0 is None:  # no two-sided size book: fall back to raw best prices
                if not ob or not oa: continue
                m0 = (ob[0][0] + oa[0][0]) / 2
            fair = m0
            if policy == "last1":
                rec = [p for (t, _, p, _) in tr if b["t"] - 6 * 3600 <= t <= b["t"]][-5:]
                if rec: fair = sum(rec) / len(rec)
            d = (v / 2 if policy == "midv2" else 1.0) / 100
            bid = math.floor(round((fair - d) / k, 6)) * k; ask = math.ceil(round((fair + d) / k, 6)) * k
            if oa and bid >= oa[0][0]: bid = oa[0][0] - k   # post-only: never cross
            if ob and ask <= ob[0][0]: ask = ob[0][0] + k
            net = yes - no
            qb = bid > 0.005 and net < 2 * size; qa = ask < 0.995 and net > -2 * size
            if not (qb or qa): continue
            allb = ob + ([(bid, size)] if qb else []); alla = oa + ([(ask, size)] if qa else [])
            mid = adj_mid(allb, alla, mn) or m0; last_mid = m0
            our = qmin(S(bid, mid, v) * size if qb else 0, S(ask, mid, v) * size if qa else 0, mid)
            q1, q2 = qside(ob, mid, v, mn), qside(oa, mid, v, mn)
            oth, oth_p = qmin(q1, q2, mid), q1 + q2
            sh = our / (our + oth) if our > 0 else 0.0; sh_p = our / (our + oth_p) if our > 0 else 0.0
            r = rate * sh * dtsec / 86400; rp = rate * sh_p * dtsec / 86400
            dk = dt.datetime.fromtimestamp(b["t"], dt.timezone.utc).date().isoformat()
            dd = day[dk]; dd["rew"] += r; dd["rew_p"] += rp
            dd["orders"] += qb + qa; rew += r; rew_p += rp
            alone += (oth == 0) * dtsec; qmins += dtsec
            cap_t[b["t"]] += (bid * size if qb else 0) + ((1 - ask) * size if qa else 0)
            # fills from real taker trades in [t, t+dt)
            rb, ra = (size if qb else 0), (size if qa else 0)
            while ti < len(tr) and tr[ti][0] < b["t"]: ti += 1
            j = ti
            while j < len(tr) and tr[j][0] < snaps[i + 1]["t"]:
                t, buy, p, z = tr[j]; j += 1
                if buy and ra > 0 and p >= ask - 1e-9:
                    q = min(ra, z); ra -= q; nf += 1
                    if yes >= q: yes -= q; cash += ask * q
                    else: no += q; cash -= (1 - ask) * q
                    fills_all.append((c, t, "sellYES", ask, q, p))
                elif not buy and rb > 0 and p <= bid + 1e-9:
                    q = min(rb, z); rb -= q; nf += 1
                    if no >= q: no -= q; cash += (1 - bid) * q
                    else: yes += q; cash -= bid * q
                    fills_all.append((c, t, "buyYES", bid, q, p))
            kk = min(yes, no); yes -= kk; no -= kk; cash += kk   # merge pairs
            cap_t[b["t"]] += yes * m0 + no * (1 - m0)
        if qmins == 0: continue
        mark = last_mid if last_mid is not None else 0.5
        if c in res and res[c].get("winner") is not None: mark = 1.0 if res[c]["winner"] == 0 else 0.0
        pnl = cash + yes * mark + no * (1 - mark)
        per_mkt[c] = dict(rew=rew, rew_p=rew_p, pnl=pnl, fills=nf, hours=qmins / 3600, alone=alone / qmins,
                          inv=yes - no, q=meta.get(c, {}).get("q", c[:10]))
    return day, per_mkt, fills_all, cap_t


span = [b["t"] for s in books.values() for b in s]
if not span: raise SystemExit("no data yet - run collect.py")
hrs = (max(span) - min(span)) / 3600
print(f"data: {len(books)} markets, {sum(len(s) for s in books.values())} snapshots, {sum(len(t) for t in trades.values())}"
      f" trades, {hrs:.2f} h  ({dt.datetime.fromtimestamp(min(span), dt.timezone.utc):%F %H:%M} UTC ->)"
      f"  mult={A.mult} gas/order=${A.gas}")
for pol in ("mid1", "midv2", "last1"):
    day, pm, fills, cap = run(pol)
    R = sum(x["rew"] for x in pm.values()); Rp = sum(x["rew_p"] for x in pm.values())
    P = sum(x["pnl"] for x in pm.values()); G = A.gas * sum(x["orders"] for x in day.values())
    scale = 24 / hrs if hrs > 0 else 0
    print(f"\n== {pol}: rewards ${R:.2f} (pess ${Rp:.2f}), fill PnL ${P:+.2f} over {len(fills)} fills, gas ${G:.2f}"
          f"  -> per 24h: rewards ${R*scale:.0f} (pess {Rp*scale:.0f}), fills {P*scale:+.0f}, net ${(R+P-G)*scale:.0f}"
          f" (pess {(Rp+P-G)*scale:.0f}) | max capital ${max(cap.values()) if cap else 0:.0f}")
    if len(day) > 1:
        print("   by day (UTC; partial days scale badly): " +
              ", ".join(f"{k} rew {v['rew']:.0f}" for k, v in sorted(day.items())))
    for bud in (50, 460):
        sel = pick(bud); _, pmb, fb, capb = run(pol, sel)
        Rb = sum(x["rew"] for x in pmb.values()); Pb = sum(x["pnl"] for x in pmb.values())
        Rpb = sum(x["rew_p"] for x in pmb.values())
        print(f"   budget ${bud}: {len(sel)} mkts (picked on first snapshot), per 24h rewards ${Rb*scale:.1f} "
              f"(pess {Rpb*scale:.1f}), fills {Pb*scale:+.1f}, net ${(Rb+Pb)*scale:.1f} | max capital ${max(capb.values()) if capb else 0:.0f}")
    for c, x in sorted(pm.items(), key=lambda kv: -(kv[1]["rew"] + kv[1]["pnl"]))[:A.top]:
        print(f"   {x['q'][:58]:58s} rew {x['rew']:6.2f} pess {x['rew_p']:6.2f} pnl {x['pnl']:+6.2f}"
              f" fills {x['fills']:2d} alone {x['alone']:.0%} inv {x['inv']:+.0f}")
    worst = sorted(pm.items(), key=lambda kv: kv[1]["pnl"])[:3]
    print("   worst fill PnL: " + "; ".join(f"{x['q'][:40]} {x['pnl']:+.2f}" for _, x in worst))
