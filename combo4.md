>> standard path ($25 + $149 activation) | cap 30 | backtest: P(money back) 50% | P(lose>$100) 16% | avg +44
>> standard path ($25 + $149 activation) | cap 30 | cautious: P(money back) 45% | P(lose>$100) 20% | avg +35
>> standard path ($25 + $149 activation) | cap 60 | backtest: P(money back) 55% | P(lose>$100) 14% | avg +50
>> standard path ($25 + $149 activation) | cap 60 | cautious: P(money back) 51% | P(lose>$100) 18% | avg +40
>> NO-activation path ($47.50, $0 activation) | cap 30 | backtest: P(money back) 55% | P(lose>$100) 16% | avg +58
>> NO-activation path ($47.50, $0 activation) | cap 30 | cautious: P(money back) 51% | P(lose>$100) 18% | avg +48
>> NO-activation path ($47.50, $0 activation) | cap 60 | backtest: P(money back) 60% | P(lose>$100) 13% | avg +62
>> NO-activation path ($47.50, $0 activation) | cap 60 | cautious: P(money back) 54% | P(lose>$100) 16% | avg +52

## Sleeve vs fee gap (own account recovers the gap in 21 days; funding spread 3x; deadline sizing)
gap $25 cap 30: backtest 79% / cautious 76% (lose>$100 4%)
gap $25 cap 60: backtest 80% / cautious 76% (lose>$100 3-4%)
gap $47.5 cap 30: backtest 71% / cautious 66% (lose>$100 7-10%)
=> 80% plan: month-1 fee gap must be only $25: Topstep standard Combine with 50% code ($25), trade it from bot ALERTS
   (no $29 API), and pay the $149 activation in month 2 (not inside month 1).
