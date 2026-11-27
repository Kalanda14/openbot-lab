"""Execution reality + wipe + edge haircut, on ALL real CME trading days (ext index incl. the Jan days m2 skipped).
Cells: P(hit 700) / P(end<100). Columns: starts 2020-05..2026 | 2024-26 | 2017-19. Output audit/a6_exec.md"""
import sys, time; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
from lib import *
t0 = time.time(); out = []
def P(s): print(s, flush=True); out.append(s)
bk = build(); X = ext_index()
B = {src: build(X, bsrc=src, trend="stack4+crypto", ref=bk) for src in ("real", "rt2")}
SA = starts_for(X, "2020-05-12", "2027", 30); ST = SA[X[SA] >= "2024"]; S17 = starts_for(X, "2017-03-01", "2020-01-01", 30)
o = B["real"]["on"]; okn = o["wc"].sum(1) != 0
mc = o["wc"].sum(1); P(f"overnight: legs worst by LOW / worst by CLOSE, per-leg median ratio {np.median((o['wl'] / np.where(o['wc'] < 0, o['wc'], np.nan))[np.isfinite(o['wl'] / np.where(o['wc'] < 0, o['wc'], np.nan))]):.2f}")
z = np.load(f"{LAB}/audit/onlow.npz"); r = z["ml"] / np.where(z["mc"] < -1e-5, z["mc"], np.nan); r = r[np.isfinite(r)]
P(f"whole night min LOW / min CLOSE drawdown: median {np.median(r):.2f}, p90 {np.percentile(r, 90):.2f}, p99 {np.percentile(r, 99):.2f}, share > 1.25: {np.mean(r > 1.25):.0%}; "
  f"extra in points (low-close) median {np.median((z['mc'] - z['ml']) * z['px']):.1f} p99 {np.percentile((z['mc'] - z['ml']) * z['px'], 99):.1f}")
LGc = {}
def lg(src="real", wsrc="close", wmult=1.25, hc=1.0):
    key = (src, wsrc, wmult, hc)
    if key not in LGc: LGc[key] = make(B[src], 30, 30, wsrc, wmult, hc)
    return LGc[key]
def row(nm, src="real", wsrc="close", wmult=1.25, hc=1.0, **kw):
    L = lg(src, wsrc, wmult, hc); tr = B[src]["tr"]
    a, b, c = sim(L, SA, tr, **kw), sim(L, ST, tr, **kw), sim(L, S17, tr, **kw)
    P(f"| {nm} | {fmt(a)} | {fmt(b)} | {fmt(c)} | {a['maxn_med']:.0f}x / {a['maxn_p90']:.0f}x | {a['cost']*100:.1f}% | {a['swap']*100:.1f}% |")
    return a, b, c
P("\n| scenario | 2020-26 | 2024-26 | 2017-19 | NQ notional/equity med/p90 | costs (% equity) | of which swap |\n|---|---|---|---|---|---|---|")
row("m2 assumptions, all real days")
row("wipe: real 1m LOWS x1.0", wsrc="low", wmult=1.0)
row("wipe: real 1m LOWS x1.25", wsrc="low", wmult=1.25)
row("wipe: lows + 10 pt bid spike at rollover", wsrc="low", wmult=1.0, spike_pt=10)
row("wipe: lows + 30 pt bid spike at rollover", wsrc="low", wmult=1.0, spike_pt=30)
row("B round trip 2.0 pt (vs 1.12)", src="rt2")
row("re-size cost 0.75 pt RTH / 1.5 pt overnight (vs 0.25)", cost_b=0.75, cost_on=1.5)
row("ON entry+exit +1.5 pt (total ~2.5 pt)", on_extra_pt=1.5)
for sw in (0.7e-4, 1.2e-4, 2.0e-4): row(f"CFD swap {sw*1e4:.1f} bp of notional per night", swap=sw)
for nc in (200, 100, 50, 20): row(f"broker leverage limit {nc}:1 notional", ncap=nc)
row("min lot 0.01 USTEC (=0.01 index units)", lot=0.01)
real = dict(src="rt2", wsrc="low", wmult=1.0, spike_pt=10, cost_b=0.75, cost_on=1.5, on_extra_pt=1.5, swap=1.2e-4, lot=0.01)
P("| **ALL CFD costs together (mid estimates)** | | | | | | |")
row("CFD mid, no leverage limit", **real)
row("CFD mid, 200:1 limit", ncap=200, **real)
row("CFD mid, 100:1 limit", ncap=100, **real)
low = dict(src="real", wsrc="low", wmult=1.0, spike_pt=5, cost_b=0.5, cost_on=1.0, on_extra_pt=0.8, swap=0.7e-4, lot=0.01)
row("CFD optimistic (raw-spread acct), no limit", **low)
P("| **forward edge haircut (B and ON mean x h), on CFD mid** | | | | | | |")
for h in (1.0, 0.8, 0.7, 0.5): row(f"edge x{h}, CFD mid, no limit", hc=h, **real)
for h in (0.8, 0.7): row(f"edge x{h}, futures costs (m2)", hc=h)
P(f"time {time.time()-t0:.0f}s")
open(f"{LAB}/audit/a6_exec.md", "w").write("\n".join(out))
