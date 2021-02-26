#import currentOp
import sys
sys.path.append('/mongodata/t00l/Anaconda_3/pkgs/lib/python3.6/site-packages')
import mongoAuth
import json
import settings
import getPing
import currentOp
import datetime
import utils
import time
import threading

lock = threading.Lock()

##overriding to prn x509 ops manager
settings.groupids = ['abcabc123123']

start = time.time()
onedayoldtimestamp = datetime.datetime.strptime((datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')),'%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(hours=24)

allhosts = []
for ops in settings.prnopsmgrlogin:
 for items in (utils.getAllGroups(omServer = ops['opsmgrurl'], user = ops['opsmgruser'], apiKey = ops['opsmgrapikey'])):
    if items['id'] in settings.groupids:
        hosts = utils.getHostsInGroup(items['id'],omServer = ops['opsmgrurl'], user = ops['opsmgruser'], apiKey = ops['opsmgrapikey'])
        for itms in hosts:
          if itms['typeName'] in ['REPLICA_PRIMARY', 'REPLICA_SECONDARY']:
           if 'lastPing' in itms:
            if (datetime.datetime.strptime(itms['lastPing'],'%Y-%m-%dT%H:%M:%SZ') - onedayoldtimestamp ).total_seconds()/60/60 < 24:
               allhosts.append(itms)
            else:
               print (itms['hostname'],itms['lastPing'])

print (len(allhosts))

def call_metrics(allhosts,thr):
    timeToRun = 60 # one hour
    collectionInterval = 5 # seconds to collect
    maxFailures = 3 # number of failed attempts for getOp before giving up for the rest of the cycle

    startTime = time.time()
    endTime = startTime + timeToRun

    for i in range(len(settings.prnopsmgrlogin)):
        p = getPing.retrieve(allhosts,part = 'cmdline',omInfo = settings.prnmmsadminOMList[i])
        if (p != None):
           print (len(p))
           break

    # Build out hostlist and connections
    hostList = []
    if p!= None:
      for i in p:
       con = mongoAuth.authenticate(i)
       ##add the check for con is none
       if con != None:
          ######
          hostList.append({'con' : con, 'name' : i['ping']['hostNameAndPort'], 'failures' : 0})

    # Start pulling currentOp with existing connection
    while time.time() < endTime:
        cycleEnd = time.time() + collectionInterval
        for h in hostList:
            try:
                if h['failures'] < maxFailures:
                    out = currentOp.getCurrentOp(h['con'],h['name'])
                    if len(out) > 0:
                        print ("current op found count " + str(len(out)))
                        lock.acquire()
                        for j in out:
                            f.write(j['metrictime']+','+j['host']+','+j['op']+','+j['ns']+','+j['planSummary']+','+str(j['count'])+'\n')
                        lock.release()
            except:
                h['failures'] += 1
        while time.time() < cycleEnd:
            time.sleep(1)
    for h in hostList:
        h['con'].close()


n=20
allhostsspilt = [allhosts[i * n:(i + 1) * n] for i in range((len(allhosts) + n - 1) // n )]
f = open('/mongodata/t00l/mongoUtils/currentOp/current_ops_prn1.out','w')
threads = []

i=0
for l in allhostsspilt:
    ##create the thread here
    i += 1
    t = threading.Thread(target=call_metrics,args= [l,i])
    t.start()
    threads.append(t)

while threading.activeCount() > 1:
    pass
else:
    f.close()

end = time.time()
print ("script took > "+ str(end-start))

