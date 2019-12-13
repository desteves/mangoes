#!/bin/sh
# set -ex

# RUN AS:
# bash get_namespaces_in_shards.sh

# /////////////////////////////////////////////////////////////////////////////
# Get a distribution of namespaces along with counts in Sharded environments
# Note: Meant to be run against an Atlas Cluster, otherwise update connection.
# /////////////////////////////////////////////////////////////////////////////
# Example contents of get_namespaces_in_shards.sh.cfg file:
# USER="admin"
# PASS="admin"
# HOST="localhost"

# Gets a list of all the primaries in the sharded cluster
# calls getS.py
# outputs primaries.txt
function get_primaries ()
{
    # if [ ! -f primaries.txt ]; then
    echo "Generating primaries.txt ..."
    python getS.py -p -U ${USER} -P ${PASS} -H ${HOST}  > primaries.txt
    # fi
}

# Iterates through the primaries, getting the count of each namespace
# calls get_namespaces.js
# outputs namespaces.txt
function list_namespaces () 
{
    # Connect to each shard and get list of dabase.collection
    echo "DATABASE.COLLECTION           COUNT"
    for p in $(cat primaries.txt); do
        echo "Primary: ${p}"
        mongo --quiet  "mongodb://${p}/admin" --ssl --authenticationDatabase admin --username ${USER} --password ${PASS} < get_namespaces.js | tee namespaces.txt
    done
    
}

# Does an sh.status and parses the output to get a list of the sharded collections
# outputs shardedcollections.txt
function parse_sh_status () 
{
    # Parse sh.status to get list of sharded collections via the mongos
    mongo --quiet  "mongodb+srv://${HOST}/config" --ssl --authenticationDatabase admin --username ${USER} --password ${PASS} --eval "sh.status(true)" > shstatus.txt
    cat shstatus.txt | grep  -B1 "shard key:" |  sed 's/--//g'  | sed 's/shard key://g' |  awk '{$1=$1}1' | paste -d' ' - - - | tee shardedcollections.txt
}


# MAIN
source environment.cfg
get_primaries
list_namespaces
parse_sh_status
exit
