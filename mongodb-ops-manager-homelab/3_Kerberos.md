# Kerberos

Note: Modified from steps listed [here](https://gist.github.com/ashrithr/4767927948eca70845db) and [here](https://www.centos.org/docs/5/html/5.1/Deployment_Guide/s1-kerberos-server.html)

- Kerberos KDC Server `kdc.cloud`
- Kerberos Client `mms.cloud`

## Steps for Installing Kerberos on CentOS 7

- Modify on the Server __AND__ Client side

  ```bash
  echo "10.18.89.6 kdc.cloud" >> /etc/hosts
  echo "10.18.89.2 mms.cloud" >> /etc/hosts
  ```
- Add packages to __KDC Server__

  ```bash
  yum install -y ntp krb5-server krb5-libs
  ntpdate 0.rhel.pool.ntp.org
  systemctl start  ntpd.service
  systemctl enable ntpd.service
  ```

- Edit `/etc/krb5.conf`

  ```bash
  cat >> /etc/krb5.conf <<EOF
  # Configuration snippets may be placed in this directory as well
  includedir /etc/krb5.conf.d/
  [libdefaults]
  default_realm = CLOUD.OSKOSS.COM
  dns_lookup_realm = false
  ticket_lifetime = 24h
  forwardable = true
  udp_preference_limit = 1000000
  default_tkt_enctypes = des-cbc-md5 des-cbc-crc des3-cbc-sha1
  default_tgs_enctypes = des-cbc-md5 des-cbc-crc des3-cbc-sha1
  permitted_enctypes = des-cbc-md5 des-cbc-crc des3-cbc-sha1
  default_ccache_name = KEYRING:persistent:%{uid}

  [realms]
  CLOUD.OSKOSS.COM = {
    kdc = kdc.cloud.oskoss.com:88
    admin_server = kdc.cloud.oskoss.com:749
  }

  [domain_realm]
  kdc.cloud.oskoss.com = CLOUD.OSKOSS.COM
  mms.cloud.oskoss.com = CLOUD.OSKOSS.COM
  .cloud.oskoss.com = CLOUD.OSKOSS.COM
  kdc.cloud = CLOUD.OSKOSS.COM
  mms.cloud = CLOUD.OSKOSS.COM

  [logging]
  kdc = FILE:/var/log/krb5kdc.log
  default = FILE:/var/log/krb5libs.log
  admin_server = FILE:/var/log/kadmind.log
  EOF
  ```

- Edit `/var/kerberos/krb5kdc/kdc.conf`

  ```bash
  cat >> /var/kerberos/krb5kdc/kdc.conf <<EOF
  default_realm = CLOUD.OSKOSS.COM

  [kdcdefaults]
  v4_mode = nopreauth
  kdc_ports = 0

  [realms]
  CLOUD.OSKOSS.COM = {
    kdc_ports = 88
    database_name = /var/kerberos/krb5kdc/principal
    master_key_type = des3-hmac-sha1
    key_stash_file = /var/kerberos/krb5kdc/stash
    max_life = 10h 0m 0s
    max_renewable_life = 7d 0h 0m 0s
    acl_file = /var/kerberos/krb5kdc/kadm5.acl
    admin_keytab = /etc/kadm5.keytab
    supported_enctypes = aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal camellia256-cts:normal camellia128-cts:normal des-hmac-sha1:normal des-cbc-md5:normal des-cbc-crc:normal
    default_principal_flags = +preauth
  }
  EOF
  ```

- Edit `/var/kerberos/krb5kdc/kadm5.acl`

  ```bash
  echo  "*/admin@CLOUD.OSKOSS.COM	    *" > /var/kerberos/krb5kdc/kadm5.acl
  ```

- Create KDC Database
  `kdb5_util create -r CLOUD.OSKOSS.COM -s`

  ```bash
  # Initializing database '/var/kerberos/krb5kdc/principal' for realm 'CLOUD.OSKOSS.COM',
  # master key name 'K/M@CLOUD.OSKOSS.COM'
  ```

- Create Principals

  ```bash
  kadmin.local
  addprinc root/admin
  addprinc diana
  ktadd -k /var/kerberos/krb5kdc/kadm5.keytab kadmin/admin kadmin/changepw
  exit
  ```

- Start Kerberos KDC and kadmin

  ```bash
  systemctl restart krb5kdc.service
  systemctl restart kadmin.service
  systemctl enable krb5kdc.service
  systemctl enable kadmin.service
  ```

- Create principal for KDC itself (inception)

  ```bash
  kadmin.local
  addprinc -randkey host/kdc.cloud.oskoss.com
  ktadd host/kdc.cloud.oskoss.com
  exit
  ```

- Copy `krb5.conf` file to ALL clients

  ```bash
  scp /etc/krb5.conf root@mms.cloud:/etc/krb5.conf
  ```

- Add packages to __Kerberos Client__

  ```bash
  ssh root@mms.cloud
  yum install -y ntp krb5-workstation
  ```

- Add Firewall/IP Table Rules

  ```bash
  iptables -A INPUT  -s 10.18.89.0/24 -j ACCEPT
  iptables -A OUTPUT -s 10.18.89.0/24 -j ACCEPT

  iptables -A INPUT  -s 10.18.89.0/24 -p udp --destination-port 88  -j ACCEPT -m comment --comment "kerberos"
  iptables -A OUTPUT -d 10.18.89.0/24 -p udp --source-port      88  -j ACCEPT -m comment --comment "kerberos"
  iptables -A INPUT  -s 10.18.89.0/24 -p udp --destination-port 749 -j ACCEPT -m comment --comment "kerberos"
  iptables -A OUTPUT -d 10.18.89.0/24 -p udp --source-port      749 -j ACCEPT -m comment --comment "kerberos"
  iptables -A INPUT  -s 10.18.89.0/24 -p tcp --destination-port 88  -j ACCEPT -m comment --comment "kerberos"
  iptables -A OUTPUT -d 10.18.89.0/24 -p tcp --source-port      88  -j ACCEPT -m comment --comment "kerberos"
  iptables -A INPUT  -s 10.18.89.0/24 -p tcp --destination-port 749 -j ACCEPT -m comment --comment "kerberos"
  iptables -A OUTPUT -d 10.18.89.0/24 -p tcp --source-port      749 -j ACCEPT -m comment --comment "kerberos"

  iptables-save > /etc/iptables.conf
  iptables-restore < /etc/iptables.conf
  iptables -L | grep 89

  firewall-cmd --get-active-zones
  firewall-cmd --permanent --zone=public --add-port=88/tcp
  firewall-cmd --permanent --zone=public --add-port=88/udp
  firewall-cmd --permanent --zone=public --add-port=749/tcp
  firewall-cmd --permanent --zone=public --add-port=749/udp
  firewall-cmd --reload
  ```

  See [here](https://web.mit.edu/kerberos/krb5-1.4/krb5-1.4.4/doc/krb5-admin/Configuring-Your-Firewall-to-Work-With-Kerberos-V5.html) for firewall configuration and [here](https://www.certdepot.net/rhel7-configure-kerberos-kdc/) for a demo.
- Add Client principal

  ```bash
  ssh root@mms.cloud
  kadmin -p root/admin
  kadmin.local
  addprinc -randkey mongodb/mms.cloud.oskoss.com
  ktadd -k /var/kerberos/krb5kdc/mongodb.keytab mongodb/mms.cloud.oskoss.com
  addprinc -randkey host/mms.cloud.oskoss.com
  ktadd host/mms.cloud.oskoss.com
  exit
  ```

<!-- KRB5_TRACE=/dev/stdout kinit admin
__TODO__
TRY:
. In case you are using MIT one - set KRB5_CONFIG env var to point to your krb5 configuration file
An ICMP type 3 packet needed to be received from the gateway for the krb5 transaction to continue.
So any ip based filter has to allow incoming udp packets with arbitrary client port numbers.
 //yum install krb5-pkinit-openssl
 default = FILE:/var/log/krb5libs.log
 kdc = FILE:/var/log/krb5kdc.log
 admin_server = FILE:/var/log/kadmind.log
echo "10.18.89.6 kdc.cloud" >> /etc/hosts
echo "10.18.89.9 mms-ix.cloud" >> /etc/hosts
cat /etc/hosts
yum install -y krb5-workstation krb5-libs krb5-auth-dialog
kadmin -p root/admin
kadmin:  addpinc --randkey host/mms-ix.cloud
kadmin:  ktadd host/mms-ix.cloud
kinit -k host/fqdn@CLOUD -->