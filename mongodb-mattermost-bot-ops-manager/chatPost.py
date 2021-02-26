#### Post items to chat system ####
import settings
import requests
import json

def post(text, image = ''):
    # Post text - add image if it's specified
    returnValue = settings.opsmgrWebHookReturnValue

    txt = text
    if image is not None and len(image) > 0:
        txt += ' ' + genChartLink(image)

    r = requests.post(settings.chatServerUrl, json.dumps({'username': settings.chatServerUser, 'text': txt}))
    if r.status_code != 200:
        print("********** Error posting to Mattermost: ")
        print(json.dumps(r.json(), indent=2))
        returnValue = r.json

    return returnValue

# Generate chart link for Chat system
def genChartLink(chart, altText='Chart'):
    if 'errorCode' in chart:
        retVal = '\n' + '    ' + chart['detail']
    else:
        retVal = '![' + altText + '](' + settings.imgserverUrl + '/' + chart + ')'
    return retVal

# Post message to given channel
def postToChannel(msg, channel, token=settings.chatServerToken):
    url = settings.chatServerAPIUrl + '/posts'

    opts = {}
    opts['channel_id'] = channel
    opts['message'] = settings.chatBotPrefix + msg

    hdr = {'Authorization': 'Bearer ' + token}

    resp = requests.post(url, data=json.dumps(opts), headers=hdr)

    if resp.status_code != 201:
        # This means something went wrong.
        print('---- ERROR Posting to channel - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))

# Open a new chat channel
def createChatChannel(alert, incident):
    channel = None

    # Add incident and alertID to channel header for
    txt = 'incident: ' + incident + " alert: " + alert['id']


    opts = {}
    opts['display_name'] = incident
    opts['name'] = incident.lower()
    opts['team_id'] = settings.chatServerTeam
    opts['purpose'] = 'Discuss incident ' + incident
    opts['header'] = txt
    opts['type'] = 'O' # Use 'O' for public or 'P' for private
                       # Note we have to use public in MatterMost to enable our webhook
                       #  The other option would be to start each request with a specific word i.e. 'mongobot ....'

    url = settings.chatServerAPIUrl + '/channels'

    hdr = {'Authorization': 'Bearer ' + settings.chatServerToken}

    resp = requests.post(url, data=json.dumps(opts), headers=hdr)
    if resp.status_code != 201:
        # This means something went wrong.
        print('---- ERROR Creating new channel - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
        print('--------')
        print(resp)
    else:
        channel = resp.json()['id']

        # Add all team members to the channel (this *should* be automatic, but it's not!
        url = settings.chatServerAPIUrl + '/teams/' + settings.chatServerTeam + '/members'
        resp = requests.get(url, headers=hdr)
        if resp.status_code != 200:
            # This means something went wrong.
            print('---- ERROR Retrieving team members during new channel creation - ' + str(resp.status_code) + ' was returned')
            print(json.dumps(resp.json()))
            print('--------')
            print(resp)
        else:
            for u in resp.json(): # loop thru each member and add to channel
                url = settings.chatServerAPIUrl + '/channels/' + channel + '/members'

                u = {'user_id' : u['user_id']}
                resp = requests.post(url, data=json.dumps(u), headers=hdr)
                if resp.status_code != 201:
                    # This means something went wrong.
                    print('---- ERROR Adding user to new channel - ' + str(resp.status_code) + ' was returned')
                    print(json.dumps(resp.json()))
                    print('--------')
                    print(resp)

        # Add the MongoBot webhook to the channel
        d = {"team_id": settings.chatServerTeam, "channel_id": channel, "display_name": "ChatBot-" + channel,
                "trigger_words" : ['Mongo', 'mongo', 'MongoBot', 'mongobot'], "callback_urls" : [settings.chatCallBackUrl], "content_type" : "application/json"}
        url = settings.chatServerAPIUrl + '/hooks/outgoing'

        resp = requests.post(url, data=json.dumps(d), headers=hdr)
        if resp.status_code != 201:
            # This means something went wrong.
            print('---- ERROR Adding MongoBot webhook to new channel - ' + str(resp.status_code) + ' was returned')
            print(json.dumps(resp.json()))
            print('--------')
            print(resp)

        # Now add the raw alert as well as ticket info to the channel
        postToChannel('This is the beginning of the conversation for incident ' + incident + ' raw alert data is below:', channel)
        postToChannel('-----------------------------------------------', channel)
        postToChannel(json.dumps(alert, indent=2), channel)
        postToChannel('-----------------------------------------------', channel)
        ticketLink = settings.ticketServerUrl +'?inc=' + incident
        postToChannel('The ticket can be found at [' + ticketLink + '](' + ticketLink + ')', channel)


    return channel

# Delete a chat channel
def deleteChatChannel(channelId):
    hdr = {'Authorization': 'Bearer ' + settings.chatServerToken}
    #url = settings.chatServerAPIUrl + '/teams/' + settings.chatServerTeam + '/channels/' + channelId # + '/delete'
    url = settings.chatServerAPIUrl + '/channels/' + channelId  # + '/delete'

    print(url)
    resp = requests.delete(url, headers=hdr)
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Deleting channel - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
        print('--------')
        print(resp)

# remove all 'inc' channels.  Delete this before publsihing
def delTemp():
    hdr = {'Authorization': 'Bearer ' + settings.chatServerToken}
    url = settings.chatServerAPIUrl + '/teams/' + settings.chatServerTeam + '/channels'
    resp = requests.get(url, headers=hdr)
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Creating new channel - ' + str(resp.status_code) + ' was returned')
        print(json.dumps(resp.json()))
        print('--------')
        print(resp)

    for c in resp.json():
        print (c['name'] + ' --- ' + c['id'])
        if c['name'].find('inc') > -1:
            deleteChatChannel(c['id'])

