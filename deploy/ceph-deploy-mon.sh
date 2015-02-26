#!/bin/bash

#. ../conf/all.conf
. ../conf/common.sh
get_conf

mon_list=`echo $deploy_mon_servers | sed 's/,/ /g'`

echo "============ceph-deploy new $mon_list==============="
ceph-deploy new $mon_list
error_check
echo 
echo "Please check the ceph.conf"
copy_to_conf "../conf/all.conf" mon
echo "***** ceph.conf *****"
cat ceph.conf
echo -e "*********************\n"
echo "Do you wanna to continue? (yes or no)"
if [ "`interact`" != "true" ]; then
    exit
fi

for mon_s in $mon_list
do
    echo "============create monitor on host $mon_s============"
    ceph-deploy --overwrite-conf mon create $mon_s
    error_check
done

sleep 10

for mon_s in $mon_list
do
    echo "============ceph-deploy gatherkeys $mon_s============"
    ceph-deploy gatherkeys $mon_s
    error_check
done

echo "============ceph-deploy admin host and push ceph.conf============"

ceph_nodes=`echo "$deploy_mon_servers,$deploy_osd_servers,$deploy_mds_servers,$deploy_rbd_nodes" | sed 's/,/\n/g' | sort -u | tr -s '\n' ' '`
for ceph_s in $ceph_nodes
do
    ceph-deploy --overwrite-conf admin localhost $ceph_s
    error_check
    ceph-deploy --overwrite-conf config push $ceph_s
    error_check
done
