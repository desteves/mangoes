import settings
import json
import datetime
from pymongo import MongoClient
import copy
import types

dbsToExclude = ['admin', 'local', 'config']
lookBackHours = 2
lookAheadHours = 2

def getPlanCacheFromt00l(host, time ):
    startTime = time - datetime.timedelta(hours=lookBackHours)
    endTime = time + datetime.timedelta(hours=lookAheadHours)

    print (startTime)
    print(endTime)

    # Stub for now.
    # Call t00l here for host and
    #  time >= startTime and time to <= endTime

    s = [

        {
            "_index": "t00lgetplancacherno-0523",
            "_type": "_doc",
            "_id": "2198345432",
            "_version": 1,
            "_score": 0,
            "_source": {
                "query": "{'_id': {'$in': [0, 0]}, 'tags.refKey': {'$in': [0, 0]}}",
                "column11": 0,
                "metrictime": "2019-05-23T22:00:45",
                "sort": "{}",
                "solution": "(index-tagged expression tree: tree=Node&---Leaf { _id: 1 }, pos: 0&---Leaf &)",
                "type": "configuration",
                "path": "/mongodata/t00l/mongoUtils/currentOp/getPlanCache_rno.out",
                "plan": "{'stage': 'IXSCAN', 'nReturned': 70, 'executionTimeMillisEstimate': 0, 'works': 71, 'advanced': 70, 'needTime': 0, 'needYield': 0, 'saveState': 1, 'restoreState': 1, 'isEOF': 1, 'invalidates': 0, 'keyPattern': {'_id': 1}, 'indexName': '_id_', 'isMultiKey': False, 'isUnique': True, 'isSparse': False, 'isPartial': False, 'indexVersion': 1, 'direction': 'forward', 'indexBounds': {'_id': [0, 0]}, 'keysExamined': 71, 'dupsTested': 0, 'dupsDropped': 0, 'seenInvalidated': 0}",
                "message": "2019-05-23T22:00:45#hostname.com:10900#haikut#CategoryObjectMapping#{'_id': {'$in': [0, 0]}, 'tags.refKey': {'$in': [0, 0]}}#{}#{}#1#(index-tagged expression tree: tree=Node&---Leaf { _id: 1 }, pos: 0&---Leaf &)#{'stage': 'IXSCAN', 'nReturned': 70, 'executionTimeMillisEstimate': 0, 'works': 71, 'advanced': 70, 'needTime': 0, 'needYield': 0, 'saveState': 1, 'restoreState': 1, 'isEOF': 1, 'invalidates': 0, 'keyPattern': {'_id': 1}, 'indexName': '_id_', 'isMultiKey': False, 'isUnique': True, 'isSparse': False, 'isPartial': False, 'indexVersion': 1, 'direction': 'forward', 'indexBounds': {'_id': [0, 0]}, 'keysExamined': 71, 'dupsTested': 0, 'dupsDropped': 0, 'seenInvalidated': 0}#",
                "@timestamp": "2019-05-23T22:01:04.689Z",
                "tags": [
                    "_dateparsefailure"
                ],
                "db": "haikut",
                "host": "hostname:10900",
                "@version": "1",
                "collection": "CategoryObjectMapping",
                "rank": "1",
                "projection": "{}"
                },
                "fields": {
                    "@timestamp": [
                        "2019-05-23T22:01:04.689Z"
                    ],
                    "metrictime": [
                        "2019-05-23T22:00:45.000Z"
                    ]
                },
                "highlight": {
                    "rank.keyword": [
                        "@kibana-highlighted-field@1@/kibana-highlighted-field@"
                    ]
                },
                "sort": [
                    1558648845000
                ]
            },

        {
            "_index": "t00lgetplancacherno-0523",
            "_type": "_doc",
            "_id": "2198345432",
            "_version": 1,
            "_score": 0,
            "_source": {
                "query": "{'_id': {'$in': [0, 0]}, 'tags.refKey': {'$in': [0, 0]}}",
                "column11": 0,
                "metrictime": "2019-05-23T22:00:55",
                "sort": "{}",
                "solution": "(mikeindex-tagged expression tree: tree=Node&---Leaf { _id: 1 }, pos: 0&---Leaf &)",
                "type": "configuration",
                "path": "/mongodata/t00l/mongoUtils/currentOp/getPlanCache_rno.out",
                "plan": "{'stage': 'IXSCAN', 'nReturned': 70, 'executionTimeMillisEstimate': 0, 'works': 71, 'advanced': 70, 'needTime': 0, 'needYield': 0, 'saveState': 1, 'restoreState': 1, 'isEOF': 1, 'invalidates': 0, 'keyPattern': {'_id': 1}, 'indexName': '_id_', 'isMultiKey': False, 'isUnique': True, 'isSparse': False, 'isPartial': False, 'indexVersion': 1, 'direction': 'forward', 'indexBounds': {'_id': [0, 0]}, 'keysExamined': 71, 'dupsTested': 0, 'dupsDropped': 0, 'seenInvalidated': 0}",
                "message": "2019-05-23T22:00:45#hostname.com:10900#haikut#CategoryObjectMapping#{'_id': {'$in': [0, 0]}, 'tags.refKey': {'$in': [0, 0]}}#{}#{}#1#(index-tagged expression tree: tree=Node&---Leaf { _id: 1 }, pos: 0&---Leaf &)#{'stage': 'IXSCAN', 'nReturned': 70, 'executionTimeMillisEstimate': 0, 'works': 71, 'advanced': 70, 'needTime': 0, 'needYield': 0, 'saveState': 1, 'restoreState': 1, 'isEOF': 1, 'invalidates': 0, 'keyPattern': {'_id': 1}, 'indexName': '_id_', 'isMultiKey': False, 'isUnique': True, 'isSparse': False, 'isPartial': False, 'indexVersion': 1, 'direction': 'forward', 'indexBounds': {'_id': [0, 0]}, 'keysExamined': 71, 'dupsTested': 0, 'dupsDropped': 0, 'seenInvalidated': 0}#",
                "@timestamp": "2019-05-23T22:01:04.689Z",
                "tags": [
                    "_dateparsefailure"
                ],
                "db": "haikut",
                "host": "hostname:10900",
                "@version": "1",
                "collection": "CategoryObjectMapping",
                "rank": "1",
                "projection": "{}"
            },
            "fields": {
                "@timestamp": [
                    "2019-05-23T22:01:04.689Z"
                ],
                "metrictime": [
                    "2019-05-23T22:00:45.000Z"
                ]
            },
            "highlight": {
                "rank.keyword": [
                    "@kibana-highlighted-field@1@/kibana-highlighted-field@"
                ]
            },
            "sort": [
                1558648845000
            ]
        }
    ]

    retVal = []
    for i in s:
        retVal.append(i['_source'])
    return retVal


