import settings
import utils
import datetime

# Date format
dateFmt = '%Y-%m-%dT%H:%M:%S'

# O/M granularity
granularity='PT1M'

# This is a list of metrics to collect
defaultMetrics = ['GLOBAL_LOCK_CURRENT_QUEUE_TOTAL',
            'OPLOG_RATE_GB_PER_HOUR',
            'OPCOUNTER_CMD',
            'OPCOUNTER_QUERY',
            'OPCOUNTER_UPDATE',
            'OPCOUNTER_DELETE',
            'OPCOUNTER_GETMORE',
            'OPCOUNTER_INSERT',
            'TICKETS_AVAILABLE_READS',
            'TICKETS_AVAILABLE_WRITE',
            'EXTRA_INFO_PAGE_FAULTS',
            'QUERY_TARGETING_SCANNED_OBJECTS_PER_RETURNED',
            'CACHE_BYTES_READ_INTO',
            'CACHE_DIRTY_BYTES',
            'MEMORY_RESIDENT',
            'CONNECTIONS']

# This is a list of sensitive metrics that might return an error if a node is in the wrong state or uses the wrong storage engine
defaultSensitiveMetrics = ['BACKGROUND_FLUSH_AVG',
                        'OPLOG_SLAVE_LAG_MASTER_TIME',
                        'OP_EXECUTION_TIME_READS',
                        'OP_EXECUTION_TIME_WRITES',
                        'OP_EXECUTION_TIME_COMMANDS',
                        'AVG_READ_EXECUTION_TIME',
                        'AVG_WRITE_EXECUTION_TIME',
                        'AVG_COMMAND_EXECUTION_TIME',
                        'OPCOUNTER_REPL_CMD',
                        'OPCOUNTER_REPL_UPDATE',
                        'OPCOUNTER_REPL_DELETE',
                        'OPCOUNTER_REPL_INSERT']


# List of values to sum and send in - ignore if not in the overriden metrics
sumVals = {}
# sum up all the OPCOUNTER_xxx metrics as 'OpCounters'
sumVals['OPCOUNTER_TOTAL'] = ['OPCOUNTER_CMD', 'OPCOUNTER_QUERY', 'OPCOUNTER_UPDATE', 'OPCOUNTER_DELETE',
                              'OPCOUNTER_GETMORE', 'OPCOUNTER_INSERT']
# sum up all the OPCOUNTER_REPL_xxx metrics as 'RplCounters'
sumVals['OPCOUNTER_REPL_TOTAL'] = ['OPCOUNTER_REPL_CMD', 'OPCOUNTER_REPL_UPDATE', 'OPCOUNTER_REPL_DELETE',
                                   'OPCOUNTER_REPL_INSERT']



sensitiveSumVals={}
sensitiveSumVals['OP_EXECUTION_TIME_TOTAL'] = ['AVG_WRITE_EXECUTION_TIME',
                       'AVG_COMMAND_EXECUTION_TIME',
                       'OP_EXECUTION_TIME_READS',
                       'OP_EXECUTION_TIME_WRITES',
                       'OP_EXECUTION_TIME_COMMANDS'
                       ]

# Due to execution time metrics being re-named in OpsMgr 4.0, we want to map the older name to the newer value.  This
# will allow t00l to maintain these metrics after O/M upgrades.  Mapping is stored as tuples to send into reduce/lambda function
renameMetricList = [['AVG_READ_EXECUTION_TIME', 'OP_EXECUTION_TIME_READS'], \
                ['AVG_WRITE_EXECUTION_TIME', 'OP_EXECUTION_TIME_WRITES'], \
                ['AVG_COMMAND_EXECUTION_TIME', 'OP_EXECUTION_TIME_COMMANDS']]

