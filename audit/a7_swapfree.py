"""Exness-style scenarios: CFD mid costs with swap 0 (swap-free) vs 1.2bp, under 400:1 and 200:1 limits; edge x0.8."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a6_exec.py").read().split('P("\\n| scenario')[0])
P("| scenario | 2020-26 | 2024-26 | 2017-19 | notional med/p90 | costs | swap |")
real = dict(src="rt2", wsrc="low", wmult=1.0, spike_pt=10, cost_b=0.75, cost_on=1.5, on_extra_pt=1.5, lot=0.01)
for sw in (1.2e-4, 0.0):
    for nc in (400, 200):
        for h in (1.0, 0.8):
            row(f"swap {sw*1e4:.1f}bp, {nc}:1, edge x{h}", hc=h, swap=sw, ncap=nc, **real)
