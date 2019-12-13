#!/bin/sh
# set -ex


# RUN AS:
# bash atlas_rs_logs.sh

### https://docs.atlas.mongodb.com/reference/api/logs/
### GET /api/atlas/v1.0/groups/{GROUP-ID}/clusters/{HOSTNAME}/logs/mongodb.gz

# /////////////////////////////////////////////////////////////////////////////
# Gets Atlas logs and processes them
# Note: Meant to be run against an Atlas Replica Set Cluster, otherwise update.
# /////////////////////////////////////////////////////////////////////////////

# Calls the Atlas REST API to grab logs from a given window
# Parses the logs using mtools
# outputs [#].log [#].con and [#].qrs for each node listed in primaries.txt.
function get_and_parse_logs () 
{
    for p in $(cat primaries.txt); do
        FILE=$(echo ${p} | cut -f1 -d'0')
        echo "Getting the log file for ${p} as ${FILE}.log.gz"
        http --json --auth "${ATLAS}:${KEY}" --auth-type digest GET "https://cloud.mongodb.com/api/atlas/v1.0/groups/${GROUP}/clusters/${p}/logs/mongodb.gz?startDate=${start}&endDate=${end}"  --output ${FILE}.log.gz 
        
        echo "Deflating the gz log file ..."
        gzip -df ${FILE}.log.gz 

        echo "Processing the log file with mtools (this part takes time)..."
        mloginfo --connstats --no-progressbar ${FILE}.log > ${FILE}.con
        mloginfo --queries   --no-progressbar ${FILE}.log > ${FILE}.qrs
    done
}

source environment.cfg
get_and_parse_logs
exit
