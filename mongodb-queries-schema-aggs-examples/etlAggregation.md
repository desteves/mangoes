# MongoDB Aggregation Framework ETL Examples

Using MongoDB's aggregation framekwork we can perform very powerful ETL queries. You don't need expensive, overengineered 3rd party solutions to get data into mongodb. Rather we take the approach to first dump "raw" data directly in MongoDB. The source in these example is normalized CSV files.

We then think about how the data will be consumed by our applications and come up with a denormalized schema design. Aggretaions and updates are applied to obtain the final form. Boooyaah!

Below we use aggregations to cover the following normalized relationshits for data, 1:1, 1:MANY, and MANY:MANY.

Note: The aggregation stages used below may require MongoDB 4.0+.

## Dumping your raws

The first step will be to import each table into a separate `raw<TableName>` collection. We do this via `mongoimport`

### 101 Example

```bash
################
################ Imports straightforward CSV files into MongoDB raw collections
################

echo "Creating sample CSV files"

echo "FIPSCODE,TIMESTAMP" > TableA.csv
echo "48015,20180305" >> TableA.csv

echo "_id,val" > TableB.csv
echo "20180305,AUSTIN" >> TableB.csv


for f in $(ls *.csv); do
    FILE="${f%.*}"
    mongoimport --host localhost:27017 --headerline --type csv --mode insert --ignoreBlanks --db etl --collection raw${FILE} ${f}
done


# verify data got imported
mongo etl --port 27017
> show tables
rawTableA
rawTableB
> db.rawTableA.find()
{ "_id" : ObjectId("5b741a745f66830eb5285a31"), "FIPSCODE" : 48015, "TIMESTAMP" : 20180305 }
> db.rawTableB.find()
{ "_id" : 20180305, "val" : "AUSTIN" }

```

### Need-to-edit-CSV-before-import Example

```bash
################
################ Imports |-delimited csv files into MongoDB raw tables
################

echo "Creating sample txt files"

echo "FIPSCODE|TIMESTAMP" > TableA.txt
echo "48015|20180305" >> TableA.txt

echo "_id|val" > TableB.txt
echo "20180305|AUSTIN" >> TableB.txt


echo "dealing with pipeline, |, as the delimeter for incoming,normalized data is a b!tch"
echo "we take a couple of prep steps to use be able to use the native mongodb utility -- mongoimport."
echo "converts tabs to spaces, pipeline separators to tabs, and inserts the file into MongoDB"
echo "no, it doesn't check for potentionally escaped pipes"

for f in $(ls *.txt); do
    FILE="${f%.*}"
    echo "Streaming ${f}"
    echo "convers existing tabs in to spaces, replaces tabs for pipes && imports to MongoDB. phew."
    tr "\t" " " < ${f} | tr "|" "\t" | mongoimport --type tsv --headerline --port 27017 -d etl -c raw${FILE}
done


# verify data got imported
mongo etl --port 27017
> db.rawTableA.txt.find()
{ "_id" : ObjectId("5b741afe5f66830eb5285a52"), "FIPSCODE" : 48015, "TIMESTAMP" : 20180305 }
> db.rawTableB.txt.find()
{ "_id" : 20180305, "val" : "AUSTIN" }

```

Okay, now all the data is in MongoDB but raw, let's get cooking.

## Denormalizing 1:1 relationships

Note: These examples embed the data. Use this schema design pattern after you've determined such suits. All the below examples are run directly from the MongoDB Shell.

### Two-Tables-One-Value 101 Example

