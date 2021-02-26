#### Utility Functions including functions to get metrics from OpsMgr ####

import settings
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime
import dateutil.parser
import time
import json
import fcntl
import errno
import functools
import copy

#### New imports
from datetime import timedelta
from pymongo import MongoClient



# Parse out request in chatbot - this is where the rubber meets the road.  We will return JSON that will
# ALWAYS have an 'action' so we know what action to take.  Other fields will be added based upon the
# action and returned add to the 'actions' list to expand capabilities of the chat bot
def parseChatRequest(text):
    retVal = {}
    retVal['sourceList'] = []

    # These are the actions we support - note that an action CAN be supportd from multiple sources,
    #   so we allow each rule to figure that out on it's own

    actions = set(['conn', 'que', 'ops', 'lag', 'health', 'upgrade', 'restart', 'sensei'])
    # for variants, the 1st item is the one you want replaced.
    # The second is the one to replace it with, which should appear in 'infoItems' or 'actions'
    # Note that the longer ones appear 1st (i.e. 'boxes' comes before 'box' in the tuple list).
    # This is due to the 'reduce' function doing the replacement in order. Specified based on the string
    # We don't want 'boxes' to become 'hostes', so we replace 'boxes' with 'hosts' before replacing 'box'
    variantList = ('opsmanager', 'opsmgr'), ('grp', 'group'), \
                  ('replicaset', 'rplset'), ('replica', 'rplset'), ('cfg', 'conf'), \
                  ('servers', 'hosts'), ('machines', 'hosts'), ('boxes', 'hosts'), \
                  ('server', 'host'), ('machine', 'host'), ('box', 'host'), \
                  ('connections', 'conn'), ('rpllag', 'lag'), ('replication', 'lag'), \
                  ('queues', 'que'), ('queue', 'que'), ('opcounters', 'ops'), \
                  ('bounce', 'restart'), ('pause', 'stop'), ('halt', 'stop'), \
                  ('resume', 'start'), ('time', 'date')

    # Items that will be added to the JSON string returned.  Each word below is expected to be
    # followed by a string (or comma separated list) that specifies the value for the info item
    infoItems = ['group', 'rplset', 'host', 'version', 'conf', 'hosts', 'date']

    # List of sources - add to this for any other capabilities (i.e. SumoLogic, internal systems, etc....)
    sourceList = ['opsmgr']

    ######################### Let's get to parsing now #########################
    # First, lowecase everything and replace all variants of words using the variantList
    text = text.lower()
    text = text.replace(', ', ',') # strip off all spaces afer commas so they don't get split by the call to split() below
    text = functools.reduce(lambda a, kv: a.replace(*kv), variantList, text)

    # Do an intersection on the text passed in and the actions we support
    textList = text.split()
    textSet = set(textList)
    actionList = actions.intersection(textSet)

    # We found an action - now check to see what the 1st one we found is
    if len(actionList) > 0:
        idx = 99999
        action = ''
        # Find the first one in the request and ignore the rest, you can not ask for both 'connections' and 'lag'
        for itm in actionList:
            i = text.find(itm)
            if i < idx:
                idx = i
                action = itm

        # Now we have the action that we will use for the rest of this request
        retVal['action'] = action

        # since we have an action, look in infoItems.  The standard here is to use the next word
        #   in the list for the value of the item.  Note that this may be a comma separated list.
        for itm in infoItems:
            if itm in textList:
                i = textList.index(itm)
                # Add code to parse date - retain the value entered as 'dateEntered' so we can complain if we can't parse it
                if itm == 'date':
                    retVal['dateEntered'] = textList[i + 1]
                    try:
                        retVal[itm] = dateutil.parser.parse(textList[i + 1])
                    except:
                        retVal[itm] = None
                        pass
                else:
                    retVal[itm] = textList[i + 1] # The list item AFTER the infoItem word is the value to use
        # We will also add items to source list as we encounter them.
        #   If we do not see any, then we will add the entire list stored in sourceList
        sl = []
        for src in sourceList:
            if src in textList:
                sl.append(src)

        # If empty, then add the default from settings when none specified
        if len(sl) < 1:
            sl = settings.defaultSources
        retVal['sourceList'] = sl

        # Provide default OpsMgr group name if none specified
        if 'group' not in retVal:
            retVal['group'] = settings.opsmgrDefaultGroup

        # If opsmgr is in source list, check to see that it is accepting connections
        if 'opsmgr' in retVal['sourceList']:
            try:
                # Provide default OpsMgr group name if none specified
                if 'group' not in retVal:
                    retVal['group'] = settings.opsmgrDefaultGroup
                g = getOpsMgrGroupId(retVal['group'])
                if g is not None:
                    retVal['omgroupid'] = g
            except:
                retVal['action'] = '<error>'
                retVal['error'] = 'Cannot complete request as Ops Manager does not appear to be responding'
                return retVal

            # get omgroupID
            grp = getOpsMgrGroupId(retVal['group'])
            if grp is not None:
                retVal['omgroupid'] = g

            retVal['hostList'] = []

        # if a RplSet was provided, fill in hostList with those hosts
        if 'rplset' in retVal:
            retVal['hostList'] = getHostsInRplSet(retVal['rplset'], grp)

        # If a host was provided, use OpsMgr to resolve and add host data to hostList
        if 'host' in retVal and not 'hosts' in retVal:
            h = getOpsMgrHost(retVal['host'], grp)
            if h is not None:
                retVal['hostList'].append(h)

        # If a list of hosts was provided, fill in the hostList array
        if 'hosts' in retVal:
            hl = retVal['hosts'].split(',')
            for h in hl:
                retVal['hostList'].append(getOpsMgrHost(h, grp))

    else: # We did not find a supported action, so set action to <unknown>
        retVal['action'] = '<unknown>'
    return retVal


