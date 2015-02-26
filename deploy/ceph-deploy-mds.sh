#!/bin/bash

. ../conf/all.conf


mds_c=`echo $deploy_mds_servers | awk -F"," '{print NF}'`

for idx in `seq 1 ${mds_c}`
do
    mds_s=`echo $deploy_mds_servers | awk -F"," '{print $'$idx'}'`
    ceph-deploy mds create $mds_s
    error_check
done
