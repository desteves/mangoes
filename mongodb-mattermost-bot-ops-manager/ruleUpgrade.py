#### Rule to upgrade/downgrade clusters ####
import utils
import settings
import requests
import chatPost
from requests.auth import HTTPDigestAuth
import json
import time


# OpsMgr alert will call this function.  We typically want to grab some metrics and post a chart
#   based on the alert that was fired.  Note that the 'alert' variable sent in should contain
#   everything we need in order to pull metrics.
def upgrade(req):
    retVal = ''
    j = {}

    if not 'confirmed' in req:
        print(json.dumps(req, indent=2))
        #First, trim down hostlist to lighten the pyload which is limited to 7900 chars
        #req["hostList"] = utils.trimItemsFromHost(req["hostList"])
        # Post Are you sure message
        cReq = req.copy()
        ncReq = req.copy()
        cReq['confirmed'] = True
        ncReq['confirmed'] = False

        msg = '**Replica Set: ' + req['rplset'] + '**\n\n'
        msg += '| Host  | State  | Last Ping | \n'
        msg += '|------------|---------------|----- | \n'
        for h in req['hostList']:
            msg += '| ' + h['hostname'] + ':' + str(h['port']) + ' | ' + h['replicaStateName'] + ' | ' + str(h['lastPing']) + ' |\n'

        print(msg)

        msg += '**Replica Set: ' + req['rplset'] + '2**\n\n'
        msg += '| Host  | State  | Last Ping | \n'
        msg += '|------------|---------------|----- | \n'
        for h in req['hostList']:
            msg += '| ' + h['hostname'] + '2:' + str(h['port']) + ' | ' + h['replicaStateName'] + ' | ' + str(
                h['lastPing']) + ' |\n'

        j = {"response_type": "ephemeral",
                "attachments": [
                {
                  "pretext": msg, #"Upgrade rplset " + req['rplset'] + "?",
                  "text": "Upgrade?",
                  "attachment_type": "default",
                  "actions": [
                    {
                      "name": req['rplset'],
                      "integration": {
                        "url": "http://docker.for.mac.localhost/confirm",
                        "context": {
                          "request" : {'rplSet' : req['rplset'], 'confirmed' : True, 'channel_id' : req['channel_id'], 'omgroupid' : req['omgroupid'], 'action' : req['action']}
                        }
                      }
                    },{
                      "name": req['rplset'] + '2',
                      "integration": {
                        "url": "http://docker.for.mac.localhost/confirm",
                        "context": {
                          "request" : {'rplSet' : req['rplset'] + '2', 'confirmed' : True, 'channel_id' : req['channel_id'], 'omgroupid' : req['omgroupid'], 'action' : req['action']}
                        }
                      }
                    },{
                      "name": "Cancel",
                      "integration": {
                        "url": "http://docker.for.mac.localhost/confirm",
                        "context": {
                          "request" : {'confirmed' : False, 'channel_id' : req['channel_id']}
                        }
                      }
                    }
                  ]
                }
              ]
        }

    headers = {'Content-Type': 'application/json'}
    r = requests.post("http://localhost:8065/hooks/knocjmacmid3zrxkh4c7hfcjzr", headers=headers, data=json.dumps(j), verify=False)

    return





    if 'omgroupid' in req and 'rplset' in req:
        newVersion = None
        if 'version' in req:
            newVersion = req['version']

        hosts = utils.getHostsInRplSet(req['rplset'], req['omgroupid'])
        if hosts is not None and len(hosts) > 0:
            vers = 'FirstOne'
            areAllTheSame = True
            for h in hosts:
                if vers == 'FirstOne':
                    vers = h['version']
                else:
                    if vers != h['version']:
                        areAllTheSame = False

            if areAllTheSame:
                chatPost.postToChannel('Upgrade ' + req['rplset'] + ' - Obtaining lock...', req['channel_id'])
                grpLock = utils.FileLock(filename=req['omgroupid'] + '.lock')
                if not grpLock.lock():
                    chatPost.postToChannel('Upgrade ' + req['rplset'] + ' - **Could not obtain lock, there is likely another request in-flight for the group**', req['channel_id'])
                    return

                autoConfig = utils.getAutomationConfig(req['omgroupid'])
                validVersion = False
                # Validate (or retrive) version to upgrade to

                if newVersion is not None:
                    if utils.getMajorVersion(newVersion) == utils.getMajorVersion(hosts[0]['version']):
                        for v in autoConfig['mongoDbVersions']:
                            if v['name'] == newVersion:
                                validVersion = True
                                break
                    else:
                        retVal = 'Error: Not the same major version as ' + hosts[0]['version']
                else:
                    # We need to get the proper version name out of automation config because the hosts endpoint
                    # Does not show us ent vs community build
                    for h in autoConfig['processes']:
                        if h['hostname'] == hosts[0]['hostname'] and h['args2_6']['net']['port'] == hosts[0]['port']:
                            newVersion = utils.getNextMinorVersion(autoConfig, h['version'])
                            if newVersion is not None:
                                validVersion = True





                # OK - time to set the new version
                if validVersion:
                    for idx, omhost in enumerate(autoConfig['processes']):
                        for h in hosts:
                            if omhost['hostname'] == h['hostname'] and omhost['args2_6']['net']['port'] == h['port']:
                                autoConfig['processes'][idx]['version'] = newVersion

                    # Send updated config
                    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + req['omgroupid'] + "/automationConfig"
                    resp = requests.put(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey),
                                        data=json.dumps(autoConfig), headers={"Content-Type": "application/json"})
                    if resp.status_code != 200:
                        # This means something went wrong.
                        print('---- ERROR Updating Automation Config while changing minor version - ' + str(resp.status_code) + ' was returned')
                        print(json.dumps(resp.json()))
                    else:

                        chatPost.postToChannel('Upgrade ' + req['rplset'] + ' - Upgrade of replica set to version ' + newVersion +
                                            ' is currently in-flight.  Will wait for ' + str(settings.waitForUpgradeSeconds) +
                                            ' seconds for it to complete.', req['channel_id'])

                        #monitor - we will check the 'hosts' endpoint to ensure that the version there matches our target version
                        timeLeft = settings.waitForUpgradeSeconds
                        isComplete = False
                        while timeLeft > 0 and not isComplete:
                            chatPost.postToChannel('Upgrade ' + req['rplset'] + ' - Sleeping for ' + str(settings.checkUpgradeStatusSeconds) +
                                            ' seconds.  ' + str(timeLeft) + ' seconds are left before abandoning request.....',
                                         req['channel_id'])
                            time.sleep(settings.checkUpgradeStatusSeconds)
                            timeLeft -= settings.checkUpgradeStatusSeconds
                            updHosts = utils.getHostsInRplSet(req['rplset'], req['omgroupid'])
                            areAllMatched = True
                            for h in updHosts:
                                # Check to see if the version is upgraded.  Note we have to strip off the '-ent' as that
                                # is not included in the 'hosts' endpoint
                                if h['version'] != newVersion.split('-')[0]:
                                    areAllMatched = False
                            if areAllMatched:
                                isComplete = True
                                retVal = 'Upgrade to version ' + newVersion + ' complete!'
                        if not isComplete:
                            retVal = 'Upgrade request was not completed within the allotted time.  Please check Ops Manager to determine the issue.'
                else:
                    retVal = 'Could not find a version to upgrade to.  Either an invalid version was specified, or there are no other higher versions made available in the major release.'
                chatPost.postToChannel('Upgrade ' + req['rplset'] + ' - Releasing lock...', req['channel_id'])
                grpLock.unlock()

            else:
                retVal = 'Error: Cannot upgrade as all the hosts are not currently running the same version'
        else:
            retVal = 'Could not find hosts to upgrade.  Please double-check the group and replica set name.'
    else:
        retVal = 'Both a group and replica set are required for an upgrade'

    chatPost.postToChannel('Upgrade ' + req['rplset'] + ' - **' + retVal + '**', req['channel_id'])
    return None