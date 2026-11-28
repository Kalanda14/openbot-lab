"""Strip HTML to text. Usage: N=4000 python3 -I txt.py file... (optional GREP=regex to show context)"""
import re,html,sys,os
N=int(os.environ.get('N','4000')); G=os.environ.get('GREP')
for f in sys.argv[1:]:
  t=open(f,errors='ignore').read()
  t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
  t=html.unescape(re.sub(r'<[^>]+>',' ',t)); t=re.sub(r'\s+',' ',t)
  print('=====',f,len(t))
  if G:
    for m in re.finditer(G,t,re.I): print('...',t[max(0,m.start()-300):m.end()+500])
  else: print(t[:N])
