# Quick Performance Test && Keyhole Analysis

## test

```bash
cat <<EOF > template.json


EOF


mgeneratejs --jsonArray -n 1000000 template.json | mongoimport --jsonArray --port 27017 --drop -d shield -c agents
```

## view


```json

    // { "$addFields": {"superpower.total_abilities": {"$size": "$superpower.ability"}}},
    // { "$unwind": "$superpower"},
    // { "$addFields": {"superpower.total_abilities": {"$size": "$superpower.ability"}}},
    // {
    //     "$project": {
    //         "superpower": 0
    //     }
    // }
    // { "$group": { "_id": "$_id", 
    //     "name": { "$first": "$name" },
    //     "agentid": { "$first": "$agentid" },
    //     "domain": { "$first": "$domain" },
    //     "total_countries_traveled": { "$first": "$total_countries" },
    //     "total_superpowers": { "$sum": "$total_abilities"},
    // }}


// 2020-07-04T20:09:48.168-0400 E QUERY    [thread1] Error: command failed: {
// 	"ok" : 0,
// 	"errmsg" : "Exceeded memory limit for $group, but didn't allow external sort. Pass allowDiskUse:true to opt in.",
// 	"code" : 16945,
// 	"codeName" : "Location16945"
// } : aggregate failed :

// db.agents.aggregate(PIPELINE, { "allowDiskUse": true});

```

```javascript




/// VIEW
var PIPELINE = [
    {
        "$match": {"superpower.category" : { "$in": [  "psychic", "physical", "bio"]}}
    },
    {
         "$addFields": { "total_countries": { "$size" : "$traveled.countries"}},
    },
    { "$project": {
        "visa": 0,
        "born": 0,
        "photo": 0,
        "traveled": 0,
        "lastloc": 0
    }}
];
db.agents.createIndex({ "name": 1});
db.agents.createIndex( { "superpower.category": 1 });
db.createView("agentsView3", "agents", PIPELINE );

var start = new Date().getTime();
for ( i=0; i<1000; ++i) {
    var cur = db.agentsView3.find({ total_countries: { $eq: i%20 } })
    while (cur.hasNext()){
        cur.next();
    }
}
var end = new Date().getTime();
var time = end - start;
alert('Execution time: ' + time);



/// $out
var PIPELINE = [
    {
        "$match": {"superpower.category" : { "$in": [  "psychic", "physical", "bio"]}}
    },
    {
         "$addFields": { "total_countries": { "$size" : "$traveled.countries"}},
    },
    { "$project": {
        "visa": 0,
        "born": 0,
        "photo": 0,
        "traveled": 0,
        "lastloc": 0
    }}, 
    { "$out": "agentsOut"}
];


var start = new Date().getTime();
for ( i=0; i<10000; ++i) {
    var cur = db.agentViews.find({ total_countries: { $eq: i%20 } })
}
var end = new Date().getTime();
var time = end - start;
print('Execution time: ' + time);

8+17+13+12+13x3+14+36+19+11+31+10+15

   // while (cur.hasNext()){
    //     cur.next();
    // }
```



