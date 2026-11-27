# pmlp - Polymarket liquidity-rewards paper test

Goal: find the TRUE $/day of quoting for Polymarket liquidity rewards before any real money.
Everything here uses public read-only endpoints. No wallet, no keys, no orders.

## Files

| file | what |
| - | - |
| `collect.py` | every run: top 1000 reward markets -> sticky watch list of 45 -> book snapshot + new trades + resolutions to `data/` |
| `sim.py` | replays `data/` with 3 pre-registered quoting policies; rewards by the documented formula, fills from real trades |
| `fillcheck.py` | backfill: last 7 days of real trades vs an hourly quote at price-history +/- 1c. Fill cost only, no rewards |
| `../.github/workflows/pmlp.yml` | runs `collect.py` every 10 min on GitHub Actions and commits `pmlp/data/` |

Run: `python pmlp/collect.py` (stdlib only), `python pmlp/sim.py [--mult 1] [--gas 0] [--maxgap 1200]`,
`python pmlp/fillcheck.py 7`.

Data size: about 20 KB per run, so about 3 MB/day. Day files older than 10 days are deleted, so the working tree stays near 30 MB.
Git history still grows; the files are plain text, append-only jsonl, so they delta-compress well.

## How the rules are modelled (docs: https://docs.polymarket.com/market-makers/liquidity-rewards.md)

- Order score `((v-s)/v)^2 * size`. `v` is the max spread in cents. `s` is the distance in cents from the
  size-cutoff-adjusted midpoint. Only orders >= `rewards_min_size` count.
- `Q_one` = bids on YES + asks on NO. `Q_two` = asks on YES + bids on NO.
  `/book` for the YES token already shows NO orders mirrored (YES bid p = NO ask 1-p; checked on a live market), so
  YES book bids = Q_one and YES book asks = Q_two.
- `Q_min = max(min(Q1,Q2), max(Q1,Q2)/3)` when mid is in [0.10, 0.90], else `min(Q1,Q2)` (c = 3.0).
- Sampled once per minute at a random offset. Epoch = one UTC day (1,440 samples). Paid daily at midnight UTC.
  Minimum payout $1.
- Our share per minute = ours / (ours + others). Others are visible only as one aggregate book:
  - `base`: others = Q_min of the aggregate book
  - `pess`: others = Q_one + Q_two (an upper bound on the sum of their separate Q_min)
- Pool per minute = `rate_per_day / 1440`. Only reward configs active today are counted.

### Ambiguities (we cannot settle these from the docs)

1. **Adjusted midpoint.** The docs say "size-cutoff-adjusted midpoint" but give no formula. We use best bid and best ask
   counting only orders >= min size, and our own quote is included. On empty books this means **our own quote sets
   the mid**. If Polymarket uses a different mid (for example the displayed price, which is last trade when the
   spread is > 10c), our quotes could score much less or zero.
2. **Is min size per order or per maker/level?** We assume per order.
3. **Empty minutes.** `Q_final = Q_epoch / sum(Q_epoch)`, so in theory a lone maker who quotes for part of the day still
   gets the whole pool. We assume pool / 1440 per minute instead (the conservative reading). We also assume no pay
   for minutes we do not quote.
4. **Two-sided bonus vs one-sided.** We do not know which other makers are two-sided. That is why we report base and pess.
5. **Hidden rules.** The docs say "discourage blatantly exploitative behaviors" but publish no per-account cap.
   We found no documented cap. Unknown in practice.
6. **Taker-delay markets.** Orders count only after resting for the delay (sports in-game). All 45 watched
   markets have `seconds_delay = 0` (checked 2026-11-27).
8. **Rates change during the day** (one Bank of Brazil market went from $149 to $101/day within 30 min). Many
   configs show `start_date` = today, which may be a rolling config and not a new allocation. The sim uses the rate in each snapshot.
7. **`market_competitiveness`.** A field in the reward list with undocumented meaning. We log it as `mc`.

### Fill model (conservative)

- Every real taker trade (data-api `/v2/trades`, taker rows only) that reaches our price fills us **first**, for
  min(our size, trade size). NO-token trades are mapped to YES equivalents.
- We cannot see takers who would trade at our better price but not at the old wide spread. Their flow is missing
  (probably less informed).
- Quotes stay fixed between snapshots (10 min on Actions). A live bot would requote faster on news. Our model is
  the slow bot (worse).
