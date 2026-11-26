# Deep search on real NQ futures (2468 days)

strategies tested: 1440
train t>2: 6 (luck alone ~33); of those also test t>2: 0 (luck alone ~0.1)

## Top 15 by TRAIN (what we would have picked), and how they did on unseen 2022-26

| feature | filter | dir | time | hold | train Sharpe | train t | TEST Sharpe | test t |
|---|---|---|---|---|---|---|---|---|
| openret_lorv | top30 | with | 10:00 | 30 | +1.12 | +2.5 | +0.43 | +1.0 |
| ret30 | all | with | 12:00 | close | +1.07 | +2.4 | +0.22 | +0.5 |
| openret_lorv | top30 | with | 10:00 | 60 | +0.96 | +2.1 | +0.48 | +1.0 |
| ret30_hirv | all | with | 12:00 | close | +0.96 | +2.1 | +0.09 | +0.2 |
| gap | top30 | with | 11:00 | 60 | +0.93 | +2.1 | -0.40 | -0.9 |
| gap | top30 | with | 12:30 | 30 | +0.93 | +2.0 | -0.58 | -1.3 |
| openret_hivol | top30 | with | 13:30 | 30 | +0.88 | +1.9 | -0.46 | -1.0 |
| vwap | all | with | 15:00 | close | +0.85 | +1.9 | -0.44 | -1.0 |
| vwap | all | with | 15:00 | 60 | +0.85 | +1.9 | -0.44 | -1.0 |
| prevday | all | against | 10:30 | close | +0.84 | +1.9 | -0.31 | -0.7 |
| ret5 | top30 | with | 12:30 | close | +0.81 | +1.8 | -0.22 | -0.5 |
| openret | top30 | with | 13:30 | 30 | +0.81 | +1.8 | -0.15 | -0.3 |
| gap | top30 | against | 15:00 | close | +0.79 | +1.8 | -0.46 | -1.0 |
| gap | top30 | against | 15:00 | 60 | +0.79 | +1.8 | -0.46 | -1.0 |
| openret_hivol | all | with | 15:00 | 60 | +0.79 | +1.8 | -0.20 | -0.4 |

Equal-weight portfolio of all 6 train-t>2 rules: train Sharpe +1.52, TEST Sharpe +0.14 (t +0.3)
Reference B: train +0.65, test +1.27

## Part 2: walk-forward ridge (all features, 11 decision times, hold 30 min)
2019-26 out-of-sample Sharpe -0.97 (t -2.7); 2022-26 -0.92; by year: 2019 -3.0, 2020 -1.9, 2021 -0.1, 2022 -0.8, 2023 +0.1, 2024 +0.3, 2025 -0.5, 2026 -3.0
