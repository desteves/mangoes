import settings
import utils
import json
import math
from pymongo import MongoClient
from bson.json_util import dumps

def getRsConf(host):
    retVal = None
    uri = 'mongodb://mike:password@' + host['hostname'] + ':' + str(host['port']) + '/admin'
    con = MongoClient(uri)
    r = con['local']['system.replset'].find()
    results = [doc for doc in r]
    if len(results) > 0:
        retVal = results[0]
    con.close()
    return retVal

def checkTopology(rplSetName, groupName = settings.opsmgrDefaultGroup, verbose = False, omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey):
    retVal = True
    if verbose:
        retVal = ''

    grp = utils.getOpsMgrGroupId(groupName, omServer=omServer, user=user, apiKey=apiKey)
    if grp is None:
        raise Exception('Group ' + groupName + ' not found')

    # get hosts in rplSet
    hostList = utils.getHostsInRplSet(rplSetName, grp, omServer=omServer, user=user, apiKey=apiKey)
    if len(hostList) < 1:
        raise Exception('Could not find any hosts for RplSet ' + rplSetName + ' in Group ' + groupName + ' not found')

    rsConf = getRsConf(hostList[0])
    # Check for multiple hosts per server:
    serverList = {}
    totalVotes = 0
    totalDataNodes = 0
    totalPrimaryCandidates = 0
    for h in hostList:
        if h['typeName'] in ['REPLICA_PRIMARY', 'REPLICA_SECONDARY', 'REPLICA_ARBITER']:
            votes = 0
            canBePrimary = False
            isDataBearing = False
            for m in rsConf['members']:
                if m['host'].lower() == (h['hostname'].lower() + ':' + str(h['port'])):
                    votes = m['votes']
                    totalVotes += m['votes']
                    if m['priority'] > 0:
                        totalPrimaryCandidates += 1
                        canBePrimary = True
                    break

            if h['typeName'] in ['REPLICA_PRIMARY', 'REPLICA_SECONDARY']:
                totalDataNodes += 1
                isDataBearing = True

            if h['hostname'] in serverList:
                serverList[h['hostname']]['votes'] += votes
                if isDataBearing:
                    serverList[h['hostname']]['dataBearingNodes'] += 1
                if canBePrimary:
                    serverList[h['hostname']]['primaryCandidates'] += 1
            else:
                serverList[h['hostname']] = {'votes' : votes, 'dataBearingNodes' : 0, 'primaryCandidates' : 0}
                if isDataBearing:
                    serverList[h['hostname']]['dataBearingNodes'] = 1
                if canBePrimary:
                    serverList[h['hostname']]['primaryCandidates'] = 1


    # Check to see if other mongods are running on the same server(s)
    allHostsList = utils.getAllHosts()
    for h in allHostsList:
        if h['hostname'] in serverList:
            otherDeployment = False
            if 'replicaSetName' not in h:
                otherDeployment = True
            elif h['replicaSetName'].lower() != rplSetName.lower():
                otherDeployment = True

            if otherDeployment:
                if verbose:
                    retVal += 'Deployments found that are not in RplSet ' + rplSetName + ' on host ' + h['hostname'] + '\n'
                else:
                    retVal = False
                break

    majority = int(math.ceil(totalVotes/2.0))
    # In case we have a rplset with an even number of voting members
    if totalVotes/2 == majority:
        majority += 1
    for h, v in serverList.iteritems():
        print (h, v)
        if v['votes'] >= majority:
            if verbose:
                retVal += 'Host ' + h + ' contains a majority of votes (' + str(v['votes']) + ' of ' + str(totalVotes) + ') and will result in the RplSet going into read only mode when down.\n'
            else:
                retVal = False

    return retVal