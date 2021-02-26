from pymongo import MongoClient
import zlib
import bson
import json
import settings

def retrieve(hostList, part = 'all', omInfo = settings.mmsadminOMList[0]):
    retVal = []

    # Build URI
    uri = 'mongodb://'
    if len(omInfo['mmsuser']) > 0 and len(omInfo['mmscred']) > 0:
        uri += omInfo['mmsuser'] + ':' + omInfo['mmscred'] + '@'
    uri += omInfo['mmshost']

    # Extract ID's from hostlist
    idList = []
    for h in hostList:
        if h['typeName'] in ['REPLICA_PRIMARY', 'REPLICA_SECONDARY']:
            idList.append(h['id'])

    con = MongoClient(uri)

    r = con['mmsdbpings']['data.hostLastPings'].find({'_id' : {'$in' : idList}})
    results = [doc for doc in r]
    con.close()

    for ping in results:
        r = {}
        r['hostId'] = ping['_id']

        # Decompress document
        unZippedPing = zlib.decompress(ping['d'])

        # Decode document
        pingText = bson.decode_all(unZippedPing)

        # use 'me' for the hostname and port since we have it here
        r['hostNameAndPort'] = pingText[0]['isMaster']['me']

        part = part.lower()
        # Add more parts here if needed
        if part == 'all':
            r['ping'] = pingText
        elif part == 'cmdline':
            # 'ping' is an array, so we get the first item and then go for the 'parsed' in the 'cmdLineOps' section
            r['ping'] = pingText[0]['cmdLineOpts']['parsed']
            r['ping']['authenticationMechanisms'] = pingText[0]['getParameterAll']['authenticationMechanisms']

        if 'ping' in r:
            retVal.append(r)

    if len(retVal) < 1:
        retVal = None
    return retVal

def getCmdLineOpts(hostList, omInfo = settings.mmsadminOMList[0]):
    return retrieve(hostList, part='cmdline', omInfo = omInfo)