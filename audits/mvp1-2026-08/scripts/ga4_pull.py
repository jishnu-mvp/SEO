import os, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
creds = service_account.Credentials.from_service_account_file(
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
    scopes=['https://www.googleapis.com/auth/analytics.readonly'])
svc = build('analyticsdata','v1beta',credentials=creds)
PID = os.environ['GA4_PROPERTY_ID']

def rep(body):
    return svc.properties().runReport(property=PID, body=body).execute()

def rows(r):
    out=[]
    for row in r.get('rows',[]):
        out.append({'dims':[d['value'] for d in row.get('dimensionValues',[])],
                    'mets':[m['value'] for m in row['metricValues']]})
    return out

MONTHS = {'2026-03':('2026-03-01','2026-03-31'),'2026-04':('2026-04-01','2026-04-30'),
 '2026-05':('2026-05-01','2026-05-31'),'2026-06':('2026-06-01','2026-06-30'),
 '2026-07':('2026-07-01','2026-07-31'),'2026-08':('2026-08-01','2026-08-31')}

METS=[{'name':'sessions'},{'name':'totalUsers'},{'name':'newUsers'},
      {'name':'screenPageViews'},{'name':'engagedSessions'},
      {'name':'averageSessionDuration'},{'name':'bounceRate'},
      {'name':'keyEvents'}]
# probe which metrics valid
valid=[]
for m in METS:
    try:
        rep({'dateRanges':[{'startDate':'2026-08-01','endDate':'2026-08-05'}],'metrics':[m]})
        valid.append(m)
    except Exception as ex:
        print('SKIP metric', m['name'], str(ex)[:80])
print('VALID METRICS:', [m['name'] for m in valid])

out={'property':PID,'months':{}}
for label,(s,e) in MONTHS.items():
    d={}
    d['totals']=rows(rep({'dateRanges':[{'startDate':s,'endDate':e}],'metrics':valid}))
    d['channels']=rows(rep({'dateRanges':[{'startDate':s,'endDate':e}],
        'dimensions':[{'name':'sessionDefaultChannelGroup'}],'metrics':valid,'limit':20}))
    d['landing']=rows(rep({'dateRanges':[{'startDate':s,'endDate':e}],
        'dimensions':[{'name':'landingPagePlusQueryString'}],
        'metrics':[{'name':'sessions'},{'name':'engagedSessions'}],'limit':40}))
    out['months'][label]=d
    tot=d['totals'][0]['mets'] if d['totals'] else []
    print(label, tot)
out['metric_names']=[m['name'] for m in valid]
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','ga4.json'),'w'), indent=1)
print('SAVED')