```javascript

mongo etl --port 27017
var docA =  db.rawTableA.findOne();
docA;
// {
// 	"_id" : ObjectId("5b741a745f66830eb5285a31"),
// 	"FIPSCODE" : 48015,
// 	"TIMESTAMP" : 20180305
// //other fields not shown...
// }
var docB =  db.rawTableB.findOne();
docB;
// { "_id" : 20180305, "val" : "AUSTIN" }

/* $lookup

Links the two raw tables via the local/forgein fields.

The `from` represents the foreign table, the matched value of the specified fields will be embeded in the `as` field as an array.

In this case, the lookup behaves as a Left Outter Join.

*/

var I_LOOKUP = {
  "$lookup": {
    "from": "rawTableB",
    "localField": "FIPSCODE",
    "foreignField": "_id",
    "as": "matchedFields"
  }
};

/* $project

We use project to transform our document structure. This means, renaming feilds, bringing out an element in an array and converting a type to a string.

*/

var II_PROJECT = {
    "$project": {
        "_id": 0,
        // other fields renamed that are not shown
        "fips": "$FIPSCODE", //field rename
        "county": { //add a field that transforms the previous stage's generated field
            "$arrayElemAt": ["$matchedFields.val", 0]
        },
         "timestamp": { // renames field and coverts it to a string
            "$toString": "$TIMESTAMP"
        }
    }
};


/* $addFields

Introduce new fields to the existing document structure, if the field already exists the expression specified is applied.

In this case, we are converting a string to a date format.

*/
var III_PROJECT = {
    "$addFields": {
        "timestamp": { // convert string to ISODate
            "$dateFromString": {
                "dateString": "$timestamp",
                "format": "%Y%m%d",
                "timezone": "America/Denver",
                "onError": "$timestamp",
                "onNull": ""
            }
        }
    }
};

/* $out

This is the destination of where all our transformation will be written. Note: in some cases we have to iterate through various aggregations, in such case we may end up with temporary collections
*/

var IV_OUT = {
    // or this can be a temp collection if further transformations are required.
  "$out": "finalSchemaCollection"
};

var PIPELINE = [ I_LOOKUP, II_PROJECT, III_PROJECT, IV_OUT];
db.rawTableA.aggregate(PIPELINE);

db.finalSchemaCollection.findOne();
/*
{
    "_id": ObjectId("5b6c67b5a41a801f2cf4c8b8"),
    "county": "AUSTIN",
    "fips": 1003,
    "timestamp": ISODate("2018-03-05T06:00:00Z")
}
*/


```

### With-pesky-FK/PK-table Example

TODO

## More Advanced "T" Transformation Requirements

### Example: Filtering through historical records to obtain only the "acitve" ones

In this example, we need to maintain an "active" collection. Each day we have to sort through millions of __state__ event changes that occured accross a number of entities but only need to keep the most recent event per entity. Each event contains the full document and the applied operation as opposed to only the incrementals ie deltas.

```javascript

use etl
db.tempSchema.ensureIndex({ "entity_id": 1,  "time_of_event": -1});

var I_SORT = {
    "$sort": {
        "entity_id": 1,
        "time_of_event": -1
    }
};

var II_GROUP = {
    "$group": {
        "_id": "$entity_id",
        "most_recent_event": {
            "$first": "$$ROOT"
        }
    }
};

var III_REPLACE_ROOT = {
    "$replaceRoot": {
        "newRoot": "$most_recent_event"
    }
};

var IV_MATCH = {
    "$match": {
        "opertaion_id": {
            "$in": ["I", "U", "C"]  // only care about inserts, updates, or creates (ignores deletes per specific requirement)
        }
    }
};

var PIPELINE = [I_SORT, II_GROUP, III_REPLACE_ROOT, IV_MATCH];
var bulk = db.activeCollection.initializeUnorderedBulkOp();
var cursor = db.tempSchema.aggregate(PIPELINE, {
    allowDiskUse: true
});

var counter = 0;
cursor.forEach(function (doc) {
    const id = doc._id;
    // delete doc._id;

    bulk.find({
        "_id": id
    }).upsert().replaceOne({
        "$set": doc
    });

    counter++;
    if (counter % 2000 == 0) {
        try {
            result = bulk.execute();
        } catch (ex) {
            console.error(result.writeErrors);
            console.error(ex);
        } finally {
            bulk = db.activeCollection.initializeUnorderedBulkOp();
        }

    }
});

if (counter % 2000 != 0) {
    try {
        result = bulk.execute();
    } catch (ex) {
        console.error(result.writeErrors);
        console.error(ex);
    }
}
```