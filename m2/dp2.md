DP (m2/dp2.py), real CME B + ON paths, base ON book, cells = P(hit 700) / P(end<100): all | 2020-23 | 2024-26
legs/day 3 (ON, B), DP value 65.6%
| DP 2 legs | no tp, no band | 67% / 23% | 73% / 21% | 59% / 26% |
| DP 2 legs | tp + band25% | 70% / 22% | 75% / 20% | 62% / 25% |
legs/day 14 (ON 1 leg, B every 30 min), DP iid value 76.4%
| DP ON1/B30 | no tp, no band | 70% / 17% | 76% / 14% | 62% / 20% |
| DP ON1/B30 | tp + band25% | 71% / 16% | 76% / 14% | 65% / 20% |
legs/day 33 (ON every 30, B every 30), DP iid value 85.3% (fake: iid sub-legs ignore within-day dependence)
| DP ON30/B30 | no tp, no band | 65% / 13% | 74% / 9% | 52% / 18% |
| DP ON30/B30 | tp + band25% | 68% / 12% | 76% / 9% | 57% / 17% |
