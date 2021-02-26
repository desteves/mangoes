#### Rule to handle Health check ####
import omCharts
import chatPost

def processChat(req):
    if 'opsmgr' in req['sourceList']:
        if 'group' not in req or 'hostList' not in req or len(req['hostList']) < 1:
            chatPost.postToChannel('Both a group name and either a host, list of hosts, or Replica Set are required for this request from Ops Manager', req['channel_id'])
        else:
            for h in req['hostList']:
                chatPost.postToChannel('#### Healthcheck for host ' + h['hostname'] + ':' + str(h['port']), req['channel_id'])
                chatPost.postToChannel('**  Replica Set : ' + h['replicaSetName'] + '**', req['channel_id'])
                chatPost.postToChannel('**  Replication Status: ' + h['replicaStateName'] + '**', req['channel_id'])
                chatPost.postToChannel('**  MongoDB Version: ' + h['version'] + '**', req['channel_id'])
                chatPost.postToChannel('**  Last Ping: ' + h['lastPing'] + '**', req['channel_id'])
                chatPost.postToChannel('**  Last Restart: ' + h['lastRestart'] + '**', req['channel_id'])

                # Op Counters
                f = omCharts.genOpsCounterChart(req['id'], req['omgroupid'], h['id'],
                                        'Op Counters for ' + h['replicaSetName'] + ' - ' + h['hostname'] + ':' + str(h['port']))
                if f is not None:
                    msg = chatPost.genChartLink(f)
                else:
                    msg = 'There are no OP counters for host ' + h['hostname'] + ':' + str(h['port']) + ' in RplSet ' + h['replicaSetName']
                chatPost.postToChannel(msg, req['channel_id'])


                # Connections
                f = omCharts.genConnectionsChart(req['id'], req['omgroupid'], h['id'],
                                        'Connections for ' + h['replicaSetName'] + ' - ' + h['hostname'] + ':' + str(h['port']))
                if f is not None:
                    msg = chatPost.genChartLink(f)
                else:
                    msg = 'There are no connections for host ' + h['hostname'] + ':' + str(h['port']) + ' in RplSet ' + h['replicaSetName']
                chatPost.postToChannel(msg, req['channel_id'])


                # Queues
                f = omCharts.genQueueChart(req['id'], req['omgroupid'], h['id'],
                                           'Queues for ' + h['replicaSetName'] + ' - ' + h['hostname'] + ':' + str(h['port']))
                if f is not None:
                    msg = chatPost.genChartLink(f)
                else:
                    msg = 'There are no queues for host ' + h['hostname'] + ':' + str(h['port']) + ' in RplSet ' + h['replicaSetName']
                chatPost.postToChannel(msg, req['channel_id'])


                # Rpl Lag
                if 'PRIMARY' not in h['replicaStateName']:
                    # Post text with chart link to chat system
                    f = omCharts.genRplLagChart(req['id'], req['omgroupid'], h['id'],
                                                'Replication Lag for ' + h['replicaSetName'] + ' - ' + h['hostname'] + ':' + str(h['port']))
                    if f is not None:
                        msg = chatPost.genChartLink(f)
                    else:
                        msg = 'There is no Replication Lag for host ' + h['hostname'] + ':' + str(h['port']) + ' in RplSet ' + h['replicaSetName']
                else:
                    msg = 'Host ' + h['hostname'] + ':' + str(h['port']) + ' is currently PRIMARY of RplSet ' + h['replicaSetName'] + ' - Replication Lag canot be plotted'
                chatPost.postToChannel(msg, req['channel_id'])

                chatPost.postToChannel('---', req['channel_id'])
