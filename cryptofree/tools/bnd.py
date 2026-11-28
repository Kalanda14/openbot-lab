"""Print Binance article body text. Usage: python3 -I bnd.py file.json [maxchars]"""
import json,sys,re,html
d=json.load(open(sys.argv[1]))['data']; N=int(sys.argv[2]) if len(sys.argv)>2 else 3000
def walk(n,out):
  if isinstance(n,dict):
    if n.get('node')=='text': out.append(n.get('text',''))
    for v in n.values(): walk(v,out)
  elif isinstance(n,list):
    for v in n: walk(v,out)
b=d.get('body','')
try: o=[]; walk(json.loads(b),o); t=' '.join(o)
except Exception: t=html.unescape(re.sub(r'<[^>]+>',' ',b))
t=re.sub(r'\s+',' ',t)
print('##',d['title']); print(t[:N])
