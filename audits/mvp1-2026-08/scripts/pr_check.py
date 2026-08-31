import re, random, json, urllib.request, gzip
from concurrent.futures import ThreadPoolExecutor
txt=open("/tmp/claude-0/-home-user-SEO/2c4ef00c-92aa-5122-9441-bd4ea24ad9bd/scratchpad/text/M1_M1_CUSTOM_Final_Report.xls.txt").read()
links=sorted(set(re.findall(r'https?://[^\s|]+/story/\d+/[^\s|]+', txt)))
print(f"total PR links parsed from deliverable: {len(links)}")
random.seed(42)
sample=random.sample(links, min(70,len(links)))
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
def chk(u):
    try:
        req=urllib.request.Request(u, headers={'User-Agent':UA,'Accept-Encoding':'gzip'})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw=r.read()
            if r.headers.get('Content-Encoding')=='gzip': raw=gzip.decompress(raw)
            h=raw.decode('utf-8','replace')
            anchors=re.findall(r'<a[^>]*href="[^"]*mvp1\.com\.au[^"]*"[^>]*>', h, re.I)
            follow=[a for a in anchors if 'nofollow' not in a.lower()]
            return (u, r.status, len(anchors), len(follow))
    except Exception as e:
        code=getattr(e,'code',0)
        return (u, code, 0, 0)
with ThreadPoolExecutor(max_workers=12) as ex:
    res=list(ex.map(chk, sample))
live=[r for r in res if r[1]==200]
dead=[r for r in res if r[1]!=200]
withlink=[r for r in live if r[2]>0]
dofollow=[r for r in live if r[3]>0]
print(f"\nSAMPLE n={len(res)}")
print(f"  HTTP 200 (live)      : {len(live):>3}  ({len(live)/len(res):.0%})")
print(f"  dead / error         : {len(dead):>3}  ({len(dead)/len(res):.0%})")
from collections import Counter
print(f"  status codes         : {dict(Counter(r[1] for r in res))}")
print(f"  live AND link to site: {len(withlink):>3}  ({len(withlink)/len(res):.0%} of sample)")
print(f"  live AND DOFOLLOW    : {len(dofollow):>3}  ({len(dofollow)/len(res):.0%} of sample)")
est=len(links)*len(dofollow)/len(res)
print(f"\n  => Extrapolated dofollow links of {len(links)} claimed: ~{est:.0f}")
json.dump([{'url':r[0],'status':r[1],'anchors':r[2],'dofollow':r[3]} for r in res],
          open("/tmp/claude-0/-home-user-SEO/2c4ef00c-92aa-5122-9441-bd4ea24ad9bd/scratchpad/data/pr_check.json","w"), indent=1)
