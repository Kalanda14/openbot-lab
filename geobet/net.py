"""Tiny HTTP helper: gzip-aware JSON GET with a generic browser UA (no personal data)."""
import gzip, json, time, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36"


def get(url, timeout=30, tries=3, pause=0.3, headers=None, data=None):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json",
                                                       "Accept-Encoding": "gzip", **(headers or {})},
                                         data=None if data is None else json.dumps(data).encode())
            if data is not None:
                req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    b = gzip.decompress(b)
            time.sleep(pause)
            return json.loads(b)
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))
