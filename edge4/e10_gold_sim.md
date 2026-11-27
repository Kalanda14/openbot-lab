overnight: legs worst by LOW / worst by CLOSE, per-leg median ratio 1.18
whole night min LOW / min CLOSE drawdown: median 1.07, p90 1.56, p99 6.40, share > 1.25: 19%; extra in points (low-close) median 2.5 p99 29.9
vol20 threshold (fixed from 2020-26) = 24% yearly
sim legs day-total train std 0.00479; gold_vm train std 0.00706; corr(gold, legs total) +0.036
| variant | SA hit/<100 | ST | S17 |
|---|---|---|---|
| base cap100 | 77%/17% | 71%/21% | 83%/5% |
  gold x0.5 rescale=True: s=0.974; day-total Sharpe all 1.69 -> 1.79; 2017-21 1.85 -> 1.91; 2022-26 1.54 -> 1.68
| gold x0.5 rescaled cap100 | 78%/18% | 75%/19% | 82%/3% |
  gold x1.0 rescale=True: s=0.927; day-total Sharpe all 1.69 -> 1.84; 2017-21 1.85 -> 1.91; 2022-26 1.54 -> 1.77
| gold x1.0 rescaled cap100 | 78%/19% | 81%/14% | 83%/3% |
  gold x2.0 rescale=True: s=0.803; day-total Sharpe all 1.69 -> 1.82; 2017-21 1.85 -> 1.81; 2022-26 1.54 -> 1.83
| gold x2.0 rescaled cap100 | 76%/21% | 85%/11% | 79%/11% |
  gold x1.0 rescale=False: s=1.000; day-total Sharpe all 1.69 -> 1.84; 2017-21 1.85 -> 1.91; 2022-26 1.54 -> 1.77
| gold x1 NOT rescaled cap100 | 78%/19% | 81%/16% | 84%/4% |
| base smooth 100*(W-100)/300 | 69%/3% | 62%/5% | 72%/5% |
  gold x0.5 rescale=True: s=0.974; day-total Sharpe all 1.69 -> 1.79; 2017-21 1.85 -> 1.91; 2022-26 1.54 -> 1.68
| gold x0.5 rescaled smooth 100*(W-100)/300 | 70%/3% | 67%/5% | 70%/1% |
  gold x1.0 rescale=True: s=0.927; day-total Sharpe all 1.69 -> 1.84; 2017-21 1.85 -> 1.91; 2022-26 1.54 -> 1.77
| gold x1.0 rescaled smooth 100*(W-100)/300 | 71%/3% | 71%/2% | 68%/1% |
  gold x2.0 rescale=True: s=0.803; day-total Sharpe all 1.69 -> 1.82; 2017-21 1.85 -> 1.81; 2022-26 1.54 -> 1.83
| gold x2.0 rescaled smooth 100*(W-100)/300 | 72%/5% | 80%/2% | 67%/3% |
  gold x1.0 rescale=False: s=1.000; day-total Sharpe all 1.69 -> 1.84; 2017-21 1.85 -> 1.91; 2022-26 1.54 -> 1.77
| gold x1 NOT rescaled smooth 100*(W-100)/300 | 71%/4% | 74%/2% | 70%/0% |