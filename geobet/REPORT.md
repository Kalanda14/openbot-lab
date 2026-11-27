# geobet: can we value-bet Georgian bookmakers? (test 2026-11-27)

**Verdict: no.** There is no usable edge for a Georgian resident with EUR400.

## What was tested
- **Books:** Betlive and Crocobet, using their public no-login odds APIs.
  - Crystalbet is geo-blocked. Adjarabet returns 403.
  - Europebet (now Betsson) and Leaderbet: API not found.
- **Fair price:** Polymarket sports order books (real bid/ask mids, not prices-history). 1,327 events within 36h.
- **Matching:** about 870 matched events per snapshot.
- **Snapshots:** 6 over 80 min, about 3,500 outcomes per book each.
- **Edge:** soft_odds x fair - 1. Filters: PM spread <= 3c, fair >= 0.08.

## Results
- **Same feed:** Betlive and Crocobet resell one B2B feed (Betradar IDs). 95% of shared outcomes have identical odds.
- **Margin:** about 12% everywhere (EPL 1X2 11.3%, lower leagues about 13%).
- **Median edge:** -10% to -12% across 1X2, O/U, BTTS, basketball and tennis.
- **Positive edges, all 6 snapshots:** only 3 events, excluding one void-risk anomaly (Emmen-Helmond).
  - +0.3%, steady.
  - +3.7% and +6.4%, each in one snapshot only.
  - The two bigger ones both came from a thin Polymarket book moving, so they are probably noise.
- **Staleness:** soft odds follow big PM moves within 15 min 57% of the time. A lag beat the margin in only 2 of 30 moves.

## Simulation (sim.py, results/sim.md)
EUR400, 30 days, Kelly with edges shrunk 50%, 5% withdrawal tax.

| Scenario | P(>= EUR700) | Median end |
|---|---|---|
| Measured (about 0 clean bets/day) | 0% | EUR380 |
| 5/day, true +3% (optimistic) | 0% | EUR390-396 |
| 10/day, true +5% (fantasy) | 0.2-11.7% | EUR422-456 |

## Rules that make it worse
- **Withdrawal tax:** 5% on the amount withdrawn, not on profit. This is bigger than any edge found.
- **Who may play:** Georgian citizens must be 25+. People on social aid and public employees are banned.
- **Cards:** Georgian cards cannot pay foreign gambling sites.
- **KYC:** expect ID checks (Veriff) before withdrawals.
- **Stake limits:** server-side max stakes and trader-acceptance flows exist, so expect sharp accounts to get limited.

Sources: oc-media.org (2021 law), parliament.ge, igamingbusiness.com (tax raised from 2% to 5%), europeangaming.eu (1.45M on the ban list).

## Not covered
- Live betting, props, corners and cards.
- Blocked books.
- Polymarket is only semi-sharp on thin lower-league books.
