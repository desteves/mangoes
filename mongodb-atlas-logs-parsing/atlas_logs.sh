#!/bin/sh
# set -ex


# RUN AS:
# bash atlas_logs.sh

### https://docs.atlas.mongodb.com/reference/api/logs/
### GET /api/atlas/v1.0/groups/{GROUP-ID}/clusters/{HOSTNAME}/logs/mongodb.gz

# /////////////////////////////////////////////////////////////////////////////
# Gets Atlas logs and processes them
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
    # if [ ! -f primaries.txt ]; then
    echo "Generating primaries.txt ..."
    python getS.py -p -U ${USER} -P ${PASS} -H ${HOST}  | cut -f1 -d':' > primaries.txt
    # fi
}


# Calls the Atlas REST API to grab logs from a given window
# Parses the logs using mtools
# outputs [#].log [#].con and [#].qrs for each shard.
function get_and_parse_logs () 
{
    for p in $(cat primaries.txt); do
        FILE=$(echo ${p} | cut -f4 -d'-')
        echo "Getting the log file for ${p} as ${FILE}.log.gz"
        http --json --auth "${ATLAS}:${KEY}" --auth-type digest GET "https://cloud.mongodb.com/api/atlas/v1.0/groups/${GROUP}/clusters/${p}/logs/mongodb.gz?startDate=${start}&endDate=${end}"  --output ${FILE}.log.gz 
        
        echo "Deflating the gz log file ..."
        gzip -df ${FILE}.log.gz 

        echo "Processing the log file with mtools (this part takes time)..."
        mloginfo --connstats --no-progressbar ${FILE}.log > ${FILE}.con
        mloginfo --queries   --no-progressbar ${FILE}.log > ${FILE}.qrs
    done

    if [ $(cat primaries.txt | wc -l ) -gt 1 ]; then
        echo "Merging the log files (this can take a while)"
        FILE=all
        mlogfilter [0-9]*.log | cut -f2- -d' ' >  ${FILE}.log
        echo "Processing the log file with mtools (this part takes time)..."
        mloginfo --connstats --no-progressbar ${FILE}.log > ${FILE}.con
        mloginfo --queries   --no-progressbar ${FILE}.log > ${FILE}.qrs
    fi
}


source environment.cfg
get_primaries
get_and_parse_logs
exit