# cryptocasino: promo EV for an honest player in Georgia, EUR400 (checked 2026-11-28)

Verdict: no real edge. 30-day EV about EUR0 to +60, and the median outcome is a loss.
F = fact from official terms or our measurement; E = estimate or third-party source.

## Georgia allowed? (from official terms)
- **Yes (F):** Stake (ToS 14.3), Duelbits (ToS 3.2), Rainbet (restricted list).
- **Not listed by third parties (E):** Roobet, Rollbit, Gamdom.
- **Grey:** Cloudbet, which bans places where its offering is "unlawful".
- **No:** Shuffle (8.3: anywhere a licence would be needed), BitStarz (F), Jackbit/Jack.com (E); Bets.io likely.
- **Unknown:** Thrill, BC.Game, Sportsbet.io, Winna, Metaspins, Fairspin.
- Georgian law needs a local permit for operators. No rule found that punishes players. Citizens must be 25+.

## Why promos lose
- **Rakeback:** net = -(1-r) x edge x amount wagered. Always negative while r < 100%.
- **Stake welcome bonus:** wagering is weighted by house edge, so the EV is about -314.
- **Slot-only 40x bonuses:** about -380.
- **BC.Game:** you pay about a 1% edge to unlock 0.2%.

## Only +EV shapes
- **Lossback with no wagering.** Roobet 20% slot cashback: +7..+58, but P(loss) is 96%.
- **A match bonus where 1%-edge Originals count 100%.** Rainbet would give +90..+125, but this is not confirmed. If only slots count, it is -380.
- **No-strings free bets.** Duelbits $100 free bets: 0..+60, terms unknown.

## Sportsbook (F, measured)
Cloudbet's public pages, 199 events, compared with Polymarket CLOB books (pm_catalog, 45 min older):
- median margin 6.7%;
- 357 clean outcomes: median edge -5.2%, 0 positive, best -0.6%.

## Risks
- **ID checks:** every site's terms allow them at any time; in practice they come after big wins.
- **Loopholes and bugs:** using them means forfeiture (Rainbet 9.7, Stake 12.7).
- **Custody:** Stake lost about $41M in the 2023 hack. Keep balances at zero.
- **Fees:** crypto in and out costs about EUR8-15.

Better and safer: the Georgian licensed promos in ../bonus/REPORT.md (EUR90-140 in 30 days).
Files: sim.py, results/sim.md, sports/cloudbet.py, sports/compare.py.