- Inventory cap |YES-NO| <= 2 x size. YES+NO pairs merge into $1. Positions are marked at the last mid, or 1/0 on resolution.
- Gas: the CLOB takes off-chain EIP-712 signed orders. Settlement and wallet ops go through the gasless relayer
  (https://docs.polymarket.com/concepts/order-lifecycle.md, https://docs.polymarket.com/trading/wallets-auth.md).
  Makers pay no fee (https://docs.polymarket.com/trading/fees.md). Default gas = $0, sensitivity with `--gas`.

## Research facts (2026-11-27)

- **Georgia (GE) is not on the restricted list.** The list covers blocked, close-only, and frontend-close-only places.
  https://docs.polymarket.com/api-reference/geoblock.md . Check with `GET https://polymarket.com/api/geoblock`
  from the trading machine.
- **VPS.** Order placement is checked by the IP of the request. Polymarket's servers are in AWS eu-west-2 (London;
  GB is close-only). The docs name **eu-west-1 (Ireland)** as the "closest non-georestricted region". Ireland is close-only on the
  frontend only; the API is not restricted. So a bot on a VPS in a non-blocked country is the documented setup.
  Using a VPN to *hide a blocked residence* is against the terms, and from mid-2026 Polymarket has enforced KYC/VPN bans
  (news: https://gizmodo.com/polymarket-cracks-down-on-vpn-users-as-legal-pressure-intensifies-2000765379).
  A Georgian resident is not in a blocked place, so a VPS is only for uptime and latency.
- **Gasless.** Yes for orders (see above). Collateral is pUSD on Polygon. USDC or USDC.e deposits are wrapped automatically.
  Bridge minimum is $2 from Polygon/Arbitrum/Base/BSC/Optimism and $7 from Ethereum
  (https://docs.polymarket.com/trading/bridge/supported-assets.md). Polymarket charges no deposit or withdrawal fee.
  From Georgia, the cheap path is probably an exchange that serves Georgia (e.g. Binance or Bybit; check KYC
  availability) -> withdraw USDC on Polygon or Base (fee usually < $1) -> the Polymarket deposit address. Not tested.
- **Caps / anti-farming.** None published beyond the $1 minimum payout and the "exploitative behaviour" clause.
  The scoring itself is the anti-farming tool: a quote far from mid scores ~0, a one-sided quote gets 1/3, and
  min size is often 200 shares.
- **Other farmers.** We found no first-person audited P&L. Guides say "modest, not a salary". The main loss is fills;
  one guide says naive calculators overstate by 3-5x for ignoring fills
  (https://medium.com/@ezzekielnjuguna/polymarket-liquidity-rewards-calculator-estimate-maker-rewards-min-size-max-spread-and-risk-7ddc4319590f).
  The open-source bot `warproxxx/poly-maker` pulls quotes during news, which points the same way. Third-party data
  (not verified) says about $200k/day is spread over about 7,300 markets.

- **Real payouts are public.** `peers.py`: data-api `/v2/activity?type=REWARD` lists each wallet's daily payout
  (all markets together). Top makers in the watched Ornn/Inception markets were paid **$500-8,000/day**. Small makers
  were paid $1-40/day. So rewards are real and big, but the big pools on competitive markets go to large,
  professional books.

## Early results (2026-11-27, 0.56 h of data, 10 snapshots x 45 markets, 173 trades) - NOT evidence

`sim.py` (gaps capped at 10 min; "per 24h" = the 34-minute sample x 43, which is almost meaningless):

| policy | all 45 mkts rewards/day (pess) | fills/day | capital | $50 budget (2 mkts) | $460 budget (9 mkts) |
| - | - | - | - | - | - |
| mid1 (mid +/- 1c) | $804 ($505) | -$337 | $5,864 | $205 net | $150 net |
| midv2 (mid +/- v/2) | $496 ($377) | -$19 | $5,550 | $205 net | $185 net |
| last1 (trades +/- 1c) | $675 ($394) | -$109 | $5,714 | $130 net | $130 net |

- The $50 result is **two Bank of Brazil Selic markets** (min size 20, pools of about $100/day each). Nobody else
  quotes within 4.5c there (alone 88-100% of the time). The scout saw the same thing hours earlier. One Meta-downgrade
  market (min size 200) is the same.
- On the competitive markets (Ornn GPU rental, Jensen Huang, AI bubble) our min-size quote gets a small share
  (0-30%) and pays for it with 200-share fills.
- Fill PnL is dominated by single 200-share fills. 19 fills in 34 min is far too few to estimate.
- With `--gas 0.02` per order, mid1 goes negative ($-216/day) because we requote 90 orders every run. Docs say
  orders are gasless, so the base case is $0.
- `fillcheck.py 7` (last 7 days, hourly quote +/- 1c, filled first): fills cost **-$312/day in total over the 45
  markets**, median -$2.5/day per market. 18 markets lost more than $5/day, the worst about -$43/day (markets that moved 30c on news).
  Bank of Brazil markets: about -$1/day each.

**Reading:** the scoring and the pools are real. The open question is not the formula. It is (1) whether empty, rich
markets stay empty for days (the Actions collector answers this), (2) whether Polymarket's "adjusted midpoint" on an
empty book really centres on our own quote (only a live pilot answers this), and (3) news-driven fills.

## What a $20-50 live pilot needs

1. A Polymarket account (Georgia is allowed; check `/api/geoblock` from the machine), about $50 USDC on Polygon or Base -> deposit.
2. A small quoting bot: 2 markets that the sim marks "alone" (e.g. the Bank of Brazil Selic markets, min size 20,
   about $20 of capital each), post-only bid/ask at adjusted mid +/- 1c, requote every 1-2 min and on any trade, cancel all if the
   mid moves > 3c or before the event date (Copom meeting).
3. Each day: read `/rewards/user/total` (L2 auth) and compare with what `sim.py` predicted for the same minutes.
   That one number settles ambiguities 1-3. Hold for 3-7 days. Stop if rewards < 50% of the sim or fills < -$5/day.
4. Run the bot on a VPS in a non-blocked region (docs: eu-west-1), with keys in env and never in git.
