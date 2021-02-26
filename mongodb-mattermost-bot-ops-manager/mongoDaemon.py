import json
import settings
import utils
import time
import isodate
import numpy
import omCharts
import ruleConnections

def processAlerts():
    for alert in utils.getOpenAlerts():
        # in this case, we use the alert rule, but pass in "True" on the 'isAcked' parameter so it will
        # only post charts and such and not try to ack or create a new channel.  Note that we will only
        # process acked alerts here if the alert is ackable

        if 'acknowledgementComment' in alert and 'incident' in alert['acknowledgementComment']:
            if alert['eventTypeName'] == 'OUTSIDE_METRIC_THRESHOLD' and alert['typeName'] == 'HOST_METRIC' and alert[
                    'metricName'] == 'CONNECTIONS' and alert['status'] == 'OPEN':
                ruleConnections.processAlert(alert, isAcked=True)
    return

def run():
    while True:
        processAlerts()
        # Add other functions here to process as part of mongoDaemon
        time.sleep(settings.daemonSleepTimeSeconds)

if __name__ == "__main__":
    run()