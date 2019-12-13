#!/bin/sh
# set -ex

# RUN AS
# bash mongotop_json.sh

# //////////////////////////////////////////////////////////////////////////
# Runs mongotop &&
# Fixes mongotop --json output to be mongoimport/mongod friendly:
#  - rename all field that contains "." or ":" chars (mostlty for FQDNs) 
# 
# NOTE: We assume the following is true (update as necessary):
#  - FQDN naming convention. We assume the character after the '.' is [a-zA-Z]
#  - The PORT numbers are at least 4 characters in length.
#  - *Anything* that matches the above patterns will be replaced accordingly.
# /////////////////////////////////////////////////////////////////////////////
# Example contents of cfg file
# MONGODB_URI="mongodb://localhost:27017/admin"
# ROW_COUNT=32400
# INTERVAL_IN_SECONDS=30
# FILE=mongotop.json

# run mongotop for desired amount of time as specified in the cfg
function run ()
{
    echo "running mongotop (this may take a while)"
    nohup mongotop --uri $MONGODB_URI --rowcount $ROW_COUNT --json $INTERVAL_IN_SECONDS > ${FILE}
    echo "cleaning up mongotop output file"
    sed -i '' -e "s;\.\([a-zA-Z]\);_\1;g"  -e "s;:\([0-9]\{4,\}\);_\1;g"  $FILE
}

# Launches a small standalone mongod on port 8989 and loads the mongotop output
function load ()
{
    if [ "$(ps aux | grep mongo | grep -c 8989)" -eq "0" ]; then
        echo "launching mongod on 8989"
        mkdir -p /tmp/mongostat/data
        mongod --port 8989 --dbpath /tmp/mongostat/data --fork --quiet --logpath /tmp/mongostat/mongod.log --wiredTigerCacheSizeGB .5
    fi

    echo "running mongoimport"  
    mongoimport --port 8989 -d util -c mongotop --drop ${FILE}
}

# Runs a handful of queries against the mongotop data
function analyze()
{
    # TODO Add your own
    echo "analyzing results"
    mongo  util --quiet --host localhost --port 8989 --eval "db.mongotop.count()"
    # mongo  util --quiet --host localhost --port 8989 < mongotop_json.js
}


# MAIN
source environment.cfg
run
load
analyze
exit
