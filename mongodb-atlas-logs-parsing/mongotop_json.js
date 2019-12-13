/////////////////////////////////////////////////
/////////////////////////////////////////////////
// mongotop output analysis already imported ///
/////////////////////////////////////////////////
/////////////////////////////////////////////////

var p = {
    "$project": {
        "_id": 0,
        "time": 1,
        "t": {
            "$objectToArray": "$totals"
        }
    }
};

var u = {
    "$unwind": "$t"
};


// print("TODO -- Add your own database name in the regex!!");

var m = {
    "$match": {
        "t.v.total.time": {
            "$gt": 0
        },
        "t.k": { "$regex": '^util.*' }
    }
};

var p2 = {
    "$project": {
        "time": 1,
        "ns": "$t.k",
        "tt": "$t.v.total.time",
        "ct": "$t.v.total.count"
    }
};

// sort by most expensive interval
var s = {
    "$sort": {
        "tt": -1
    }
};


db.mongotop.aggregate([p, u, m, p2, s]);


// sum the entire sample period, and sort by the the most expensive overall
// The line "interval: { $push: "$$ROOT" }," can be omitted for a quick summary
var g = {
    "$group": {
        "_id": "$ns",
        "interval": {
            $push: "$$ROOT"
        },
        "totalTime": {
            $sum: "$tt"
        },
        "totalCount": {
            $sum: "$ct"
        }
    }
};
var sg = {
    "$sort": {
        "totalTime": -1
    }
};
db.mongotop.aggregate([p, u, m, p2, g, sg]);

