# Docker

## Docker Engine

- Note: This is being isntalled on `docker.cloud` at `10.18.89.13` 
- Note: Following steps listed [here](https://docs.docker.com/engine/installation/linux/docker-ce/centos/)
- Install

    ```bash
    yum --enablerepo=extras install epel-release
    yum remove docker \
                    docker-common \
                    docker-selinux \
                    docker-engine
    yum install -y yum-utils device-mapper-persistent-data lvm2
    yum-config-manager \
        --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo
    yum-config-manager --enable docker-ce-edge
    yum-config-manager --enable docker-ce-test
    yum makecache fast
    yum install -y docker-ce
    ```
- Start

    ```bash
    systemctl start docker
    docker run hello-world
    ```
- Create user and group

    ```bash
    groupadd docker
    usermod -aG docker $
    docker run hello-world
    ```
- Enable service `systemctl enable docker.service`
- Configure Network

    ```bash
    ## IP forwarding
    mkdir -p /usr/lib/systemd/network/
    touch /usr/lib/systemd/network/80-container-host0.network
    cat <<EOF > /usr/lib/systemd/network/80-container-host0.network
    [Network]
    IPForward=kernel
    # OR
    IPForward=true
    EOF
    cat /etc/resolv.conf
    echo <<EOF > /etc/docker/daemon.json
    {
    "dns": ["10.0.0.1", "8.8.8.8", "8.8.4.4" ]
    }
    EOF
    ##
    systemctl restart  docker docker pull hello-world

    ## Test
    docker run --rm -it alpine ping -c4 docker.cloud
    # --- docker.cloud ping statistics ---
    # 4 packets transmitted, 4 packets received, 0% packet loss

    ## Firewall Rules
    firewall-cmd --permanent --zone=public --add-port=2376/tcp
    firewall-cmd --permanent --zone=public --add-port=2375/tcp
    firewall-cmd --reload
    ```

## Compose

- Note: Following steps listed [here](https://docs.docker.com/compose/install/)
- Install

    ```bash
    curl -L https://github.com/docker/compose/releases/download/1.14.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    docker-compose --version
    ```

## Run mongo in a container

```bash
mkdir -p /mongod-data/27017
chcon -Rt svirt_sandbox_file_t !$
docker pull mongo:3.5
docker run -p 27017:27017 --add-host="27017.docker.cloud:10.18.89.17" -h 27017.docker.cloud --name docker-27017 -v /mongod-data/27017:/data/db  -it  --entrypoint /bin/sh --rm --privileged  -d mongo:3.5
docker exec -it docker-27017 /bin/sh
```

## Install Automation Agent (AA) in `docker.cloud`

```bash
curl -OL http://mms.cloud:80/download/agent/automation/mongodb-mms-automation-agent-manager-3.2.12.2107-1.x86_64.rhel7.rpm
rpm -U mongodb-mms-automation-agent-manager-3.2.12.2107-1.x86_64.rhel7.rpm
vi /etc/mongodb-mms/automation-agent.config
mmsGroupId=123
mmsApiKey=abc
mmsBaseUrl=http://mms.cloud:80
mkdir -p /data
chown mongod: /data
systemctl start mongodb-mms-automation-agent.service

Install MA and BA from http://mms.cloud/v2/123#deployment/servers
REVIEW & DEPLOY
CONFIRM & DEPLOY

semanage port -a -t mongod_port_t -p tcp 27017
iptables -A INPUT  -s 10.18.89.0/24 -p tcp --destination-port 27017 -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -d 10.18.89.0/24 -p tcp --source-port 27017 -m state --state ESTABLISHED -j ACCEPT
iptables-save > /etc/iptables.conf
iptables-restore < /etc/iptables.conf
iptables -L | grep 89
firewall-cmd --get-active-zones
firewall-cmd --permanent --zone=public --add-port=27017/tcp
firewall-cmd --reload
```