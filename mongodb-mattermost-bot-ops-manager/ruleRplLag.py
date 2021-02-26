#### Rule to handle alerts and/or requests for RplLag ####
import utils
import omCharts
import chatPost
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

    # Generate RplLag chart
    f = omCharts.genRplLagChart(alert['id'], alert['groupId'], alert['hostId'],
                                'Replication Lag for ' + alert['replicaSetName'] + ' - ' + alert['hostnameAndPort'])
    if f is not None:
        msg = chatPost.genChartLink(f)
    else:
        msg = 'There is no Replication Lag for host ' + alert['hostnameAndPort'] + ' in RplSet ' + alert['replicaSetName']
    chatPost.postToChannel(msg, channel)

    # Generate OpsMgr Queue chart
    f = omCharts.genQueueChart(alert['id'], alert['groupId'], alert['hostId'],
                                'Queues for ' + alert['replicaSetName'] + ' - ' + alert['hostnameAndPort'])
    if f is not None:
        msg = chatPost.genChartLink(f)
    else:
        msg = 'There are no Queues for host ' + alert['hostnameAndPort'] + ' in RplSet ' + alert['replicaSetName']
    chatPost.postToChannel(msg, channel)
    return


def processChat(req):
    if 'opsmgr' in req['sourceList']:
        if 'group' not in req or 'hostList' not in req or len(req['hostList']) < 1:
            chatPost.postToChannel('Both a group name and either a host, list of hosts, or Replica Set are required for this request from Ops Manager', req['channel_id'])
        else:
            # show message for PRIMARY member 1st
            for h in req['hostList']:
                # check to see that the host is a primary - this metric does not exist for the primary
                if 'PRIMARY' in h['replicaStateName']:
                    msg = 'Host ' + h['hostname'] + ':' + str(h['port']) + ' is currently PRIMARY of RplSet ' + h['replicaSetName'] + ' - Replication Lag canot be plotted'
                    chatPost.postToChannel(msg, req['channel_id'])

            # Now loop thru non-primaries
            for h in req['hostList']:
                if 'PRIMARY' not in h['replicaStateName']:
                    # Post text with chart link to chat system
                    f = omCharts.genRplLagChart(req['id'], req['omgroupid'], h['id'],
                                                    'Replication Lag for ' + h['replicaSetName'] + ' - ' + h['hostname'] + ':' + str(h['port']))
                    if f is not None:
                        msg = chatPost.genChartLink(f)
                    else:
                        msg = 'There is no Replication Lag for host ' + h['hostname'] + ':' + str(h['port']) + ' in RplSet ' + h['replicaSetName']
                    chatPost.postToChannel(msg, req['channel_id'])
