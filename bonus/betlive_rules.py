"""Fetch Betlive promo rules (public). usage: python3 betlive_rules.py proj1 proj2 ..."""
import json,re,html,subprocess,sys,os
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'raw','bl'); os.makedirs(out,exist_ok=True)
def get(u): return subprocess.run(['curl','-s','-m','30','-A','Mozilla/5.0',u],capture_output=True,text=True).stdout
def clean(x): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',x)))
for p in sys.argv[1:]:
    for lang in ['en','ka']:
        txt=''
        for alias in ['1','2','3']:
            r=get(f'https://promotioncdn.betlive.com/api/public/getRules?project={p}&language={lang}&alias={alias}')
            if r and not r.startswith('<'): txt+=f'[alias {alias}] '+clean(r)+'\n'
        open(f'{out}/rules_{p}_{lang}.txt','w').write(txt)
        print(p,lang,len(txt))
