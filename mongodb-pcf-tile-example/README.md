# PCF MongoDB On Demand tile and Ops Manager example

## Install

* Download [MongoDB Enterprise Service for PCF](https://network.pivotal.io/products/mongodb-enterprise-service/)
* Go to your PCF Ops Manager -> Import a Product -> mongodb-on-demand-0.8.4.pivotal
* After message `Successfully added product`, click `+` next to MongoDB-On-Demand 0.8.4
* Click the tile `MongoDB-On-Demand`
* Configure the tile (example below)
* Go back to Installation Dashboard
* Apply Changes

### Example Configuration of "MongoDB-On-Demand"

#### AZ and Network Assignments

* Place singleton jobs in `AZ1`
* Balance other jobs in `AZ1` and `AZ2`
* Network `Services`
* Service Network `On-Demand`
* `SAVE`

*Note*: The selected networks were previously created via the `PCF Ops Manager Director` at `https://<URL>/infrastructure/networks/edit`

#### MongoDB-On-Demand

* MongoDB Ops Manager URL `http://mms.cloud`
* MongoDB Ops Manager username `admin@ldap.cloud`
* MongoDB Ops Manager API key `014087b9-87ff-4378-80a8-061e4c156e6d`
* MongoDB VM Type ``
* MongoDB disk type ``
* MongoDB availability zone(s)  `AZ1` and `AZ2`

*Note*: Test the Ops Manager API with a curl command or similar to ensure is working. (No smoke tests atm)

```bash
curl --user "admin@ldap.cloud:014087b9-87ff-4378-80a8-061e4c156e6d" --digest \
 --header "Accept: application/json" \
 --header "Content-Type: application/json" \
 --include \
 --request GET "http://mms.cloud/api/public/v1.0/groups?pretty=true"
```

*Note*: Ensure you have specified the protocol (ie `http` or `https`) as part of the `URL`.

#### Stemcell

A stemcell is a template from which Ops Manager creates the VMs needed for a wide variety of components and products.

`mongodb-on-demand` requires BOSH stemcell version 3421 ubuntu-trusty

* Go to Pivotal Network and download Stemcell 3421 ubuntu-trusty.
* Download Ubuntu Trusty Stemcell 3421.31, in my case for vSphere.
* Click `Import Stemcell`, select `bosh-stemcell-3421.31-vsphere-esxi-ubuntu-trusty-go_agent.tgz`

## Use

```bash
#######################################
### log in
cf login -a https://api.sys.<URL>.com -u admin  --skip-ssl-validation

#######################################

cf marketplace | grep mongo
# mongodb-odb                   standalone, replica_set, sharded_cluster   MongoDB Service

#######################################
### Create an instance of the MongoDB Enterprise Service. 
cf create-service mongodb-odb replica_set p-mongo-replset -c '{"version": "3.4.9-ent"}'
cf create-service mongodb-odb sharded_cluster p-mongo-replset -c '{"shards": 3, "replicas": 3, "config_servers": 3, "mongos": 2, "version": "3.4.9-ent"}'
cf create-service mongodb-odb standalone p-mongo-replset  -c '{"version": "3.4.9-ent"}'

#######################################
### Check that the service(s) was(were) created.
cf service p-mongo-replset
: ' Service instance: p-mongo-replset
Service: mongodb-odb
Bound apps:
Tags:
Plan: replica_set
Description: MongoDB Service
Documentation url:
Dashboard: http://mms.cloud/v2/5a0a21439234e254affceabe
'
cf service p-mongo-sharded
: ' Service instance: p-mongo-sharded
Service: mongodb-odb
Bound apps:
Tags:
Plan: sharded_cluster
Description: MongoDB Service
Documentation url:
Dashboard: http://mms.cloud/v2/5a0a240308b4b70676866ff6
'
cf service pcfmongos349e
: ' Service instance: pcfmongos349e
Service: mongodb-odb
Bound apps:
Tags:
Plan: standalone
Description: MongoDB Service
Documentation url:
Dashboard: http://mms.cloud/v2/5a0cf7099234e254af0bec12
'

#######################################
### Bind the service to an app.
cd ~/workspace/diana/pcfmongo/simple-nodejs-mongodb-app
cf login -a api.sys.pcf.cloud.<URL>.com -u admin -p  --skip-ssl-validation
cf push
: '
Using manifest file /Users/d/workspace/diana/pcfmongo/simple-nodejs-mongodb-app/manifest.yml

Starting app simple-nodejs-mongodb-app in org myorg / space prod as admin...
Creating container
Successfully created container
Downloading build artifacts cache...
Downloading app package...
Downloaded build artifacts cache (282B)
Downloaded app package (627.2K)
-----> Download go 1.9.1
-----> Running go build supply
-----> Nodejs Buildpack version 1.6.12
-----> Installing binaries
       engines.node (package.json): 6.11.x
       engines.npm (package.json): 5.5.x
-----> Installing node 6.11.5
       Download [https://buildpacks.cloudfoundry.org/dependencies/node/node-6.11.5-linux-x64-c7adcc32.tgz]
       Downloading and installing npm 5.5.x (replacing version 3.10.10)...
-----> Installing yarn 1.2.1
       Download [https://buildpacks.cloudfoundry.org/dependencies/yarn/yarn-v1.2.1-a16106e2.tar.gz]
       Installed yarn 1.2.1
-----> Creating runtime environment
       NODE_ENV=production
       NODE_HOME=/tmp/contents570173318/deps/0/node
       NODE_MODULES_CACHE=true
       NODE_VERBOSE=false
       NPM_CONFIG_LOGLEVEL=error
       NPM_CONFIG_PRODUCTION=true
-----> Restoring cache
       Loading 3 from cacheDirectories (default):
       - .npm (not cached - skipping)
       - .cache/yarn (not cached - skipping)
       - bower_components (not cached - skipping)
-----> Building dependencies
       Prebuild detected (node_modules already exists)
       Rebuilding any native modules
mongodb@2.2.33 /tmp/app/node_modules/mongodb
es6-promise@3.2.1 /tmp/app/node_modules/es6-promise
mongodb-core@2.1.17 /tmp/app/node_modules/mongodb-core
bson@1.0.4 /tmp/app/node_modules/bson
require_optional@1.0.1 /tmp/app/node_modules/require_optional
resolve-from@2.0.0 /tmp/app/node_modules/resolve-from
semver@5.4.1 /tmp/app/node_modules/semver
readable-stream@2.2.7 /tmp/app/node_modules/readable-stream
buffer-shims@1.0.0 /tmp/app/node_modules/buffer-shims
core-util-is@1.0.2 /tmp/app/node_modules/core-util-is
inherits@2.0.3 /tmp/app/node_modules/inherits
isarray@1.0.0 /tmp/app/node_modules/isarray
process-nextick-args@1.0.7 /tmp/app/node_modules/process-nextick-args
string_decoder@1.0.3 /tmp/app/node_modules/string_decoder
safe-buffer@5.1.1 /tmp/app/node_modules/safe-buffer
util-deprecate@1.0.2 /tmp/app/node_modules/util-deprecate
       Installing any new modules (package.json)
added 46 packages in 2.531s
-----> Caching build
       Clearing previous node cache
       Saving 3 cacheDirectories (default):
       - .npm (nothing to cache)
       - .cache/yarn (nothing to cache)
       - bower_components (nothing to cache)
-----> Running go build finalize
Exit status 0
Uploading droplet, build artifacts cache...
Uploading build artifacts cache...
Uploading droplet...
Uploaded build artifacts cache (280B)
Uploaded droplet (18.5M)
Uploading complete
Stopping instance aa92fe74-9f52-4baf-833c-d06840281554
Destroying container
Successfully destroyed container

1 of 1 instances running

App started


OK

App simple-nodejs-mongodb-app was started using this command `npm start`

Showing health and status for app simple-nodejs-mongodb-app in org myorg / space prod as admin...
OK

requested state: started
instances: 1/1
usage: 512M x 1 instances
urls: simple-nodejs-mongodb-app-unseeding-schlimazel.apps.pcf.cloud.oskoss.com
last uploaded: Mon Dec 4 20:51:33 UTC 2017
stack: cflinuxfs2
buildpack: https://github.com/cloudfoundry/nodejs-buildpack

     state     since                    cpu    memory          disk        details
#0   running   2017-12-04 02:52:43 PM   0.0%   14.7M of 512M   75M of 1G
'

cf apps
: '
name                        requested state   instances   memory   disk   urls
simple-nodejs-mongodb-app   started           1/1         512M     1G     simple-nodejs-mongodb-app-unseeding-schlimazel.apps.pcf.cloud.oskoss.com
'

cf env simple-nodejs-mongodb-app
:'
System-Provided:


{
 "VCAP_APPLICATION": {
  "application_id": "1be991b6-9eb3-4d23-9b20-883cbce541a5",
  "application_name": "simple-nodejs-mongodb-app",
  "application_uris": [
   "simple-nodejs-mongodb-app-unseeding-schlimazel.apps.pcf.cloud.oskoss.com"
  ],
  "application_version": "ca1c5f06-3275-425b-b7a5-b5dcad2a684c",
  "cf_api": "https://api.sys.pcf.cloud.oskoss.com",
  "limits": {
   "disk": 1024,
   "fds": 16384,
   "mem": 512
  },
  "name": "simple-nodejs-mongodb-app",
  "space_id": "cadc59f3-0faa-44d3-aff2-641926cf9d01",
  "space_name": "prod",
  "uris": [
   "simple-nodejs-mongodb-app-unseeding-schlimazel.apps.pcf.cloud.oskoss.com"
  ],
  "users": null,
  "version": "ca1c5f06-3275-425b-b7a5-b5dcad2a684c"
 }
}

No user-defined env variables have been set

No running env variables have been set

No staging env variables have been set
'


cf bind-service  simple-nodejs-mongodb-app p-mongo-replset
:'
Binding service p-mongo-replset to app simple-nodejs-mongodb-app in org myorg / space prod as admin...
OK
TIP: Use 'cf restage simple-nodejs-mongodb-app' to ensure your env variable changes take effect
'

cf env simple-nodejs-mongodb-app
:'
Getting env variables for app simple-nodejs-mongodb-app in org myorg / space prod as admin...
OK

System-Provided:
{
 "VCAP_SERVICES": {
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
 }
}

{
 "VCAP_APPLICATION": {
  "application_id": "1be991b6-9eb3-4d23-9b20-883cbce541a5",
  "application_name": "simple-nodejs-mongodb-app",
  "application_uris": [
   "simple-nodejs-mongodb-app-unseeding-schlimazel.apps.pcf.cloud.oskoss.com"
  ],
  "application_version": "ca1c5f06-3275-425b-b7a5-b5dcad2a684c",
  "cf_api": "https://api.sys.pcf.cloud.oskoss.com",
  "limits": {
   "disk": 1024,
   "fds": 16384,
   "mem": 512
  },
  "name": "simple-nodejs-mongodb-app",
  "space_id": "cadc59f3-0faa-44d3-aff2-641926cf9d01",
  "space_name": "prod",
  "uris": [
   "simple-nodejs-mongodb-app-unseeding-schlimazel.apps.pcf.cloud.oskoss.com"
  ],
  "users": null,
  "version": "ca1c5f06-3275-425b-b7a5-b5dcad2a684c"
 }
}

No user-defined env variables have been set

No running env variables have been set

No staging env variables have been set
'

cf restage simple-nodejs-mongodb-app

In your browser, go to the random route generated, (eg, simple-nodejs-mongodb-app-unseeding-schlimazel.apps.pcf.cloud.oskoss.com)



#######################################
### Add users

cf create-service-key pcfmongos349e pcfmongos349e-key
cf service-key pcfmongos349e pcfmongos349e-key
# Getting key pcfmongos349e-key for service instance pcfmongos349e as admin...
: ' {
 "database": "default",
 "password": "d936e0f372a9ae078d3a952a26f938f0",
 "servers": [
  "10.0.5.1:28000"
 ],
 "uri": "mongodb://pcf_c5032fcec2dff4510077018fb2a11eec:d936e0f372a9ae078d3a952a26f938f0@10.0.5.1:28000/default?authSource=admin",
 "username": "pcf_c5032fcec2dff4510077018fb2a11eec"
}
'

cf create-service-key p-mongo-replset  pmr-key
cf service-key p-mongo-replset pmr-key
: 'Getting key pmr-key for service instance p-mongo-replset as admin...
{
 "database": "default",
 "password": "952a0d5fa7b11219714185b89b5aea3a",
 "servers": [
  "10.0.5.3:28000",
  "10.0.5.0:28000",
  "10.0.5.4:28000"
 ],
 "uri": "mongodb://pcf_65a2ced0c2fe8a220798227ab673a8fe:952a0d5fa7b11219714185b89b5aea3a@10.0.5.3:28000,10.0.5.0:28000,10.0.5.4:28000/default?authSource=admin",
 "username": "pcf_65a2ced0c2fe8a220798227ab673a8fe"
}
'

### *Note*: This will create a user in the admin database with the following:
: '
{
  "_id": "admin.pcf_c5032fcec2dff4510077018fb2a11eec",
  "user": "pcf_c5032fcec2dff4510077018fb2a11eec",
  "db": "admin",
  "roles": [
    {
      "role": "userAdmin",
      "db": "admin"
    },
    {
      "role": "dbAdmin",
      "db": "admin"
    },
    {
      "role": "readWrite",
      "db": "admin"
    },
    {
      "role": "userAdmin",
      "db": "default"
    },
    {
      "role": "dbAdmin",
      "db": "default"
    },
    {
      "role": "readWrite",
      "db": "default"
    }
  ]
}
'

#######################################
### MongoShell Login
# get connection string from Ops Manager
mongo 10.0.5.1:28000 -u admin --authenticationDatabase admin -p admin
# get the password

#######################################
### Delete the service
cf delete-service p-mongo-sharded
cf delete-service p-mongo-replset

```