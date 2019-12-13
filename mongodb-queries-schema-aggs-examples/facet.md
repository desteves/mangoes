# facet.md

Manipulate a doc in X ways, account for it in multple ways, etc.

## Examples

### Percentiles

//TODO

### Anomaly buckets

In this example, we're creating anomaly buckets to determine how many times users had to refresh a given page wihthin a time window for a particular "session". We want to capture:

- how many users refreshed a page more than 3  times?
- how many users refreshed a page more than 5  times?
- how many users refreshed a page more than 10 times?

Note: The range sample period is omitted in this example, but pesudo code is provided.

1. Create some data to use for testing using mgenerate
    ```bash

    mgenerate --num 10000000 --port 8989 '{
    "sessionId": { "$number": [100, 999] },
    "userid":    { "$string": {"length": 3}},
    "userSessionStartTime": { "$date": ["2016-05-12", "2017-05-17"] }}'

    mgenerate --num 100000 --port 8989 '{
    "sessionId": { "$number": [100, 200] },
    "userid":   {"$choose": ["aZ4", "biA", "Ii6", "gUs", "wf2", "Liam", "Noah", "Ethan", "Mason", "Logan", "Jacob", "Lucas", "Jackson", "Aiden", "Jack", "James", "Elijah", "Luke", "William", "Michael", "Alexander", "Oliver", "Owen", "Daniel", "Gabriel", "Henry", "Matthew", "Carter", "Ryan", "Wyatt", "Andrew", "Connor", "Caleb", "Jayden", "Nathan", "Dylan", "Isaac", "Hunter", "Joshua", "Landon", "Samuel", "David", "Sebastian", "Olivia", "Emma", "Sophia", "Ava", "Isabella", "Mia", "Charlotte", "Emily", "Abigail", "Avery", "Harper", "Ella", "Madison", "Amelie", "Lily", "Chloe", "Sofia", "Evelyn", "Hannah", "Addison", "Grace", "Aubrey", "Zoey", "Aria", "Ellie", "Natalie", "Zoe", "Audrey", "Elizabeth", "Scarlett", "Layla", "Victoria", "Brooklyn", "Lucy", "Lillian", "Claire", "Nora", "Riley", "Leah"] },
    "userSessionStartTime": { "$date": ["2016-05-12", "2017-05-17"] }}'
    ```
2. Log into the MongoDB Shell via `mongo --port 8989`
3. Run the following code
    ```javascript

    sessionid = 100;
    /// threshold_b4 = 60 // minutes
    /// u_start = s.sessionStartTime + threshold_b4

    match_______0x0  =
    {
        $match: {
                sessionId: sessionid
                ///  userSessionStartTime: { $and : [
                ///                                    { $gte:  u_start },
                ///                                    { $lte:  sessionStopTime }
                ///                                  ]
                ///                         }

                }
    };

    // Each F5 is a document, group these and sort by the largest.
    sortbycount_0x1 = {  $sortByCount: "$userid" };

    // Eliminate all the irrelevant users -- defined as users who only have less than three F5s i.e, a count strictly less than 3.
    match_______0x2 =
    {
        $match: {
                count:   { $gte:  3 }
                }
    };

    // Stages to answer "how many users F5ed more than 0x3 times?."
    count________0x11 = { $count: "gte_0x3" };

    // Stages to answer "how many users F5ed more than 0x5 times?."
    match________0x21 =
    {
        $match: {
                count:   { $gte:  5}
                }
    };
    count________0x22 = { $count: "gte_0x5" };

    // Stages to answer "how many users F5ed more than 0xA times?."
    match________0x31 =
    {
        $match: {
                count:   { $gte:  10}
                }
    };
    count________0x32 = { $count: "gte_0xA" };

    // Depending on the thresholds for the various anomaly buckets, fill such per user F5s.
    facet_______0x3 =
    {
        $facet:
            {
                gte_0x3: [
                            count________0x11
                        ],
                gte_0x5: [
                            match________0x21,
                            count________0x22
                        ],
                gte_0xA: [
                            match________0x31,
                            count________0x32
                        ],

            }
    }

    // putting the pipeline together.
    pipeline =
    [
        match_______0x0,
        sortbycount_0x1,
        match_______0x2,
        facet_______0x3
    ]

    // the command to generate the report
    db.mgendata.aggregate( pipeline, { allowDiskUse: true})
    ```
4. Run the aggregation.
    ```javascript
    db.mgendata.aggregate( pipeline, { allowDiskUse: true})
    {
    "result": [
        {
        "gte_0x3": [
            {
            "gte_0x3": 82
            }
        ],
        "gte_0x5": [
            {
            "gte_0x5": 82
            }
        ],
        "gte_0xA": [
            {
            "gte_0xA": 68
            }
        ]
        }
    ],
    "ok": 1
    }
    ```