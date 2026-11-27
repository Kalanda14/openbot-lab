# a12 (research agent): bending the hit / big-loss frontier, EUR400 -> 700 in 31 trading days

Setup = a11_80 exactly (a8b -> a8_starttime -> a6_exec; CFD swap-free costs spike 10pt, cost_b 0.75, cost_on 1.5, on_extra 1.5; start rule vol20 high | ret60 top third; f 0.5, band 0.5). New sim copy: audit/lib2.py `sim2` (hooks: wealth/regime cap function, Browne target function, floor F; lib.py untouched; reproduces a11 cap100/50/30 exactly).
Cells = P(hit 700) / P(end < 100). SA = starts 2020-05..2026 (n=480, overlapping), ST = 2024-26 (n=168, subset of SA), S17 = 2017-19 (n=105).
Variants tried (31 days, excluding 3 baselines): **76**, plus 2 21-day reference rows and 1 FOMC event study. Selection always on SA only.

## Key rows
| variant | SA hit/<100 | ST | S17 |
|---|---|---|---|
| base cap100 | 77% / 17% | 71% / 21% | 83% / 5% |
| base cap50 | 68% / 9% | 64% / 8% | 74% / 5% |
| base cap30 | 54% / 1% | 49% / 4% | 61% / 0% |
| A step hi100 W<200->cap30 | 72% / 7% | 66% / 10% | 80% / 1% |
| A step hi100 W<250->cap30 | 69% / 5% | 63% / 7% | 74% / 2% |
| A step hi100 W<300->cap30 | 69% / 4% | 64% / 6% | 72% / 1% |
| A step hi200 W<200->cap10 | 68% / 2% | 64% / 2% | 75% / 0% |
| B stop-out W<150 | 68% / 4% | 63% / 5% | 73% / 2% |
| C smooth hi100*((W-100)/300)^1 | 69% / 3% | 62% / 5% | 72% / 5% |
| G 3-level 150 (W>=350) / 50 (>=250) / 20 | 68% / 2% | 64% / 4% | 72% / 1% |
| J late-game only: cap10 if W<250 and day>=21 | 75% / 14% | 70% / 14% | 82% / 3% |
| D vol cap hi100 (vol<24%) lo50 | 74% / 16% | 70% / 21% | 82% / 5% |
| E target 500 while W<250 | 76% / 16% | 70% / 20% | 80% / 8% |
| F floor-cushion F100 cap100 | 73% / 21% | 66% / 23% | 70% / 11% |
| FOMC kF1 cap100 | 75% / 19% | 68% / 24% | 86% / 3% |
| FOMC kF1 cap30 | 54% / 1% | 52% / 4% | 63% / 0% |
| FOMC kF1 + A step hi100 W<250->cap30 | 70% / 5% | 63% / 7% | 78% / 1% |
| ref 21d base cap100 | 72% / 18% | 65% / 18% | 68% / 7% |
| ref 21d step hi100 W<250->cap30 | 64% / 5% | 56% / 4% | 66% / 2% |

## Picks (made on SA, then read off ST / S17)
- best SA hit with SA <100 <= 5%: **C smooth hi100*((W-100)/300)^1** -> C smooth hi100*((W-100)/300)^1 | 69% / 3% | 62% / 5% | 72% / 5% |
- lowest SA <100 with SA hit >= 75%: **E target 500 while W<250** -> E target 500 while W<250 | 76% / 16% | 70% / 20% | 80% / 8% |
  (J late-game cap shows 75% / 14% but its SA hit is just under 75% unrounded, so it is not eligible; either way the tail stays >= 14%.)
- best worst-period hit with <100 <= 5% in ALL three periods (uses all periods, so in-sample): **G 3-level 150 (W>=350) / 50 (>=250) / 20** -> G 3-level 150 (W>=350) / 50 (>=250) / 20 | 68% / 2% | 64% / 4% | 72% / 1% |

## Theory bound (why 80% / 5% is not reachable by sizing alone)
Complete-market lognormal model: unconstrained deadline (Browne) P(hit)=77% implies theta*sqrt(T) = 0.559. The best possible P(hit) with P(end<100) <= 5% (payoff 700 / 100 / 0) at that edge is **73.1%**. 80% at 5% needs theta*sqrt(T) >= 0.765, i.e. Sharpe x1.37 or time x1.87 (~58 trading days). Empirical best at <=5% (69%) is already close to the 73% bound, and the bound ignores gaps, costs and lot size.

## What failed
- D regime cap by vol20: no help (tail comes from grinding losses, not only high-vol days).
- E smaller Browne target when behind: no help (cap binds anyway).
- F Browne on cushion over a 50/100 floor: worse tail (cap still binds, gaps).
- B2 permanent stop / I path-drawdown trigger: safe but costs too much hit.
- H f 0.35/0.7 with step cap: no better than f 0.5.
- FOMC sleeve: the pre-FOMC overnight drift is REAL in the data (15:55->03:30 before statements: train 2017-21 +29 bp t=3.6, test 2022-26 +19.5 bp t=2.25 vs +5.5/+1.8 bp other nights; RTH 09:30->13:55 part is zero), but adding it to the ON legs at kF 0.5-3 x ON notional HURTS SA and ST at every cap (helps only S17). Rejected. Only ~1.3 events per 31-day window and added variance at capped leverage outweigh +20 bp.

## What worked (a bit)
- Wealth-aware step cap (cap 100 while W >= 200-300, cap 20-30 below) beats a flat cap at the same tail: flat cap30 = 54/1, 49/4, 61/0 vs 3-level 150/50/20 = 68/2, 64/4, 72/1. That bends the frontier ~+14 hit points at the safe end, but tops out near 69% at <=5% tail, under the 80% goal.

Files: lib2.py, a12_base.py, a12_sizing.py/.md/.json, a12_fomc.py/.md, a12_fomc_days.csv, a12_fomc_sim.py/.md/.json, a12_more.py/.md/.json, a12_agent.py.
