# Configure CentOS 7 VMs for MongoDB Ops Manager

Steps here include (not in strict order):

- Configure VM networking in the homelab.
- Adds MongoDB Ops Manager's internal databases (AppDB and Blockstore).
- Configures the Backup Daemon.
- Configures HTTP Service

![MMS Homelab](https://github.com/desteves/mms/blob/master/mms.svg "Homelab MMS Architecture")

More details on the purpose of these components can be found [here](https://docs.opsmanager.mongodb.com/current/core/system-overview/)

## Configure the network

- TODO: Use internal `dnspal` application to add EdgeRouter Lite - EdgeOS entries.
- See `00_vcenter.md`
- Check all hostnames/IPs are resolvable

  ```bash
  nslookup <IP>
  nslookup <HOSTNAME>
  arp -a
  ```

- [Optional] Add RSA Keys
  - `ssh-keygen -t rsa` on every host
  - From __one__ of the hosts add the public key of all other hosts
    ```bash
    ssh root@mms.cloud
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    ssh mms-x.cloud   cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    ssh mms-xi.cloud  cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    scp ~/.ssh/authorized_keys mms-x.cloud:~/.ssh/
    scp ~/.ssh/authorized_keys mms-xi.cloud:~/.ssh/
    ```
  - Test
    ```bash
    ssh mms.cloud     ls -l /tmp
    ssh mms-x.cloud   ls -l /tmp
    ssh mms-xi.cloud  ls -l /tmp
    ```

## AppDB Replica Set

Steps to set up the `AppDB` as a Primary-Secondary-Arbiter (PSA) Replica Set.

- __Note__: This assumes all VMs have the *network and RSA keys configured*.
- __Note__: These are modified steps as listed [here](https://docs.mongodb.com/v3.6/tutorial/install-mongodb-on-red-hat/)
- `ssh root@10.18.89.2`, `ssh root@10.18.89.10`, and `ssh root@10.18.89.11` then `iterm2`-broadcast

```bash
APPDB_PORT=27001
APPDB_DATA_DIR=/mongod-data/appdb/data
APPDB_LOG_DIR=/var/log/mongodb
APPDB_LOG_FILE=/var/log/mongodb/appdb.log
APPDB_KEY_DIR=/mongod-data/appdb/
APPDB_KEY_FILE=/mongod-data/appdb/appdb.key
```

- Download and install MongoDB 3.6-ent

```bash
cat <<EOF > /etc/yum.repos.d/mongodb-org-3.6.repo
[mongodb-org-3.6]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/3.6/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-3.6.asc
EOF
yum install -y cyrus-sasl cyrus-sasl-gssapi cyrus-sasl-plain krb5-libs libcurl libpcap lm_sensors-libs net-snmp net-snmp-agent-libs openldap openssl rpm-libs tcp_wrappers-libs
yum -y install policycoreutils-python
yum install -y -q ntp
yum install -y mongodb-org
systemctl start ntpd.service
systemctl enable ntpd.service
```

- Create directories and configure ownership

```bash
mkdir -p $APPDB_DATA_DIR
mkdir -p $APPDB_LOG_DIR
rm -rf $APPDB_DATA_DIR/* $APPDB_LOG_DIR/* $APPDB_LOG_FILE
touch $APPDB_LOG_FILE
chown -R mongod: $APPDB_DATA_DIR $APPDB_LOG_DIR $APPDB_LOG_FILE
ls -Z $APPDB_DATA_DIR $APPDB_LOG_DIR $APPDB_LOG_FILE
# -rw-r--r--. mongod mongod unconfined_u:object_r:mongod_log_t:s0 /var/log/mongodb/appdb.log
# /mongod-data/appdb/data:
# /var/log/mongodb:
# -rw-r--r--. mongod mongod unconfined_u:object_r:mongod_log_t:s0 appdb.log
```

- Set SELinux for MongoDB

```bash
yum install -y setroubleshoot-server
sealert -a /var/log/audit/audit.log > /var/log/audit/audit_human_readable.log
sestatus
# SELinux status:                 enabled
# SELinuxfs mount:                /sys/fs/selinux
# SELinux root directory:         /etc/selinux
# Loaded policy name:             targeted
# Current mode:                   enforcing
# Mode from config file:          enforcing
# Policy MLS status:              enabled
# Policy deny_unknown status:     allowed
# Max kernel policy version:      28
semanage port --add --type mongod_port_t -p tcp $APPDB_PORT
semanage port --list | grep mongod_port_t #verify

chcon -R --reference=/var/lib/mongo $APPDB_DATA_DIR
chcon -R --reference=/var/log/mongo $APPDB_LOG_DIR

semanage fcontext --delete /mongod-data/app.*
semanage fcontext --add    --type mongod_var_lib_t --seuser system_u  /mongod-data/app.*
semanage fcontext --list   | grep mongod_var_lib_t #verify
# recursively apply policies and show the changes
restorecon -R -v  -F           /mongod-data/*
# chcon -R --reference /file/w/desired/context/ $APPDB_DATA_DIR*
# semanage fcontext --add    --type mongod_log_t --seuser system_u  $APPDB_LOG_DIR/
# semanage fcontext --add    --type mongod_log_t --seuser system_u  $APPDB_LOG_DIR/*
# semanage fcontext --list | grep mongod_log_t #verify
# restorecon -Rv $APPDB_LOG_DIR*
```

<!--
# fcontext Manage file context mapping definitions
setenforce 0 -- to switch to permissive
setenforce 1 -- to switch to enforcing

By default SELinux log messages are written to /var/log/audit/audit.log via the Linux Auditing System auditd, which is started by default. If the auditd daemon is not running, then messages are written to /var/log/messages . SELinux log messages are labeled with the "AVC" keyword so that they might be easily filtered from other messages, as with grep.

Check when something gets logged due to SELinux here:
### sealert -a /var/log/audit/audit.log > ~/trackSELinux | tail -f

to add a file context of type httpd_sys_content_t for everything under /html.

Create a permanent rule for the everything under this directory:
### semanage fcontext -a -t httpd_sys_content_t "/html(/.*)?"

Check if anything needs to be restored to the defaults:
### restorecon -Rv -n /var/www/html

To Actually restore the defaults:
### restorecon -Rv /var/www/html

To relabel content that has a customizable type associated with it, run restorecon as above with the extra flag:
### restorecon -RvF /var/www/html -->

- Configure iptables (on every host)

```bash
iptables -A INPUT  -s 10.18.89.0/24 -p tcp --destination-port $APPDB_PORT -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -d 10.18.89.0/24 -p tcp --source-port $APPDB_PORT -m state --state ESTABLISHED -j ACCEPT
iptables-save > /etc/iptables.conf
iptables-restore < /etc/iptables.conf
iptables -L | grep
# ACCEPT     tcp  --  10.18.89.0/24        anywhere             tcp dpt:27001 state NEW,ESTABLISHED
# ACCEPT     tcp  --  anywhere             10.18.89.0/24        tcp spt:27001 state ESTABLISHED
```

- Set up the firewall entries

```bash
firewall-cmd --get-active-zones
firewall-cmd --permanent --zone=public --add-port=$APPDB_PORT/tcp
firewall-cmd --reload
# success
```

- Disable default `mongod` process.

```bash
systemctl disable mongod
#  Removed symlink /etc/systemd/system/multi-user.target.wants/mongod.service.
```

- Create the config file for the App DB.

```bash
cat <<EOF > /etc/appdb.conf
net:
  port: $APPDB_PORT
  bindIp: $HOSTNAME
### This should be `false` when using systemd, unless Amazon Linux go figure...
processManagement:
  pidFilePath: /var/run/mongodb/mongodb-app.pid 
#  fork: true
replication:
  replSetName: "APPDB"
  oplogSizeMB: 100
storage:
  dbPath: $APPDB_DATA_DIR
  wiredTiger:
    engineConfig:
      cacheSizeGB: .5
      journalCompressor: zlib
systemLog:
  destination: file
  path: $APPDB_LOG_FILE
  logAppend: true
### Increase verbosity to debug
#  verbosity: 5
setParameter:
  enableLocalhostAuthBypass: true
### Enable after creating the first user (ig "root") and all nodes have the same keyfile (ig "/")
#security:
#  authorization: enabled
#  keyFile: $APPDB_KEY_FILE
#  clusterAuthMode: keyFile
### Enable after all x509 are in place
#  clusterAuthMode: x509
### Enable D@RE
#   enableEncryption: <boolean>
#   encryptionCipherMode: <string>
#   encryptionKeyFile: <string>
### Enable D@RE with KMIP
#   kmip:
#      keyIdentifier: <string>
#      rotateMasterKey: <boolean>
#      serverName: <string>
#      port: <string>
#      clientCertificateFile: <string>
#      clientCertificatePassword: <string>
#      serverCAFile: <string>
#   sasl:
#      hostName: <string>
#      serviceName: <string>
#      saslauthdSocketPath: <string>
#   ldap:
#      servers: <string>
#      bind:
#         method: <string>
#         saslMechanism: <string>
#         queryUser: <string>
#         queryPassword: <string>
#         useOSDefaults: <boolean>
#      transportSecurity: <string>
#      timeoutMS: <int>
#      userToDNMapping: <string>
#      authz:
#         queryTemplate: <string>
EOF
```

- Configure AppDB MongoD Service

```bash
cp --preserve=context /lib/systemd/system/mongod.service /lib/systemd/system/mongod-app.service
ls -Z !$
sed -i 's/^\(Environment=\).*/\1"OPTIONS=\-f\ \/etc\/appdb.conf"/' /lib/systemd/system/mongod-app.service
cat !$ | grep Environment
restorecon -Fv /lib/systemd/system/mongod-app.service
# Environment="OPTIONS=-f /etc/appdb.conf"
systemctl daemon-reload
systemctl enable mongod-app
# Created symlink from /etc/systemd/system/multi-user.target.wants/mongod-app.service to /usr/lib/systemd/system/mongod-app.service.
```

- Start Daemon

```bash
mongod -f /etc/appdb.conf --fork
systemctl status mongod-app
journalctl -u    mongod-app
q
tail -f /var/log/mongodb/appdb.log
q

# For Amazon Linux
# chkconfig --add <new service name>
```

- Configure Replica Set from `mms-x`

```bash
cd /mongod-data
cat <<EOF > appdb.js
rs.initiate(
  { _id    : 'APPDB',
    members: [
              {
                _id: 0,
                host: 'mms-x.cloud:27001',
                priority: 2
              }
            ]
  }
);
sleep(5000);
rs.status();
rs.add(  'mms-xi.cloud:27001' );
sleep(5000);
rs.addArb(  'mms.cloud:27001');
sleep(5000);
rs.status();
exit;
EOF

mongo --host $HOSTNAME admin --port $APPDB_PORT < appdb.js
```

- Add `root` user from the primary's Mongo Shell (localhost exception)

```bash
mongo admin --host $HOSTNAME admin --port $APPDB_PORT
db.createUser({user: 'root', pwd: 'r00t', roles: ['root']});
db.auth( "root", "r00t");
exit
```

- Add a keyfile to the replica set, from `mms-x.cloud`

```bash
openssl rand -base64 512 > $APPDB_KEY_FILE
scp $APPDB_KEY_FILE root@mms-xi.cloud:$APPDB_KEY_DIR
scp $APPDB_KEY_FILE root@mms.cloud:$APPDB_KEY_DIR

# On every node:
cd $APPDB_KEY_DIR
chown mongod: $APPDB_KEY_FILE
chmod 400 $APPDB_KEY_FILE
semanage fcontext --add    --type mongod_var_lib_t --seuser system_u  $APPDB_KEY_FILE
semanage fcontext --list   | grep mongod_var_lib_t #verify
restorecon -R -v  -F $APPDB_KEY_FILE
chown -R mongod: $APPDB_KEY_DIR
ls -Z
```

- Uncomment the following from `/etc/appdb.conf`

```bash
security:
  authorization: enabled
  keyFile: /mongod-data/appdb/appdb.key
  clusterAuthMode: keyFile
```

- On each server with the AppDB `systemctl restart mongod-app`
- Upgrade cluster to use TLS as per [docs](https://docs.mongodb.com/manual/tutorial/upgrade-cluster-to-ssl/)
  - Note: Certificates must already be available. See `4_CertificateAuthority.md` for more details.
  - Note: For this example, we do a "rolling upgrade" to add TLS, ie no downtime.
- Edit `/etc/appdb.conf` to include:

```bash
net:
  ssl:
    mode: allowSSL
    PEMKeyFile: /mongod-data/mongod-noex.pem
    PEMKeyPassword: "mms-H0m3L4b"
    CAFile: /mongod-data/ca-chain.cert.pem
```

- On each node,

```bash

mongo admin --port 27001 --host $HOSTNAME -u root -p "r00t" --authenticationDatabase admin --ssl --sslPEMKeyFile /mongod-data/mongod-noex.pem --sslCAFile /mongod-data/ca-chain.cert.pem --sslPEMKeyPassword mms-H0m3L4b

rs.slaveOk()
db.getSiblingDB('admin').runCommand( { setParameter: 1, sslMode: "preferSSL" } )
## look for ""ok" : 1,"
db.getSiblingDB('admin').runCommand( { setParameter: 1, sslMode: "requireSSL" } )
## look for ""ok" : 1,"
exit

vi /etc/appdb.conf
net:
  ssl:
    mode: requireSSL
```

- On each server with the AppDB `systemctl restart mongod-app`

## Blockstore Replica Set

- Set up `BLOCKSTORE` as a Primary-Secondary-Arbiter (PSA) Replica Set
- __Note__: This assumes all VMs have the network and RSA keys configured.
- __Note__: Some steps are omitted as these were already covered when installing the APPDB.
- __Note__: These are modified steps as listed [here](https://docs.mongodb.com/v3.4/tutorial/install-mongodb-on-red-hat/)
- `ssh root@10.18.89.10`, `ssh root@10.18.89.11`, and `ssh root@10.18.89.2` then `iterm2 broadcast`

  ```bash
  BLOCKSTORE_PORT=27002
  BLOCKSTORE_DATA_DIR=/mongod-data/blockstore/data
  BLOCKSTORE_LOG_DIR=/var/log/mongodb
  BLOCKSTORE_LOG_FILE=/var/log/mongodb/blockstore.log
  BLOCKSTORE_KEY_DIR=/mongod-data/blockstore/
  BLOCKSTORE_KEY_FILE=/mongod-data/blockstore/blockstore.key
  ```

- Create directories and configure ownership

  ```bash
  mkdir -p $BLOCKSTORE_DATA_DIR
  mkdir -p $BLOCKSTORE_LOG_DIR
  rm -rf $BLOCKSTORE_DATA_DIR/* $BLOCKSTORE_LOG_DIR/* $BLOCKSTORE_LOG_FILE
  touch $BLOCKSTORE_LOG_FILE
  chown -R mongod: $BLOCKSTORE_DATA_DIR $BLOCKSTORE_LOG_DIR $BLOCKSTORE_LOG_FILE
  ls -Z $BLOCKSTORE_DATA_DIR $BLOCKSTORE_LOG_DIR $BLOCKSTORE_LOG_FILE
  ```

- Set SELinux

  ```bash
  semanage port -a -t mongod_port_t -p tcp $BLOCKSTORE_PORT
  semanage fcontext -a -t mongod_var_lib_t $BLOCKSTORE_DATA_DIR
  restorecon -Rv $BLOCKSTORE_DATA_DIR
  semanage fcontext -a -t mongod_log_t $BLOCKSTORE_LOG_DIR
  restorecon -Rv $BLOCKSTORE_LOG_DIR
  ```

- Configure iptables

  ```bash
  iptables -A INPUT  -s 10.18.89.0/24 -p tcp --destination-port $BLOCKSTORE_PORT -m state --state NEW,ESTABLISHED -j ACCEPT
  iptables -A OUTPUT -d 10.18.89.0/24 -p tcp --source-port $BLOCKSTORE_PORT -m state --state ESTABLISHED -j ACCEPT
  iptables-save > /etc/iptables.conf
  iptables-restore < /etc/iptables.conf
  iptables -L | grep 89
  ```

- Configure firewall

  ```bash
  firewall-cmd --get-active-zones
  firewall-cmd --permanent --zone=public --add-port=$BLOCKSTORE_PORT/tcp
  firewall-cmd --reload
  ```

- Create the config file

```bash
cat <<EOF > /etc/blockstore.conf
net:
  port: $BLOCKSTORE_PORT
  bindIp: $HOSTNAME
### This should be `false` when using systemd, unless Amazon Linux go figure...
#processManagement:
#  fork: true
replication:
  replSetName: "BLOCKSTORE"
  oplogSizeMB: 500
storage:
  dbPath: $BLOCKSTORE_DATA_DIR
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2
      journalCompressor: zlib
systemLog:
  destination: file
  path: $BLOCKSTORE_LOG_FILE
  logAppend: true
EOF
```

- Configure daemon

```bash
cp --preserve=context /lib/systemd/system/mongod.service /lib/systemd/system/mongod-blockstore.service
sed -i.bak 's/^\(Environment=\).*/\1"OPTIONS=\-f\ \/etc\/blockstore.conf"/' /lib/systemd/system/mongod-blockstore.service
cat !$ | grep Environment
systemctl daemon-reload
systemctl enable mongod-blockstore
```

- Start Daemon

```bash
rm -rf /mongod-data/blockstore/data/mongod.lock
systemctl start mongod-blockstore
systemctl status mongod-blockstore
#journalctl -u mongod-blockstore
#q
tail -f $BLOCKSTORE_LOG_FILE
```

- Configure Replica Set from `mms-xi`

```bash
mongo --host $HOSTNAME admin --port $BLOCKSTORE_PORT
use admin
rs.initiate({ '_id'    : 'BLOCKSTORE',
  'members': [{ '_id': 0,
                'host': 'mms-xi.cloud:27002',
                'priority': 2 }]});
rs.add(    'mms-x.cloud:27002' );
rs.addArb( 'mms.cloud:27002'   );
rs.status();

## Add "root" user from the primary's mongo shell
db.createUser({user: 'root', pwd: 'r00t', roles: ['root']});
## Successfully added user: { "user" : "root", "roles" : [ "root" ] }
db.auth( "root", "r00t");
exit
```

- Add a keyfile to the replica set, from `mms-x.cloud`

```bash
cd $BLOCKSTORE_KEY_DIR
openssl rand -base64 512 > $BLOCKSTORE_KEY_FILE
scp $BLOCKSTORE_KEY_FILE root@mms.cloud:$BLOCKSTORE_KEY_DIR
scp $BLOCKSTORE_KEY_FILE root@mms-xi.cloud:$BLOCKSTORE_KEY_DIR

# On every node:
cd $BLOCKSTORE_KEY_DIR
chown mongod: $BLOCKSTORE_KEY_FILE
chmod 400 $BLOCKSTORE_KEY_FILE
semanage fcontext -a -t mongod_var_lib_t $BLOCKSTORE_KEY_FILE
restorecon -Rv $BLOCKSTORE_KEY_FILE
ls -Z $BLOCKSTORE_KEY_DIR
EOF
```

- Add the following from `/etc/blockstore.conf`

```bash
security:
  authorization: enabled
  keyFile: /mongod-data/blockstore/blockstore.key
  clusterAuthMode: keyFile
```

- Upgrade cluster to use TLS as per [docs](https://docs.mongodb.com/manual/tutorial/upgrade-cluster-to-ssl/)
  - Note: Certificates must already be available. See `4_CertificateAuthority.md` for more details.
  - Note: For this example, we shutdown the nodes then restart with TLS.
  - Add to the blockstore.conf

```bash
vi /etc/blockstore.conf
net:
  ssl:
    mode: requireSSL
    PEMKeyFile: /mongod-data/mongod-noex.pem
    PEMKeyPassword: "mms-H0m3L4b"
    CAFile: /mongod-data/ca-chain.cert.pem
```

- To login via the mongo shell `mongo admin --port 27002 --host $HOSTNAME -u root -p "r00t" --authenticationDatabase admin --ssl --sslPEMKeyFile /mongod-data/mongod-noex.pem --sslCAFile /mongod-data/ca-chain.cert.pem --sslPEMKeyPassword mms-H0m3L4b`

## Install the MongoDB Ops Manager HTTP Service -- TODO with 3.6

We are installing the HTTP Service in two hosts and using the HAProxy as the Load Balancer.

- Install `.rpm`

  ```bash
  scp mongodb-mms-3.4*.rpm root@mms-x.cloud:~
  scp mongodb-mms-3.4*.rpm root@mms-xi.cloud:~

  ssh root@mms-x.cloud # start mms config on this server
  rpm -ivh mongodb-mms-3.4.*.x86_64.rpm

  ssh root@mms-xi.cloud # come back to finish configuring this one
  rpm -ivh mongodb-mms-3.4.*.x86_64.rpm
  ```

- Configure `.properties` file for `APPDB` and TLS

  ```bash
  sed -i.bak 's/^\(mongo.mongoUri=\).*/\1mongodb\:\/\/mms-x.cloud\:27001,mms-xi.cloud\:27001,mms-xii.cloud\:27001\/\?replicaSet=APPDB\&maxPoolSize=150/' /opt/mongodb/mms/conf/conf-mms.properties
  cat !$ | grep mongoUri #verify

  cp /mongod-data/tls/mongod-noex.pem /opt/mongodb/mms/conf/
  cp /mongod-data/tls/ca-chain.cert.pem /opt/mongodb/mms/conf/
  chown -R mongodb-mms: /opt/mongodb/mms/conf/*.pem

  sed -i.bak 's/^\(mongo.ssl=\).*/\1true' /opt/mongodb/mms/conf/conf-mms.properties
  sed -i.bak 's/^\(mongodb.ssl.CAFile=\).*/\1\/opt\/mongodb\/mms\/conf\/ca\-chain.cert.pem/' /opt/mongodb/mms/conf/conf-mms.properties
  sed -i.bak 's/^\(mongodb.ssl.PEMKeyFile=\).*/\1\/opt\/mongodb\/mms\/conf\/mongod\-noex.pem/' /opt/mongodb/mms/conf/conf-mms.properties
  sed -i.bak 's/^\(mongodb.ssl.PEMKeyFilePassword=\).*/\1PEMKEYPASSChangeMe1\!/' /opt/mongodb/mms/conf/conf-mms.properties
  cat !$ | grep ssl #verify
  ```

<!-- FIX:
`service mongodb-mms start`
Failed to read MongoDB SSL config `/mongod-data/tls/mongod-noex.pem`/`/mongod-data/tls/ca-chain.cert.pem`. Error: /mongod-data/tls/ca-chain.cert.pem (Permission denied) -->
- Start daemon via `service mongodb-mms start`
- Encrypt credentials `/opt/mongodb/mms/bin/credentialstool --username root --password`

  ```bash
  Username: e5b2f41be812a4fcaa13b1132b61e75f-14f045bc32af5fba
  Password: e5b2f41be812a4fcaa13b1132b61e75f-2c9b0e1e15e14346
  ```

- Stop mms via `service mongodb-mms stop`
- Configure `.properties` file to use encrypted credentials

  ```bash
  sed -i.bak 's/^\(mongo.mongoUri=\).*/\1mongodb\:\/\/e5b2f41be812a4fcaa13b1132b61e75f\-14f045bc32af5fba\:e5b2f41be812a4fcaa13b1132b61e75f\-2c9b0e1e15e14346@mms-x.cloud\:27001,mms-xi.cloud\:27001,mms-xii.cloud\:27001\/\?replicaSet=APPDB/' /opt/mongodb/mms/conf/conf-mms.properties
  cat !$ | grep mongoUri=

  cat >> /opt/mongodb/mms/conf/conf-mms.properties <<EOF
  mongo.encryptedCredentials=true
  ## mongo.backup.encryptedCredentials=true
  EOF
  ```

- Copy Ops Manager `.key` file

  ```bash
  ssh root@mms-x.cloud
  base64 /etc/mongodb-mms/gen.key | ssh root@mms-xi.cloud "base64 -d > /etc/mongodb-mms/gen.key"

  ssh root@mms-xi.cloud
  chmod 600 /etc/mongodb-mms/gen.key
  chown mongodb-mms: !$
  ls -Z !$

  service mongodb-mms start
  ```

- Configure iptables (on every Ops Manager host)

  ```bash
  iptables -I INPUT 1 -i ens192 -p tcp --dport 8080 -j ACCEPT -v
  iptables-save > /etc/iptables.conf
  iptables-restore < /etc/iptables.conf
  iptables -S | grep 8080
  ```

## Configure Ops Manager -- TODO with 3.6

- __TODO__ ADD STEPS
- `yum install -y unzip java-1.8.0-openjdk openldap-clients # for LDAP`

<!-- opsmgr_cache_mongodb_binaries -->

  ```bash
  # Link Mongo shell to path, as we need it to hack the OpsMgr DB.
  ln -s $dir/bin/mongo /usr/bin/
  opsmgr_config_hacks

  ```

<!-- -e "s|^automation.versions.source=mongodb|automation.versions.source=local|" \ -->

  ```bash
  OPS_MGR_USERNAME=admin@ldap.cloud
  OPS_MGR_PASSWORD=adm1n@ldap.cloud
  OPS_MGR_FQDN=mms.cloud #http://mms.cloud/user/login, mms.cloud.oskoss.com
  OPS_MGR_GROUP=mms
  OPS_MGR_APP_DB_PORT=27001
  OPS_MGR_LOG=/opt/mongodb/mms/logs/mms.log
  TMP_DIR=/tmp
  COOKIE=$TMP_DIR/cookie
  email=noreply@$OPS_MGR_FQDN
  MMS_CONF=/opt/mongodb/mms/conf/conf-mms.properties
  mkdir -p $TMP_DIR $OPS_MGR_LOG
  ```

- Configure Backup Daemon

  ```bash
  ## Disable from other servers  `ssh root@10.18.89.8` and `ssh root@10.18.89.9`
  service mongodb-mms-backup-daemon stop
  systemctl disable mongodb-mms-backup-daemon

  ## Copy files
  scp mongodb-mms-3.4.5.424-1.x86_64.rpm root@mms-ix.cloud:/root/
  scp mongodb-mms-3.4.5.424-1.x86_64.rpm root@mms-viii.cloud:/root/
  base64 /etc/mongodb-mms/gen.key | ssh root@mms-ix.cloud "base64 -d > /etc/mongodb-mms/gen.key"
  base64 /etc/mongodb-mms/gen.key | ssh root@mms-viii.cloud "base64 -d > /etc/mongodb-mms/gen.key"
  scp /opt/mongodb/mms/conf/conf-mms.properties root@mms-ix.cloud:/opt/mongodb/mms/conf/
  scp /opt/mongodb/mms/conf/conf-mms.properties root@mms-viii.cloud:/opt/mongodb/mms/conf/
  scp /opt/mongodb/mms/conf/*.pem root@mms-ix.cloud:/opt/mongodb/mms/conf/
  scp /opt/mongodb/mms/conf/*.pem root@mms-vii.cloud:/opt/mongodb/mms/conf/

  ## Enable `ssh root@10.18.89.8` and `ssh root@10.18.89.9`
  mkdir -p /headdb
  chown mongodb-mms: !$
  rpm -ivh mongodb-mms-3.4.*.x86_64.rpm
  chmod 600 /etc/mongodb-mms/gen.key
  chown mongodb-mms: !$
  chown -R mongodb-mms: /opt/mongodb/mms/conf/*.pem

  service mongodb-mms-backup-daemon start
  # Example,
  # Successfully finished pre-flight checks
  # Start Backup Daemon...                                     [  OK  ]

  ## Obtain encrypted credentials
  ./credentialstool --username root --password

  ## Go to http://mms.cloud/admin/backup/setup
  Put /headdb
  The configured directory (/headdb/) has been found. It has 4.67 GB of free space.
  ENABLE DAEMON
  CONFIGURE A BLOCKSTORE
  <hostname>:<port>:  mms-ix.cloud:27002,mms-viii.cloud:27002
  MongoDB Auth Username: e5b2f41be812a4fcaa13b1132b61e75f-14f045bc32af5fba
  MongoDB Auth Password: e5b2f41be812a4fcaa13b1132b61e75f-2c9b0e1e15e14346
  Encrypted Credentials: YES
  Use TLS/SSL: YES

  ## Configure 2nd Daemon at http://mms.cloud/admin/backup/daemonStats
  /headdb/
  ENABLE DAEMON
  ```
