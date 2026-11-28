"""Matched-betting calculator (Betfair.es Exchange lay). Usage:
  python mb/calc.py q  STAKE BACK_ODDS LAY_ODDS [COMM=0.05]   # qualifying bet (real money)
  python mb/calc.py snr FREEBET BACK_ODDS LAY_ODDS [COMM]     # free bet, stake NOT returned
  python mb/calc.py sr  FREEBET BACK_ODDS LAY_ODDS [COMM]     # free bet, stake returned
Prints lay stake, liability (cash you need on the exchange) and profit if back wins / lay wins (should be ~equal)."""
import sys
def lay(kind, s, b, l, c=0.05):
    win_back = s * (b - 1) if kind == "snr" else s * b if kind == "sr" else s * b
    ls = win_back / (l - c)
    liab = ls * (l - 1)
    if kind == "q":   pb, pl = s * (b - 1) - liab, ls * (1 - c) - s
    elif kind == "snr": pb, pl = s * (b - 1) - liab, ls * (1 - c)
    else:             pb, pl = s * (b - 1) - liab, ls * (1 - c)
    return ls, liab, pb, pl
if __name__ == "__main__":
    k, s, b, l = sys.argv[1], *map(float, sys.argv[2:5]); c = float(sys.argv[5]) if len(sys.argv) > 5 else 0.05
    ls, liab, pb, pl = lay(k, s, b, l, c)
    print(f"{k}: back {s:.2f} @ {b} | LAY {ls:.2f} @ {l} (liability {liab:.2f}) | if back wins {pb:+.2f} | if lay wins {pl:+.2f}"
          + (f" | keeps {min(pb,pl)/s:.0%} of free bet" if k != "q" else f" | qualifying loss {min(pb,pl)/s:.1%}"))
