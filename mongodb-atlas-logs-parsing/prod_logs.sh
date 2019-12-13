#!/bin/sh
# set -ex

# RUN AS:
# bash prod_logs.sh
# bash prod_logs.sh get_logs
# bash prod_logs.sh parse_logs
# bash prod_logs.sh get_mdiag

# /////////////////////////////////////////////////////////////////////////////
# Gets "production" logs, uploads to S3, &&  processes them.
#  - The production system is only accessible via a jumbox (where this script runs)
#  - The cluster has no internet access
#  - Logs are encrypted
#  - Logs are uploaded to an S3 bucket
# /////////////////////////////////////////////////////////////////////////////


# Example contents of prod_logs.sh.cfg file:
# USER="admin"
# PASS="admin"
# HOST="localhost"
# LOGDIR=/log     ## Directory for the log files
# MONGOSDIR=/data/mongos
# DATADIR=/data
# NUMLOG=3        ## Number of most recent log files to upload
# S3_KEY=         ## AWS S3 bucket to upload the file
# S3_AWS=         ## AWS S3 bucket to upload the file
# S3_ENC=         ## AWS S3 bucket to upload the file
# S3_ACL=         ## AWS S3 bucket to upload the file
# S3_POL=         ## AWS S3 bucket to upload the file
# S3_SIG=         ## AWS S3 bucket to upload the file
# S3_URL=         ## AWS S3 bucket to upload the file
# JUMPBOX=$(hostname)
# LOGDIR=/log/
# NUMLOG=1
# USER=$(whoami)


# Create primaries.txt example
# cat <<EOF > primaries.txt
# mongod.region-az.env.company
# mongod.region-az.env.company
# mongod.region-az.env.company
# EOF


# Checks we have a list of all the primaries in the sharded cluster
function is_primaries ()
{
    if [ ! -f primaries.txt ]; then
        echo "Please create a primaries.txt file with a list of all primaries..."
        echo "Exiting now."
        exit 1
    else
        echo "Using primaries.txt"
    fi
}


# Uploads the log to S3
#  upload_s3 $1=TARZ.enc
function upload_s3()
{
    curl -F "key=${S3_KEY}\${filename}" \
         -F "AWSAccessKeyId=${S3_AWS}" \
         -F "acl=${S3_ACL}" \
         -F "x-amz-server-side-encryption=${S3_ENC}" \
         -F "policy=${S3_POL}" \
         -F "signature=${S3_SIG}" \
         -F "file=@$1" \
         ${S3_URL}

}

# getlog $1=LOGDIR $2=NUMLOG $3=$TARZ
function getlog {
    cd ${1}
    echo "Zipping ${2} most recent logs for ${3} (this can take a while)"
    tar -czf $3 $(ls -t | head -${2} | tr '\n' ' ') 
}

# dellog $1=$TARZ
function delfile()
{
    echo "Removing $1 file..."
    rm -f $1
}

# From the jumpbox, ssh to each shard's primary and scp the tar logs.
function get_logs () 
{
    is_primaries
    DATE=$(date +%s)
    for p in $(cat primaries.txt); do
        TARZ="/tmp/${p}_${DATE}_logs.tar.gz"
        
        echo "Generating $TARZ"
        ssh $p "$(typeset -f getlog); getlog $LOGDIR $NUMLOG $TARZ"
    
        echo "Moving $TARZ to $JUMPBOX"
        scp  ${USER}@${p}:${TARZ}  .     

        echo "Removing $TARZ from $p"
        ssh $p "$(typeset -f delfile); delfile $TARZ"

        echo "Encrypting the $TARZ file"
        openssl enc -aes-256-cbc -in ${TARZ} -out ${TARZ}.enc -pass pass:${PASS}

        # TEST - upload to S3 (for staging, otherwise move locally then upload)
        echo "Uploading encrypted $TARZ from $JUMPBOX to $S3_URL"
        echo "Note: Let it fail if jumbox has no internet access"
        upload_s3 ${TARZ}.enc
        
        echo ""
    done

    echo "DONE"
}

# TODO TEST THIS \/\/\/\/\\/\/\/\/
# function download_from_jumpbox()
# {
#     scp ${USER}@${JUMPBOX}:~/*.enc  .
# }


# TODO TEST THIS \/\/\/\/\\/\/\/\/
# # getlog $1=DATADIR  $2=JUMPBOX $3=DATE
# function getdiagnostic {

#     FILE=$(hostname)
#     TARZ="/tmp/${FILE}_${3}_diag.tar.gz"

#     cd /tmp/
#     echo "Zipping diagnostic data for ${FILE}"
#     tar -czf $TARZ ${1}/diagnostic.data

# }

# From the jumpbox, ssh to each shard's primary and scp the tar diagnostics.
# function get_diagnostics () 
# {
#     # is_primaries
#     # for p in $(cat primaries.txt); do
#     #     echo "Getting diagnostics for $p"
#     #     ssh $p "$(typeset -f getdiagnostic); getdiagnostic $DATADIR $JUMPBOX"
#     # done
# }

# decrypt_file $1=TARZ.enc $2=index
function decrypt_file()
{
    openssl enc -d -aes-256-cbc -in $1 -pass pass:${PASS} -out ${2}.tar.gz
}

# outputs [#].log [#].con and [#].qrs for each shard.
function parse_local_downloaded_ecrypted_logs()
{
    # Works in $PWD
    # Ru this after downloading the logs from S3 to local, current folder
    i=0
    for FILE in $(ls *.enc);  do
        echo "Decrypting $FILE"
        decrypt_file $FILE $i
        tar -xzf ${i}.tar.gz 

        # If we concatenated more than one file, clean up..
        if [ $(ls mongodb.log* | wc -l ) -gt 1 ]; then
            # This assumes the logs themselves are not compressed
            echo "Merging the log files (this can take a while)"
            mlogfilter mongodb.log* > ${i}.log

            cat ${i}.log | cut -f2- -d' ' > ${i}.log_fix
            mv ${i}.log_fix ${i}.log
        fi

        echo "Processing connection stats (this can take a while)"
        mloginfo --connstats ${i}.log > ${i}.con
        echo "Processing query stats (this can take a while)"
        mloginfo --queries ${i}.log > ${i}.qrs


        echo "Cleaning up temp files"
        rm -f $FILE ${i}.tar.gz mongodb.log*


        let i=i+1 

    done
}




# MAIN
# source {0}.cfg
# for var in "$@"
# do
#     $var
# done
exit