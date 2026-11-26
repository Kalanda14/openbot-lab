leverageable book Sharpe: all 1.66, 2022-26 1.57

## Simulation on real days (deadline sizing, leverage cap 30x)

| edge | deposit/mo | P(10k in 1 yr) | P(end < 100) | median end |
|---|---|---|---|---|
| backtest | 0 | 17% | 9% | 2,271 |
| backtest | 100 | 32% | 0% | 7,127 |
| backtest | 250 | 68% | 0% | 10,001 |
| backtest | 350 | 83% | 0% | 10,001 |
| backtest | 500 | 95% | 0% | 10,001 |
| forward Sharpe 1.0 | 0 | 1% | 23% | 410 |
| forward Sharpe 1.0 | 100 | 9% | 2% | 1,705 |
| forward Sharpe 1.0 | 250 | 26% | 0% | 5,229 |
| forward Sharpe 1.0 | 350 | 39% | 0% | 8,818 |
| forward Sharpe 1.0 | 500 | 73% | 0% | 10,001 |
## Theory: best possible P(EUR 10k in time T), any strategy

| leverageable Sharpe | 1 yr, no deposits | 1 yr, +100/mo | 1 yr, +250/mo | 1 yr, +350/mo | 2 yr, +100/mo | 3 yr, +100/mo |
|---|---|---|---|---|---|---|
| 1.0 | 23% | 50% | 72% | 82% | 80% | 93% |
| 1.3 | 33% | 62% | 81% | 88% | 90% | 98% |
| 1.6 | 44% | 73% | 88% | 93% | 95% | 99% |
| 2.0 | 60% | 84% | 94% | 97% | 99% | 100% |
| 2.6 | 80% | 95% | 99% | 99% | 100% | 100% |
| 3.0 | 89% | 98% | 100% | 100% | 100% | 100% |

needed for 80% in 1 year with no deposits: Sharpe x sqrt(T) >= 2.59

leverageable book Sharpe: all 1.66, 2022-26 1.57

## Simulation on real days (deadline sizing, leverage cap 30x)

| edge | deposit/mo | P(10k in 1 yr) | P(end < 100) | median end |
|---|---|---|---|---|
| backtest | 0 | 17% | 9% | 2,271 |
| backtest | 100 | 32% | 0% | 7,127 |
| backtest | 250 | 68% | 0% | 10,001 |
| backtest | 350 | 83% | 0% | 10,001 |
| backtest | 500 | 95% | 0% | 10,001 |
| forward Sharpe 1.0 | 0 | 1% | 23% | 410 |
| forward Sharpe 1.0 | 100 | 9% | 2% | 1,705 |
| forward Sharpe 1.0 | 250 | 26% | 0% | 5,229 |
| forward Sharpe 1.0 | 350 | 39% | 0% | 8,818 |
| forward Sharpe 1.0 | 500 | 73% | 0% | 10,001 |
forward Sharpe 1.0, deposit 600 -> P(10k)=90%
forward Sharpe 1.0, deposit 700 -> P(10k)=98%
backtest, no deposit, cap 100x -> P(10k) 18%, P(<100) 30%
