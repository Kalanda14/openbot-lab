| book | weights | Sharpe 20-21 | 22-26 | 24-26 | Browne(22-26) | Browne(24-26) |
|---|---|---|---|---|---|---|
| ref: stack4 B (=real CME), base ON, rp (m1 book) | {'B': np.float64(0.377), 'ON': np.float64(0.601), 'TREND': np.float64(0.022)} | 1.80 | 1.58 | 1.47 | 73.7% | 72.7% |
| base ON, risk parity | {'B': np.float64(0.376), 'ON': np.float64(0.602), 'TREND': np.float64(0.022)} | 1.75 | 1.54 | 1.44 | 73.4% | 72.5% |
| base ON, train maxSharpe shrunk 50% | {'B': np.float64(0.255), 'ON': np.float64(0.708), 'TREND': np.float64(0.037)} | 2.07 | 1.39 | 1.41 | 72.0% | 72.1% |
| base ON + EOM3, risk parity | {'B': np.float64(0.124), 'ON': np.float64(0.198), 'TREND': np.float64(0.007), 'EOM': np.float64(0.67)} | 1.41 | 1.56 | 1.46 | 73.6% | 72.6% |
| base ON + EOM3, train maxSharpe shrunk 50% | {'B': np.float64(0.112), 'ON': np.float64(0.356), 'TREND': np.float64(0.019), 'EOM': np.float64(0.513)} | 2.00 | 1.47 | 1.45 | 72.7% | 72.5% |
| plus ON, risk parity | {'B': np.float64(0.404), 'ON': np.float64(0.572), 'TREND': np.float64(0.024)} | 1.89 | 1.82 | 2.03 | 75.9% | 77.8% |
| plus ON, train maxSharpe shrunk 50% | {'B': np.float64(0.26), 'ON': np.float64(0.705), 'TREND': np.float64(0.035)} | 2.20 | 1.63 | 2.00 | 74.3% | 77.5% |
| plus ON + EOM3, risk parity | {'B': np.float64(0.127), 'ON': np.float64(0.18), 'TREND': np.float64(0.007), 'EOM': np.float64(0.686)} | 1.53 | 1.83 | 1.97 | 76.1% | 77.3% |
| plus ON + EOM3, train maxSharpe shrunk 50% | {'B': np.float64(0.113), 'ON': np.float64(0.351), 'TREND': np.float64(0.018), 'EOM': np.float64(0.518)} | 2.13 | 1.70 | 2.01 | 74.9% | 77.6% |
| (Dukascopy B paths) base ON, rp | {'B': np.float64(0.413), 'ON': np.float64(0.567), 'TREND': np.float64(0.021)} | 1.99 | 1.35 | 1.36 | 71.6% | 71.7% |
B sleeve stack4: Sharpe 20-21 0.22 22-26 1.43
B sleeve duka: Sharpe 20-21 0.55 22-26 1.08
B sleeve real: Sharpe 20-21 0.14 22-26 1.37
EOM3 sleeve: 20-21 0.04 22-26 0.69
