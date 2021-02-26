import settings
import json
import datetime

# Only return topN ops
topNThreshold = 20
# Ignore score (sum of all microsecs_running for the shape) that fall below this threshold
# This is regardless of the topN, so if only 5 have a score above this and topN is 20, only 5 ops will be returned
scoreThreshold = 0


def getCurrentOp(con, host):
    retVal = []
    dateFmt = '%Y-%m-%dT%H:%M:%S'

    t = datetime.datetime.utcnow().strftime(dateFmt)

    r = con['admin'].current_op(True)

    # Add filter options below to weed out ops you dont want to see.
    for j in r['inprog']:
        if 'ns' in j and 'op' in j and j['ns'] != '' and not str(j['ns']).startswith('admin') and not str(
                j['ns']).startswith('local'):
            found = False
            o = None
            ps = ''
            if 'planSummary' in j:
                ps = j['planSummary'].split()[0]
            if len(retVal) > 0:
                try:
                    o = next(d for d in retVal if d['op'] == j['op'] and d['ns'] == j['ns'] and d['planSummary'] == ps)
                    if o is not None:
                        found = True
                except:
                    pass

            if found:
                o['count'] += 1
                o['score'] += j['microsecs_running']
            else:
                # Add new ops found with count of 1
                op = {'metrictime': t,
                      'host': host,
                      'op': j['op'],
                      'ns': j['ns'],
                      'planSummary': ps,
                      'count': 1,
                      'score': j['microsecs_running']}
                retVal.append(op)

    # Sort and return only TopN that are at least the threshold
    if len(retVal) > 0:
        opList = sorted(retVal, key=lambda k: k['score'], reverse=True)
        retVal = []
        n = 0
        for l in opList:
            n += 1
            if l['score'] < scoreThreshold or n > topNThreshold:
                break
            else:
                retVal.append(l)

    return retVal