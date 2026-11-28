# Matched betting Spain: +EUR300 in month 1 (plan, 2026-11-28)

Why this and not trading: 150+ trading ideas tested (see memory openbot-project). Best honest trading plan is about 50% to reach +300
in a month, with about 27% risk of ending below EUR100. Matched betting turns bookmaker welcome bonuses into cash. Each bet is
covered by an opposite bet (lay) on Betfair.es Exchange, so the result does not depend on who wins.

## Who can do it
- Spain resident with DNI/NIE, a Spanish bank account and an address. One account per person per bookmaker.
- 18+. Betfair.es exchange commission 5% (check your rate). The Spanish exchange pool is thin: use big matches only (LaLiga, UCL, Premier League).

## Real terms (apuestas-deportivas.es, checked 2026-11-25; check the bookmaker T&C before each one)
Net = what you keep after lay (calc.py) minus qualifying loss. Order = best and simplest first.

| # | bookmaker | offer | face | est. net |
|---|---|---|---|---|
| 1 | Betfair Sportsbook | 10 freebets x 20 after 10 qualifying bets of 10, odds >=1.50, code ZBBES2 | 200 | ~135 |
| 2 | Sportium | freebets = 1st and 2nd deposit (100+100), odds >=1.50, press "Me apunto" | 200 | ~130 |
| 3 | bet365 | betting credits up to 200 on deposit | 200 | ~120 |
| 4 | MARCA Apuestas | freebet 10 per 25 staked (SNR), up to 200, odds >=1.50 | 200 | ~120 |
| 5 | Retabet | 100% freebet on 1st deposit, max 25 per freebet, odds 2.00-3.50 | 200 | ~118 |
| 6 | William Hill | freebets on first 3 bets (25/50/75), code WH150 | 150 | ~97 |
| 7 | Kirolbet | freebet after qualifying bet, code kb100, use within 2 days | 100 | ~65 |
| 8 | Paf | freebets | 50 | ~35 |
| 9 | bwin / OlyBet / Winamax | refund of first losing bet as freebet (harder: lay the first bet so it loses on the bookie side) | 350 | ~150 |
| skip | VERSUS (bet-builder only, cannot lay), TonyBet x25, Betway 48x, 1xBET (licence unclear), casino offers | | | 0 |

Sum of est. net, rows 1-8: ~820. Rows 1-4 alone: ~500. Target +300 needs about 3-4 offers done right.
Honest P(+300 in 30 days): ~0.85 if resident and careful. Main risks: making a mistake with the lay (wrong market or odds),
a lay that does not get matched (thin Spanish pool, so lay first, then back), an offer gone or changed, an account limited.
Loss is small even when things go wrong (qualifying loss ~5%).

## How to do one offer (example: freebet 25 SNR)
1. Pick a big match. On the bookie, find a selection with back odds close to the Betfair.es lay odds.
2. Qualifying bet: `python3 mb/calc.py q 25 2.10 2.16` -> lay 24.88 at 2.16 (need 28.86 on exchange). Loss ~1.36.
3. Freebet: use high odds (4-7): `python3 mb/calc.py snr 25 6.0 6.4` -> lay 19.69 (liability 106). Keep ~18.70.
4. Always place the LAY first, check it is fully matched, then place the back bet.
5. Write every bet in a log (date, bookie, stake, odds, lay, result).

## Capital
EUR400 is enough if you do offers one after another: a 100 SNR freebet at 5.0 needs ~330 liability.
Keep ~150 on Betfair.es and move the rest bookie by bookie.

## Tax
In Spain, net gambling winnings count as income (IRPF), per year and in total. Keep the log.
