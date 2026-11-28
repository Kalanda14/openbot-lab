"""EV + Monte Carlo for crypto-casino promos, one honest player, EUR400 bankroll, 30 days.
All money in EUR. 1 USD = 0.86 EUR (E). Promo terms come from REPORT.md (F = official terms, E = third-party/estimate).
Fees (E): buy USDT with GEL + withdraw/sell back ~1.5% round trip + ~EUR2 network fees."""
import random, statistics as st
USD = 0.86
FEE = lambda amt: 0.015 * amt + 2.0
R = random.Random(7)

def summ(xs):
    xs = sorted(xs); n = len(xs)
    return dict(mean=round(st.mean(xs), 1), p10=round(xs[n // 10], 1), p50=round(xs[n // 2], 1), p90=round(xs[9 * n // 10], 1),
                p_loss=round(sum(x < 0 for x in xs) / n, 3))

# --- 1. rakeback / VIP only: EV = -(1 - r) * edge * volume  (closed form, no simulation needed)
def rakeback_table():
    out = []
    for r in (0.05, 0.10, 0.25, 0.50, 0.70):
        for V in (20000, 50000):
            out.append((r, V, round(-(1 - r) * 0.01 * V, 1)))
    return out

# --- 2. wagering bonus on a 1%-edge game, flat bets, sticky (deposit+bonus locked until done)
def wager_bonus(dep, bonus, mult_on, mult, edge, contrib, bet, p_win=None, runs=4000):
    """mult_on='db' -> requirement = mult*(dep+bonus); contrib = share of each bet that counts.
    Game: even-money-ish dice, p_win = (1-edge)/2 for 2x payout. Returns P(finish) and net EUR distribution."""
    p = p_win or (1 - edge) / 2
    req = mult * ((dep + bonus) if mult_on == "db" else bonus)
    res = []; fin = 0
    for _ in range(runs):
        bal = dep + bonus; done = 0.0
        while done < req and bal >= bet:
            bal += bet if R.random() < p else -bet
            done += bet * contrib
        if done >= req:
            fin += 1; net = bal - dep - FEE(bal)
        else:
            net = bal - dep   # bust (bal < bet): almost everything lost
        res.append(net)
    return dict(req_wager_real=round(req / contrib), exp_cost=round(req / contrib * edge), p_finish=round(fin / runs, 3), **summ(res))

# --- 3. loss rebate (cashback on net losses, no wagering)
def slot_spin(rtp):
    # high-volatility slot: 30% hit rate, lognormal hits; per-spin sd ~6x stake
    if R.random() < 0.30:
        return (rtp / (0.30 * 3.597)) * R.lognormvariate(0, 1.6)
    return 0.0

def roobet_cashback(rtp=0.96, days=7, bank=400.0, cb=0.20, cap=200 * USD, frac=0.25, max_spins=12, runs=20000):
    """Each day: bet frac*start-of-day bank per spin, stop when ahead, bust or after max_spins.
    Cashback = cb * net slot loss of the day, capped. Withdraw at the end.
    Slot wins are heavy-tailed, so the sample mean is noisy; EV is reported as
    E[cashback] - (1-rtp)*E[wager] - fees, which uses the exact slot expectation."""
    res = []; W = []; C = []
    for _ in range(runs):
        b = bank; w = c = 0.0
        for d in range(days):
            if b < 1: break
            b0 = b; bet = frac * b0; n = 0
            while n < max_spins and b >= bet and b <= b0:
                b += bet * (slot_spin(rtp) - 1); n += 1; w += bet
            x = min(cb * max(0.0, b0 - b), cap); b += x; c += x
        res.append(b - bank - FEE(b)); W.append(w); C.append(c)
    ev = st.mean(C) - (1 - rtp) * st.mean(W) - FEE(bank * 0.6)
    return dict(EV=round(ev, 1), mean_wager=round(st.mean(W)), mean_cashback=round(st.mean(C), 1), **{k: v for k, v in summ(res).items() if k != "mean"})

def dice_lossback(cb=0.10, bank=400.0, edge=0.01, runs=20000):
    """One even-money dice bet of the whole bank, lossback paid on the net loss, no wagering."""
    p = (1 - edge) / 2; res = []
    for _ in range(runs):
        if R.random() < p: end = 2 * bank
        else: end = cb * bank
        res.append(end - bank - FEE(end))
    return summ(res)

# --- 4. sportsbook free bet (stake not returned): value = F*(1-1/o)/(1+m) at book odds o, margin m
def free_bet_value(F, o, m):
    return round(F * (1 - 1 / o) / (1 + m), 1)

if __name__ == "__main__":
    L = []
    P = lambda *a: (print(*a), L.append(" ".join(str(x) for x in a)))
    P("## 1. Rakeback only, 1% edge game, EV EUR for 30-day volume V")
    for r, V, ev in rakeback_table(): P(f"  rakeback {int(r*100)}% of edge, V={V}: EV {ev}")
    P("\n## 2. Stake-style 200% welcome, 40x (dep+bonus), wagering weighted by edge/4% (1% dice counts 25%), bet = 1% of deposit")
    P("  ", wager_bonus(400, 800, "db", 40, 0.01, 0.25, 4.0, runs=300))
    P("  same, bonus capped/sized 100% (EUR400) ", wager_bonus(400, 400, "db", 40, 0.01, 0.25, 4.0, runs=300))
    P("\n## 3. Rainbet/Shuffle-style 100% match, 40x (dep+bonus)")
    P("  IF 1% originals count 100% (best case, NOT confirmed), bet EUR5:", wager_bonus(400, 400, "db", 40, 0.01, 1.0, 5.0, runs=1500))
    P("  IF 1% originals count 100%, bet EUR20:", wager_bonus(400, 400, "db", 40, 0.01, 1.0, 20.0, runs=3000))
    P("  IF slots only (RTP 96%, modelled as 4% edge coin), bet EUR5:", wager_bonus(400, 400, "db", 40, 0.04, 1.0, 5.0, runs=1500))
    P("\n## 4. Roobet 20% slot-loss cashback, 7 days, cap $200/day, no wagering (third-party terms)")
    for rtp in (0.96, 0.94):
        for frac in (0.25, 0.5, 1.0):
            P(f"  slot RTP {rtp}, bet {frac} of day-start bank:", roobet_cashback(rtp=rtp, frac=frac))
    P("\n## 5. 10% lossback, one all-in 1%-edge dice bet (Thrill-type, terms unverified)")
    P("  ", dice_lossback(0.10))
    P("  20% lossback for comparison:", dice_lossback(0.20))
    P("\n## 6. Free bet value (stake not returned), $100 = EUR86 free bet, 6.7% margin (Cloudbet measured)")
    for o in (1.5, 2.0, 3.0, 5.0): P(f"  odds {o}: EUR {free_bet_value(86, o, 0.067)}")
    open("results/sim.md", "w").write("# sim.py output\n\n```\n" + "\n".join(L) + "\n```\n")
