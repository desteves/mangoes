#!/bin/sh
# set -ex

# RUN AS:
# bash set-log-everything.sh

# /////////////////////////////////////////////////////////////////////////////
# Sets the logging level of each node in the primaries.txt file to 100 (milliseconds)
# Note: Meant to be run against an Atlas Cluster, otherwise update.
# /////////////////////////////////////////////////////////////////////////////
# Example contents of atlas_logs.sh.cfg file:
# USER="admin"
# PASS="admin"
# HOST="localhost"

# Gets a list of all the primaries in the sharded cluster
# calls getS.py
# outputs primaries.txt
function get_primaries ()
{
#    if [ ! -f primaries.txt ]; then
    echo "Generating primaries.txt ..."
    python getS.py -p -U ${USER} -P ${PASS} -H ${HOST}  | cut -f1 -d':' > primaries.txt
#    fi
}

# Iterates through the primaries, setting the logging level to the argument specified.
# calls get_namespaces.js
# outputs namespaces.txt
function set-log () 
{
    # Connect to each shard and get list of dabase.collection
    for p in $(cat primaries.txt); do
        echo "Logging back to default for ${p}"
        mongo --quiet  "mongodb://${p}/admin" --ssl --authenticationDatabase admin --username ${USER} --password ${PASS} --eval "db.setProfilingLevel(0, 100);"
    done
    
}

source environment.cfg
set-log
exit
