"""Summarize snapshot edges. Usage: python3 analyze.py [snapfile ...] (default: latest)."""
import json, glob, os, sys, collections, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
files = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "data", "snaps", "*.json")))[-1:]
MAXSPREAD = 0.03     # PM book must be tight
MINFAIR = 0.08       # ignore longshots (PM mids on tiny probs are noisy)

for f in files:
    rows = json.load(open(f))
    good = [r for r in rows if r["pm_spread"] <= MAXSPREAD and r["fair"] >= MINFAIR and r["match"] >= 0.8
            and r["hours_to_start"] > 0.05]
    anom = [r for r in good if abs(r["fair"] - r.get("book_fair", r["fair"])) > 0.20]
    good = [r for r in good if abs(r["fair"] - r.get("book_fair", r["fair"])) <= 0.20]
    print(f"\n=== {os.path.basename(f)}  rows={len(rows)} usable={len(good)} "
          f"events={len({(r['book'], r['event']) for r in good})}  excluded_anomalies(|pm-book|>0.20)={len(anom)} "
          f"in {len({r['event'] for r in anom})} events: {sorted({r['event'] for r in anom})[:6]}")
    for book in ("betlive", "crocobet"):
        g = [r for r in good if r["book"] == book]
        if not g:
            continue
        e = [r["edge"] for r in g]
        print(f"{book:9s} n={len(g):5d} median edge={st.median(e):+.3f}  mean={st.mean(e):+.3f}  "
              f">0:{sum(x > 0 for x in e):4d}  >2%:{sum(x > .02 for x in e):4d}  >5%:{sum(x > .05 for x in e):3d}  "
              f"edge_lo>2%:{sum(r['edge_lo'] > .02 for r in g):3d}  median overround={st.median(r['overround'] for r in g):.3f}")
        by = collections.defaultdict(list)
        for r in g:
            by[(r["sport"], r["kind"])].append(r)
        for k, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
            e = [r["edge"] for r in v]
            print(f"   {k[0]:13s} {k[1]:5s} n={len(v):5d} med={st.median(e):+.3f} p90={sorted(e)[int(.9 * len(e))]:+.3f} "
                  f">2%:{sum(x > .02 for x in e):3d} >5%:{sum(x > .05 for x in e):3d}  overround={st.median(r['overround'] for r in v):.3f}")
    top = sorted(good, key=lambda r: -r["edge"])[:25]
    print("  top edges:")
    for r in top:
        print(f"   {r['edge']:+.3f} lo={r['edge_lo']:+.3f} {r['book']:8s} {r['sport'][:10]:10s} {r['kind']:4s} {str(r['line'] or ''):4s} "
              f"{r['sel']:5s} @{r['odds']:<5} fair={r['fair']:.3f} spr={r['pm_spread']:.3f} m={r['match']:.2f} "
              f"{r['event'][:38]:38s} | {r['pm_event'][:38]} h={r['hours_to_start']}")
