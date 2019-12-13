# Operating System Tunnables

Note: This is not on the homelab but rather an AWS Instance. However, most settings are applicable...

## AWS Linux RHEL 7.3: Best Practices

Follow the [Production Checklist](https://docs.mongodb.com/v3.2/administration/production-checklist-operations/) for latest and greatest.

- Disable SELINUX (if not required)
- Disable THP
- Create single partition on EBS
- Create xfs
- Mount on /data
- Remove readahead
- Configure NUMA
- Disable tuned
- file/pid limits
- keepalive settings
- file permissions
- Update ULIMITS

```bash
### Disable SELINUX #######################################
vi /etc/selinux/config
  SELINUX=disabled
reboot
ssh -i dianaAws.pem ec2-user@<IP>
sestatus

### Disable THP ###########################################
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
grep -i HugePages_Total /proc/meminfo
cat /proc/sys/vm/nr_hugepages
sysctl vm.nr_hugepages
# or [Init script](https://docs.mongodb.com/v3.2/tutorial/transparent-huge-pages/)
# or sudo chkconfig --add disable-transparent-hugepages
sudo wget -O /etc/init.d/disable-transparent-hugepages https://git.io/viv32
sudo chmod 755 /etc/init.d/disable-transparent-hugepages
sudo chkconfig disable-transparent-hugepages on


### Create single partition ###############################
lsblk
sudo su
fdisk /dev/xvdf
  p
  n <Enter All Defaults>
  w
partprobe

### Create xfs ############################################
mkfs.xfs -n size=64k -f /dev/xvdf1
blkid /dev/xvdf1

### Mount on /data ########################################
sudo mount /dev/xvdf1 /data -t xfs -o defaults,auto,noatime,noexec,nodiratime,nofail
# noatime - file access time
# nodiratime - dir inode access time
# nofail - Do not report errors for this device if it does not exist.

lsblk
df -H | grep data

### Remove readahead ######################################
sudo blockdev --report  /dev/xvdf1
sudo blockdev --setra 0 /dev/xvdf1


### Configure NUMA ########################################
which numactl
yum -y install numactl
echo 0 | sudo tee /proc/sys/vm/zone_reclaim_mode
sudo sysctl -w vm.zone_reclaim_mode=0

### Disable tuned #########################################
sudo tuned-adm off

### file/pid limits for 'large systems' ###################
sysctl -w fs.file-max=98000
sysctl -w kernel.pid_max=64000
sysctl -w kernel.threads-max=64000
# or to persist the changes
# echo "fs.file-max=98000" >> /etc/sysctl.conf

### Keep alive settings ###################################

### Not Persistent:
sysctl net.ipv4.tcp_keepalive_time
echo 120 > /proc/sys/net/ipv4/tcp_keepalive_time
### Persistent:
/etc/sysctl.conf
net.ipv4.tcp_keepalive_time = 300

### file permissions ######################################
sudo  chown mongod:mongod /data

### Swap space ############################################
### repartition the /
echo "TODO"
### add a small EBS volume
echo "TODO"
### add a 512MB swap file on the /
sudo su
dd if=/dev/zero of=/swapfile bs=1024 count=524288
chown root:root /swapfile
chmod 0600 /swapfile
mkswap /swapfile
swapon /swapfile
vi /etc/fstab
  /swapfile none swap sw 0 0
free -m
swapon -s
less /proc/meminfo | grep Swap

### Ulimits
echo "mongod - fsize unlimited
mongod - cpu unlimited
mongod - as unlimited
mongod - nofile 64000
mongod - rss unlimited
mongod - nproc 64000" | sudo tee -a /etc/security/limits.d/99-mongodb.conf
```