def getCorrelatedMetrics(item, \
                         type, \
                         startTime = datetime.datetime.utcnow() - datetime.timedelta(minutes=7), \
                         endTime = datetime.datetime.utcnow() - datetime.timedelta(minutes=2), \
                         discardNulls = True,
                         metrics = defaultMetrics,
                         sensitiveMetrics = defaultSensitiveMetrics,
                         omServer = settings.opsmgrServerUrl, \
                         user = settings.opsmgrUser, \
                         apiKey = settings.opsmgrApiKey):
    retVal = []


    if len(item) <= 0:
        raise Exception('Item must contain a host:port or a rplset name')

    if type.lower() not in ['host', 'rplset']:
        raise Exception ('Type must be "host" or "rplset"')

    grp = None
    hostList = []

    # Determine if we have stuff to sum up in the list (see sumVals up top)
    hasSummedMetrics = False
    for m in metrics:
        for i in sumVals.itervalues():
            if m in i:
                hasSummedMetrics = True
                break
        if hasSummedMetrics:
            break;

    # Get groups
    omGroups = utils.getAllGroups(omServer=omServer, user=user, apiKey=apiKey)
    # Iterate thru each group and check for a name match
    for group in omGroups:
      if group['id'] in settings.groupids:
        # Check to see that item (host:port or RplSet) is in group before proceeding
        try:
            if utils.isItemInGroup(type, item, group['id'], omServer=omServer, user=user, apiKey=apiKey):
                # We found the item - get ready to pull metrics
                grp = group['id']
                tempList = utils.getHostsInGroup(grp, omServer=omServer, user=user, apiKey=apiKey)

                # Build out list of either single host or all host in rplSet
                if type.lower() == 'host':
                    for h in tempList:
                        if item.lower() == h['hostname'].lower() + ':' + str(h['port']):
                            hostList.append(h)
                            break
                else:
                    hostList = utils.getHostsInRplSet(item, grp, omServer=omServer, user=user, apiKey=apiKey)
        except:
            pass

    print (metrics)
    for h in hostList:
        if h['typeName'] in ['REPLICA_PRIMARY', 'REPLICA_SECONDARY']:
            if len(metrics) > 0:

                # Get regular metrics
                omMetrics = utils.getOpsMgrMetrics(metrics,
                                     grp,
                                     h['id'],
                                     granularity=granularity,
                                     period=None,
                                     startTime=startTime,
                                     endTime=endTime,
                                     omServer=omServer,
                                     user=user,
                                     apiKey=apiKey)


                # Transform metrics
                tsm = utils.transformMetrics(omMetrics)

                # Scrub metrics (in this case, we're only doing this to convert the 'None' values to zero) if specified
                if discardNulls:
                    scrubbedMetrcis = tsm
                else:
                    scrubbedMetrcis = utils.scrubMetrics(tsm, removeBlowThreshhold=-9999.0)

                summedMetrics = None
                if hasSummedMetrics:
                    # Sum up our metrics if we have any to sum
                    summedMetrics = utils.sumMetrics(scrubbedMetrcis, sumVals)

                entry = {'host' : h['hostname'].lower() + ':' + str(h['port'])}

                # Add in standard metrics
                if 'measurements' in omMetrics:
                  if scrubbedMetrcis is not None:
                    for k in scrubbedMetrcis.keys():
                        if k != 'timestamp':
                            metricName = k
                            for rm in renameMetricList:
                                if rm[0] == k:
                                    metricName = rm[1]
                                    break
                            ln = ''
                            for idx, val in enumerate(scrubbedMetrcis['timestamp']):
                                t = val.strftime (dateFmt)
                                metric = str(scrubbedMetrcis[k][idx])
                                if metric is not None and str(metric) != 'None':
                                    ln += h['hostname'].lower() + ':' + str(h['port']) + ","  + metricName + "," + t + "," + metric + '\n'

                            if len(ln) > 0:
                                a = entry.copy()
                                a['metric'] = metricName
                                a['data'] = ln
                                retVal.append(a)

                    # Add in summed up metrics as well if we have any
                    if hasSummedMetrics:
                        for k in summedMetrics.keys():
                            if k != 'timestamp':
                                ln = ''
                                for idx, val in enumerate(summedMetrics['timestamp']):
                                    t = val.strftime (dateFmt)
                                    metric = str(summedMetrics[k][idx])
                                    if metric is not None and str(metric) != 'None':
                                        ln += h['hostname'].lower() + ':' + str(h['port']) + ","  + k + "," + t + "," + metric + '\n'

                                if len(ln) > 0:
                                    a = entry.copy()
                                    a['metric'] = k
                                    a['data'] = ln
                                    retVal.append(a)

            # Get sensitive metrics one group a time - these ones are likely to throw an error, so we need to pull one at a time.
            # However, we need to sum them up in some cases, so there is a little bit more gymnastics in order to add them up
            # We will pull all metrics that will be summed together, but only one group at a time.  For example, execution times
            # can be either 'AVG_xxx_EXECUTION_TIME' or 'OP_EXECUTION_TIME_xxx', but not both, so we pull each of these
            # three at the same time and then sum the ones we get back.

            # Determine if we have stuff to sum up in the list (see sensitiveSumVals up top)
            hasSensitiveSummedMetrics = False
            for m in sensitiveMetrics:
                for i in sensitiveSumVals.itervalues():
                    if len(set(m).intersection(i)) > 0:
                        hasSensitiveSummedMetrics = True
                        break
                if hasSensitiveSummedMetrics:
                    break;

            for sm in sensitiveMetrics:
                try:
                    # Get regular metrics
                    omMetrics = utils.getOpsMgrMetrics(sm,
                                                       grp,
                                                       h['id'],
                                                       granularity=granularity,
                                                       period=None,
                                                       startTime=startTime,
                                                       endTime=endTime,
                                                       omServer=omServer,
                                                       user=user,
                                                       apiKey=apiKey)

                    # Transform metrics
                    tsm = utils.transformMetrics(omMetrics)
                    # Scrub metrics (in this case, we're only doing this to convert the 'None' values to zero)
                    if discardNulls:
                        scrubbedMetrcis = tsm
                    else:
                        scrubbedMetrcis = utils.scrubMetrics(tsm, removeBlowThreshhold=-9999.0)

                    entry = {'host': h['hostname'].lower() + ':' + str(h['port'])}

                    # Add in sensitive metrics
                    if 'measurements' in omMetrics:
                        for k in scrubbedMetrcis.keys():
                            if k != 'timestamp':
                                metricName = k
                                for rm in renameMetricList:
                                    if rm[0] == k:
                                        metricName = rm[1]
                                        break

                                ln = ''
                                for idx, val in enumerate(scrubbedMetrcis['timestamp']):
                                    t = val.strftime(dateFmt)
                                    metric = str(scrubbedMetrcis[k][idx])
                                    if metric is not None and str(metric) != 'None':
                                        ln += h['hostname'].lower() + ':' + str(h['port']) + "," + metricName + "," + t + "," + metric + '\n'
                                if len(ln) > 0:
                                    a = entry.copy()
                                    a['metric'] = metricName
                                    a['data'] = ln
                                    retVal.append(a)

                    # Add in summed up metrics as well if we have any
                    summedMetrics = None
                    if hasSensitiveSummedMetrics:
                        summedMetrics = utils.sumMetrics(scrubbedMetrcis, sensitiveSumVals)
                        for k in summedMetrics.keys():
                            if k != 'timestamp':
                                ln = ''
                                for idx, val in enumerate(summedMetrics['timestamp']):
                                    t = val.strftime(dateFmt)
                                    metric = str(summedMetrics[k][idx])
                                    if metric is not None and str(metric) != 'None':
                                        ln += h['hostname'].lower() + ':' + str(
                                            h['port']) + "," + k + "," + t + "," + metric + '\n'

                                if len(ln) > 0:
                                    a = entry.copy()
                                    a['metric'] = k
                                    a['data'] = ln
                                    retVal.append(a)

                except:
                    pass

    return retVal


#hostlist = ['host.customer.com:10905']
#with open('/mongodata/t00l/mongoUtils/'+'Metric_t00l3.txt', 'w') as f:
# for hosts in hostlist:
#   finaldata = getCorrelatedMetrics(hosts, 'host', omServer = settings.opsmgrServerUrl, user = settings.opsmgrUser, apiKey = settings.opsmgrApiKey)
#   for items in finaldata:
#      f.write(items['data'])
#f.close()

