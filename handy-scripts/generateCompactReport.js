var fmt = function (bytes) {
  var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes == 0) return '0 Byte';
  var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
  return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
}


var dbSizeReport = function (dbname, formatOutput) {
  var results = [];
  db.getSiblingDB(dbname).getCollectionNames().forEach(function (c) {
    var coll = db.getSiblingDB(dbname).getCollection(c);
    var s = coll.stats();
    var detail = {
      name: s.ns,
      size: s.size,
      storageSize: s.storageSize,
      reusableSpace: s["wiredTiger"]["block-manager"]["file bytes available for reuse"]
    };

    // check for mongos
    if (db.isMaster().msg == "isdbgrid") {
     // print("Detected mongos, adding stats from all the shards.")
      detail.reusableSpace = 0;
      db.adminCommand({ listShards: 1 }).shards.forEach(function (shard) {
        try {
          detail.reusableSpace += s["shards"][shard._id].wiredTiger["block-manager"]["file bytes available for reuse"];
        } catch (err) {
        //  print("Shard " + shard._id + " not found, skipping...");
        }
      })
    }
    results.push(detail); 
  });
  var totals = [0, 0, 0];
  print(["Namespace", "Uncompressed", "Compressed", "Reusable"].join(","))
  for (var i = 0; i < results.length; i++) {
    var row = results[i];
    if (formatOutput)
      print([row.name, fmt(row.size), fmt(row.storageSize), fmt(row.reusableSpace)].join(","))
    else
      print([row.name, row.size, row.storageSize, row.reusableSpace].join(","))
    totals[0] += row.size;
    totals[1] += row.storageSize;
    totals[2] += row.reusableSpace;
  }
  var dbs = db.getSiblingDB(dbname).stats();
  if (formatOutput) {
    print(["Total", fmt(totals[0]), fmt(totals[1]), fmt(totals[2])].join(","));
    print(["DB Stats", fmt(dbs.dataSize), fmt(dbs.storageSize)].join(","))
  } else {
    print(["Total", totals[0], totals[1], totals[2]].join(","));
    print(["DB Stats", dbs.dataSize, dbs.storageSize].join(","))
  }
}


db.getMongo().getDBs().databases.reduce(function (result, element) {
  if (["admin", "config", "local"].indexOf(element.name) < 0)
    result.push(element.name);
  return result;
}, []).forEach(function (name) {
  dbSizeReport(name, true);
});