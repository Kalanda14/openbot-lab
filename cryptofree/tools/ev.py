"""30/90-day EV table for free crypto rewards, Georgian resident, EUR400. Numbers in EUR. 1 EUR = 1.095 USD.
Each row: (name, low, mid, high, p_live_and_eligible). mid already includes costs. See REPORT.md for sources (F/E)."""
U=1/1.095
rows30=[
 # Binance Bonanza: new user can reach 0.88 + 7*0.66 + ~13*0.05 = 6.15 -> claim tier 1 = 5 USDC; small-trade costs ~1.5 USD
 ('Binance Black Friday Bonanza (to Dec 8)', 2*U, 3.5*U, 4.5*U, 0.9),
 # Binance new-user Simple Earn: 200*0.35*7/365=1.34 + 3% bonus on 438 for 13d=0.47 + 2% base 30d=0.72
 ('Binance USDT Earn (35% new-user + 5% promo)', 1.5, 2.3, 2.6, 0.9),
 ('Binance Rewards Hub new-user tasks (14d)', 0, 8, 14, 0.6),
 ('Binance Word of the Day x4 weeks', 0.3, 1.5, 3.5, 0.9),
 # Bybit: 5+10+2 = 17 USDT (skip 40k-volume step) + Fiat Welcome 10 USDT; cost ~1.5 USD
 ('Bybit welcome 17 USDT + Fiat Welcome 10 USDT', 0, 23*U, 25.5*U, 0.5),
 ('Bitget/OKX in-app new-user cash parts', 0, 6, 12, 0.6),
 ('Referrals (real friends only, 0-2)', 0, 3, 8, 1.0),
 ('HODLer/Launchpool on EUR400 BNB', 0.07, 0.15, 0.25, 1.0),  # see hodler_ev.py; ignores +-EUR51 1-sd BNB move
 ('Airdrop farming, 1 new wallet', -5, -2, 0, 1.0),          # gas spent, no drop inside 30d
 ('Conversion EUR->USDT->GEL + transfers', -8, -5, -3, 1.0),
]
def tot(rows):
    lo=sum(r[1] if r[1]<0 else 0 for r in rows)
    mid=sum(r[2]*r[4] for r in rows)
    hi=sum(r[3] for r in rows)
    return lo,mid,hi
print('30 days')
for r in rows30: print(f'  {r[0]:48s} mid*p = {r[2]*r[4]:6.2f}   (if live: {r[1]:.1f}..{r[3]:.1f})')
lo,mid,hi=tot(rows30); print(f'  TOTAL 30d: worst {lo:.0f}, expected {mid:.0f}, best {hi:.0f}')
extra90=[('WOTD 8 more weeks',0.6,3,7,0.9),('stablecoin yield 60 more days @3%',1.5,2,4,1.0),
         ('recurring promos for existing users (2 months)',0,6,15,0.7),('airdrop lottery from 90d of use',0,6,40,1.0),
         ('more gas',-5,-3,-1,1.0)]
lo2,mid2,hi2=tot(rows30+extra90); print(f'  TOTAL 90d: worst {lo2:.0f}, expected {mid2:.0f}, best {hi2:.0f}')
print('Conditional, not in total: Bybit Card 10% new-user cashback (cap $150) IF still live, on EUR400 of spending you do anyway: ~EUR32-36')
