#!/bin/bash

. ../../conf/all.conf
get_conf

#check the ceph-deploy
ceph-deploy --version

servers=`echo "$deploy_mon_servers,$deploy_osd_servers,$deploy_mds_servers,$deploy_rbd_nodes" | sed 's/,/\n/g' | sort -u | sed 's/\n//g'`

for host in $servers
do
    echo "============Settings on $host============"
    echo "/etc/apt/apt.conf"
    ssh $host cat /etc/apt/apt.conf | grep -v "#"
    echo ""
    echo "/etc/apt/sources.list"
    ssh $host cat /etc/apt/sources.list | grep -v "#"
    echo ""
    echo "/etc/wgetrc"
    ssh $host cat /etc/wgetrc | sed '/^$/d' | grep -v "#"
    ssh $host wget ceph.com
    ssh $host rm index.html
done
