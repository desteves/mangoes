FROM centos:7

ENV H /home/root
ENV PATH ${PATH}:${H}/

EXPOSE 27017

WORKDIR ${H}
RUN    yum update -y   \
    && yum install -y  \ 
           numactl     \
           cyrus-sasl-plain  \
           cyrus-sasl-gssapi \
           krb5-libs \
           libcurl   \
           libpcap   \
           net-snmp  \
           openldap  \
           openssl   \
           sysstat   \
           nc        \
    && yum clean all \
    && ulimit -f unlimited \
    && ulimit -t unlimited \
    && ulimit -v unlimited \
    && ulimit -n 64000     \
    && ulimit -m unlimited \
    && ulimit -u 32000     \
    && ulimit -s 4096      \
    && echo "kernel.pid_max=64000" >> /etc/sysctl.conf            \
    && echo "net.ipv4.tcp_keepalive_time=300" >> /etc/sysctl.conf \
    && echo "kernel.threads-max=64000" >> /etc/sysctl.conf        \
    && echo "vm.swappiness=1" >> /etc/sysctl.conf         \
    && echo "vm.max_map_count=128000" >> /etc/sysctl.conf \
    && echo "fs.file-max=98000" >> /etc/sysctl.conf       \
    && echo "vm.zone_reclaim_mode=0" >> /etc/sysctl.conf  

# ADD https://github.com/desteves/mongos-for-cf/docker/docker-entrypoint.sh ${H}
ADD docker-entrypoint.sh ${H}

ENTRYPOINT ["/bin/bash"]
CMD        ["./docker-entrypoint.sh"]