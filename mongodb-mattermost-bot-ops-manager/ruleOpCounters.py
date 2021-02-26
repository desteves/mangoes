#### Rule to handle Op Counters ####
import omCharts
import chatPost

def processChat(req):
    if 'opsmgr' in req['sourceList']:
        if 'group' not in req or 'hostList' not in req or len(req['hostList']) < 1:
            chatPost.postToChannel('Both a group name and either a host, list of hosts, or Replica Set are required for this request from Ops Manager', req['channel_id'])
        else:
            for h in req['hostList']:
                # Post text with chart link to chat system
                f = omCharts.genOpsCounterChart(req['id'], req['omgroupid'], h['id'],
                                        'Op Counters for ' + h['replicaSetName'] + ' - ' + h['hostname'] + ':' + str(h['port']))
                if f is not None:
                    msg = chatPost.genChartLink(f)
                else:
                    msg = 'There are no OP counters for host ' + h['hostname'] + ':' + str(h['port']) + ' in RplSet ' + h['replicaSetName']
                chatPost.postToChannel(msg, req['channel_id'])