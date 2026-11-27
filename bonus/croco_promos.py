"""Fetch Crocobet promo list + each landing's rules text (public, no login)."""
import json,re,html,subprocess,sys,os
UA=['-A','Mozilla/5.0']
def get(u,h=[]):
    return subprocess.run(['curl','-s','-m','30',*UA,*h,u],capture_output=True,text=True).stdout
out=os.path.join(os.path.dirname(__file__),'raw','croco'); os.makedirs(out,exist_ok=True)
G='https://external-prod-native-gateway.crocobet.com/route/web/game-cms/api/public/content'
d=json.loads(get(G+'/banners-group?hash=-1&type=PROMO',['-H','Accept-Language: en']))
for g in d['groups']:
    for b in g['banners']:
        url=(b.get('redirectUrl') or '').strip()
        m=re.search(r'/landings/crc/([a-z0-9-]+)',url)
        if not m: print('SKIP',b['title'],url); continue
        name=m.group(1); base=f'https://promotions.crocobet.com/crc/{name}/'
        h=get(base); js=re.findall(r'src="(main[^"]+\.js)"',h)
        if not js: print('NOLANDING',name); continue
        mj=get(base+js[0]); chunks=re.findall(r'"\./(chunk-[A-Z0-9]+\.js)"',mj)
        src=mj+''.join(get(base+c) for c in chunks)
        rk=re.findall(r'rulesKey:"([^"]+)"',src); ep=re.findall(r'endpoints:\{([^}]+)\}',src)
        txt=''
        for k in set(rk):
            r=get(f'https://cms.crocobet.com/ui/policy/en/categories/promotions/{k}')
            try:
                for it in json.loads(r)['data']:
                    txt+='## '+it['title']+'\n'+html.unescape(re.sub(r'<[^>]+>',' ',it.get('content',''))).strip()+'\n'
            except Exception as e: txt+=f'ERR {k} {r[:100]}\n'
        open(f'{out}/{name}.txt','w').write(f'# {b["title"]} {url}\nrulesKey={rk}\nendpoints={ep[:1]}\n\n{txt}')
        print('OK',name,rk,len(txt))
