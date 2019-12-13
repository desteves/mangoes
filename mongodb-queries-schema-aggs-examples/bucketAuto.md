# bucketAuto.md

Use bucketAuto to obtain an even-ish distribution of your data, e.g. from these X buckets, give me the ranges so as to obtain an even distribution.

## example 1

Use `bucketAuto` to be assign documents to different workers/process/thread.

```javascript

var my_doc = db.myCollection.findOne();

/*
my_doc

{
    _id: 123,
    trueFalseField: true,

    //...

    highCardinalityField: "alkfjseg124r"
}
*/

var total_workers = 50;

db.myCollection.aggregate( [
   {
     $bucketAuto: {
         groupBy: "$highCardinalityField",
         buckets: total_workers
     }
   }
] )
```
