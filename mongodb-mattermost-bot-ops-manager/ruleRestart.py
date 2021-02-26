#### Rule to restart host or clusters ####
import utils
import settings
import requests
import chatPost
from requests.auth import HTTPDigestAuth
import json
import time


def bounceHost(host, omgroupid):
    autoConfig = utils.getAutomationConfig(omgroupid)

    for idx, omhost in enumerate(autoConfig['processes']):
        if omhost['hostname'] == host['hostname'] and omhost['args2_6']['net']['port'] == host['port']:
            autoConfig['processes'][idx]['disabled'] = True

            # Send updated config
            url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + omgroupid + "/automationConfig"
            resp = requests.put(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey),
                            data=json.dumps(autoConfig), headers={"Content-Type": "application/json"})
            if resp.status_code != 200:
                # This means something went wrong.
                print(
                            '---- ERROR Updating Automation Config while changing minor version - ' + str(resp.status_code) + ' was returned')
                print(json.dumps(resp.json()))
                return False

            # Sleep for a bit
            time.sleep(settings.waitForRestartSeconds)

            # Re-enable the process
            autoConfig['processes'][idx]['disabled'] = False
            resp = requests.put(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey),
                            data=json.dumps(autoConfig), headers={"Content-Type": "application/json"})
            if resp.status_code != 200:
                # This means something went wrong.
                print(
                            '---- ERROR Updating Automation Config while restarting server - ' + str(resp.status_code) + ' was returned')
                print(json.dumps(resp.json()))
                return False
            return True

def restart(req):
    retVal = ''
    if 'group' not in req or 'hostList' not in req or len(req['hostList']) < 1:
        chatPost.postToChannel(
            'Both a group name and either a host, list of hosts, or Replica Set are required for this request from Ops Manager',
            req['channel_id'])
    else:
        chatPost.postToChannel('**Restarting**', req['channel_id'])

        primary = -1
        # Determine the primary and bouce that one last.
        for i, h in enumerate(req['hostList']):
            if h['replicaStateName'] == 'PRIMARY':
                primary = i

        chatPost.postToChannel('Restart - Obtaining lock...', req['channel_id'])
        grpLock = utils.FileLock(filename=req['omgroupid'] + '.lock')
        if not grpLock.lock():
            chatPost.postToChannel('Restart - **Could not obtain lock, there is likely another request in-flight for the group**',
                                   req['channel_id'])
            return
        # OK let's start bouncing non-primaries servers
        somethingWentWrong = False
        for i, host in enumerate(req['hostList']):
            if (i != primary and not somethingWentWrong):
                chatPost.postToChannel('   Restarting non-primary host ' + host['hostname'], req['channel_id'])

                if not bounceHost(host, req['omgroupid']):
                    somethingWentWrong = True
                    chatPost.postToChannel(
                        '   Restart of host  ' + host['hostname'] + ' failed - skipping remaining hosts', req['channel_id'])
                else:
                    chatPost.postToChannel('   Restart of host ' + host['hostname'] + ' complete', req['channel_id'])
                    time.sleep(settings.waitForRestartSeconds)

        if not somethingWentWrong and primary > -1:
            chatPost.postToChannel('   Restarting PRIMARY host ' + req['hostList'][primary]['hostname'], req['channel_id'])
            if not bounceHost(req['hostList'][primary], req['omgroupid']):
                chatPost.postToChannel('   Restart of PRIMARY host  ' + req['hostList'][primary]['hostname'] + ' failed', req['channel_id'])
            else:
                chatPost.postToChannel('   Restart of PRIMARY host ' + req['hostList'][primary]['hostname'] + ' complete', req['channel_id'])


            chatPost.postToChannel('Restart - Releasing lock...', req['channel_id'])
            grpLock.unlock()

            if somethingWentWrong:
                retVal = 'Error Restarting hosts - see Ops Manager for details'
            else:
                retVal = '**Restart completed sucesfully**'

    chatPost.postToChannel(retVal, req['channel_id'])
    return