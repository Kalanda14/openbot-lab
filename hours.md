  h = d.resample("1h").last().pct_change().dropna()
train t by UTC hour: {0: 0.7, 1: 0.9, 2: -1.4, 3: -0.9, 4: -1.5, 5: 0.8, 6: 1.9, 7: 0.8, 8: 0.5, 9: -0.4, 10: 0.4, 11: 0.1, 12: 0.9, 13: 3.4, 14: -1.8, 15: 1.4, 16: 0.3, 17: 0.4, 18: 0.1, 19: 1.4, 20: 0.6, 21: 3.5, 22: 0.9, 23: -1.1}
chosen: {13: 1, 21: 1}
same hours in TEST (t): {13: np.float64(-1.4), 21: np.float64(0.8)}
strategy daily Sharpe TRAIN -0.88 TEST -6.46, TEST %/yr -106.3
