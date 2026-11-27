"""(A) Book variants: Sharpe 2020-21 (weights train) / 2022-26 (test) / 2024-26, and Browne bound P(400->700 in 21 d)."""
from common import *
rows = [("ref: stack4 B (=real CME), base ON, rp (m1 book)", dict(bsrc="stack4"))]
for on in ("base", "plus"):
    for eom in (False, True):
        for wm in ("rp", "ms"):
            rows.append((f"{on} ON{' + EOM3' if eom else ''}, {'risk parity' if wm=='rp' else 'train maxSharpe shrunk 50%'}", dict(bsrc="real", on=on, eom=eom, wmode=wm)))
rows.append(("(Dukascopy B paths) base ON, rp", dict(bsrc="duka")))
print("| book | weights | Sharpe 20-21 | 22-26 | 24-26 | Browne(22-26) | Browne(24-26) |\n|---|---|---|---|---|---|---|")
for nm, kw in rows:
    bk = build(**kw); R = sum(bk["P"].values())
    a, b, c = sh(R[:NTR]), sh(R[NTR:]), sh(R[idx >= "2024"])
    print(f"| {nm} | {bk['w']} | {a:.2f} | {b:.2f} | {c:.2f} | {browne(b):.1%} | {browne(c):.1%} |", flush=True)
for src in ("stack4", "duka", "real"):
    bk = build(bsrc=src); x = bk["P"]["B"]; print(f"B sleeve {src}: Sharpe 20-21 {sh(x[:NTR]):.2f} 22-26 {sh(x[NTR:]):.2f}")
x = EOM; print(f"EOM3 sleeve: 20-21 {sh(x[:NTR]):.2f} 22-26 {sh(x[NTR:]):.2f}")
