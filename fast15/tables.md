
## Delay 0s: pre-registered picks + always-up baseline (TEST)

| signal | H s | train acc | test acc ± se | n | trades/day | tie % | avg signed move | cost RT | >52.1%? | >55.6%? | beats cost? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT burst/all | 15 | 0.658 | 0.6362 ± 0.0010 | 242457 | 2923 | 9.8 | +0.40 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 30 | 0.661 | 0.6406 ± 0.0015 | 98414 | 1130 | 5.3 | +0.60 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 60 | 0.618 | 0.6022 ± 0.0019 | 67199 | 753 | 3.0 | +0.63 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 300 | 0.555 | 0.5305 ± 0.0035 | 20615 | 225 | 0.6 | +0.56 bps | 15 bps | yes | no | no |
| BTCUSDT up/all | 15 | 0.498 | 0.5018 ± 0.0008 | 437986 | 5760 | 17.3 | +0.00 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 30 | 0.498 | 0.5015 ± 0.0010 | 237077 | 2880 | 10.5 | +0.01 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 60 | 0.500 | 0.5016 ± 0.0014 | 125080 | 1440 | 5.6 | +0.02 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 300 | 0.499 | 0.4971 ± 0.0031 | 26299 | 288 | 0.7 | +0.08 bps | 15 bps | no | no | no |
| ETHUSDT logit/top10 | 15 | 0.580 | 0.5895 ± 0.0011 | 193879 | 2256 | 6.6 | +0.37 bps | 15 bps | yes | yes | no |
| ETHUSDT logit/top10 | 30 | 0.555 | 0.5624 ± 0.0013 | 136927 | 1542 | 3.5 | +0.39 bps | 15 bps | yes | yes | no |
| ETHUSDT logit/top10 | 60 | 0.538 | 0.5344 ± 0.0017 | 81880 | 907 | 1.9 | +0.34 bps | 15 bps | yes | no | no |
| ETHUSDT logit/top10 | 300 | 0.527 | 0.5067 ± 0.0046 | 11915 | 130 | 0.3 | +0.23 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 15 | 0.503 | 0.5015 ± 0.0007 | 469823 | 5760 | 11.3 | +0.00 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 30 | 0.503 | 0.5016 ± 0.0010 | 249359 | 2880 | 5.9 | +0.01 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 60 | 0.504 | 0.5034 ± 0.0014 | 128902 | 1440 | 2.7 | +0.02 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 300 | 0.507 | 0.4989 ± 0.0031 | 26386 | 288 | 0.4 | +0.08 bps | 15 bps | no | no | no |
| NQ logit/top10 | 15 | 0.530 | 0.5150 ± 0.0026 | 35684 | 451 | 1.2 | -0.05 pt | 1 pt | no | no | no |
| NQ logit/top10 | 30 | 0.530 | 0.5075 ± 0.0034 | 22076 | 279 | 1.0 | -0.18 pt | 1 pt | no | no | no |
| NQ logit/top10 | 60 | 0.524 | 0.5021 ± 0.0048 | 10879 | 137 | 0.5 | -0.03 pt | 1 pt | no | no | no |
| NQ tod/all | 300 | 0.527 | 0.5016 ± 0.0066 | 5800 | 73 | 0.2 | -0.19 pt | 1 pt | no | no | no |
| NQ up/all | 15 | 0.507 | 0.5010 ± 0.0014 | 119963 | 1519 | 1.3 | -0.02 pt | 1 pt | no | no | no |
| NQ up/all | 30 | 0.508 | 0.4983 ± 0.0020 | 60171 | 759 | 0.9 | -0.05 pt | 1 pt | no | no | no |
| NQ up/all | 60 | 0.510 | 0.4973 ± 0.0029 | 30146 | 379 | 0.6 | -0.10 pt | 1 pt | no | no | no |
| NQ up/all | 300 | 0.516 | 0.4991 ± 0.0065 | 5987 | 75 | 0.2 | -0.51 pt | 1 pt | no | no | no |

