// Switch to admin database and get list of databases.
db = db.getSiblingDB("admin");
dbs = db.runCommand({
    "listDatabases": 1
}).databases;

// Iterate through each database and get its collections.
dbs.forEach(function (database) {
    db = db.getSiblingDB(database.name);
    cols = db.getCollectionNames();
    // print("Database: " + db);
    // Iterate through each collection.
    cols.forEach(function (col) {
        // Do something with each collection.
        // s = db.coll.stats()
        ct = db.getCollection(col).count()
        print(db + "." + col + "\t" + ct); 
    });

});