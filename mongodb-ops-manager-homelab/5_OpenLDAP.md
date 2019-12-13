# OpenLDAP

Note: This is being configured on `ldap.cloud` at `10.18.89.3`.

- LDAP Input Format (LDIF)
- Lightweight Directory Access Protocol (LDAP)

## Server

The below steps have been modified from [here](http://www.itzgeek.com/how-tos/linux/centos-how-tos/step-step-openldap-server-configuration-centos-7-rhel-7.html)

- Log in `ssh root@ldap.cloud`
- Install packages

  ```bash
  yum -y install openldap compat-openldap openldap-clients openldap-servers openldap-servers-sql openldap-devel
  yum -y install net-tools
  ```

- Start service

  ```bash
  systemctl start slapd.service
  systemctl enable slapd.service
  netstat -antup | grep -i 389
  ```

- Add root password

  ```bash
  slappasswd
  New password: <ChangeMe1>
  Re-enter new password: <ChangeMe1>
  {SSHA}abc123
  ```

- Configure

  ```bash
  cd /etc/openldap/

  cat <<EOF >  db.ldif
  dn: olcDatabase={2}hdb,cn=config
  changetype: modify
  replace: olcSuffix
  olcSuffix: dc=cloud,dc=oskoss,dc=com

  dn: olcDatabase={2}hdb,cn=config
  changetype: modify
  replace: olcRootDN
  olcRootDN: cn=root,dc=cloud,dc=oskoss,dc=com

  dn: olcDatabase={2}hdb,cn=config
  changetype: modify
  replace: olcRootPW
  olcRootPW: {SSHA}abc123
  EOF

  ldapmodify -Y EXTERNAL  -H ldapi:/// -f db.ldif
  # Example
  # SASL/EXTERNAL authentication started
  # SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
  # SASL SSF: 0
  # modifying entry "olcDatabase={2}hdb,cn=config"
  # modifying entry "olcDatabase={2}hdb,cn=config"
  # modifying entry "olcDatabase={2}hdb,cn=config"


  # restrict the monitor access only to ldap root (ldapadm) user not to others.
  cat <<EOF >  monitor.ldif
  dn: olcDatabase={1}monitor,cn=config
  changetype: modify
  replace: olcAccess
  olcAccess: {0}to * by dn.base="gidNumber=0+uidNumber=0,cn=peercred,cn=external, cn=auth" read by dn.base="cn=root,dc=cloud,dc=oskoss,dc=com" read by * none
  EOF

  ldapmodify -Y EXTERNAL  -H ldapi:/// -f monitor.ldif
  # Example
  # SASL/EXTERNAL authentication started
  # SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
  # SASL SSF: 0
  # modifying entry "olcDatabase={1}monitor,cn=config"
  ```

  - Note: `olcSuffix` is the Database Suffix or your domain.
  - Note: `olcRootDN` is the root distingued name for the superuser (like root)
  - Note: `olcRootPW` is the password for the above dude.

- Add certificate
  Note: We'll use our Intermediate CA `ca.cloud` to sign the certs

  ```bash
  ssh root@ca.cloud
  # Generate key to sign the certs
  cd /root/ca
  openssl genrsa -out intermediate/private/ldap.key.pem 2048
  chmod 400 intermediate/private/ldap.key.pem

  # Generate Certificate Signing Requests (CSR's)
  openssl req -config intermediate/openssl.cnf -key intermediate/private/ldap.key.pem -new -sha256 -out intermediate/csr/ldap.cloud.csr.pem

  #  Use the Intermediate CA to sign the CSRs 
  openssl ca -config intermediate/openssl.cnf  -days 375 -notext -md sha256  -in  intermediate/csr/ldap.cloud.csr.pem -out intermediate/certs/ldap.cloud.cert.pem

  chmod 444 intermediate/certs/ldap.cloud*
  openssl verify -CAfile intermediate/certs/ca-chain.cert.pem  intermediate/certs/ldap.cloud*

  # Copy the generated certs to servers
  cd intermediate/
  scp certs/ca-chain.cert.pem \
      certs/ldap.cloud.cert.pem private/ldap.key.pem \
      root@ldap.cloud:/etc/openldap/certs/
  exit
  ```

- Set permissions

  ```bash
  ssh root@ldap.cloud

  cd /etc/openldap/certs
  chown ldap: *.pem
  chmod 444 *.pem
  ls -Z !$

  cd /etc/openldap
  cat <<EOF > certs.ldif
  dn: cn=config
  changetype: modify
  replace: olcTLSCACertificateFile
  olcTLSCACertificateFile: /etc/openldap/certs/ca-chain.cert.pem

  dn: cn=config
  changetype: modify
  replace: olcTLSCertificateFile
  olcTLSCertificateFile: /etc/openldap/certs/ldap.cloud.cert.pem

  dn: cn=config
  changetype: modify
  replace: olcTLSCertificateKeyFile
  olcTLSCertificateKeyFile: /etc/openldap/certs/ldap.key.pem
  EOF

  ldapmodify -Y EXTERNAL  -H ldapi:/// -f certs.ldif

  slaptest -u
  #config file testing succeeded
  ```

- Set up Database

  ```bash
  cp /usr/share/openldap-servers/DB_CONFIG.example /var/lib/ldap/DB_CONFIG
  chown ldap: /var/lib/ldap/*

  ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/cosine.ldif
  ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/nis.ldif 
  ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/inetorgperson.ldif

  cat <<EOF > base.ldif
  dn: dc=cloud,dc=oskoss,dc=com
  dc: cloud
  objectClass: top
  objectClass: domain

  dn: cn=root,dc=cloud,dc=oskoss,dc=com
  objectClass: organizationalRole
  cn: root
  description: LDAP Manager

  dn: ou=user,dc=cloud,dc=oskoss,dc=com
  objectClass: organizationalUnit
  ou: user

  dn: ou=group,dc=cloud,dc=oskoss,dc=com
  objectClass: organizationalUnit
  ou: group
  EOF

  ldapadd -x -W -D "cn=root,dc=cloud,dc=oskoss,dc=com" -f base.ldif
  # Example,
  # adding new entry "dc=cloud,dc=oskoss,dc=com"
  # adding new entry "cn=root,dc=cloud,dc=oskoss,dc=com"
  # adding new entry "ou=user,dc=cloud,dc=oskoss,dc=com"
  # adding new entry "ou=group,dc=cloud,dc=oskoss,dc=com"

  # Check
  ldapsearch -x ou=user -b dc=cloud,dc=oskoss,dc=com
  ldapsearch -x ou=group -b dc=cloud,dc=oskoss,dc=com
  ldapsearch -x cn=root -b dc=cloud,dc=oskoss,dc=com
  ```

- Test dummy user __TODO__

  ```bash
  cat <<EOF > diana.ldif
  dn: uid=diana,ou=user,dc=cloud,dc=oskoss,dc=com
  objectClass: top
  objectClass: user
  objectClass: posixAccount
  cn: diana
  uid: desteves
  uidNumber: 9999
  gidNumber: 9999
  homeDirectory: /home/diana
  loginShell: /bin/bash
  userPassword: {crypt}x
  EOF
  ```

- Add Logging

  ```bash
  echo "local4.* /var/log/ldap.log" >> /etc/rsyslog.conf
  systemctl restart rsyslog
  ```

- Set firewall rules

  ```bash
  firewall-cmd --add-service=ldap --permanent 
  firewall-cmd --reload 
  ```

## Client

- Log in `ssh root@mms-xi.cloud`
- Install packages `yum install -y openldap-clients nss-pam-ldapd`
- Add SSO

  ```bash
  authconfig --enableldap --enableldapauth --ldapserver=ldap.cloud --ldapbasedn="dc=cloud,dc=oskoss,dc=com" --enablemkhomedir --update
  systemctl restart  nslcd
  ```

- Verify login

  ```bash
  getent passwd root
  # root:x:0:0:root:/root:/bin/bash
  ```
