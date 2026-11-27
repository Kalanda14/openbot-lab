"""EV of the verified Georgian casino promos (Crocobet Registration Missions, Betlive Welcome, Crocobet Cashback Roulette).
Facts used (from public APIs, saved in raw/):
  - Crocobet free spin = 0.15 GEL  (raw/lp/croco_regmissions_cashout.json: transfer_prizes value 0.15)
  - Betlive free spin  = 0.15 GEL  (raw/bl/rules_welcome-bonus-bank_en.txt)
  - Crocobet missions, doubled until 2026-12-01 11:59: M1 reg 200 FS, M2 dep 50 + wager it 200 FS,
    M3 5,000 GEL total bets 1,000 FS, M4 10,000 GEL total bets 1,400 FS, all within 7 days of registering
  - 5% tax on the amount withdrawn (Georgian citizens), Crocobet: wager >=30% of deposits or up to 20% fee.
Estimates: free-spin slot RTP 0.96; wagering game RTP 0.99 (BGaming Plinko 2 published RTP, operator may set lower)
or 0.97/0.985 (fast games). Per-drop sd ~1.0x stake (low/medium risk plinko; estimate).
"""
import random, statistics as st
EURGEL = 2.843; TAX = 0.05; FS = 0.15; FS_RTP = 0.96

def missions(rtp, doubled=True, bet=2.0, bank=300.0, sd=1.0, runs=4000, seed=1):
    k = 1 if doubled else 0.5
    fs = {"M1": 200*k, "M2": 200*k, "M3": 1000*k, "M4": 1400*k}
    rng = random.Random(seed); res = []; bust = 0
    for _ in range(runs):
        bal = bank; wag = 0.0
        while wag < 10000 and bal >= bet:
            bal += bet * (rng.gauss(rtp, sd) - 1); wag += bet
        if wag < 10000: bust += 1
        got = fs["M1"] + fs["M2"] + (fs["M3"] if wag >= 5000 else 0) + (fs["M4"] if wag >= 10000 else 0)
        fsval = sum(rng.gauss(FS * FS_RTP, FS * 3) for _ in range(int(got)))   # free-spin wins, noisy
        end = max(bal, 0) + max(fsval, 0)
        res.append(end * (1 - TAX) - bank)                                      # withdraw everything, pay 5%
    res.sort()
    return {"rtp": rtp, "doubled": doubled, "mean_GEL": round(st.mean(res), 1), "mean_EUR": round(st.mean(res)/EURGEL, 1),
            "p10_EUR": round(res[len(res)//10]/EURGEL, 1), "p90_EUR": round(res[9*len(res)//10]/EURGEL, 1),
            "P(loss)": round(sum(r < 0 for r in res)/len(res), 3), "P(bust before 10k)": round(bust/runs, 3)}

def m1m2_only():
    # register (200 FS) + deposit 50 and wager it once (200 FS); withdraw at end
    ev = 400 * FS * FS_RTP + 50 * (0.97 - 1)
    return round((ev + 50) * (1 - TAX) - 50, 1)

def cashback_roulette(budget=200.0, v=0.946, edge=0.027, cap=200.0, minpay=10.0):
    # daily roulette number 0..36 -> cashback %, known BEFORE you play. One even-money bet of X if worth it.
    pct = {0: .90, 36: .40}
    for n in range(1, 36): pct[n] = 0.05 * ((n - 1)//5 + 1)
    tot = 0.0
    for n in range(37):
        c = pct[n]; best = 0.0
        for X in [budget * i / 20 for i in range(1, 21)]:
            pay = min(c * X, cap); pay = pay if pay >= minpay else 0
            best = max(best, -edge * X + (19/37) * pay * v)
        tot += best / 37
    return round(tot, 2)

if __name__ == "__main__":
    out = []
    for rtp in (0.99, 0.985, 0.97):
        for d in (True, False):
            r = missions(rtp, d); out.append(r); print(r)
    print("Crocobet M1+M2 only (GEL net):", m1m2_only(), "EUR", round(m1m2_only()/EURGEL, 1))
    b = 500 * FS * FS_RTP * (1 - TAX)
    print("Betlive 500 FS welcome (no deposit) net GEL", round(b, 1), "EUR", round(b/EURGEL, 1))
    for B in (100, 200, 400):
        x = cashback_roulette(B); print(f"Cashback Roulette daily EV, max bet {B} GEL: {x} GEL/day = {round(x/EURGEL,2)} EUR/day (before 5% tax)")
