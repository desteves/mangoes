import json
from datetime import datetime, timezone, timedelta
import dateutil.parser
import requests
from requests.auth import HTTPDigestAuth
import os

apiKeyFile = './apiKey.json'
maxAgeMinutes = 1
keyName = 'Mikes Mongo Bot'

def getApiKey(omServer = 'http://opsmgr.vagrant.local:8080', user = 'admin@localhost.com', apiKey = '352d153e-b4d3-4a48-a7e8-b201de1733fb'):
    # 1st, check if file exists for very first time around
    userId = None
    key = None
    if not os.path.isfile(apiKeyFile):
        userId = getUserID(omServer, user, apiKey)
        if userId is None:
            raise Exception('Could not get user ID for user name ' + user)

        #get current key from OpsMgr
        key = getCurrentKey(omServer, user, apiKey, userId)
    else:
        with open(apiKeyFile) as kf:
            key = json.load(kf)
            apiKey = key['key']

    if key is None:
        raise Exception('Could not retrive API key from OpsManager or from file')

    # Check age of key first
    c = dateutil.parser.parse(key['createdAt'])
    diff =  datetime.now(timezone.utc) - c
    mins = diff.days * 24 * 60 + diff.seconds / 60

    # too old - time to replace
    if mins > maxAgeMinutes:
        key = genNewKey(omServer, user, apiKey, key)

    return key

def getCurrentKey(omServer, user, apiKey, userId):
    retVal = None
    url = omServer + '/api/public/v1.0/users/' + userId + '/keys'
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Keys - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        for k in resp.json()['results']:
            if k['obfuscatedKey'][-12:] == apiKey[-12:]:
                return (k)
    return retVal

def genNewKey(omServer, user, apiKey, oldKey):
    retVal = None
    url = omServer + '/api/public/v1.0/users/' + oldKey['userId'] + '/keys'

    desc = {'description': keyName}

    resp = requests.post(url, json=desc, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 201:
    # This means something went wrong.
        print('---- ERROR Generating new Key - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()
        with open(apiKeyFile, 'w') as kf:
            json.dump(retVal, kf)

        url = omServer + '/api/public/v1.0/users/' + oldKey['userId'] + '/keys/' + oldKey['id']
        resp = requests.delete(url, auth=HTTPDigestAuth(user, retVal['key']))
        if resp.status_code != 200:
            # This means something went wrong.
            print('---- ERROR Deleting old Key - ' + str(resp.status_code) + ' was returned')
            print(json.dumps(resp.json()))

    return retVal

def getUserID(omServer, user, apiKey):
    retVal = None
    url = omServer + '/api/public/v1.0/users/byName/' + user
    resp = requests.get(url, auth=HTTPDigestAuth(user, apiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving User - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()['id']
    return retVal