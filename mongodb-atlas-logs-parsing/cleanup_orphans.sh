#!/bin/sh
# set -ex

# RUN AS:
# bash cleanup_orphans.sh


# This script ensures all migrations have been cleaned up.
# Extra documents may appear during migrations when doing count()
# A workaround to get accurate counts is to ensure all migrations have been cleaned up and no migrations are active. 


# Gets a list of all the primaries in the sharded cluster
# calls getS.py
# outputs primaries.txt
function get_primaries () {
    # if [ ! -f primaries.txt ]; then
    echo "Generating primaries.txt ..."
    python getS.py -p -U ${USER} -P ${PASS} -H ${HOST}  > primaries.txt
    # else
        # echo "File primaries.txt is already created, to recreate please remove it and rerun."
    fi
}

# Gets a list of all the sharded collections in the sharded cluster
# calls getS.py
# outputs collections.txt
function get_sharded_collections () {
    # if [ ! -f collections.txt ]; then
    echo "Generating list of sharded collections.txt ..."
    python getS.py -c -U ${USER} -P ${PASS} -H ${HOST}  > collections.txt
    # else
        # echo "File collections.txt is already created, to recreate please remove it and rerun"
    fi
}

# Iterates through every shard's primary and runs the cleanupOrphaned for each sharded collection.
# https://docs.mongodb.com/manual/reference/command/cleanupOrphaned/
# db.runCommand( {
#    cleanupOrphaned: "<database>.<collection>",
#    startingFromKey: minKey,
#    secondaryThrottle: <boolean>,
#    writeConcern: <document>
# } )
function cleanup_orphaned () {
    for p in $(cat primaries.txt); do
        for c in $(cat collections.txt); do
            echo "$p $c"
            # mongo --quiet  "mongodb://${p}/admin" --ssl --authenticationDatabase admin --username ${USER} --password ${PASS}  --eval "db.runCommand( { cleanupOrphaned: \"$c\" });"
        done
    done
}



function main () 
{
    if [ ! -f environment.cfg ]; then
        echo "Please set up the env variables in environment.cfg"
    else 
        # TODO Check if the file is not present, then download
        curl -O https://raw.githubusercontent.com/desteves/atlas/master/getS.py
        source environment.cfg
        get_primaries
        get_sharded_collections
        cleanup_orphaned
    fi
}


main
exit