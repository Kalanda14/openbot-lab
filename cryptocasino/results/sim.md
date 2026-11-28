# sim.py output

```
## 1. Rakeback only, 1% edge game, EV EUR for 30-day volume V
  rakeback 5% of edge, V=20000: EV -190.0
  rakeback 5% of edge, V=50000: EV -475.0
  rakeback 10% of edge, V=20000: EV -180.0
  rakeback 10% of edge, V=50000: EV -450.0
  rakeback 25% of edge, V=20000: EV -150.0
  rakeback 25% of edge, V=50000: EV -375.0
  rakeback 50% of edge, V=20000: EV -100.0
  rakeback 50% of edge, V=50000: EV -250.0
  rakeback 70% of edge, V=20000: EV -60.0
  rakeback 70% of edge, V=50000: EV -150.0

## 2. Stake-style 200% welcome, 40x (dep+bonus), wagering weighted by edge/4% (1% dice counts 25%), bet = 1% of deposit
   {'req_wager_real': 192000, 'exp_cost': 1920, 'p_finish': 0.113, 'mean': -313.9, 'p10': -400.0, 'p50': -400.0, 'p90': -47.4, 'p_loss': 0.907}
  same, bonus capped/sized 100% (EUR400)  {'req_wager_real': 128000, 'exp_cost': 1280, 'p_finish': 0.13, 'mean': -332.6, 'p10': -400.0, 'p50': -400.0, 'p90': -181.4, 'p_loss': 0.933}

## 3. Rainbet/Shuffle-style 100% match, 40x (dep+bonus)
  IF 1% originals count 100% (best case, NOT confirmed), bet EUR5: {'req_wager_real': 32000, 'exp_cost': 320, 'p_finish': 0.826, 'mean': 89.6, 'p10': -400.0, 'p50': 70.8, 'p90': 592.9, 'p_loss': 0.436}
  IF 1% originals count 100%, bet EUR20: {'req_wager_real': 32000, 'exp_cost': 320, 'p_finish': 0.533, 'mean': 125.1, 'p10': -400.0, 'p50': -126.2, 'p90': 1095.2, 'p_loss': 0.543}
  IF slots only (RTP 96%, modelled as 4% edge coin), bet EUR5: {'req_wager_real': 32000, 'exp_cost': 1280, 'p_finish': 0.08, 'mean': -378.8, 'p10': -400.0, 'p50': -400.0, 'p90': -400.0, 'p_loss': 0.979}

## 4. Roobet 20% slot-loss cashback, 7 days, cap $200/day, no wagering (third-party terms)
  slot RTP 0.96, bet 0.25 of day-start bank: {'EV': 57.7, 'mean_wager': 2491, 'mean_cashback': 162.9, 'p10': -401.6, 'p50': -399.0, 'p90': -285.2, 'p_loss': 0.962}
  slot RTP 0.96, bet 0.5 of day-start bank: {'EV': 37.6, 'mean_wager': 2650, 'mean_cashback': 149.2, 'p10': -401.7, 'p50': -401.2, 'p90': -371.8, 'p_loss': 0.987}
  slot RTP 0.96, bet 1.0 of day-start bank: {'EV': 11.9, 'mean_wager': 2948, 'mean_cashback': 135.4, 'p10': -401.7, 'p50': -401.4, 'p90': -396.3, 'p_loss': 0.996}
  slot RTP 0.94, bet 0.25 of day-start bank: {'EV': 7.1, 'mean_wager': 2477, 'mean_cashback': 161.3, 'p10': -401.6, 'p50': -399.3, 'p90': -303.6, 'p_loss': 0.966}
  slot RTP 0.94, bet 0.5 of day-start bank: {'EV': -2.6, 'mean_wager': 2422, 'mean_cashback': 148.4, 'p10': -401.7, 'p50': -401.2, 'p90': -377.4, 'p_loss': 0.988}
  slot RTP 0.94, bet 1.0 of day-start bank: {'EV': 5.8, 'mean_wager': 2036, 'mean_cashback': 133.6, 'p10': -401.7, 'p50': -401.4, 'p90': -396.5, 'p_loss': 0.995}

## 5. 10% lossback, one all-in 1%-edge dice bet (Thrill-type, terms unverified)
   {'mean': 8.2, 'p10': -362.6, 'p50': -362.6, 'p90': 386.0, 'p_loss': 0.505}
  20% lossback for comparison: {'mean': 31.4, 'p10': -323.2, 'p50': 386.0, 'p90': 386.0, 'p_loss': 0.5}

## 6. Free bet value (stake not returned), $100 = EUR86 free bet, 6.7% margin (Cloudbet measured)
  odds 1.5: EUR 26.9
  odds 2.0: EUR 40.3
  odds 3.0: EUR 53.7
  odds 5.0: EUR 64.5
```
