
# Zone Sharding Example

- Set up 3 shard cluster

```bash
mlaunch init --config 1 --csrs --nodes 1 --replicaset --sharded s1 s2 s3
# launching: mongod on port 27018
# launching: mongod on port 27019
# launching: mongod on port 27020
# launching: config server on port 27021
# replica set 'configRepl' initialized.
# replica set 's1' initialized.
# replica set 's2' initialized.
# replica set 's3' initialized.
# launching: mongos on port 27017
```

- Generate a bunch of sample documents

```bash
mgeneratejs -n1000000  '{"tradeDate": "$date", "name": "$name" }' | mongoimport -d test -c demo
mongo
```

- Inside the MongoDB Shell run the following:

```javascript

// Add Tags
mongos> sh.addShardTag("s1", "recent")
mongos> sh.addShardTag("s2", "recent")
mongos> sh.addShardTag("s2", "recent")

// Verify
mongos> sh.status()
// #         {  "_id" : "s1",  "host" : "s1/localhost:27018",  "state" : 1,  "tags" : [ "recent" ] }
// #         {  "_id" : "s2",  "host" : "s2/localhost:27019",  "state" : 1,  "tags" : [ "archive" ] }
// #         {  "_id" : "s3",  "host" : "s3/localhost:27020",  "state" : 1,  "tags" : [ "archive" ] }

// Active is anything newer than 105 days.
var range = new Date(ISODate().getTime() - 1000 * 86400 * 105);

// Enable Sharding at the database level
sh.enableSharding("test");

// Create Index for the shard key
db.demo.createIndex({ "tradeDate": 1, "name": 1} );

// Shard the collection
sh.shardCollection("test.demo", { "tradeDate": 1, "name": 1} );

// Add Ranges and associate them with a zone
sh.addTagRange("test.demo",                         // namespace
  { "tradeDate" : MinKey, "name" : MinKey },  // lower bound
  { "tradeDate" : range,  "name" : MinKey },  // upper bound
   "archive");                                      // zone

sh.addTagRange("test.demo",                         // namespace
  { "tradeDate" : range,  "name" : MinKey },  // lower bound
  { "tradeDate" : MaxKey, "name" : MaxKey },  // upper bound
   "recent");                                       // zone

// Verify
mongos> sh.status()
// # test.demo
// #   shard key: { "tradeDate" : 1, "name" : 1 }
// #   chunks:
// #           s1	1
// #           s2	2
// #           s3	3

```