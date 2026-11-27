# Hartley-Schwarz (2019) end-of-month Treasury effect. Rules fixed before looking:
# EOM1: long 7-10y Treasuries (IEF proxy for ZN) close T-1 -> close of last trading day of month.
# EOM3: long close T-3 -> close of last trading day (last 3 days).
# Return = IEF adj-close return minus T-bill (^IRX) daily = futures-like excess return.
# Cost: 2 bp per round trip (ZN: 1 tick spread+comm ~1.8bp on ~$110k).
import json, pandas as pd, numpy as np
D = '/private/tmp/claude-501/-Users-churchxelachurchxela/dc54c735-467e-48e2-abbf-5b84c893f120/scratchpad/edge3/data/yf/'
def load(n, adj=True):
    j = json.load(open(D + n + '.json'))['chart']['result'][0]
    idx = pd.to_datetime(j['timestamp'], unit='s').normalize()
    v = j['indicators']['adjclose'][0]['adjclose'] if adj else j['indicators']['quote'][0]['close']
    return pd.Series(v, idx).dropna().groupby(level=0).last()
ief = load('IEF'); tlt = load('TLT'); irx = load('IRX', adj=False)
rf = (irx.reindex(ief.index).ffill() / 100 / 252).shift(1).fillna(0)
COST = 0.0002
def run(px, k):
    r = px.pct_change() - rf.reindex(px.index).fillna(0)
    r = r.dropna()
    ym = r.index.to_period('M')
    # position k last trading days of each month (except current incomplete month)
    rank_from_end = r.groupby(ym).cumcount(ascending=False)  # 0 = last day
    pos = (rank_from_end < k).astype(float)
    pos[ym == ym[-1]] = 0
    strat = pos * r
    # cost once per month on the last day
    strat = strat - COST * (rank_from_end == 0) * (ym != ym[-1])
    return strat, pos
def stats(s, pos, lab):
    s = s.copy()
    act = s[pos > 0]
    # per-trade = monthly sum
    tr = s.groupby(s.index.to_period('M')).sum()
    tr = tr[tr != 0]
    sh = s.mean() / s.std() * np.sqrt(252)
    print(f"{lab:14s} Sharpe {sh:5.2f}  trades {len(tr):4d}  win {100*(tr>0).mean():4.1f}%  mean/trade {1e4*tr.mean():5.1f}bp  t {tr.mean()/tr.std()*np.sqrt(len(tr)):4.2f}")
    return tr
for name, px in [('IEF', ief), ('TLT', tlt)]:
    for k in (1, 3):
        s, pos = run(px, k)
        print(f'--- {name} EOM{k}')
        tr = stats(s[s.index < '2022'], pos[s.index < '2022'], 'train 02-21')
        tt = stats(s[s.index >= '2022'], pos[s.index >= '2022'], 'test 22-26')
        yr = s.groupby(s.index.year).sum()
        print('  by year (bp):', ' '.join(f"{y%100}:{1e4*v:+.0f}" for y, v in yr.items()))
        if name == 'IEF':
            pd.DataFrame({'r': s}).to_csv(D + f'../eom{k}_daily.csv')
# correlation with book sleeves (daily, test period)
st = pd.read_csv('/Users/churchxelachurchxela/Projects/openbot/stack4_daily.csv', index_col=0, parse_dates=True)
for k in (1, 3):
    s = pd.read_csv(D + f'../eom{k}_daily.csv', index_col=0, parse_dates=True)['r']
    j = st[['B', 'ON', 'TREND']].join(s, how='inner')
    j = j[j.index >= '2022']
    print(f'EOM{k} corr 2022-26:', j.corr()['r'].round(3).to_dict(), 'n', len(j))
    # monthly corr
    m = j.resample('M').sum()
    print(f'   monthly corr:', m.corr()['r'].round(3).to_dict())
