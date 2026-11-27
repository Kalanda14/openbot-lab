# Breedon-Ranaldo (2013) FX time-of-day. Rule fixed from paper Table 1/2 (NY time):
#  EUR leg: short EUR/USD 02:00 -> 08:00 NY (Europe open to US open)
#  USD leg: long  EUR/USD 08:00 -> 16:00 NY (US session)
# Weekdays only. Price = open of the hourly bar starting at that NY hour.
# Cost: 0.8 bp per leg round trip (6E futures / ECN EURUSD), i.e. 1.6 bp/day for both legs.
import glob, json, pandas as pd, numpy as np
B = '/private/tmp/claude-501/-Users-churchxelachurchxela/dc54c735-467e-48e2-abbf-5b84c893f120/scratchpad/edge3/'
COST = 0.00008
def binance():
    fs = sorted(glob.glob(B + 'data/eurusdt/*.csv'))
    df = pd.concat([pd.read_csv(f, header=None, usecols=[0, 1]) for f in fs])
    t = df[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
    s = pd.Series(df[1].values, pd.to_datetime(t, unit='ms', utc=True))
    return s[~s.index.duplicated()].sort_index()
def yahoo(sym):
    j = json.load(open(B + f'data/yf/{sym}_1h.json'))['chart']['result'][0]
    s = pd.Series(j['indicators']['quote'][0]['open'], pd.to_datetime(j['timestamp'], unit='s', utc=True)).dropna()
    return s[~s.index.duplicated()].sort_index()
def legs(op):
    ny = op.tz_convert('America/New_York')
    df = pd.DataFrame({'p': ny.values, 'd': ny.index.date, 'h': ny.index.hour, 'm': ny.index.minute, 'wd': ny.index.weekday})
    df = df[(df.m == 0) & (df.wd < 5)]
    pv = df.pivot_table(index='d', columns='h', values='p', aggfunc='first')
    eu = -(pv[8] / pv[2] - 1) - COST
    us = (pv[16] / pv[8] - 1) - COST
    out = pd.DataFrame({'EU': eu, 'US': us}).dropna()
    out.index = pd.to_datetime(out.index)
    out['BOTH'] = out.EU + out.US
    return out
def rep(r, lab):
    sh = r.mean() / r.std() * np.sqrt(252)
    t = r.mean() / r.std() * np.sqrt(len(r))
    print(f'  {lab:12s} n {len(r):4d} Sharpe {sh:5.2f} win {100*(r>0).mean():4.1f}% mean {1e4*r.mean():5.2f}bp t {t:4.2f}')
res = {}
for name, s in [('BINANCE EURUSDT', binance()), ('YAHOO EURUSD', yahoo('EURUSD=X')), ('YAHOO GBPUSD', yahoo('GBPUSD=X'))]:
    L = legs(s); res[name] = L
    print('===', name, L.index[0].date(), L.index[-1].date())
    for c in ('EU', 'US', 'BOTH'):
        r = L[c]
        if name.startswith('BINANCE'):
            rep(r[r.index < '2022'], c + ' 20-21'); rep(r[r.index >= '2022'], c + ' 22-26')
        else:
            rep(r, c + ' all')
    yr = L.groupby(L.index.year).agg(['mean'])
    print('  by year mean bp:', {y: tuple(round(1e4 * v, 2) for v in row) for y, row in zip(yr.index, yr.values)})
    print('  gross (no cost) mean bp:', round(1e4 * (L.EU.mean() + COST), 2), round(1e4 * (L.US.mean() + COST), 2))
# overlap check Binance vs Yahoo
a, b = res['BINANCE EURUSDT'], res['YAHOO EURUSD']
j = a.join(b, lsuffix='_bn', rsuffix='_yf', how='inner')
print('Binance vs Yahoo leg corr (overlap):', round(j.EU_bn.corr(j.EU_yf), 2), round(j.US_bn.corr(j.US_yf), 2), 'n', len(j))
st = pd.read_csv('/Users/churchxelachurchxela/Projects/openbot/stack4_daily.csv', index_col=0, parse_dates=True)
k = st[['B', 'ON', 'TREND']].join(a.BOTH.rename('FX'), how='inner')
k = k[k.index >= '2022']
print('corr BOTH vs book 2022-26:', k.corr()['FX'].round(3).to_dict(), 'n', len(k))
a.to_csv(B + 'fx_binance_legs.csv')