All 324 test variants at delay 0s: |z|>3.8 in 147; acc-2se > 52.1%: 76; > 55.6%: 32; edge > cost: 1

Top 8 test variants by z (not pre-registered, for context):

| inst | feat/subset | H | test acc | n | trades/day | edge |
|---|---|---|---|---|---|---|
| BTCUSDT | burst/all | 15 | 0.6362 | 242457 | 2923 | +0.40 |
| BTCUSDT | logit/top10 | 15 | 0.6696 | 139843 | 1666 | +0.55 |
| BTCUSDT | mom1/top10 | 15 | 0.6402 | 170610 | 1971 | +0.59 |
| BTCUSDT | logit/top10 | 30 | 0.6406 | 98414 | 1130 | +0.60 |
| BTCUSDT | logit/all | 15 | 0.5667 | 437986 | 5760 | +0.19 |
| BTCUSDT | burst/all | 30 | 0.6097 | 161018 | 1854 | +0.48 |
| ETHUSDT | logit/top10 | 15 | 0.5895 | 193879 | 2256 | +0.37 |
| BTCUSDT | ofi15/top10 | 15 | 0.6175 | 105643 | 1415 | +0.31 |

## Delay 1s: pre-registered picks + always-up baseline (TEST)

| signal | H s | train acc | test acc ± se | n | trades/day | tie % | avg signed move | cost RT | >52.1%? | >55.6%? | beats cost? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT burst/all | 15 | 0.635 | 0.6181 ± 0.0010 | 229888 | 2808 | 11.0 | +0.31 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 30 | 0.647 | 0.6317 ± 0.0017 | 80917 | 950 | 7.4 | +0.46 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 60 | 0.609 | 0.5958 ± 0.0021 | 56451 | 639 | 4.0 | +0.49 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 300 | 0.551 | 0.5296 ± 0.0037 | 18104 | 198 | 0.5 | +0.44 bps | 15 bps | yes | no | no |
| BTCUSDT up/all | 15 | 0.497 | 0.5020 ± 0.0008 | 410251 | 5400 | 17.4 | +0.00 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 30 | 0.497 | 0.5016 ± 0.0010 | 229508 | 2787 | 10.5 | +0.01 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 60 | 0.498 | 0.4990 ± 0.0014 | 123038 | 1416 | 5.6 | +0.02 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 300 | 0.496 | 0.4992 ± 0.0031 | 26196 | 287 | 0.8 | +0.08 bps | 15 bps | no | no | no |
| ETHUSDT logit/top10 | 15 | 0.561 | 0.5669 ± 0.0012 | 163464 | 1954 | 9.1 | +0.21 bps | 15 bps | yes | yes | no |
| ETHUSDT logit/top10 | 30 | 0.543 | 0.5463 ± 0.0015 | 117112 | 1337 | 4.8 | +0.22 bps | 15 bps | yes | no | no |
| ETHUSDT logit/top10 | 60 | 0.531 | 0.5263 ± 0.0019 | 67191 | 748 | 2.3 | +0.17 bps | 15 bps | yes | no | no |
| ETHUSDT logit/top10 | 300 | 0.535 | 0.5092 ± 0.0053 | 8825 | 96 | 0.2 | -0.06 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 15 | 0.503 | 0.5011 ± 0.0008 | 440439 | 5400 | 11.3 | +0.00 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 30 | 0.503 | 0.5021 ± 0.0010 | 241211 | 2787 | 5.9 | +0.01 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 60 | 0.503 | 0.5016 ± 0.0014 | 126566 | 1416 | 2.9 | +0.02 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 300 | 0.501 | 0.4960 ± 0.0031 | 26300 | 287 | 0.4 | +0.07 bps | 15 bps | no | no | no |
| NQ logit/top10 | 15 | 0.529 | 0.5110 ± 0.0026 | 35614 | 450 | 1.1 | -0.07 pt | 1 pt | no | no | no |
| NQ logit/top10 | 30 | 0.531 | 0.5151 ± 0.0035 | 20157 | 254 | 0.9 | +0.00 pt | 1 pt | no | no | no |
| NQ logit/top10 | 60 | 0.527 | 0.5062 ± 0.0048 | 10995 | 138 | 0.7 | +0.06 pt | 1 pt | no | no | no |
| NQ tod/all | 300 | 0.532 | 0.5018 ± 0.0066 | 5799 | 73 | 0.2 | -0.35 pt | 1 pt | no | no | no |
| NQ up/all | 15 | 0.503 | 0.5009 ± 0.0015 | 112497 | 1424 | 1.2 | -0.03 pt | 1 pt | no | no | no |
| NQ up/all | 30 | 0.506 | 0.4995 ± 0.0021 | 58249 | 735 | 0.9 | -0.05 pt | 1 pt | no | no | no |
| NQ up/all | 60 | 0.509 | 0.5004 ± 0.0029 | 29638 | 373 | 0.7 | -0.09 pt | 1 pt | no | no | no |
| NQ up/all | 300 | 0.518 | 0.4982 ± 0.0065 | 5986 | 75 | 0.2 | -0.54 pt | 1 pt | no | no | no |

