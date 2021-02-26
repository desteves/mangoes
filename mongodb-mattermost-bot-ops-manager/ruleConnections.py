#### Rule to handle connections ####
import utils
import chatPost
import omCharts
import json




def processAlert(alert, isAcked = False):
    channel = None
    ticket = None

    if not isAcked:
        # create incident and alert chat channel if not already acked
        ticket = utils.createIncident(alert)
        if ticket is not None:
            channel = chatPost.createChatChannel(alert, ticket)
            if channel is not None:
                utils.ackOpsMgrAlert(alert, ticket, channel)
    else:
        c = json.loads(alert['acknowledgementComment'])
        channel = c['channel']
        ticket = c['incident']

        # Code to update ticket with SenSei info goes here

    # Generate connections chart
    f = omCharts.genConnectionsChart(alert['id'], alert['groupId'], alert['hostId'],
                                     'Connections for ' + alert['replicaSetName'] + ' - ' + alert['hostnameAndPort'])
    if f is not None:
        msg = chatPost.genChartLink(f)
    else:
        msg = 'There are no connections for host ' + alert['hostnameAndPort'] + ' in RplSet ' + alert['replicaSetName']
    chatPost.postToChannel(msg, channel)

    # Generate Op Counter chart
    f = omCharts.genOpsCounterChart(alert['id'], alert['groupId'], alert['hostId'],
                                     'Op Counters for ' + alert['replicaSetName'] + ' - ' + alert['hostnameAndPort'])
    if f is not None:
        msg = chatPost.genChartLink(f)
    else:
        msg = 'There are no Op Counters for host ' + alert['hostnameAndPort'] + ' in RplSet ' + alert['replicaSetName']
    chatPost.postToChannel(msg, channel)

    # Generate OpsMgr Queue chart
    #f = omCharts.genQueueChart(alert['id'], alert['groupId'], alert['hostId'],
    #                                 'Queues for ' + alert['replicaSetName'] + ' - ' + alert['hostnameAndPort'])
    #if f is not None:
    #    msg = chatPost.genChartLink(f)
    #else:
    #    msg = 'There are no queues for host ' + alert['hostnameAndPort'] + ' in RplSet ' + alert['replicaSetName']
    #chatPost.postToChannel(msg, channel)
    return

def processChat(req):
    if 'opsmgr' in req['sourceList']:
        if 'group' not in req or 'hostList' not in req or len(req['hostList']) < 1:
            chatPost.postToChannel('Both a group name and either a host, list of hosts, or Replica Set are required for this request from Ops Manager', req['channel_id'])
        else:
            for h in req['hostList']:
                # Post text with chart link to chat system
                f = omCharts.genConnectionsChart(req['id'], req['omgroupid'], h['id'],
                                        'Connections for ' + h['replicaSetName'] + ' - ' + h['hostname'] + ':' + str(h['port']))
                if f is not None:
                    msg = chatPost.genChartLink(f)
                else:
                    msg = 'There are no connections for host ' + h['hostname'] + ':' + str(h['port']) + ' in RplSet ' + h['replicaSetName']
                chatPost.postToChannel(msg, req['channel_id'])

