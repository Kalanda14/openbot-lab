# Pre-registered picks (fixed from TRAIN only, before reading any test column) — 2026-11-27
Rule: per instrument x horizon, the variant with the highest train z. Latency re-test (D=1s, 2s) on all variants,
headline = the same picks.
| inst | H | pick | train acc | train z |
|---|---|---|---|---|
| BTCUSDT | 15 | burst / all | 0.658 | 151.9 |
| BTCUSDT | 30 | logit / top10 | 0.661 | 102.2 |
| BTCUSDT | 60 | logit / top10 | 0.618 | 61.7 |
| BTCUSDT | 300 | logit / top10 | 0.555 | 15.8 |
| ETHUSDT | 15 | logit / top10 | 0.580 | 73.6 |
| ETHUSDT | 30 | logit / top10 | 0.556 | 42.0 |
| ETHUSDT | 60 | logit / top10 | 0.538 | 21.9 |
| ETHUSDT | 300 | logit / top10 | 0.527 | 6.3 |
| NQ | 15 | logit / top10 | 0.530 | 11.5 |
| NQ | 30 | logit / top10 | 0.530 | 9.1 |
| NQ | 60 | logit / top10 | 0.524 | 5.2 |
| NQ | 300 | tod / all | 0.527 | 4.2 |
