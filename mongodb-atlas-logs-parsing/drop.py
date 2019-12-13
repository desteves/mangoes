
# Dropping Dabases and Collections in Sharded environments

# https://jira.mongodb.org/browse/SERVER-17397


import pymongo
import re
import argparse


'''
Example:

py drop.py -c null.string string.null  -d nullstring -U admin -P admin  -H localhost

You can pass in an array collections and/or databases to drop separated by whitespace as in the example above.


NOTE: There is no write access to the config database in Atlas. Thus, this will **not** work.

'''


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

# Connect to each shard's primary and verify the namespace has been dropped.
# If it has not, drop it.


def verifyDropDatabase(args, db, DATABASE):
    for shard in getShards(db):
        replSetName, hosts = shard.split("/")
        tmpClient = pymongo.MongoClient("mongodb://" + args.U + ":" + args.P + "@" + hosts +
                                        "/?replicaSet=" + replSetName + "&authMechanism=SCRAM-SHA-1&ssl=true&authSource=admin")
        try:
            result = tmpClient.drop_database(DATABASE)
            print("Dropped " + DATABASE + " in " +
                  replSetName + " . Result is " + result)
        except:
            print("Err drop_database for " +
                  DATABASE + " in " + replSetName + ".")
        tmpClient.close()


def verifyDropCollection(args, db,  DATABASE, COLLECTION):
    for shard in getShards(db):
        replSetName, hosts = shard.split("/")
        tmpClient = pymongo.MongoClient("mongodb://" + args.U + ":" + args.P + "@" + hosts +
                                        "/?replicaSet=" + replSetName + "&authMechanism=SCRAM-SHA-1&ssl=true&authSource=admin")
        try:
            result = tmpClient[DATABASE][COLLECTION].drop()
            print("Dropped " + DATABASE + "." + COLLECTION +
                  " in " + replSetName + " . Result is " + result)
        except:
            print("Err drop for " + DATABASE + "." +
                  COLLECTION + " in " + replSetName + ".")
        tmpClient.close()


# When dropping a database in a sharded environment
def dropDatabase(args, db, DATABASE):

    # drop the database
    try:
        client.drop_database(DATABASE)
        print result + " - From drop_database"
    except:
        print("Err client.drop_database for " + DATABASE)

    # check it has been dropped in all shards
    verifyDropDatabase(args, db, DATABASE)

    # remove all meta
    db = client.config
    regx = re.compile("^" + DATABASE + "\.")

    try:
        result = db.collections.delete_many({"_id":  regx})
        print result + " - From  collections delete many."
    except:
        print("Err collections delete_many.")

    try:
        db.databases.delete_one({"_id":  DATABASE})
        print result + " - From  databases delete one."
    except:
        print("Err databases delete_one.")

    try:
        db.chunks.delete_many({"_id":  regx})
        print result + " - From  chunks delete many."
    except:
        print("Err chunks delete_many.")

    try:
        db.locks.delete_many({"_id":  regx})
        print result + " - From  locks delete many."
    except:
        print("Err locks delete_many.")

    flushRouterConfig(args, db)

# When dropping a collection in a sharded environment


def dropCollection(args, db, DATABASE, COLLECTION, NAMESPACE):

    # drop the collection
    try:
        client[DATABASE][COLLECTION].drop()
        print result + " - From drop"
    except:
        print("Err client.drop for " + DATABASE + "." + COLLECTION)

    # verify the collection has been dropped
    verifyDropCollection(args, db, DATABASE, COLLECTION)

    # remove all meta
    db = client.config
    try:
        db.collections.delete_one({"_id": NAMESPACE})
        print result + " - From  collections delete one."
    except:
        print("Err collections delete_one.")

    try:
        db.chunks.delete_one({"_id": NAMESPACE})
        print result + " - From  chunks delete one."
    except:
        print("Err chunks delete_one.")

    try:
        db.locks.delete_one({"_id": NAMESPACE})
        print result + " - From  locks delete one."
    except:
        print("Err locks delete_one.")

    flushRouterConfig(args, db)

# Connect to each mongos and run `flushRouterConfig`

def flushRouterConfig(args, db):
    for mongos in getMongos(db):
        tmpClient = pymongo.MongoClient(
            host=mongos, port=27016, username=args.U, password=args.P, authSource="admin", ssl=True)
        try:
            result = tmpClient.admin.command("flushRouterConfig")
            print result
        except:
            print("Err, try again.")
        tmpClient.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Drop Databases/Collections in an  Atlas Cluster")
    parser.add_argument('-d', '--database', nargs='*',
                        help='List of DATABASE to drop')
    parser.add_argument('-n', '--namespace', nargs='*',
                        help='List of DATABASE.COLLECTION to drop')

    # USER, PASSWORD, HOSTNAME
    parser.add_argument('-U', help='MongoClient USER', required=True)
    parser.add_argument('-P', help='MongoClient PASSWORD', required=True)
    parser.add_argument('-H', help='MongoClient HOST', required=True)
    args, leftovers = parser.parse_known_args()

    client = pymongo.MongoClient(
        "mongodb+srv://" + args.U + ":" + args.P + "@" + args.H)
    db = client.config

    ### TEST ###
    # Test flushRouterConfig
    # flushRouterConfig(args, db)

    # Test verifyDropDatabase
    # verifyDropDatabase(args, db,  "nullstring")

    # Test verifyDropCollection
    # verifyDropCollection(args, db,  "null", "string")

    for database in args.database:
        # drop database
        print "Dropping database " + database + "."
        dropDatabase(args, db, database)

    for ns in args.namespace:
        # drop collection
        database, coll = ns.split(':')
        print "Dropping " + collection + " in the " + database + " database."
        dropCollection(args, db, database, coll, ns)
