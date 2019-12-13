
///////////////////////////////////////////////////////////////////////////////
// Run inside the Mongo Shell
// Usefull snippets of code for DBA type of stuff
///////////////////////////////////////////////////////////////////////////////

// Add permissions to read cache plans
use admin
db.createRole(
   {
     role: "planCacheReadAll",
     privileges: [
       { resource: { db: "", collection: "" }, actions: [ "planCacheRead" ] }
     ],
     roles: []
   }
)
db.getRole("planCacheReadAll", { showPrivileges: true } );
db.grantRolesToUser( "diana", ["planCacheReadAll"] );
db.getUser("diana", { showPrivileges: true } );





// Create an Index Filter
use mynulldb
db.runCommand( { planCacheListFilters: "mynullcoll" } )
db.runCommand(
   {
      planCacheSetFilter: "mynullcoll",
      query: {"onefield": 1},
      indexes: [ "onefield_1"]
   }
)
db.runCommand( { planCacheListFilters: "mynullcoll" } )




// Redact logs
db.adminCommand(  { setParameter: 1, redactClientLogData : true  } )



// Obtain index usage stats in sharded clusters
use myshardeddatabase
db.myshardedcollection.aggregate( [{ $indexStats: {}}, {$group: { _id: "$name", ac: { $sum: "$accesses.ops" }}}])

// Find sharded collections, log in to the mongos and
use config
db.collections.find({} ,{"key" : 1 } )


// hint an index on aggregation
db.mycollection.aggregate([
    {"$match": {"year": { "$gt": 2010}, "countries": "Costa Rica"}},
    {"$sort": {"title":1}}],
  {"hint":{"countries": 1}});


// Get document size
Object.bsonsize({ "company": "MongoDB"})

// Extract the timestamp from an ObjectID
db.mycollection.findOne()._id.getTimestamp()



// Disable replication chaining
rsc = rs.conf()
rsc.settings.chainingAllowed = false;
rs.reconfig(rsc)


// move an unsharded database's primary shard
use admin
db.runCommand( { movePrimary : "123", to : "abc" } )


// monitor index creation status
// Note: Perform this operation during a maintenance window or off-peak hours
// Note:  Index creation speeds are dependent on a multitude of factors including available memory, disk iops, and the documents in question.
db.currentOp(
    {
      $or: [
        { op: "command", "query.createIndexes": { $exists: true } },
        { op: "none", ns: /\.system\.indexes\b/ }
      ]
    }
)
