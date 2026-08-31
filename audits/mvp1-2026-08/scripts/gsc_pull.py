import os, json, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

SITE = os.environ['GSC_PROPERTY']
creds = service_account.Credentials.from_service_account_file(
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
    scopes=['https://www.googleapis.com/auth/webmasters.readonly'])
svc = build('searchconsole','v1',credentials=creds)

def q(body, retries=4):
    for i in range(retries):
        try:
            return svc.searchanalytics().query(siteUrl=SITE, body=body).execute()
        except Exception as e:
            if i==retries-1: raise
            time.sleep(2**i)

MONTHS = {
 '2026-03': ('2026-03-01','2026-03-31'),
 '2026-04': ('2026-04-01','2026-04-30'),
 '2026-05': ('2026-05-01','2026-05-31'),
 '2026-06': ('2026-06-01','2026-06-30'),
 '2026-07': ('2026-07-01','2026-07-31'),
 '2026-08': ('2026-08-01','2026-08-31'),
}
out = {'site': SITE, 'months': {}}
for label,(s,e) in MONTHS.items():
    m = {}
    m['totals'] = q({'startDate':s,'endDate':e,'dimensions':[],'dataState':'all'}).get('rows',[])
    for dim in ['query','page','device','country']:
        lim = 250 if dim in ('query','page') else 50
        m[dim] = q({'startDate':s,'endDate':e,'dimensions':[dim],'rowLimit':lim,'dataState':'all'}).get('rows',[])
    out['months'][label] = m
    print('done', label, m['totals'])

# daily series across whole window
daily = q({'startDate':'2026-03-01','endDate':'2026-08-31','dimensions':['date'],'rowLimit':400,'dataState':'all'}).get('rows',[])
out['daily'] = daily
print('daily rows', len(daily), 'last', daily[-1] if daily else None)

json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','gsc.json'),'w'), indent=1)
print('SAVED')
