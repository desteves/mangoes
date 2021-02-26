import settings
import utils
import datetime
import json
import requests
from requests.auth import HTTPDigestAuth

# O/M granularity
granularity='PT1M'


def getExecutionMetrics( grpId,
                         hostId,
                         hostNameandPort,
                         metric,
                         discardNulls=True,
                         omServer=settings.opsmgrServerUrl,
                         user=settings.opsmgrUser,
                         apiKey=settings.opsmgrApiKey):
    retVal = []

    url = omServer + '/api/public/v1.0/groups/' + grpId + '/hosts/' + hostId + \
          '/metrics/' + metric + '?granularity=MINUTE&period=PT5M'
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Ops Manager metrics - HTTP status ' + 'resp.status_code' + ' was returned')
        print(json.dumps(resp.json()))
    else:
        if 'dataPoints' in resp.json():

            entry = {'host' : hostNameandPort}
            ln = ''
            for dp in resp.json()['dataPoints']:
                t = dp['timestamp'][:-1]
                v = str(dp['value'])
                if v is not None and str(v) != 'None':
                    ln += hostNameandPort + "," + metric + "," + t + "," + v + '\n'

            if len(ln) > 0:
                a = entry.copy()
                a['metric'] = metric
                a['data'] = ln
                retVal.append(a)
    return retVal


#hostlist = ['host.customer.com:10905']
#with open('/mongodata/t00l/mongoUtils/'+'Metric_t00l3.txt', 'w') as f:
# for hosts in hostlist:
#   finaldata = getCorrelatedMetrics(hosts, 'host', omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey)
#   for items in finaldata:
#      f.write(items['data'])
#f.close()

