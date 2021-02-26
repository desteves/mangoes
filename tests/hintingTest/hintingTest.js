//
// FILE: hintingTest.js
// ABOUT: Tests LOOPS by $sample(ing) the collection specified and checks which
//        index was selected for the specified QUERY_SHAPES.
// 
//        Works against sharded or RS cluster
//
// Run AS:
// replace URI, dbNAME, and collectionNAME
// mongo ${URI_TO_MONGOD/S} --eval 'load("hintingTest.js"); hintingTest("dbNAME", "collectionNAME");' | tee /tmp/hintingTest_$(date +%s).out
//
// Process hintingTest_*.out 
// Use sed/awk/wc to process the hintingTest_*.out file contents and get a count.


// here we go!


// Helpers -- 
// This particular customer has a **large** array out of which they're choosing a small number 
// of random values from the array to query upon + other static search params. 
// The array elements are "randonmly" picked to dynamically assemble the 
// queries during the hinting test.
pickValuesFromArrayField = function (pick = 3, arrayFieldName = "arrayFieldName") {
  // TODO -- move code from below here.
};

// Main Function
hintingTest = function (dbName = "test", collectionName = "test") {
  database = db.getSiblingDB(dbName);
  namespace = database.getCollection(collectionName);

  const SELECTED = 3;
  const LOOPS = 1; // ensure this is < 5% of the total documents in the collection to avoid COLLSCAN
  const ARRAYFIELD = "$arrayFieldName"
  // pickValuesFromArrayField(SELECTED, ARRAYFIELD)

  var SAMPLES = namespace.aggregate([
    { $sample: { size: LOOPS * SELECTED } },
    {
      $bucketAuto: {
        "groupBy": "$_id", // something randomish
        "buckets": LOOPS,
        "output":
          { "IN": { $push: ARRAYFIELD } }
      }
    },
    {
      $project: { "IN": 1, _id: 0 }
    }],
    { allowDiskUse: true });
  var QUERY_SHAPES = [ // these are the queries being tested with and without the hint. Add as many as needed.
    {
      FILTER: {
        "arrayFieldName": { $in: ["###"] }, // place holder for the dynamic array
        "dateRangeField": { $gte: new Date(1542130780000), $lte: new Date(1605289180000) }, // 2 years
        "staticField1": { $in: ["DONE"] },
        "staticField2": { $nin: ["A", "B", "C"] },
        "staticField3": { $ne: "Y" },
      },
      PROJECT: { "fieldA": 1, "fieldB": 1 },
      SORT: { "dateRangeField": -1, "staticField1": 1, "anotherDate": -1 },
      LIMIT: 50,
      MAXTIMEMS: 10000,
      HINT: "MyIndexNameToHintWith"
    }
  ];



  // Capture Stats before testing
  // ixStats = namespace.aggregate([{ $indexStats: {} }, { $group: { _id: "$name", ac: { $sum: "$accesses.ops" } } }, { $sort: { _id: 1 } }]);
  // printjson(ixStats);



  // MAIN LOOP
  while (SAMPLES.hasNext()) {
    var SAMPLE = SAMPLES.next();

  
    QUERY_SHAPES.forEach(function (QUERY_SHAPE) {

      // TEST AS-IS/ PHASE ONE
      // 1. build the query shape by replacing '###' with real values
      var GENERATED_FILTER = QUERY_SHAPE.FILTER;
      GENERATED_FILTER[ARRAYFIELD] = { "$in": SAMPLE.IN }

      // 2. clear the plan cache, the values in the query predicate are insignificant for this command
      namespace.getPlanCache().clearPlansByQuery(GENERATED_FILTER, QUERY_SHAPE.PROJECT, QUERY_SHAPE.SORT);
      
      // 3. run the query shape
      var result = {};
      try {
        var result = namespace.find(GENERATED_FILTER, QUERY_SHAPE.PROJECT).sort(QUERY_SHAPE.SORT).hint(QUERY_SHAPE.HINT).limit(QUERY_SHAPE.LIMIT).maxTimeMS(QUERY_SHAPE.MAXTIMEMS).batchSize(QUERY_SHAPE.LIMIT).explain("executionStats");
        result["queryPlanner"]["winningPlan"]["shards"].forEach(function (SHARD) {
          try {
            printjson({ "h": QUERY_SHAPE.HINT });
            printjson(SHARD["winningPlan"]["inputStage"]["inputStage"]["inputStage"]["inputStage"]); //;.inputStage.indexName or inputStages
          } catch (error) {
            print({ "e": "-999" });
          }
        });
        // printjson({ "FILTER": GENERATED_FILTER["patientInfo.patientAgn"], "PROJECT": QUERY_SHAPE.PROJECT, "SORT": QUERY_SHAPE.SORT,"RESULT": result.length, "HINT": QUERY_SHAPE.HINT });
      } catch (error) {
        // printjson(result);
        print({ "e": "-999" });
        // printjson({ "FILTER": GENERATED_FILTER, "PROJECT": QUERY_SHAPE.PROJECT, "SORT": QUERY_SHAPE.SORT,"RESULT": -999, "HINT": QUERY_SHAPE.HINT });
      }
      
      // 4. learn about the winning plan cache
      // var response = namespace.getPlanCache().getPlansByQuery(GENERATED_FILTER, QUERY_SHAPE.PROJECT, QUERY_SHAPE.SORT);
      // printjson(response);
    }); // end forEach
  } // end while
} // end of hint test


// Capture Stats at the end of testing to compare
// ixStats = namespace.aggregate([{ $indexStats: {} }, { $group: { _id: "$name", ac: { $sum: "$accesses.ops" } } }, { $sort: { _id: 1 } }]);
// printjson(ixStats);
