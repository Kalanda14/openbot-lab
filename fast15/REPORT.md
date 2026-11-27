# fast15: is there an edge in 15 s – 5 min "up or down" bets?

Date 2026-11-27. Free data only. No account, no trades, Databento key not used (NQ trades were already on disk).

## Short answer
- **On the Binance tape, yes, BTC direction over 15-60 s can be predicted.** Accuracy is 60-64% out of sample, it still holds with a 2 s delay, and every month looks the same. ETH is weaker (54-57%). **NQ has nothing usable** (best pre-registered pick 51.5%, under break-even).
- **As trading, it is worthless.** The average move we catch is 0.3-0.6 bps. The cheapest Binance round trip is 15 bps, so the edge is 25-50x too small. In NQ the caught move is about 0 pt against about 1 pt of cost.
- **As binary options, it only works on paper**, and only with Binance's own prices. A binary platform settles on its own feed, not Binance's. We cannot test that feed. The platform is also the counterparty that pays us. Also, at 15 s ties happen 10-17% of the time. If the platform counts a tie as a loss, 15 s BTC drops to 53.5% with a 2 s delay, which is below break-even for most payouts.
- **Verdict: nothing here we could actually use. It adds nothing to the book.** Details below.

## Data
| inst | train | test | rows (s) | price used for the label |
|---|---|---|---|---|
| BTCUSDT, ETHUSDT | Binance spot 1 s klines, 2025-07..09 | 2026-08..10 | 7.95 M / 7.95 M | last trade price (close) |
| NQ (CME, NQ.v.0) | Databento trades, RTH, Apr-Jul 2026 (83 d) | Aug-Nov 2026 (80 d) | 3.81 M total | mid proxy = (last buy-aggressor px + last sell-aggressor px)/2, which removes most bid-ask bounce. Horizons that cross a contract roll are dropped |

Order flow comes from the klines' taker-buy volume (crypto) and the aggressor side (NQ). No aggTrades were needed.
EURUSD (Dukascopy) was **not done**, to save time and disk (Mac disk 96% full). It was optional.

## Method (pre-registered in updown.py docstring; picks in PICKS.md, committed before reading test)
- 13 features: mom1/5/15/60, ofi5/15/60, burst (trade-count burst x direction), round-number proximity, z15 (momentum scaled by volatility), time of day, second of minute, and a logistic regression on all 12.
- 4 horizons (15/30/60/300 s), 2 subsets (all seconds with a signal; top 10% |signal| using the train threshold), 3 instruments: 312 variants, plus 12 "always up" baselines, so **324 per delay**.
- Delays 0, 1, 2 s (entry price = px[t+D]): **972 variant evaluations in total.** Extra checks: 18 monthly stability checks and 14 null diagnostics. Every number is in res_{train,test}_D*.csv.
- Direction (with or against the signal) was chosen on train. Trades are greedy and non-overlapping: a new bet only after the last one expires. Ties are refunded and left out of accuracy, and the tie rate is reported. se = sqrt(p(1-p)/n).
- Picks: for each instrument and horizon, the highest train z (12 picks). Test was read only after PICKS.md was committed.

## Main table (TEST, pre-registered picks)
Break-even: payout 92% means 52.1%; payout 80% means 55.6% (ties refunded). "Yes" means acc - 2 se is above the line.
Cost: crypto 15 bps round trip (2 x 0.075% taker with BNB; 20 bps without; maker is also 0.1%/side at VIP0). NQ 1 pt (CFD spread is 1-1.5 pt).

| signal | H | delay | test acc ± se | n | trades/day | tie % | avg caught move | beats 52.1 / 55.6? | beats cost? |
|---|---|---|---|---|---|---|---|---|---|
| BTC burst/all | 15 s | 0 s | 0.636 ± 0.001 | 242,457 | 2,923 | 9.8 | +0.40 bps | yes / yes | no (15 bps) |
| BTC burst/all | 15 s | 1 s | 0.618 ± 0.001 | 229,888 | 2,808 | 11.0 | +0.31 bps | yes / yes | no |
| BTC burst/all | 15 s | 2 s | 0.605 ± 0.001 | 220,037 | 2,703 | 11.5 | +0.26 bps | yes / yes | no |
| BTC logit/top10 | 30 s | 0 / 1 / 2 s | 0.641 / 0.632 / 0.622 (±0.002) | 98k / 81k / 74k | 1,130 / 950 / 881 | 5-8 | +0.60 / +0.46 / +0.39 bps | yes / yes | no |
| BTC logit/top10 | 60 s | 0 / 1 / 2 s | 0.602 / 0.596 / 0.590 (±0.002) | 67k / 56k / 52k | 753 / 639 / 593 | 3-4.5 | +0.63 / +0.49 / +0.43 bps | yes / yes | no |
| BTC logit/top10 | 300 s | 0 / 2 s | 0.531 / 0.527 (±0.004) | 21k / 17k | 225 / 185 | 0.6 | +0.56 / +0.35 bps | 0 s: yes / no; 2 s: no / no | no |
| ETH logit/top10 | 15 s | 0 / 1 / 2 s | 0.590 / 0.567 / 0.556 (±0.001) | 194k / 163k / 146k | 2,256 / 1,954 / 1,778 | 7-10 | +0.37 / +0.21 / +0.16 bps | yes / 2 s: no | no |
| ETH logit/top10 | 30 s | 0 / 2 s | 0.562 / 0.539 | 137k / 104k | 1,542 / 1,201 | 3.5-5.5 | +0.39 / +0.15 bps | yes / no | no |
| ETH logit/top10 | 60 s | 0 / 2 s | 0.534 / 0.524 | 82k / 59k | 907 / 662 | 2 | +0.34 / +0.12 bps | 0 s: yes; 2 s: no | no |
| ETH logit/top10 | 300 s | 0 s | 0.507 ± 0.005 | 11,915 | 130 | 0.3 | +0.23 bps | no | no |
| NQ logit/top10 | 15 s | 0 / 2 s | 0.515 / 0.507 (±0.003) | 35.7k / 32.5k | 451 / 412 | 1.2 | -0.05 / -0.13 pt | no | no (1 pt) |
| NQ logit/top10 | 30 s | 0 / 1 s | 0.508 / 0.515 | 22k / 20k | 279 / 254 | 1.0 | -0.18 / +0.00 pt | no | no |
| NQ logit/top10 | 60 s | 0 s | 0.502 ± 0.005 | 10,879 | 137 | 0.5 | -0.03 pt | no | no |
| NQ tod/all | 300 s | 0 s | 0.502 ± 0.007 | 5,800 | 73 | 0.2 | -0.19 pt | no | no |
| baseline always-up (all 12) | 15-300 s | 0-2 s | 0.497-0.503 | | | | about 0 | no | no |

