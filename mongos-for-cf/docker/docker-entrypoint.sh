#!/bin/bash


set -eu

echo "Configuring yum repo"

cat <<EOF > /etc/yum.repos.d/mongodb-enterprise-4.2.repo
[mongodb-enterprise-4.2]
name=MongoDB Enterprise Repository
baseurl=https://repo.mongodb.com/yum/redhat/$releasever/mongodb-enterprise/4.2/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc
EOF

echo "Downloading mongos from ${URL}"
yum install -y mongodb-enterprise-mongos-4.2.6




echo "Starting mongos"

mongos --configdb <configReplSetName>/cfg1.example.net:27019,cfg2.example.net:27019,cfg3.example.net:27019 --bind_ip localhost,<hostname(s)|ip address(es)>


# COPY mongodb-linux-x86_64-enterprise-rhel70-3.6.9/bin/mongos ${H}
 #\
    # && curl -OL http://xxx.yyyyy.com:8080/download/agent/automation/ 
#COPY . ${H}

# COPY automation-mongod.conf ${H}
# COPY agentconfig.yaml ${H}
# RUN mkdir -p  ${H}/tls /mongodata/logs 
# COPY tls/* ${H}/tls/