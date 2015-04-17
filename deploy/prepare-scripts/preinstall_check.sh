#!/bin/bash

. ../../conf/all.conf
get_conf

#check the ceph-deploy
ceph-deploy --version

servers=`echo "$deploy_mon_servers,$deploy_osd_servers,$deploy_mds_servers,$deploy_rbd_nodes" | sed 's/,/\n/g' | sort -u | sed 's/\n//g'`

for host in $servers
do
    echo "============Settings on $host============"
    ssh $host apt-get update
    statu=$?
    echo $statu
    if [ $statu -gt 0 ]
       then
       flag_1=1
       host_apt_proxy_down=${host_apt_proxy_down}" "${host}
    fi
    echo "/etc/wgetrc"
#   ssh $host cat /etc/wgetrc | sed '/^$/d' | grep -v "#"
    ssh $host wget ceph.com
    if [ $? -gt 0 ]
        then
        flag_2=1
        host_wget_proxy_down=${host_wget_proxy_down}" "${host}
    fi
    ssh $host rm index.html
done
    if [ ${flag_1} -eq 1 ]
        then
        echo "the proxy of ${host_apt_proxy_down} is unvaliable,you need to edit /etc/apt/apt.conf, /etc/environment or /etc/yum.conf"
       echo ""
    fi
    if [ ${flag_2} -eq 1 ]
        then
        echo "the proxy in /etc/wgetrc of ${host_wget_proxy_down} is unvaliable"
        echo ""
   fi