The "top 10%" subset is the logit/top10 rows. For BTC 15 s, the not-pre-registered logit/top10 does better: 0.670 / 0.654 / 0.642 at 0/1/2 s, with 1,666 / 1,356 / 1,213 trades/day.
Full per-delay tables, including always-up, are in tables.md.

**Always-up baseline:** test drift was flat (49.7-50.3% at every horizon). Train NQ was up 50.7-51.6% (the Apr-Jul rally). That bias did not carry into test, which is why the NQ tod/300 pick (really a drift fit) failed.

## Multiple testing
- Expected best |z| from 324 pure-noise variants: p95 ≈ 3.8.
- I also ran a circular-shift label null. It came out at p95 |z| 6.5-13 on train, 3.5-7.2 on test. Diagnostics (nulldiag.py) show the non-seasonal features give a normal N(0,1) null under shifting. The inflation comes from the in-sample tod/som/logit fits keeping real intraday seasonality when the shift lines up. So that null is conservative.
- The BTC/ETH winners have test z of 50-134 at 0 s and stay huge at 2 s. **They are not data-mining luck.** NQ's best pick (z 5.7 at 0 s, 2.5 at 2 s, accuracy 51.5%) is borderline and below the binary break-even anyway.
- The one test variant whose caught move beat cost (NQ mom5/all 300 s, +1.00 pt) has accuracy 50.96%, z 1.5. It was not pre-registered. It is noise.

## Robustness
- Per test month, simplest rule only (bet the sign of the last 1 s move when |r1| > train p90; 2 s delay): BTC is **58.6 / 58.8 / 59.3%** at 15 s and 57.3 / 56.5 / 57.4% at 30 s (Aug/Sep/Oct). It is stable, with 0.31-0.47 bps per bet. ETH's simple rule is only 50.2-51.2%. ETH's edge needs the logistic model and order flow.

## Why this does not become money
1. **Trading the move:** we catch 0.26-0.63 bps per bet. Break-even needs total fees under about 0.15 bps per side (0.0015%). No retail venue is that cheap, even Binance's top VIP taker rate. A maker-only version would not fill on the momentum side. **Dead by about 30-50x.** NQ: about 0 pt caught versus 1-1.5 pt CFD spread (1.12 pt futures). **Dead.**
2. **Binary options:**
   - Our accuracy is measured on Binance's last-trade price, second by second. Binary/"up-down" platforms (Pocket Option, Quotex, IQ Option, Binomo, ...) **settle on their own price feed**, which they make and control. The effect is short-lived trade-tape momentum. Whether it exists on their feed is unknown and untestable with free data. A smoothed or lagged feed could remove it or flip it.
   - Ties: at 15 s, 10-17% of BTC bets end exactly flat. Counted as losses, BTC 15 s burst at 2 s delay becomes 60.5% x 0.885 = **53.5%**. That is below the 55.6% (80% payout) line and only about 1 pt above the 52.1% (92% payout) line. Platforms rarely pay 92% on 15 s crypto.
   - Latency: platforms set the strike price when they accept the order. A ~0.5-2 s total delay is already in our 2 s numbers. Any extra delay or requote eats more.
   - Counterparty: the platform is the bookmaker. Accounts that win steadily on short expiries are known to be limited or have withdrawals refused. Most of these brokers are offshore and unregulated.
   - **Legal:** ESMA banned binary options for retail clients in the EU from July 2018, and the UK FCA made the ban permanent in April 2019. In the US, only CFTC-regulated exchanges may offer them. Selling them to retail elsewhere mostly happens through unregulated offshore firms.
3. **Running it on GitHub Actions / VPS:** BTC accuracy survives a 1-2 s delay, but this is 1,000-3,000 bets a day. That needs a steady, always-on process and a venue/feed match. Actions cron cannot do it.

## How it adds to our book
It doesn't. There is no tradeable edge after costs in any venue we could legally and reliably use. The only real fact here is that BTC spot tape has 1-60 s momentum, worth about 0.3-0.6 bps. If anything, our crypto trend book can avoid sending a market order right against a 1 s burst. That saves fractions of a basis point. It is not worth building.

A regulated up/down market (for example Polymarket 5-15 min crypto markets, if they still list them) would be the only honest venue to test. But the prices there already include public momentum, and our signal is weak at 300 s (52.7-53.1%, about 0.4 bps). Not recommended without a separate test on that market's own price history.

## Files
updown.py (main test), build_nq.py, fetch_crypto.py, nulldiag.py, monthly.py, tables.py, PICKS.md, tables.md, res_*.csv, null_*.json. Raw data is in fast15/raw/ (git-ignored, about 0.9 GB crypto npz + NQ npz).