def analyzePlanCache(host, time):
    changedList = []
    planList = []

    t00lList = getPlanCacheFromt00l(host, time)
    for t in t00lList:
        logged = False
        try:
            loggedPlans = [i for i in changedList if \
                        i['host'] == t['host'] and i['db'] == t['db'] and i['collection'] == t['collection'] and \
                           i['query'] == t['query'] and i['sort'] == t['sort'] and i['projection'] == t['projection']]
            if len(loggedPlans) > 0:
                logged = True
        except:
            pass

        if not logged:
            try:
                prevPlan = [i for i in planList if \
                            i['host'] == t['host'] and i['db'] == t['db'] and i['collection'] == t['collection'] and \
                            i['query'] == t['query'] and i['sort'] == t['sort'] and i['projection'] == t['projection']]
                # Not found, so add it
                if len(prevPlan) < 1:
                    planList.append(t)
                else:
                    for r in prevPlan: # should just be 1
                        # Plan changed - log both old and new to results
                        if set(r['solution'].split('&')) != set(t['solution'].split('&')):
                            c = {'host' : r['host'],
                                 'db' : r['db'],
                                 'collection' : r['collection'],
                                 'query' : r['query'],
                                 'sort' : r['sort'],
                                 'projection' : r['projection'],
                                 'time' : t['metrictime'],
                                 'old' : {'plan' : r['plan'], 'solution' : r['solution']},
                                 'new' : {'plan' : t['plan'], 'solution' : t['solution']}}
                            changedList.append(c)
            except:
                # empty list, so add this one
                planList.append(t)
                pass
    return changedList


def getPlanCache(con, host):
    retVal = []
    dateFmt = '%Y-%m-%dT%H:%M:%S'

    t = datetime.datetime.utcnow().strftime(dateFmt)

    for db in con.list_database_names():
        if db not in dbsToExclude:
            for col in con[db].collection_names():
                if not col.lower().startswith('system.'):
                    shapeList = con[db].command({'planCacheListQueryShapes' : col})
                    for shape in shapeList['shapes']:
                        if 'query' in shape and 'projection' in shape and 'sort' in shape:
                            planList = con[db].command({'planCacheListPlans': col,
                                                       'query' : shape['query'],
                                                       'projection' : shape['projection'],
                                                       'sort' : shape['sort']})
                            rank = 1
                            for plan in planList['plans']:
                                if 'scores' in plan['feedback']:
                                    p = {}
                                    p['host'] = host
                                    p['timestamp'] = t
                                    p['db'] = db
                                    p['collection'] = col
                                    p['query'] = generifyShape(shape['query'])
                                    p['sort'] = shape['sort']
                                    p['projection'] = shape['projection']
                                    p['rank'] = rank
                                    p['solution'] = str(plan['details']['solution']).replace('\n', '&')
                                    p['plan'] = generifyPlan(plan['reason']['stats']['inputStage'])
                                    retVal.append(p)
                                    rank += 1
    return retVal

def generifyPlan(plan):
    p = copy.deepcopy(plan)
    if 'inputStages' in p:
        i = 0
        for stg in p['inputStages']:
            p['inputStages'][i] = generifyPlan(stg)
            i += 1
    if 'inputStage' in p and 'indexBounds' in p['inputStage']:
        p['inputStage']['indexBounds'] =  generifyShape(p['inputStage']['indexBounds'])
    if 'inputStage' in p and 'inputStage' in p['inputStage']:
        p['inputStage']['inputStage'] =  generifyShape(p['inputStage']['inputStage'])
    if 'filter' in p:
        p['filter'] = generifyShape(p['filter'])
    if 'indexBounds' in p:
        p['indexBounds'] = generifyShape(p['indexBounds'])
    return p

def generifyShape(p):
    defaultDate = datetime.datetime(1979, 10, 12, 0, 0 ,0)
    plan = copy.deepcopy(p)
    for k, v in plan.items():
        if isinstance(v, int):
            plan[k] = 0
        elif isinstance(v, float):
            plan[k] = 0.0
        elif isinstance(v, datetime.datetime):
            plan[k] = defaultDate
        elif isinstance(v, dict):
            plan[k] = generifyShape(v)
        elif isinstance(v, str):
            plan[k] = 'X'
        elif isinstance(v, list):
            if isinstance(v[0], dict):
                for key, val in enumerate(v):
                    v[key] = generifyShape(val)
                plan[k] = v
            else:
                plan[k] = [0, 0]
    return plan