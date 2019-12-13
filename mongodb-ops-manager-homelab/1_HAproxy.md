# HA Proxy VM

Steps to set up a trivial HA Proxy as the Load Balancer for MongoDB Ops Manager HTTP Service running on port `8080`.

## Quick commands

```bash
systemctl restart haproxy
systemctl status haproxy
open http://mms.cloud/haproxy?stats
```

## Set up the network

Taken and modified from steps listed [here](http://www.serverlab.ca/tutorials/linux/administration-linux/configure-centos-6-network-settings/
). See `00_vcenter.md`

## Set up HA Proxy

Taken and modified from steps listed [here](https://www.upcloud.com/support/haproxy-load-balancer-centos/)

```bash
ssh root@mms.cloud
yum info haproxy
yum install wget gcc pcre-static pcre-devel -y
wget http://www.haproxy.org/download/1.6/src/haproxy-1.6.3.tar.gz -O ~/haproxy.tar.gz
tar xzvf ~/haproxy.tar.gz -C ~/
cd ~/haproxy-1.6.3
make TARGET=linux2628
make install
cp /usr/local/sbin/haproxy /usr/sbin/
cp ~/haproxy-1.6.3/examples/haproxy.init /etc/init.d/haproxy
chmod 755 /etc/init.d/haproxy
mkdir -p /etc/haproxy
mkdir -p /run/haproxy
mkdir -p /var/lib/haproxy
touch /var/lib/haproxy/stats
useradd -r haproxy
haproxy -v
cat <<EOF > /etc/haproxy/haproxy.cfg
global
   log /dev/log local0
   log /dev/log local1 notice
   chroot /var/lib/haproxy
   stats socket /run/haproxy/admin.sock mode 660 level admin
   stats timeout 30s
   user haproxy
   group haproxy
   daemon

defaults
   log global
   mode http
   option httplog
   option dontlognull
   timeout connect 5000
   timeout client 50000
   timeout server 50000

frontend http_front
   bind *:80
   stats uri /haproxy?stats
   default_backend http_back

backend http_back
   balance roundrobin
   server mms-x.cloud  10.18.89.10:8080 check
   server mms-xi.cloud 10.18.89.11:8080 check
EOF

mkdir -p /run/haproxy/
vi /etc/rc.d/init.d/haproxy
# change
[ ${NETWORKING} = "no" ] && exit 0
# to
[[ ${NETWORKING} = "no" ]] && exit 0

systemctl daemon-reload
systemctl restart haproxy
systemctl status haproxy

curl http://10.18.89.2/haproxy?stats
curl http://mms.cloud/haproxy?stats

## Adding security 
firewall-cmd --permanent --zone=public --add-service=http
firewall-cmd --permanent --zone=public --add-port=8181/tcp
firewall-cmd --reload

cat <<EOF >> /etc/haproxy/haproxy.cfg
listen stats
   bind *:8181
   stats enable
   stats uri /
   stats realm Haproxy\ Statistics
   stats auth haproxy:PASSWORD
EOF

systemctl restart haproxy
systemctl status haproxy

echo "This should fail"
curl http://10.18.89.2:8181
#<html><body><h1>401 Unauthorized</h1>
#You need a valid user and password to access this content.
#</body></html>

## modified /etc/init.d/haproxy so that /run/haproxy/ directory is created upon server restart.
vi /etc/init.d/haproxy
start() {
  quiet_check
  if [ $? -ne 0 ]; then
    echo "Errors found in configuration file, check it with '$BASENAME check'."
    return 1
  fi

  echo -n "Starting $BASENAME: "
  # ADDING LINE BELOW
  mkdir -p /run/haproxy
  daemon $BIN -D -f $CFG -p $PIDFILE
  RETVAL=$?
  echo
  [ $RETVAL -eq 0 ] && touch $LOCKFILE
  return $RETVAL
}
```