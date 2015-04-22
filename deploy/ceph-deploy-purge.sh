#!/bin/bash

. ../conf/common.sh
get_conf

list_ceph=`echo ${deploy_osd_servers},${deploy_rbd_nodes},${deploy_mon_servers},${deploy_mds_servers} | sed 's/,/\n/g' | sort -u | sed 's/\n/ /g'`

for host in $list_ceph
do
    ssh ${host} killall -9 ceph-osd
    ssh ${host} killall -9 ceph-mon
    ceph-deploy purge ${host}
    error_check
    ceph-deploy purgedata ${host}
    error_check
done
ceph-deploy forgetkeys
error_check
