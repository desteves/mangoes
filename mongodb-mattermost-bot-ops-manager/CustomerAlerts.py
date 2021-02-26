##!/home/mongod/bin/python
###THIS CRON GENERATES TICKETS FROM MMS ALERTS COLLECTION EVERY 5 MINS,IF ANY ISSUES PLEASE CONTACT MJANI###
import sys
import json

#sys.path.append('/home/mongod/mmsagent/PyMongo/lib64/python/pymongo-3.2.1-py2.4-linux-x86_64.egg')

import re
import pymongo
import subprocess
import os.path
from datetime import datetime, timedelta


def append(obj1, obj2):
    ret = ""
    try:
        ret += obj1.encode('ascii', 'ignore')
        ret += obj2.encode('ascii', 'ignore').strip()
        return ret
    except:
        return obj1


# set this to False for prod
debug = False

now = datetime.now()
future_ack_ts = now + timedelta(days=800)

os.environ[
    'PATH'] = '/home/mongod/bin:/home/mongod/mongosys/3.2.0/bin:/usr/bin:/bin:/usr/ucb:/usr/sbin:/etc:/usr/local/bin'
os.environ['PYTHONPATH'] = '/home/mongod/mmsagent/PyMongo/lib64/python'
os.environ['PWD'] = '/mongodata/cronjobs/'

# conn = pymongo.MongoClient('mongodb://mongoadmin:*********@host.customer.com:12345/admin')
# conn = pymongo.MongoClient(username="mongoadmin", password=“********", host=['host.customer.com:12345'],replicaset='OPSMGR3')
conn = pymongo.MongoClient(
    'mongodb://mongoadmin:***************@host.customer.com:12345/?replicaSet=OPSMGR3')
db = conn['mmsdb']

if debug:
    now = datetime.now()
    pasttimestamp = now - timedelta(minutes=15)
    cursor = db.data.alerts.v2.find({"cre": {"$gt": pasttimestamp}})
else:
    cursor = db.data.alerts.v2.find({"status": "OPEN", "acknowledgingUsername": {"$exists": False}})

for doc in cursor:
    priority = 1
    print("Found an open ticket")
    outputMessage = "\n_id : " + str(doc['_id'])
    outputMessage = "\nPLEASE refer to below connectMe URL for further details on this Alert & Action:"
    outputMessage += append("\nURL", "")
    outputMessage += append(" ", " ")
    if "et" in doc:
        outputMessage += append("\nCATEGORY           : ", doc['et'])
        if doc['et'] == "HOST_DOWN":
            priority = 1
    if "mt" in doc:
        outputMessage += append("\nMETRIC-DETAILS     : ", json.dumps(doc['mt']))
    if "hp" in doc:
        outputMessage += append("\nHOST-NAME          : ", doc['hp'])
    if "lnd" in doc:
        outputMessage += append("\nEVENT DATE         : ", doc['lnd'])
    if "ver" in doc:
        outputMessage += append("\nMONGODB-VERSION    : ", doc['ver'])
    if "rsId" in doc:
        outputMessage += append("\nReplicaSetName     : ", doc['rsId'])
    if "_t" in doc:
        outputMessage += "\nAlert type         : " + str(doc['_t'])
    alertfile = str(doc['_id']) + ".txt"

    alertout = os.path.join('/mongodata/cronjobs', alertfile)
    print ("alert file is being created at " + alertout)

    if os.path.isfile(alertout) and os.access(alertout, os.R_OK):
        print ('Alert already exists: ' + alertout)
    else:
        with open(alertout, "w+") as outfile:
            outfile.write(outputMessage)
            print ('Writing alert: ' + alertout)
        outfile.close()

        subject = "OPSMGR2:"
        try:
            host = append("", doc['hp'])
            print(host)
            print (doc['hp'])
            #       host=re.sub(':\d*',''           ,host,flags=re.IGNORECASE)
            #       host=re.sub('.(prz.)?customer.com','',host,flags=re.IGNORECASE)
            subject += " Host: " + host
            print (subject)
        except:
            pass

        try:
            type = append("", doc['et'])
            if type == 'OUTSIDE_METRIC_THRESHOLD':
                type = str(doc['mt']['metric'])
            if type == 'OPLOG_BEHIND':
                type = "Replag: " + doc['rsId']
            if type == 'NO_PRIMARY':
                type = "No Primary: " + doc['rsId']
            if type == 'LATE_SNAPSHOT':
                type = "BRS-Snapshot is behind: " + doc['rsId']
            if type == 'RESYNC_REQUIRED':
                type = "Resync Required: " + doc['rsId']
            subject += " " + type
        except:
            pass

        if debug:
            print ("Execing: " + "/bin/cat  " + alertout + "  | /home/mongod/bin/gsd_create_ticket 1 \"" + subject.encode(
                'ascii', 'ignore') + " \"")

        else:
            x = subprocess.call(
                "/bin/cat  " + alertout + "  | /home/mongod/bin/gsd_create_ticket 0 \"" + subject.encode('ascii',
                                                                                                         'ignore') + " \"",
                shell=True)
            #             x = subprocess.call("/bin/cat  "+alertfile+"  | /home/mongod/bin/gsd_notify \"" + subject.encode('ascii','ignore') + " \" 2" , shell=True)
            #	x = subprocess.call("/bin/cat  "+alertfile+"  | /home/mongod/bin/gsd_notify \"" + subject.encode('ascii','ignore') + " \" \"OpsManager\" \"SCRIPT\" \"OPSMgr-PRN\" WARNING OPS-MGRMONGO", shell=True)

            if (x == 0):
                # db.data.alerts.v2.update({'_id':(doc['_id'])}, { "$set": {"ackUntil" : "ISODate('2114-11-10T22:18:45.888Z')","acknowledgementComment" : None,"acknowledgingUsername" : "gcsdbamon@customer.com"}})
                db.data.alerts.v2.update_one({'_id': (doc['_id'])}, {
                    "$set": {"ackUntil": future_ack_ts, "acknowledgementComment": '{"incident": "' + str(inc) + '"}',
                             "acknowledgingUsername": "gcsdbamon@customer.com"}})
                subprocess.call("/bin/mv  " + alertout + " /mongodata/data/cronjobs/dump/", shell=True)
            # subprocess.call("WARNING - MMS-Notificatin NON-PROD ALERT -TESTING" | /home/mongod/bin/gsd_notify, shell=True)
            # subprocess.call("/bin/cat 5329fbd1498e599d8d233e94.txt | /home/mongod/bin/gsd_create_ticket 3 \"AAA\"", shell=True)

conn.close()
