| filter | days kept train | B Sh train | days kept test | B Sh test |
|---|---|---|---|---|
| base (no filter) | 100% | 0.71 | 100% | 1.52 |
| vol20 >= train p33 | 66% | 0.69 | 94% | 1.64 |
| vol20 <= train p67 | 66% | 0.82 | 55% | 1.06 |
| |gap| <= train p90 | 88% | 1.06 | 84% | 1.14 |
| |gap| >= train p10 | 88% | 1.03 | 91% | 1.37 |
| VIX(t-1) >= train median | 50% | 0.50 | 65% | 1.21 |
| skip Mondays | 81% | 0.53 | 81% | 1.67 |
| prior 5d B pnl > 0 | 51% | 0.72 | 52% | 0.68 |
| prior 5d B pnl <= 0 | 48% | 0.33 | 48% | 1.53 |

variants: 8