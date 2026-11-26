## Theory: best possible P(EUR 10k in time T), any strategy

| leverageable Sharpe | 1 yr, no deposits | 1 yr, +100/mo | 1 yr, +250/mo | 1 yr, +350/mo | 2 yr, +100/mo | 3 yr, +100/mo |
|---|---|---|---|---|---|---|
| 1.0 | 23% | 50% | 72% | 82% | 80% | 93% |
| 1.3 | 33% | 62% | 81% | 88% | 90% | 98% |
| 1.6 | 44% | 73% | 88% | 93% | 95% | 99% |
| 2.0 | 60% | 84% | 94% | 97% | 99% | 100% |
| 2.6 | 80% | 95% | 99% | 99% | 100% | 100% |
| 3.0 | 89% | 98% | 100% | 100% | 100% | 100% |
Traceback (most recent call last):
  File "/Users/churchxelachurchxela/Projects/openbot-lab/goal80.py", line 25, in <module>
    print("\nneeded for 80% in 1 year with no deposits: Sharpe x sqrt(T) >= %.2f" % (norm.ppf(0.8) - norm.ppf(X0 / G)))
TypeError: not enough arguments for format string
