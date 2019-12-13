#! /bin/sh

export VCAP_SERVICES='{
  "mongodb-odb": [
   {
    "credentials": {
     "database": "default",
     "password": "0ab80c9ddf78e802ffddcbe0f023f601",
     "servers": [
      "10.0.5.4:28000",
      "10.0.5.0:28000",
      "10.0.5.3:28000"
     ],
     "uri": "mongodb://pcf_b6b4ffbd5c5548ea029e1f2666123c1c:0ab80c9ddf78e802ffddcbe0f023f601@10.0.5.4:28000,10.0.5.0:28000,10.0.5.3:28000/default?authSource=admin",
     "username": "pcf_b6b4ffbd5c5548ea029e1f2666123c1c"
    },
    "label": "mongodb-odb",
    "name": "p-mongo-replset",
    "plan": "replica_set",
    "provider": null,
    "syslog_drain_url": null,
    "tags": [
     "mongodb"
    ],
    "volume_mounts": []
   }
  ]
 }'

echo $VCAP_SERVICES | jq .
npm start
