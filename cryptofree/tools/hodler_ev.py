"""HODLer/Launchpool EV per EUR400 of BNB, 2026 data. Pools (F) from Binance announcements; prices (F) Binance klines first-day close;
eligible BNB pool size is an ESTIMATE (not published)."""
import json,math,statistics,datetime
R='raw/'
def k(s): return json.load(open(R+f'kl_{s}.json'))
def day_close(s,date):
    for r in k(s):
        if datetime.datetime.fromtimestamp(r[0]/1000,datetime.UTC).date().isoformat()>=date: return float(r[4])
drops=[('BREV',15e6,'2026-01-06'),('NIGHT',240e6,'2026-03-11'),('ROBO',100e6,'2026-03-04'),('CHIP',25e6,'2026-04-28'),
       ('AIGENSYN',100e6,'2026-05-21'),('GENIUS',10e6,'2026-05-29'),('OPG',6.4e6,'2026-06-30'),('OPN',20e6*0.7,'2026-03-05')]  # OPN: Launchpool, ~70% assumed to BNB pool (E)
tot=0
for s,amt,d in drops:
    p=day_close(s+'USDT',d); v=amt*p; tot+=v
    print(f'{s:9s} {d} price {p:.4f} pool ${v/1e6:5.2f}M  now {float(k(s+"USDT")[-1][4]):.4f}')
eur=1/1.0949; bnb=float(k('BNBUSDT')[-1][4]); stake_bnb=400/eur/bnb
print(f'total 2026 (Jan-Nov) ${tot/1e6:.1f}M; EUR400 = {stake_bnb:.3f} BNB at ${bnb}')
for pool in (10e6,20e6,35e6):
    per_bnb=tot/pool; yr=per_bnb/bnb*12/11
    print(f' eligible pool {pool/1e6:.0f}M BNB: ${per_bnb:.2f}/BNB over 11 mo -> {yr*100:.2f}%/yr -> EUR{stake_bnb*per_bnb/11*eur:.2f} per 30d on EUR400')
c=[float(r[4]) for r in k('BNBUSDT')][-366:]
lr=[math.log(c[i]/c[i-1]) for i in range(1,len(c))]
sd30=statistics.stdev(lr)*math.sqrt(30)
print(f'BNB 30d vol (last yr) {sd30*100:.1f}% -> 1-sd move on EUR400 = EUR{400*sd30:.0f}')
