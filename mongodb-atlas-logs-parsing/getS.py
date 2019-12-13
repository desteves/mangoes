import pymongo
import argparse

'''
Example:

py getS.py -p -U USERNAME -P PASSWORD  -H HOST

'''


def getShardedCollections(db) :
    sharded_collections = []
    res = db["collections"].find( {}, {"_id": 1})
    for tmp in res:
        sharded_collections.append(tmp["_id"])
    return sharded_collections

def getMongos(db):
    mongos = []
    res = db["mongos"].find({}, {"_id": 1})
    for tmp in res:
        mongos.append(tmp["_id"])
    return mongos

def getShards(db):
    shards = []
    res = db["shards"].find({}, {"host": 1, "_id": 0})
    for tmp in res:
        shards.append(tmp["host"])
    return shards

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get details from Atlas Cluster")
    parser.add_argument('-d', help='Get list of mongod', action='store_true')
    parser.add_argument('-p', help='Get list of primaries', action='store_true')
    parser.add_argument('-s', help='Get list of mongos', action='store_true')
    parser.add_argument('-c', help='Get list of sharded collections', action='store_true')
    
    # USER, PASSWORD, HOSTNAME
    parser.add_argument('-U', help='MongoClient USER', required=True)
    parser.add_argument('-P', help='MongoClient PASSWORD', required=True)
    parser.add_argument('-H', help='MongoClient HOST DNS SRV', required=True)
    args, leftovers = parser.parse_known_args()
 
    client = pymongo.MongoClient("mongodb+srv://" + args.U + ":" + args.P + "@" + args.H)
    db = client.config

    if args.c:
        for collection in getShardedCollections(db):
            print collection
    if args.s:
        # print "MongoS"
        for mongos in getMongos(db):
            print mongos
    if args.d:
        # print "Shards"
        for shard in getShards(db):    
            print shard    
    if args.p:
        # print "Primaries"
        for shard in getShards(db):
            tmpArr = shard.split("/")
            replSetName = tmpArr[0]
            hosts = tmpArr[1]
            tmpClient = pymongo.MongoClient("mongodb://" + args.U + ":" + args.P + "@" + hosts + "/?replicaSet=" + replSetName + "&authMechanism=SCRAM-SHA-1&ssl=true&authSource=admin")
            try:
                primary =  tmpClient.admin.command('ismaster')
                if primary["ismaster"]:
                    print primary["me"]
            except ConnectionFailure:
                print("Server not available")
            tmpClient.close() 