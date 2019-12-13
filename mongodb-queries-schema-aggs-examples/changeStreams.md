# Change Streams




## 101

- Adds a watch to the namespace `cstest.collection`.
- This is a namespace level change stream that's 3.6/4.0 compatible.

```
cat watch.js

while( true) 
{
  var cur =  db.getSiblingDB("cstest").collection.watch();
  while (!cur.isExhausted())
  {
    if (cur.hasNext())
    {
      print (JSON.stringify(cur.next(), null, 2));
    }
}

print ("exhausted cursor");

}
```


## Advanced Filters


- Adds a filtered watch to the namespace `cstest.collection`.
- This is a namespace level change stream that's 3.6/4.0 compatible.


The following example satisfies the requirements for a given namespace:

- Accept all inserts.
- Accept only those updates that __don't__ exclusively affect `ROOT_LEVEL_FIELD_TO_SKIP_scalar` and `ROOT_LEVEL_FIELD_TO_SKIP_subdoc`

```bash

# Example run
mongo cstest --quiet --port 9999 < watch_with_pipe.js
```

Contents of `watch_with_pipe.js`

```javascript

//works with inserts or qualified updates as per the req's above.


while( true) {

var ROOT_LEVEL_FIELD_TO_SKIP_scalar = "scalar"; // a string
var ROOT_LEVEL_FIELD_TO_SKIP_subdoc = "subdoc"; // a complex nested subdocument
var PIPELINE = [
  { "$match"    : { "operationType" : { "$in": [ "update", "insert"] }  }},

// need to array up the updated fields to do any meaningful operations on it.
  { "$addFields": {
      "updatedFields": { "$objectToArray": "$updateDescription.updatedFields" },
  }},

// extract the fields that change, skipping those defined above in ROOT_LEVEL*
  { "$addFields": {
      "wantedFields": {
        "$filter": {
          input: "$updatedFields.k",
          as: "fieldname",
          cond: { "$and": [
             { "$eq": [ "$$fieldname", { $ltrim: { input: "$$fieldname",  chars: ROOT_LEVEL_FIELD_TO_SKIP_subdoc } } ] },
             { "$ne": [ "$$fieldname", ROOT_LEVEL_FIELD_TO_SKIP_scalar ] }
          ] }
        }
      }
    }
  },

// handle the null when operationType is an insert
  { "$addFields": { "wantedFieldsSize": { "$size": { "$ifNull": [ "$wantedFields", ["operationType==insert"] ] } }}},

// only receive events that contain updates not exclusive to fields ROOT_LEVEL* ||  are inserts.
  { "$match"    : { "wantedFieldsSize": { "$gt" : 0}}},

// clean up the mess, dont send it to the application
  { "$project"  : {
    "wantedFieldsSize": 0,
    "wantedFields": 0,
    "updatedFields": 0,
    }},
];

print ( "Starting a change stream watch with the following pipeline " );
print (JSON.stringify(PIPELINE, null, 2));
var cur =  db.getSiblingDB("cstest").collection.watch(PIPELINE);
while (!cur.isExhausted()){
    if (cur.hasNext()){
    print (JSON.stringify(cur.next(), null, 2));
   }
}

print ("exhausted cursor, trying again...  ");

}
```
