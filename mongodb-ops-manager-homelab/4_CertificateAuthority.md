# Root and Intermediate Certificate Authority (CA)

Note: Follow the steps listed [here](https://jamielinux.com/docs/openssl-certificate-authority/introduction.html) for server `ca.cloud` running on static IP `10.18.89.7`



- Configure Root CA and Intermediate CA

  ```bash
    vi /root/ca/openssl.cnf
    # Optionally, specify some defaults.
    countryName_default             = US
    stateOrProvinceName_default     = Texas
    localityName_default            = Austin
    0.organizationName_default      = Oskoss Cloud
    organizationalUnitName_default  =
    emailAddress_default            = diana@mongodb.com
  ```

- Generate Client/Server certificates
  - Note: Do __NOT__ use `-extensions server_cert` for `mongod` certs as per [link](https://groups.google.com/forum/#!topic/mongodb-user/EmESxx5KK9Q)
- Generate key(s) to sign the certs
    ```bash
    ssh root@ca.cloud
    cd /root/ca
    openssl genrsa -aes256 -out intermediate/private/mms-noex.key.pem 2048
    # Enter pass phrase for intermediate/private/mms-noex.key.pem: mms-H0m3L4b
    chmod 400 intermediate/private/mms-noex.key.pem
    ```
- Generate Certificate Signing Requests (CSR's)
    ```bash
    openssl req -config intermediate/openssl.cnf -key intermediate/private/mms-noex.key.pem -new -sha256 -out intermediate/csr/mms-x.cloud-noex.csr.pem
    openssl req -config intermediate/openssl.cnf -key intermediate/private/mms-noex.key.pem -new -sha256 -out intermediate/csr/mms-xi.cloud-noex.csr.pem
    openssl req -config intermediate/openssl.cnf -key intermediate/private/mms-noex.key.pem -new -sha256 -out intermediate/csr/mms.cloud-noex.csr.pem
    ```
- Use the Intermediate CA to sign the CSRs 
    ```bash
    openssl ca \
    -config intermediate/openssl.cnf -days 375 -notext -md sha256 \
        -in  intermediate/csr/mms-xi.cloud-noex.csr.pem \
        -out intermediate/certs/mms-xi.cloud-noex.cert.pem
    openssl ca \
    -config intermediate/openssl.cnf -days 375 -notext -md sha256 \
        -in  intermediate/csr/mms-x.cloud-noex.csr.pem \
        -out intermediate/certs/mms-x.cloud-noex.cert.pem
    openssl ca \
    -config intermediate/openssl.cnf -days 375 -notext -md sha256 \
        -in  intermediate/csr/mms.cloud-noex.csr.pem \
        -out intermediate/certs/mms.cloud-noex.cert.pem
    chmod 444 intermediate/certs/mms*noex*
    openssl verify -CAfile intermediate/certs/ca-chain.cert.pem  intermediate/certs/mms*noex*
    ```
- Copy the generated certs to servers
    ```bash
    cd intermediate/
    scp certs/ca-chain.cert.pem \
        certs/mms-xi.cloud-noex.cert.pem  private/mms-noex.key.pem \
        root@mms-xi.cloud:/mongod-data/

    scp certs/ca-chain.cert.pem \
        certs/mms-x.cloud-noex.cert.pem   private/mms-noex.key.pem \
        root@mms-x.cloud:/mongod-data/

    scp certs/ca-chain.cert.pem \
        certs/mms.cloud-noex.cert.pem  private/mms-noex.key.pem \
        root@mms.cloud:/mongod-data/
    ```
- Set file permissions
    ```bash
    cd /mongod-data/
    cat mms-noex.key.pem mms*.cloud-noex.cert.pem > mongod-noex.pem
    chmod 400     *.pem
    chown mongod: *.pem
    ```
- Change the SELinux context of the certs
    ```bash
    cd /mongod-data/
    chown -R mongod: !$
    ls -Z !$
    semanage fcontext -a -t mongod_var_lib_t /mongod-data/mongod-noex.pem
    semanage fcontext -a -t mongod_var_lib_t /mongod-data/ca-chain.cert.pem
    semanage fcontext -a -t mongod_var_lib_t /mongod-data/
    restorecon -Rv !$
    semanage fcontext --list | grep mongod

    #Example:
    #drwxr-xr-x. mongod mongod unconfined_u:object_r:mongod_var_lib_t:s0 tls
    #[root@mms-xi mongod-data]# ls -Z tls/
    #-r--------. mongod mongod unconfined_u:object_r:mongod_var_lib_t:s0 ca-chain.cert.pem
    #-r--------. mongod mongod unconfined_u:object_r:default_t:s0 mms-xi.cloud.cert.pem
    #-r--------. mongod mongod unconfined_u:object_r:default_t:s0 mms-xi.cloud.key.pem
    #-r--------. mongod mongod unconfined_u:object_r:mongod_var_lib_t:s0 mongod.pem
    ```
- Update the `conf` file
    ```bash
    vi appdb.conf
    ___TODO___  ___COMPLETED BUT NEED LIST STEPS__
    ```
- Restart the AppDB node so the config file changes take effect `systemctl restart mongod-app`
- Install the Root CA as a server-wide cert __TODO__
    ```bash
    ca-certificates
    yum reinstall ca-certificates
    update-ca-certificates
    ```