All 324 test variants at delay 1s: |z|>3.8 in 140; acc-2se > 52.1%: 78; > 55.6%: 26; edge > cost: 0

Top 8 test variants by z (not pre-registered, for context):

| inst | feat/subset | H | test acc | n | trades/day | edge |
|---|---|---|---|---|---|---|
| BTCUSDT | burst/all | 15 | 0.6181 | 229888 | 2808 | +0.31 |
| BTCUSDT | logit/top10 | 15 | 0.6537 | 109850 | 1356 | +0.40 |
| BTCUSDT | mom1/top10 | 15 | 0.6060 | 162846 | 1907 | +0.40 |
| BTCUSDT | logit/all | 15 | 0.5624 | 410251 | 5400 | +0.15 |
| BTCUSDT | burst/all | 30 | 0.5975 | 156176 | 1811 | +0.38 |
| BTCUSDT | ofi5/top10 | 15 | 0.5841 | 202045 | 2691 | +0.24 |
| BTCUSDT | logit/top10 | 30 | 0.6317 | 80917 | 950 | +0.46 |
| BTCUSDT | ofi15/top10 | 15 | 0.6131 | 102973 | 1383 | +0.25 |

## Delay 2s: pre-registered picks + always-up baseline (TEST)

| signal | H s | train acc | test acc ± se | n | trades/day | tie % | avg signed move | cost RT | >52.1%? | >55.6%? | beats cost? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT burst/all | 15 | 0.620 | 0.6049 ± 0.0010 | 220037 | 2703 | 11.5 | +0.26 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 30 | 0.639 | 0.6216 ± 0.0018 | 74155 | 881 | 8.5 | +0.39 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 60 | 0.601 | 0.5901 ± 0.0022 | 52101 | 593 | 4.5 | +0.43 bps | 15 bps | yes | yes | no |
| BTCUSDT logit/top10 | 300 | 0.548 | 0.5271 ± 0.0038 | 16897 | 185 | 0.6 | +0.35 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 15 | 0.498 | 0.5019 ± 0.0008 | 386226 | 5082 | 17.4 | +0.00 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 30 | 0.496 | 0.5009 ± 0.0011 | 222331 | 2700 | 10.5 | +0.01 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 60 | 0.499 | 0.4988 ± 0.0014 | 121089 | 1393 | 5.5 | +0.01 bps | 15 bps | no | no | no |
| BTCUSDT up/all | 300 | 0.496 | 0.5004 ± 0.0031 | 26112 | 286 | 0.8 | +0.09 bps | 15 bps | no | no | no |
| ETHUSDT logit/top10 | 15 | 0.552 | 0.5564 ± 0.0013 | 146474 | 1778 | 10.5 | +0.16 bps | 15 bps | yes | no | no |
| ETHUSDT logit/top10 | 30 | 0.540 | 0.5385 ± 0.0015 | 104498 | 1201 | 5.5 | +0.15 bps | 15 bps | yes | no | no |
| ETHUSDT logit/top10 | 60 | 0.528 | 0.5239 ± 0.0020 | 59393 | 662 | 2.5 | +0.12 bps | 15 bps | no | no | no |
| ETHUSDT logit/top10 | 300 | 0.532 | 0.5085 ± 0.0057 | 7804 | 85 | 0.4 | +0.11 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 15 | 0.504 | 0.5020 ± 0.0008 | 414687 | 5082 | 11.3 | +0.01 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 30 | 0.503 | 0.5017 ± 0.0010 | 233549 | 2700 | 6.0 | +0.01 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 60 | 0.503 | 0.5009 ± 0.0014 | 124645 | 1393 | 2.8 | +0.02 bps | 15 bps | no | no | no |
| ETHUSDT up/all | 300 | 0.502 | 0.5002 ± 0.0031 | 26213 | 286 | 0.4 | +0.08 bps | 15 bps | no | no | no |
| NQ logit/top10 | 15 | 0.523 | 0.5069 ± 0.0028 | 32542 | 412 | 1.4 | -0.13 pt | 1 pt | no | no | no |
| NQ logit/top10 | 30 | 0.530 | 0.5081 ± 0.0035 | 20274 | 256 | 0.9 | -0.11 pt | 1 pt | no | no | no |
| NQ logit/top10 | 60 | 0.523 | 0.5038 ± 0.0049 | 10504 | 132 | 0.6 | -0.09 pt | 1 pt | no | no | no |
| NQ tod/all | 300 | 0.531 | 0.4968 ± 0.0066 | 5801 | 73 | 0.2 | -0.36 pt | 1 pt | no | no | no |
| NQ up/all | 15 | 0.505 | 0.5018 ± 0.0015 | 105928 | 1341 | 1.3 | -0.02 pt | 1 pt | no | no | no |
| NQ up/all | 30 | 0.507 | 0.5010 ± 0.0021 | 56448 | 712 | 0.9 | -0.04 pt | 1 pt | no | no | no |
| NQ up/all | 60 | 0.509 | 0.4997 ± 0.0029 | 29168 | 367 | 0.7 | -0.11 pt | 1 pt | no | no | no |
| NQ up/all | 300 | 0.519 | 0.4974 ± 0.0065 | 5987 | 75 | 0.2 | -0.46 pt | 1 pt | no | no | no |

All 324 test variants at delay 2s: |z|>3.8 in 135; acc-2se > 52.1%: 70; > 55.6%: 21; edge > cost: 0

Top 8 test variants by z (not pre-registered, for context):

| inst | feat/subset | H | test acc | n | trades/day | edge |
|---|---|---|---|---|---|---|
| BTCUSDT | burst/all | 15 | 0.6049 | 220037 | 2703 | +0.26 |
| BTCUSDT | logit/top10 | 15 | 0.6423 | 96492 | 1213 | +0.34 |
| BTCUSDT | ofi5/top10 | 15 | 0.5825 | 194862 | 2596 | +0.20 |
| BTCUSDT | mom1/top10 | 15 | 0.5890 | 157029 | 1849 | +0.33 |
| BTCUSDT | logit/all | 15 | 0.5562 | 386226 | 5082 | +0.13 |
| BTCUSDT | burst/all | 30 | 0.5869 | 152149 | 1771 | +0.32 |
| BTCUSDT | ofi15/top10 | 15 | 0.6053 | 100454 | 1352 | +0.22 |
| BTCUSDT | logit/top10 | 30 | 0.6216 | 74155 | 881 | +0.39 |