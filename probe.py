"""Which US stocks does Dukascopy's free feed have? Tries 1-min candle file for one recent day."""
import lzma, struct, requests, sys
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
T = "AAPL MSFT AMZN GOOGL META NVDA TSLA AMD NFLX INTC BA JPM BAC C WFC XOM CVX PFE MRK KO PEP WMT HD DIS NKE MCD V MA PYPL ADBE CRM ORCL CSCO QCOM AVGO TXN IBM GS MS T VZ CMCSA ABBV ABT TMO UNH LLY JNJ PG COST SBUX UBER ABNB SNOW PLTR COIN MU F GM CAT DE GE MMM HON LMT RTX UPS FDX BABA NIO SHOP SQ ZM ROKU".split()
ok = []
for t in T:
    for name in (f"{t}USUSD",):
        u = f"https://datafeed.dukascopy.com/datafeed/{name}/2026/10/19/BID_candles_min_1.bi5"
        try:
            r = S.get(u, timeout=30)
            if r.status_code == 200 and r.content:
                d = lzma.decompress(r.content); rows = list(struct.iter_unpack(">IIIIIf", d))
                live = [x for x in rows if x[5] > 0]
                ok.append(name); print(name, len(rows), "bars", len(live), "with volume, first close", live[0][2] if live else None, flush=True)
            else: print(name, "status", r.status_code, len(r.content), flush=True)
        except Exception as e: print(name, "ERR", e, flush=True)
print("FOUND", len(ok), " ".join(ok))
