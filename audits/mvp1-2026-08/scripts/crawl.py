import json, re, time, urllib.request, urllib.error, gzip, io, os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
urls = [u.strip() for u in open('/tmp/urls.txt') if u.strip()]

def fetch(u, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(u, headers={'User-Agent':UA,'Accept-Encoding':'gzip'})
            t0=time.time()
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
                if r.headers.get('Content-Encoding')=='gzip':
                    raw = gzip.decompress(raw)
                return r.status, raw.decode('utf-8','replace'), time.time()-t0, dict(r.headers), r.url
        except urllib.error.HTTPError as e:
            return e.code, '', 0, {}, u
        except Exception as e:
            if i==tries-1: return 0, f'ERR {e}', 0, {}, u
            time.sleep(2**i)

def analyse(u):
    st, html, ttfb, hdrs, final = fetch(u)
    d = {'url':u,'status':st,'load_s':round(ttfb,2),'final_url':final,
         'bytes':len(html.encode('utf-8')) if html else 0}
    if st!=200 or not html:
        return d
    s = BeautifulSoup(html,'lxml')
    t = s.find('title')
    d['title'] = t.get_text(strip=True) if t else None
    d['title_len'] = len(d['title']) if d['title'] else 0
    md = s.find('meta', attrs={'name':re.compile('^description$',re.I)})
    d['meta_desc'] = md.get('content','').strip() if md else None
    d['meta_desc_len'] = len(d['meta_desc']) if d['meta_desc'] else 0
    can = s.find('link', attrs={'rel':re.compile('canonical',re.I)})
    d['canonical'] = can.get('href') if can else None
    rb = s.find('meta', attrs={'name':re.compile('^robots$',re.I)})
    d['meta_robots'] = rb.get('content') if rb else None
    d['h1'] = [h.get_text(' ',strip=True) for h in s.find_all('h1')]
    d['h2_count'] = len(s.find_all('h2')); d['h3_count'] = len(s.find_all('h3'))
    d['og'] = {m.get('property'):m.get('content') for m in s.find_all('meta') if (m.get('property') or '').startswith('og:')}
    d['twitter'] = {m.get('name'):m.get('content') for m in s.find_all('meta') if (m.get('name') or '').startswith('twitter:')}
    d['hreflang'] = [(l.get('hreflang'), l.get('href')) for l in s.find_all('link', attrs={'hreflang':True})]
    # schema
    schemas=[]
    for sc in s.find_all('script', attrs={'type':re.compile('ld\\+json',re.I)}):
        try:
            j=json.loads(sc.string or sc.get_text())
            schemas.append(j)
        except Exception as ex:
            schemas.append({'__PARSE_ERROR__':str(ex)[:120]})
    def types(o, acc):
        if isinstance(o,dict):
            if '@type' in o:
                tv=o['@type']; acc.extend(tv if isinstance(tv,list) else [tv])
            for v in o.values(): types(v,acc)
        elif isinstance(o,list):
            for v in o: types(v,acc)
        return acc
    d['schema_types']=types(schemas,[])
    d['schema_errors']=[x for x in schemas if isinstance(x,dict) and '__PARSE_ERROR__' in x]
    d['schema_raw']=schemas
    # images
    imgs=s.find_all('img')
    d['img_count']=len(imgs)
    d['img_no_alt']=sum(1 for i in imgs if not (i.get('alt') or '').strip())
    d['img_no_dims']=sum(1 for i in imgs if not (i.get('width') and i.get('height')))
    d['img_lazy']=sum(1 for i in imgs if (i.get('loading')=='lazy'))
    d['img_srcs']=[i.get('src') or i.get('data-src') for i in imgs][:40]
    # text
    for tag in s(['script','style','noscript']): tag.decompose()
    body = s.find('body')
    txt = body.get_text(' ',strip=True) if body else ''
    d['word_count']=len(txt.split())
    d['text_sample']=txt[:600]
    # links
    links=[a.get('href') for a in s.find_all('a', href=True)]
    d['links_total']=len(links)
    d['internal']=[l for l in links if l.startswith('/') or 'mvp1.com.au' in l]
    d['external']=sorted({re.sub(r'https?://([^/]+).*',r'\1',l) for l in links if l.startswith('http') and 'mvp1.com.au' not in l})
    d['int_link_count']=len(d['internal'])
    d['viewport']= bool(s.find('meta', attrs={'name':'viewport'}))
    d['lang']= (s.find('html') or {}).get('lang') if s.find('html') else None
    return d

with ThreadPoolExecutor(max_workers=6) as ex:
    res=list(ex.map(analyse, urls))
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','crawl.json')
json.dump(res, open(out,'w'), indent=1)
ok=sum(1 for r in res if r['status']==200)
print(f"crawled {len(res)}  ok={ok}  non200={[ (r['url'],r['status']) for r in res if r['status']!=200 ]}")
