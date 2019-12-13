# Examples using `mgeneratejs` 

See the [npm website](https://www.npmjs.com/package/mgeneratejs) for `mgeneratejs`.
We use this utility to create semi-random, application-relevant documents that adhere to a given schema.

Note: This requires `nodejs` and `npm` to be installed. `mgeneratejs` can be installed via `npm install -g mgeneratejs`.

## Schema with  Attribution Lists

We are adding 100k documents to a local `mongod` running on `9999`.

- Save the following schema pattern to `template.json`
```json
{
    "domain": {
        "$choose": {
            "from": ["ABC", "123", "XYZ"],
            "weights": [10, 3, 1]
        }
    },
    "type": "$numberLong",
    "name": "$string",
    "loc": "$coordinates",
    "attributes": {
        "$array": {
            "of": {
                "key": "$name",
                "val": {
                    "$choose": {
                        "from": [ {"$integer": {"min": 0, "max": 100}}, "$date", "$coordinates", "$numberDecimal", "hello world string"]
                    }
                }
            },
            "number": {
                "$integer": {
                    "min": 1,
                    "max": 20
                }
            }
        }
    }
}
```

- Run mgenerate to load 100k docs as follows
`mgeneratejs --jsonArray -n 100000 template.json | mongoimport --jsonArray --port 9999 --drop -d mySampleDatabase -c mySampleCollection`


The `attributes` array will contain between 1 and 20 elements. Each element is a small key/value document. The `value` portion can be of various types such as an integer between 0 and a 100, a date, location coordinates, a decimal, or a fixed strig.