# VCenter configurations

## Configurations

- Physical
  - Server: Dell PowerEdge R720
  - 16 CPUs x 2.4 GHz
  - 256 GB RAM
  - Data stores
    - SSD = 2.86 TB
    - HDD = 2.73 TB
    - vsan datastore with Cache + Cold RAID 1

- Virtual
  - ESXI Host with VCenter
  - 3 Nested ESXI hosts in a Cluster


## VMs

- CentOS 7
- Standard Security Profile
- `yum update`
- Manual entries for network:
    ```bash
    cat <<EOF > /etc/sysconfig/network-scripts/ifcfg-ens192
    TYPE=Ethernet
    BOOTPROTO=none
    DEFROUTE=yes
    IPV4_FAILURE_FATAL=no
    IPV6INIT=no
    DEVICE=ens192
    ONBOOT=yes
    IPADDR=10.18.89.2
    PREFIX=8
    DNS1=10.0.0.1
    GATEWAY=10.0.0.1
    EOF
    echo "mms.cloud" > /etc/hostname
    hostnamectl status | grep "Static hostname"
    service network restart
    ```
- Register the FQDN with `dnspal`
- Clone template VM

## Errors and Fixes

1. __Error__ "Selected cluster is not in DRS mode, please select a specific host within the cluster."
  __FIX__ Turning on vSphere ON DRS Automation to `Fully Automated`
2. __Error__
  The operation failed for an undetermined reason. Typically this problem occurs due to certificates that the browser does not trust. If you are using self-signed or custom certificates, open the URL below in a new browser tab and accept the certificate, then retry the operation.
  __FIX__  Go to `https://nested-esxi-1.DOMAIN.com` and accept the exception.
