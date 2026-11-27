"""Copy of lib.sim with hooks (lib.py untouched):
capf(W, i, d, l) -> per-path cap (array or scalar): wealth/regime/day-aware cap.
gbf(W, i) -> target used INSIDE the Browne formula (tp/goal stays at G).
lmult: optional per-leg extra return array list (new sleeve added on top of a leg), handled outside."""
from lib import *
from lib import _ppf

def sim2(LG, starts, tr, f=0.5, cap=100, band=0.25, tp=True, cost_b=0.25, cost_on=0.25, on_extra_pt=0.0, swap=0.0,
         swap_leg=4, spike_pt=0.0, ncap=None, lot=None, days=21, G=700.0, ret_all=False, capf=None, gbf=None, W0=400.0, F=0.0, trace=False):
    trn = np.where(tr)[0]
    lv = np.array([np.var(l["r"][trn]) for l in LG]); tv = lv.sum(); tail = np.cumsum(lv[::-1])[::-1] / tv
    W = np.full(len(starts), W0); minW = W.copy(); TR_ = []; JW = np.zeros(len(starts)); JD = np.full(len(starts), -1)
    for i in range(days):
        d = starts + i; prev = np.zeros(len(starts)); grp = -1
        for j, l in enumerate(LG):
            act = (W < G) & (W > 1)
            if not act.any(): break
            if l["grp"] != grp: prev = np.zeros(len(starts)); grp = l["grp"]
            rem = (days - i - 1) + tail[j]
            Gb = G if gbf is None else gbf(W, i)
            x = np.clip((W - F) / (Gb - F), 1e-6, 0.999999)
            lev = pdf(_ppf(x)) * (Gb - F) / (f * g.sig_tr * np.sqrt(rem) * np.maximum(W, 1e-9))
            if F > 0: lev = np.where(W <= F, 0.0, lev)
            lev = np.where(W >= Gb, 0.0, lev) if gbf is not None else lev
            cp = cap if capf is None else capf(W, i, d, l, minW)
            lev = np.minimum(lev, cp)
            c = l["c"][d]
            if ncap is not None: lev = np.minimum(lev, ncap / np.maximum(c, 1e-12))
            if lot is not None:
                ln = lot * l["px"][d] / 1.1; nl = np.round(lev * c * W / ln)
                lev = np.where(c > 0, nl * ln / np.maximum(c * W, 1e-12), lev)
            h = l["held"][d] & act
            keep = h & (np.abs(lev - prev) <= band * np.maximum(prev, 1e-9)) if band > 0 else np.zeros_like(h)
            lev = np.where(keep, prev, lev)
            ch = h & ~keep & (np.abs(lev - prev) > 1e-9)
            cpt = cost_on if l["on"] else cost_b
            cc = np.where(ch, cpt / l["px"][d] * c * np.abs(lev - prev), 0)
            if l["on"] and l["j"] == 0: cc = cc + np.where(c > 0, on_extra_pt / l["px"][d] * c * lev, 0)
            if l["on"] and l["j"] == swap_leg: cc = cc + np.where(c > 0, swap * c * lev, 0)
            W = np.where(act, W * (1 - cc), W)
            r = l["r"][d]; wv = l["w"][d]
            if l["on"] and l["j"] == swap_leg and spike_pt: wv = wv - spike_pt / l["px"][d] * c
            wiped = act & (1 + lev * wv <= 0)
            hit = act & ~wiped & tp & (W * (1 + lev * l["up"][d]) >= G)
            # intraday low wealth (for cap rules that look at drawdown) - uses leg worst
            minW = np.where(act, np.minimum(minW, np.maximum(W * (1 + lev * np.minimum(wv, 0)), 0)), minW)
            Wb = W.copy(); W = np.where(act, W * (1 + lev * r), W)
            W = np.where(hit, G, W); W = np.where(wiped | (act & (W <= 1)), 0.0, W)
            dead = act & (W < 100) & (JD < 0); JW = np.where(dead, Wb, JW); JD = np.where(dead, i, JD)
            prev = lev / np.maximum(1 + lev * r, 1e-9)
        if trace: TR_.append(W.copy())
    res = dict(hit=(W >= G - 1e-9).mean(), lt100=(W < 100).mean(), med=np.median(W))
    if ret_all: res["W"] = W
    if trace: res.update(T=np.array(TR_), JW=JW, JD=JD)
    return res