# Create new incident in ticketing system stub - be sure to return the incidentID
def createIncident(alert, text = ''):
    # Change to logic to create new incident.  This is just a placeholder value for testing
    return 'INC' + str(time.time()).split('.')[0]



# Get all groups in OpsMgr
def getAllGroups(omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = None
    url = omServer + '/api/public/v1.0/groups'
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Groups - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()['results']
    return retVal

####### Alert Blackout functions
# Blackout Alert(s) for a given RplSet or Host
def blackoutAlerts(item, type, typeNameList = settings.alertsToBlackOut, grpList = settings.alertGroupsToBlackOut, storeData=True):
    if len(item) <= 0:
        raise Exception('Item must contain a host:port or a rplset name')

    if type.lower() not in ['host', 'rplset']:
        raise Exception ('Type must be "host" or "rplset"')

    # Check to see if a blackout exists - note getBlackout will return the rplSet in blackout if called with
    # a host that is a member of the blackout
    b = getBlackout(type, item)
    if b is not None:
        exc = type + ' "' + item + '" is already blacked out'
        if b['type'].lower() == 'rplset' and type.lower() != 'rplset':
            exc += ' as part of RplSet "' + b['name'] + '" blackout'
        raise Exception (exc)

    # init these two - if either one is blank, no alerts will be updated.
    fname = ''
    alertTypes = []
    bDoc = {}

    # Note that some alert types only apply to hosts or RplSets, so we will filter based on the
    # type sent in.  For example, 'PRIMARY_ELECTED' only applies to rplsets, so we don't want to
    # modify any existing alerts when the type sent in is 'host'
    if type.lower() == 'host':
        alertTypes = settings.alertsToBlackOutHostAlerts
        fname = 'HOSTNAME_AND_PORT'
    elif type.lower() == 'rplset':
        alertTypes = settings.alertsToBlackOutRplSetAlerts
        fname = 'REPLICA_SET_NAME'

    # If we don't have any alert types, then there is nothing to do
    if len(alertTypes) > 0:
        # Iterate thru the list of OpsManagers
        for om in settings.alertBlackoutOMList:
            omGroups = getAllGroups(omServer=om['url'], user=om['user'], apiKey=om['apiKey'])
            # Iterate thru each group and check for a name match
            for grpName in grpList:
                grp = None
                for omg in omGroups:
                    if omg['name'].lower() == grpName.lower():
                        grp = omg['id']
                        break
                # We have a matching group
                if grp is not None:
                    # Check to see that item (host:port or RplSet) is in group before proceeding
                    if isItemInGroup(type, item, grp, omServer=om['url'], user=om['user'], apiKey=om['apiKey']):
                        if (storeData):  # Build out entire doc
                            now = datetime.utcnow()
                            bDoc['type'] = type
                            bDoc['name'] = item
                            bDoc['createDate'] = now
                            bDoc['expireDate'] = now + timedelta(minutes=settings.alertAutoUnBlackoutTimeMins)
                            bDoc['omHost'] = om['url']
                            bDoc['groupId'] = grp
                            bDoc['alerts'] = []
                        else: # We will just pass back list of alerts to the caller
                            bDoc['alerts'] = []
                        # Build a matcher to exclude the item (host:port or RplSet set passed in from the alert)
                        matcher = {"fieldName": fname, "operator": "NOT_EQUALS", "value": item}
                        alertList = getAlertConfigsInGroup(grp, omServer=om['url'], user=om['user'], apiKey=om['apiKey'])

                        # Now go thru all alert configs and add matcher
                        for a in alertList:
                            # Matcher will only be added when:
                            #   1) Event matches passed in event(s)
                            #   2) Event is correcdt for type (i.e. 'Host Down' only applies to host and not RplSet alerts
                            #   3) Matcher does not already exist
                            if a['eventTypeName'] in typeNameList \
                                    and a['eventTypeName'] in alertTypes:
                                    #and not matcherExists(matcher, a['matchers']):
                                id = a['id']
                                # Remove fields that POST does not like
                                del a['groupId']
                                del a['updated']
                                del a['links']
                                del a['created']
                                del a['enabled']
                                del a['id']

                                m = []
                                m.append(matcher)
                                # Add alert info to list
                                bDoc['alerts'].append({'alertConfigId' : id, 'type' : type, 'matcher' : matcher})

                                # Add new matcher to exclude given rplSet or host:port
                                if not matcherExists(matcher, a['matchers']):
                                    a['matchers'].append(matcher)
                                    url = om['url'] + '/api/public/v1.0/groups/' + grp + '/alertConfigs/' + id
                                    resp = requests.put(url, json=a, auth=HTTPDigestAuth(om['user'], om['apiKey']))
                                    if resp.status_code != 200:
                                        # This means something went wrong.
                                        print('---- ERROR Updating alert configuration - ' + resp.status_code + ' was returned')
                                        print(json.dumps(resp.json()))

                        # If blackout was for a RplSet, loop thru each host and apply the host blackouts
                        if type.lower() == 'rplset':
                            hostList = getHostsInRplSet(item, grp, omServer=om['url'], user=om['user'], apiKey=om['apiKey'])
                            for h in hostList:
                                try:
                                    alertListToAdd = blackoutAlerts(h['hostname'] + ':' + str(h['port']), 'host', typeNameList=typeNameList, grpList=grpList, storeData=False)
                                    for a in alertListToAdd['alerts']:
                                        bDoc['alerts'].append(a)
                                except:
                                    pass
        if storeData:
            storeBlackout(bDoc)
        return bDoc


#unBlackout alerts - we remove the host:port or rplset provided from the alert matchers causing the blackout to end
#   This is done based on the alrt blackout data we saved.
def unBlackoutAlerts(item, type):
    if len(item) <= 0:
        raise Exception('Item must contain a host:port or a rplset name')

    if type.lower() not in ['host', 'rplset']:
        raise Exception ('Type must be "host" or "rplset"')

    bo = getBlackout(type, item)
    if bo is None:
        raise Exception(type + ' ' + item + ' is not in blackout')

    user = None
    apiKey = None
    for om in settings.alertBlackoutOMList:
        if om['url'] == bo['omHost']:
            user = om['user']
            apiKey = om['apiKey']

    if user is None or apiKey is None:
        raise Exception('Could not retrieve credentials for "' + bo['omHost'] + '" from settings')

    for a in bo['alerts']:
        url = bo['omHost'] + '/api/public/v1.0/groups/' + bo['groupId'] + '/alertConfigs/' + a['alertConfigId']
        resp = requests.get(url, auth=HTTPDigestAuth(om['user'], om['apiKey']))
        if resp.status_code != 200:
            # This means something went wrong.
            print('---- ERROR Retrieving Ops Manager Alert Configuration - ' + str(resp.status_code) + ' was returned')
            print(json.dumps(resp.json()))
        else:
            alertConfig = resp.json()
            update = False
            for idx, m in reversed(list(enumerate(alertConfig['matchers']))):
                if m['fieldName'] == a['matcher']['fieldName'] and m['operator'] == a['matcher']['operator'] and m['value'] == a['matcher']['value']:
                    del alertConfig['matchers'][idx]
                    update = True
            if update:
                # Remove fields that POST does not like
                del alertConfig['groupId']
                del alertConfig['updated']
                del alertConfig['links']
                del alertConfig['created']
                del alertConfig['enabled']
                del alertConfig['id']

                # Post up the alert with the host:port or rplset exception removed.
                resp = requests.put(url, json=alertConfig, auth=HTTPDigestAuth(om['user'], om['apiKey']))
                if resp.status_code != 200:
                    # This means something went wrong.
                    print('---- ERROR Updating alert configuration - ' + str(resp.status_code) + ' was returned')
                    print(json.dumps(resp.json()))

    deleteBlackout(bo['type'], bo['name'])

#create blackout collection and indexes if it does not exist
def createBlackoutCollection(con):
    exists = False
    for d in con.database_names():
        if d == settings.alertBlackoutMongoDB:
            for col in con[d].collection_names():
                if col == settings.alertBlackoutMongoCollection:
                    exists = True
                    break

    if not exists:
        con[settings.alertBlackoutMongoDB][settings.alertBlackoutMongoCollection].create_index([("type", 1), \
                                                                                                ("name", 1), \
                                                                                                ("createDate", 1)])
        con[settings.alertBlackoutMongoDB][settings.alertBlackoutMongoCollection].create_index([("expireDate", 1)])

def storeBlackout(blackoutDoc):
    con = MongoClient(settings.alertBlackoutMongoURI)
    # 1st, make sure collections and indexes exist
    createBlackoutCollection(con)

    # Now store settings
    con[settings.alertBlackoutMongoDB][settings.alertBlackoutMongoCollection].insert(blackoutDoc)
    con.close()

def deleteBlackout(type, name):
    retVal = None
    con = MongoClient(settings.alertBlackoutMongoURI)
    r = con[settings.alertBlackoutMongoDB][settings.alertBlackoutMongoCollection].delete_many({'type' : type, 'name' : name})
    retVal = r.deleted_count
    con.close()
    return retVal

def getBlackout(type, name):
    retVal = None
    con = MongoClient(settings.alertBlackoutMongoURI)
    r = con[settings.alertBlackoutMongoDB][settings.alertBlackoutMongoCollection].find({'type' : type, 'name' : name}).limit(1)
    results = [doc for doc in r]
    if len(results) > 0:
        retVal = results[0]
    else:
        # Check to see if host is blacked out as part of rplSet
        if type.lower() == 'host':
            r = con[settings.alertBlackoutMongoDB][settings.alertBlackoutMongoCollection].find({'alerts.matcher.value': name}).limit(1)
        results = [doc for doc in r]
        if len(results) > 0:
            retVal = results[0]
    con.close()
    return retVal

def sendUnBlackOutWarning(bo):
    print ('E-mail warning goes here ' + bo['type'] + ' ' + bo['name'])


# This will be called by the deamon process
def autoUnBlackOut(warnMins=settings.alertAutoUnBlackoutWarnTimeMins):
    now = datetime.utcnow()
    warningTime = now + timedelta(minutes=warnMins)
    con = MongoClient(settings.alertBlackoutMongoURI)
    db = con[settings.alertBlackoutMongoDB][settings.alertBlackoutMongoCollection]

    # Look for expired blackouts that have a warning sent long enough ago and un-blackout
    r = db.find({'expireDate' : {'$lte': now}, 'warningSent' : {'$exists': True}, 'warningSent' : {'$lte': warningTime}})
    results = [doc for doc in r]
    for bo in results:
        # First, run healthcheck - returns list of all problems found
        h = unBlackoutHealthCheck(bo['name'], bo['type'])
        if len(h) < 1:
            unBlackoutAlerts(bo['name'], bo['type'])

    # Find all blackouts that have NOT had a warning sent and are within the window
    #  We take the current time and add the wanring minutes to it, then find all blackouts <= the result
    #  without a warningSent field
    r = db.find({'expireDate' : {'$lte': warningTime}, 'warningSent' : {'$exists': False}})
    results = [doc for doc in r]
    for bo in results:
        sendUnBlackOutWarning(bo)
        # Now update warning time
        db.update({'_id': bo['_id']}, {'$set': {'warningSent': now}})

    con.close()

# Healthcheck for auto-unblackout
def unBlackoutHealthCheck(item, type, grpList=settings.alertGroupsToBlackOut):
    if len(item) <= 0:
        raise Exception('Item must contain a host:port or a rplset name')

    if type.lower() not in ['host', 'rplset']:
        raise Exception ('Type must be "host" or "rplset"')

    healthIssues = []
    now = datetime.utcnow()
    period = 'PT' + str(settings.alertBlackoutHealthCheckTimeMins) + 'M'

    # Iterate thru the list of OpsManagers and find the host or rplSet
    for om in settings.alertBlackoutOMList:
        omGroups = getAllGroups(omServer=om['url'], user=om['user'], apiKey=om['apiKey'])
        # Iterate thru each group and check for a name match
        for grpName in grpList:
            grp = None
            for omg in omGroups:
                if omg['name'].lower() == grpName.lower():
                    grp = omg['id']
                    break
            # We have a matching group
            if grp is not None:
                # Check to see that item (host:port or RplSet) is in group before proceeding
                if isItemInGroup(type, item, grp, omServer=om['url'], user=om['user'], apiKey=om['apiKey']):

                    # We found the item - do a healthcheck
                    hostList = []
                    tempList = getHostsInGroup(grp, omServer=om['url'], user=om['user'], apiKey=om['apiKey'])

                    # Build out list of either single host or all host in rplSet
                    if type.lower() == 'host':
                        for h in tempList:
                            if item.lower() == h['hostname'].lower() + ':' + str(h['port']):
                                hostList.append(h)
                                break
                    else:
                        hostList = getHostsInRplSet(item, grp, omServer=om['url'], user=om['user'], apiKey=om['apiKey'])

                    ####### RplSet Level Health checks
                    if type.lower() == 'rplset':
                        ### No election in last settings lookback time - note the envents enpoint is not
                        ###  supported OpsMgr in versions < 4.0, so we'll ignore this in earlier versions
                        ###  as customer is planning to migrate all OpsMgrs to 4.0 soon.
                        hadElection = False
                        keepLooking = True
                        url = om['url'] + '/api/public/v1.0/groups/' + grp + '/events'
                        while keepLooking:
                            resp = requests.get(url, auth=HTTPDigestAuth(om['user'], om['apiKey']))
                            if resp.status_code == 404: # Not found - likely OpsMgr is < 4.0, so we just bail
                                keepLooking = False
                            elif resp.status_code != 200:
                                # This means something went wrong.
                                print('---- ERROR Retrieving Events - ' + str(resp.status_code) + ' was returned')
                                print(json.dumps(resp.json()))
                            else:
                                for event in resp.json()['results']:
                                    if 'eventTypeName' in event and event['eventTypeName'] == 'PRIMARY_ELECTED':
                                        if event['replicaSetName'].lower() == item.lower() \
                                                and (now - datetime.strptime(event['created'],'%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 60 < settings.alertBlackoutHealthCheckTimeMins:
                                            hadElection = True
                                            break
                                    # Since these are returned in reverse time order, we stop looking after we reach the lookback time
                                    if (now - datetime.strptime(event['created'],'%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 60 >= settings.alertBlackoutHealthCheckTimeMins:
                                        keepLooking = False

                                # Check for next page if we need to keep looking
                                if keepLooking:
                                    keepLooking = False
                                    for l in resp.json()['links']:
                                        if l['rel'] == 'next':
                                            url = l['href']
                                            keepLooking = True
                        if hadElection:
                            healthIssues.append('RplSet ' + item + ' had and election.')

                    ####### Start health checks by host
                    for h in hostList:
                        hName = h['hostname'].lower() + ':' + str(h['port'])

                        ### Uptime >= settings lookback time
                        if 'lastRestart' in h:
                            if (now - datetime.strptime(h['lastRestart'], '%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 60 < settings.alertBlackoutHealthCheckTimeMins:
                                healthIssues.append('Host ' + hName + ' has not been up long enough.')

                        ### Queues <= 50
                        m = getOpsMgrMetrics(['GLOBAL_LOCK_CURRENT_QUEUE_WRITERS', 'GLOBAL_LOCK_CURRENT_QUEUE_READERS'],
                                             grp,
                                             h['id'],
                                             granularity='PT1M',
                                             period=period,
                                             omServer=om['url'],
                                             user=om['user'],
                                             apiKey=om['apiKey'])
                        if not checkMetricThresholds(m, '<=', 50):
                            healthIssues.append('Host ' + hName + ' has exceeded 50 queues')

                        ### RplLag <= 10 minutes (does not apply to Primary)
                        if h['replicaStateName'] != 'PRIMARY':
                            m = getOpsMgrMetrics(['OPLOG_SLAVE_LAG_MASTER_TIME'],
                                                 grp,
                                                 h['id'],
                                                 granularity='PT1M',
                                                 period=period,
                                                 omServer=om['url'],
                                                 user=om['user'],
                                                 apiKey=om['apiKey'])
                            if not checkMetricThresholds(m, '<=', 10 * 60):
                                healthIssues.append('Host ' + hName + ' Replication Lag has exceeded 10 minutes')

                        ### Read and Write tickets available >= 60
                        m = getOpsMgrMetrics(['TICKETS_AVAILABLE_READS', 'TICKETS_AVAILABLE_WRITE'],
                                             grp,
                                             h['id'],
                                             granularity='PT1M',
                                             period=period,
                                             omServer=om['url'],
                                             user=om['user'],
                                             apiKey=om['apiKey'])
                        if not checkMetricThresholds(m, '>=', 60):
                            healthIssues.append('Host ' + hName + ' has less than 60 tickets available')

                        ### Oplog window >= 12 hours
                        # Use 'local' db size to make this determination - oplog should be almost all of the size of this DB
                        # So we look at the db size, and divide by 12 to determine the max OplogGBPerHour number allowed
                        m = getOpsMgrMetrics(['DATABASE_DATA_SIZE'],
                                             grp,
                                             h['id'] + '/databases/local',
                                             granularity='PT1M',
                                             period='PT24H',
                                             omServer=om['url'],
                                             user=om['user'],
                                             apiKey=om['apiKey'])
                        # Grab value and convert to GB
                        oplogSize = float(m['measurements'][0]['dataPoints'][0]['value']) / 1024.0 / 1024.0 / 1024.0
                        # Now let's pull oplog gb per hour
                        m = getOpsMgrMetrics(['OPLOG_RATE_GB_PER_HOUR'],
                                             grp,
                                             h['id'],
                                             granularity='PT1M',
                                             period=period,
                                             omServer=om['url'],
                                             user=om['user'],
                                             apiKey=om['apiKey'])
                        # GB per hour needs to be less than the oplog size / the number of hours
                        if not checkMetricThresholds(m, '<=', oplogSize / settings.alertBlackoutHealthCheckMinOplogWindowHours):
                            healthIssues.append('Host ' + hName + ' has less than ' + str(settings.alertBlackoutHealthCheckMinOplogWindowHours) + ' hours of oplog window')
    return healthIssues

# See if any metrics have exceeded a threshold
# call in the form of what you are looking for for example if you want metrics to be
# less than 50, call with an op of '<' and a value fo 50.  The function will return True
# if ALL values are < 50
def checkMetricThresholds(metrics, op, value):
    for m in metrics['measurements']:
        for dp in m['dataPoints']:
            if dp['value'] is not None:
                v = dp['value']
                if op == '<':
                    if v >= value:
                        return False
                elif op == '<=':
                    if v > value:
                        return False
                elif op == '>':
                    if v <= value:
                        return False
                elif op == '>=':
                    if v < value:
                        return False
    return True


# Get list of alert configs in a given group
def getAlertConfigsInGroup(grp, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = None
    url = omServer + '/api/public/v1.0/groups/' + grp + '/alertConfigs'
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Groups - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()['results']
    return retVal

def getHostsInGroup(groupId, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = []
    if groupId is not None:
        morePages = True
        url = omServer + '/api/public/v1.0/groups/' + groupId + "/hosts"
        while morePages:
            resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
            if resp.status_code != 200:
                # This means something went wrong.
                print('---- ERROR Retrieving Ops Manager Hosts - ' + str(resp.status_code) + ' was returned')
                print(json.dumps(resp.json()))
                morePages = False
            else:
                # Add results to return value
                retVal.extend(resp.json()['results'])

                # Check for more pages (we will have a 'next' link if so)
                morePages = False
                for l in resp.json()['links']:
                    if l['rel'] == 'next':
                        url = l['href']
                        morePages = True
    if len(retVal) < 1:
        retVal = None
    return retVal


def isItemInGroup(type, itm, grp, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = False
    hostList = getHostsInGroup(grp, omServer = omServer, user = user, apiKey = apiKey)

    if type.lower() == 'host':
        if hostList is not None:
            for h in hostList:
                if (h['hostname'] + ':' + str(h['port'])).lower() == itm.lower():
                    retVal = True
                    break
    elif type.lower() == 'rplset':
        for h in hostList:
            if h['replicaSetName'].lower() == itm.lower():
                retVal = True
                break
    return retVal

def matcherExists(matcher, matcherList):
    retVal = False
    for m in matcherList:
        if m['fieldName'] == matcher['fieldName'] and m['operator'] == matcher['operator'] and  m['value'] == matcher['value']:
            retVal = True
            break
    return retVal


###### Converted functions from utils

# get Host names, ID and ports given a group and rplset
def getHostsInRplSet(rplSet, groupId, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = []
    for h in getHostsInGroup(groupId, omServer=omServer, user=user, apiKey=apiKey):
        if 'replicaSetName' in h:
            if h['replicaSetName'].lower() == rplSet.lower():
                retVal.append(h)
        else:
            continue
    if len(retVal) < 1:
        retVal = None
    return retVal

# get metrics from OpsMgr
def getOpsMgrMetrics(measurements, groupId, hostId, granularity = settings.opsmgrMetricGranularity, period = settings.opsmgrMetricPeriod, startTime = None, endTime = None, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = None
    # Build out measurement string in the form of "&m=<Item1>&m=<Item2>...."
    m = ''
    for itm in measurements:
        m = m + '&m=' + itm

    # To not break existing code, we will always use period if present here.
    # If we want a start and end time, pass period=None into this function ans specify start/end times
    rangeString = ''
    if period is not None:
        rangeString = '&period=' + period
    else:
        rangeString = '&start=' + startTime.isoformat() + 'Z' + \
                      '&end=' + endTime.isoformat() + 'Z'

    url = omServer + '/api/public/v1.0/groups/' + groupId + '/hosts/' + hostId + \
          '/measurements?granularity=' + granularity + rangeString + m + "&pretty=true"
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Ops Manager metrics - HTTP status ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    retVal = resp.json()
    return retVal




######### End blackout functions


######### Changed 1/10/10
# Get list of open alerts in O/M
def getOpenAlerts(omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    alertList = []
    for grp in getAllGroups():
        url = omServer + '/api/public/v1.0/groups/' + grp['id'] + '/alerts/?status=open'

        resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
        if resp.status_code != 200:
            # This means something went wrong.
            print('---- ERROR Retrieving Ops Manager Alerts - ' + str(resp.status_code) + ' was returned')
            print(json.dumps(resp.json()))
        else:
            alertList.extend(resp.json()['results'])

    return alertList


###### End changes from 1/10/19


# Ack OpsMgr alert and put incident and channel ID in the comment
def ackOpsMgrAlert(alert, incident, channel):
    dt = str(datetime.now().year + 100) + '-' + str(datetime.now().month) + '-' + str(datetime.now().day) + 'T00:00:00-0700'

    txt = {}
    txt['incident'] = incident
    txt['channel'] = channel

    payload = {'acknowledgedUntil': dt, 'acknowledgementComment': json.dumps(txt)}

    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + alert['groupId'] + '/alerts/' + alert['id']

    resp = requests.patch(url, json=payload, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Acknowledging Ops Manager alsert - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))


# get groupID from OpsMgr given a group name
def getOpsMgrGroupId(name, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = None
    url = omServer + '/api/public/v1.0/groups'
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Ops Manager groups - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        for grp in resp.json()['results']:
            if grp['name'].lower() == name.lower():
                retVal = grp['id']
                break
    return retVal


# get group name from OpsMgr given a group id
def getOpsMgrGroupName(grp, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = None
    url = omServer + '/api/public/v1.0/groups/' + grp
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Ops Manager groups - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()['name']
    return retVal


# get Host ID given either a host or a host and port
def getOpsMgrHostId(name, group):
    retVal = None
    h = getOpsMgrHost(name, group)
    if h is not None:
        retVal = h['id']
    return retVal


# get Host name, ID and port given either a host or a host and port
#   Note we want to be permissive here and allow hostnames less than the FQDN
#     so, we will match on the hostname sent in and the port (if specified) separately
def getOpsMgrHost(name, group):
    retVal = None
    host = getHostName(name)
    port = getPort(name)
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + group + "/hosts"
    resp = requests.get(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Ops Manager Hosts - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        for h in resp.json()['results']:
            # Split out the 2 names being compared and compare up to what we sent in
            #    i.e. 'node1', 'node1.aaa', etc will all match with 'node1.aaa.bbb.com'
            hostList = host.split('.')
            omList = h['hostname'].lower().split('.')
            match = True
            for i, item in enumerate(hostList):
                if omList[i] != hostList[i]:
                    match = False
                    break
            if match:
                if port is not None:
                    if port == h['port']:
                        retVal = h
                        break
                else:
                    retVal = h
                    break
    return retVal

# Get all hosts in OpsMgr from all groups
def getAllHosts():
    retVal = None
    hosts = []
    for grp in getAllGroups():
        lst = getHostsInGroup(grp['id'])
        if lst is not None and len(lst) > 0:
            for l in lst:
                hosts.append(l)
    if len(hosts) > 0:
        retVal = hosts
    return retVal

# Pull automation config for a group
def getAutomationConfig(groupId):
    retVal = None
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + groupId + '/automationConfig'
    resp = requests.get(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Automation Config - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()
    return retVal


# Parse out minor version number from a string
def getMinorVersion(version):
    n = version.split('-')[0]
    l = n.split('.')
    v = l[len(l) - 1]
    return int(v)


# Parse out major version as a string (i.e. '3.2')
def getMajorVersion(version):
    l = version.split('.')
    return l[0] + '.' + l[1]


# Get next available minor version based on version sent in
# i.e.  3.2.11-ent  would return 3.2.12-ent if enabled
#       Note that it might skip versions too : 3.2.11-ent -> 3.2.14-ent
def getNextMinorVersion(automationConfig, version):
    retVal = None
    currentMinor = getMinorVersion(version)
    desiredMinor = 999
    currentMajor = getMajorVersion(version)

    for v in automationConfig['mongoDbVersions'] :
        if getMajorVersion(v['name']) == currentMajor and \
                getMinorVersion(v['name']) > currentMinor and \
                v['name'].endswith('ent') == version.endswith('ent') and \
                getMinorVersion(v['name']) < desiredMinor:
            desiredMinor = getMinorVersion(v['name'])
            retVal = v['name']

    return retVal


# transform data from OpsMgr JSON to array of arrays for charting
def transformMetrics(j):
    metrics = j
    if j is not None and 'errorCode' not in j:
        metrics = {}
        metrics[settings.chartingXAxisSeries] = []
        tsAdded = False
        offset = getUTCOffset()
        for itm in j['measurements']:
            metrics[itm['name']] = []
            # Add in each measurement
            for dp in itm['dataPoints']:
                # Add in timeseries for x axis if not there yet.
                if not tsAdded:
                    metrics['timestamp'].append(dateutil.parser.parse(dp['timestamp']) + offset)
                metrics[itm['name']].append(dp['value'])
            tsAdded = True
    return metrics


# scrub data - including removing out metrics below the defined threshhold
#   This expects an array of arrays which is returned by the 'transformMetrics' function
def scrubMetrics(d, removeBlowThreshhold = settings.chartingRemoveBelowThreshold):
    if d is not None and 'errorCode' not in d:
        keysToRemove = []

        # Build list of items to remove
        for i in range(len(d[list(d.keys())[0]])):
            remove = True
            for k in d.keys():
                if d[k][i] is None:
                    d[k][i] = 0
                if k != settings.chartingXAxisSeries and d[k][i] >= removeBlowThreshhold:
                    remove = False
            if remove:
                keysToRemove.append(i)

        # now remove the data for the given keys
        for rmKey in reversed(keysToRemove):
            for k in d.keys():
                del d[k][rmKey]
        # Check to see if we scrubbed it all
        if len(d[list(d.keys())[0]]) < 1:
            d = None
    return d


# sum up metrics - sum up the metrics defined in the sumFields.values dict and return as set of sumFields.keys
def sumMetrics(d, sumFields):
    s = d
    if d is not None and 'errorCode' not in d:
        s = {}
        # Copy xaxis (date) series over
        s[settings.chartingXAxisSeries] = d[settings.chartingXAxisSeries]

        # init all of this to zeros
        for k in sumFields.keys():
            s[k] = [0] * len(s[settings.chartingXAxisSeries])

        # Now loop thru it all and bucket according to the sumFields
        for origKey in d.keys():
            for newKey in sumFields.keys():
                if origKey in sumFields[newKey]:
                    i = 0
                    for val in d[origKey]:
                        if val is not None:
                            s[newKey][i] += val
                        i += 1
    return s


# Get Y axis limit for scaling charts (note that the default set in the settings class is 1.5x the largest value
def getYAxisLimit(d):
    max = 0.0
    for series in d.keys():
        if (series != settings.chartingXAxisSeries):
            for val in d[series]:
                if val > max:
                    max = val

    return max * settings.chartingYLimitScaling


# get UTC Offset
def getUTCOffset():
    now_timestamp = time.time()
    return (datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp))


# Strip port number from OpsMgr host
def getHostName(hostnameAndPort):
    return hostnameAndPort.split(':')[0]


# Get port number from OpsMgr host
def getPort(hostnameAndPort):
    retVal = None
    p = hostnameAndPort.split(':')
    if len(p) > 1:
        retVal = int(p[1])
    return retVal


# Create a lock to ensure that 2 MongoBot requests cannot take an action at the same time
# Note that for OpsMgr type actions, the lock file is the group ID from OpsMgr as it's not
# a problem to modify different OpsMgr groups concurrently.
class FileLock:
    def __init__(self, filename=None):
        self.filename = './MONGODB_AUTOMATION_LOCK_FILE' if filename is None else filename
        self.lock_file = open(self.filename, 'w+')

    def unlock(self):
        fcntl.flock(self.lock_file, fcntl.LOCK_UN)

    def lock(self):
        waited = 0
        while True:
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

                return True
            except IOError as e:
                if e.errno != errno.EAGAIN:
                    raise e
                else:
                    time.sleep(1)
                    waited += 1
                    if waited >= settings.waitForGroupLockSeconds:
                        return False





# Healthcheck for os patching
def osPatchHealthCheck(item, hcType = 'root', type = 'rplset', groupName = settings.opsmgrDefaultGroup,  omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    if len(item) <= 0:
        raise Exception('Item must contain a host:port or a rplset name')

    if type.lower() not in ['host', 'rplset']:
        raise Exception ('Type must be "host" or "rplset"')

    if hcType.lower() not in ['root', 'inc']:  # 'root' or 'incremental' healthcheck
        raise Exception ('Type must be "root" or "inc"')

    healthIssues = []
    now = datetime.utcnow()
    grp = getOpsMgrGroupId(groupName, omServer=omServer, user=user, apiKey=apiKey)
    if grp is None:
        raise Exception('Group ' + groupName + ' not found')


    # Check to see that item (host:port or RplSet) is in group before proceeding
    if isItemInGroup(type, item, grp, omServer=omServer, user=user, apiKey=apiKey):

        # We found the item - do a healthcheck
        hostList = []
        tempList = getHostsInGroup(grp, omServer=omServer, user=user, apiKey=apiKey)

        # Build out list of either single host or all host in rplSet
        if type.lower() == 'host':
            for h in tempList:
                if item.lower() == h['hostname'].lower() + ':' + str(h['port']):
                    hostList.append(h)
                    break
        else:
            hostList = getHostsInRplSet(item, grp, omServer=omServer, user=user, apiKey=apiKey)

        ####### RplSet Level Health checks
        if type.lower() == 'rplset':
            ### No election in last 24 hours - note the events endpoint is not
            ###  supported OpsMgr in versions < 4.0, so we'll ignore this in earlier versions
            ###  as customer is planning to migrate all OpsMgrs to 4.0 soon.
            hadElection = False
            keepLooking = True
            url = omServer + '/api/public/v1.0/groups/' + grp + '/events'
            while keepLooking:
                resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
                if resp.status_code == 404: # Not found - likely OpsMgr is < 4.0, so we just bail
                    keepLooking = False
                elif resp.status_code != 200:
                    # This means something went wrong.
                    print('---- ERROR Retrieving Events - ' + str(resp.status_code) + ' was returned')
                    print(json.dumps(resp.json()))
                else:
                    for event in resp.json()['results']:
                        if 'eventTypeName' in event and event['eventTypeName'] == 'PRIMARY_ELECTED':
                            if event['replicaSetName'].lower() == item.lower() \
                                    and (now - datetime.strptime(event['created'],'%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 60 < 1440:
                                hadElection = True
                                break
                        # Since these are returned in reverse time order, we stop looking after we reach the lookback time
                        if (now - datetime.strptime(event['created'],'%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 60 >= 1440:
                            keepLooking = False

                    # Check for next page if we need to keep looking
                    if keepLooking:
                        keepLooking = False
                        for l in resp.json()['links']:
                            if l['rel'] == 'next':
                                url = l['href']
                                keepLooking = True
            if hadElection:
                healthIssues.append('RplSet ' + item + ' had and election.')

        ####### Start health checks by host
        for h in hostList:
            if h['typeName'] in ['REPLICA_PRIMARY', 'REPLICA_SECONDARY', 'REPLICA_ARBITER']:
                hName = h['hostname'].lower() + ':' + str(h['port'])

                period = 'PT1H'
                if hcType.lower() == 'inc':
                    period = 'PT30S'

                ### RplLag <= 5 minutes in last hour for root check, <= 1 second in latest 3 measurements for incremental check (does not apply to Primary)
                if h['replicaStateName'] != 'PRIMARY':
                    m = getOpsMgrMetrics(['OPLOG_SLAVE_LAG_MASTER_TIME'],
                                         grp,
                                         h['id'],
                                         granularity='PT10S',
                                         period=period,
                                         omServer=omServer,
                                         user=user,
                                         apiKey=apiKey)

                    val = 5*60 # 5 minutes for RplLag
                    txt = '5 minutes'
                    if hcType.lower() == 'inc':
                        val = 1 # 1 second for incremental check
                        txt = '1 second'
                    if not checkMetricThresholds(m, '<=', val):
                        healthIssues.append('Host ' + hName + ' Replication Lag has exceeded ' + txt)

                ### Read and Write tickets available >= 80 for last hour
                m = getOpsMgrMetrics(['TICKETS_AVAILABLE_READS', 'TICKETS_AVAILABLE_WRITE'],
                                     grp,
                                     h['id'],
                                     granularity='PT10S',
                                     period='PT1H',
                                     omServer=omServer,
                                     user=user,
                                     apiKey=apiKey)
                if not checkMetricThresholds(m, '>=', 80):
                    healthIssues.append('Host ' + hName + ' has less than 80 tickets available')

                ### Host is up and , if doing a root check, Uptime >= 1 hour
                if 'lastRestart' in h:
                    # host should be up - type should match state name for PSA type hosts
                    if h['typeName'].split('_')[1] != h['replicaStateName']:
                        healthIssues.append('Host ' + hName + ' is not currently up.')
                    else:
                        if hcType.lower() == 'root':
                            if (now - datetime.strptime(h['lastRestart'], '%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 60 < 60:
                                healthIssues.append('Host ' + hName + ' has not been up for at least 1 hour.')



                ### Queues <= 50 for last 3 measurements
                m = getOpsMgrMetrics(['GLOBAL_LOCK_CURRENT_QUEUE_WRITERS', 'GLOBAL_LOCK_CURRENT_QUEUE_READERS'],
                                     grp,
                                     h['id'],
                                     granularity='PT10S',
                                     period='PT30S',
                                     omServer=omServer,
                                     user=user,
                                     apiKey=apiKey)
                if not checkMetricThresholds(m, '<=', 50):
                    healthIssues.append('Host ' + hName + ' has exceeded 50 queues')



                ### Oplog window >= 12 hours for last 3 measurements
                # Use 'local' db size to make this determination - oplog should be almost all of the size of this DB
                # So we look at the db size, and divide by 12 to determine the max OplogGBPerHour number allowed
                m = getOpsMgrMetrics(['DATABASE_DATA_SIZE'],
                                     grp,
                                     h['id'] + '/databases/local',
                                     granularity='PT10S',
                                     period='PT24H',
                                     omServer=omServer,
                                     user=user,
                                     apiKey=apiKey)
                # Grab value and convert to GB
                oplogSize = float(m['measurements'][0]['dataPoints'][0]['value']) / 1024.0 / 1024.0 / 1024.0
                # Now let's pull oplog gb per hour
                m = getOpsMgrMetrics(['OPLOG_RATE_GB_PER_HOUR'],
                                     grp,
                                     h['id'],
                                     granularity='PT10S',
                                     period='PT30S',
                                     omServer=omServer,
                                     user=user,
                                     apiKey=apiKey)
                # GB per hour needs to be less than the oplog size / 12
                if not checkMetricThresholds(m, '<=', oplogSize / 12):
                    healthIssues.append('Host ' + hName + ' has less than 12 hours of oplog window')
    return healthIssues
