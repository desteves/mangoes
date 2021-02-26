
import web
import settings
import utils
import requests
import os
import random
import json


# Import each rule here and add to the logic below to call.  Each rule should take the alert as a parameter
import ruleConnections
import ruleRplLag
import ruleUpgrade
import ruleRestart
import ruleQueues
import ruleOpCounters
import ruleHealth
import ruleSenSei
import threading
import time
import chatPost


urls = ('/alerthook', 'alerthook', '/chatbot', 'chatbot', '/images/(.*)', 'images', '/confirm', 'confirm', '/fwdToChat/(.*)', 'fwdtochat', '/confirmtext', 'confirmtext')
app = web.application(urls, globals())


def f(req):
    chatPost.postToChannel('Starting', req['channel_id'])
    time.sleep(3)
    chatPost.postToChannel('Ending', req['channel_id'])

class confirmtext:
    def POST(self):
        j = json.loads(web.data())
        print(json.dumps(j, indent=2))
        req = json.loads(j['state'])
        print('---Original request---')
        print(json.dumps(req, indent=2))


class confirm:
    def POST(self):
        retVal = json.dumps({
            'update': {'message': 'OK - you are continuing'}
        })
        j = json.loads(web.data())

        req = j['context']['request']


        if 'confirmed' in req and req['confirmed']:
            url = settings.chatServerAPIUrl + '/actions/dialogs/open'

            dlgJson = {
                'trigger_id': j['trigger_id'],
                'url': 'http://docker.for.mac.localhost/confirmtext',
                'req': req,
                'dialog': {
                    'state': json.dumps(req),
                    'title': 'I have a question for you',
                    "elements": [
                        {'display_name' : 'Enter something here',
                         'name' : 'txtSomething',
                         'type' : 'text',
                         'min_length' : 4,
                         'max_length' : 128,
                         'optional' : False,
                         'help_text' : 'Enter something between 4 and 150 chars here - or suffer the wrath of MatterMost!'}
                    ],
                    'submit_label': 'OK',
                    'notify_on_cancel' : True,  # Set this to true if you want the cancel action to post back to the endpoint as well
                }
            }

            headers = {'Content-Type': 'application/json'}
            r = requests.post(url, headers=headers, data=json.dumps(dlgJson), verify=False)


        else:
            retVal = json.dumps({
                'update': {'message': 'Sorry you did not want to continue'}
            })

        return (retVal)



class fwdtochat:
    def POST(self,ignore):
        j = json.loads(web.data())
        print (j['content'])
        chatPost.post(j['content'])





class chatbot:
    def POST(self):
        ruleFound = False
        j = json.loads(web.data())

        # This indicates that we are posting back to the channel from a rule, so ignore the post
        if j['user_name'].lower() in settings.chatIgnoreUsers:
            return

        req = utils.parseChatRequest(j['text'])
        req['channel_id'] = j['channel_id']

        if req['action'] != '<unknown>' and req['action'] != '<error>':
            ruleFound = True
            req['id'] = j['post_id']
            if req['action'] == 'conn':
                ruleConnections.processChat(req)
            elif req['action'] == 'lag':
                ruleRplLag.processChat(req)
            elif req['action'] == 'health':
                ruleHealth.processChat(req)
            elif req['action'] == 'que':
                ruleQueues.processChat(req)
            elif req['action'] == 'ops':
                ruleOpCounters.processChat(req)
            elif req['action'] == 'upgrade':
                ruleUpgrade.upgrade(req)
            elif req['action'] == 'restart':
                ruleRestart.restart(req)
            elif req['action'] == 'sensei':
                ruleSenSei.processChat(req)
            else:
                ruleFound = False

        # If we did not fire a rule, we respond with a snarky reply
        if not ruleFound:
            return json.dumps({'text': settings.snarkyReplies[random.randrange(0, len(settings.snarkyReplies) - 1)]})
        else:
            return None

class alerthook:
    def POST(self):
        # Note that acknowleding the alert - even from here will send the alert to this function again
        #  If we've already acknowledged it, then we should see 'incident' in the ack comments
        isAlreadyAcked = False
        alert = json.loads(web.data())

        if 'acknowledgementComment' in alert and 'incident' in alert['acknowledgementComment']:
            isAlreadyAcked = True

        if not isAlreadyAcked:
            # Rule for connections
            if alert['eventTypeName'] == 'OUTSIDE_METRIC_THRESHOLD' and alert['typeName'] == 'HOST_METRIC' and alert[
                    'metricName'] == 'CONNECTIONS' and alert['status'] == 'OPEN':
                ruleConnections.processAlert(alert, False)

            # Rule for Rpl Lag
            if alert['eventTypeName'] == 'OUTSIDE_METRIC_THRESHOLD' and alert['typeName'] == 'HOST_METRIC' and \
                    alert[
                        'metricName'] == 'OPLOG_SLAVE_LAG_MASTER_TIME' and alert['status'] == 'OPEN':
                ruleRplLag.processAlert(alert, False)


class images:
    def GET(self,name):
        ext = name.split(".")[-1] # Get extension

        cType = {
            "png":"images/png",
            "jpg":"images/jpeg",
            "gif":"images/gif" }

        if name in os.listdir(settings.imgserverFolder):  # Security
            web.header("Content-Type", cType[ext]) # Set the Header
            return open(settings.imgserverFolder + '/%s'%name,"rb").read() # Notice 'rb' for reading images
        else:
            raise web.notfound()
if __name__ == '__main__':
    app.run()