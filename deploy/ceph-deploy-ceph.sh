#!/bin/bash
. ../conf/common.sh
get_conf

#. ../conf/all.conf
#create a cluster so that you can use ceph-deploy to install ceph
servers=`echo "$deploy_mon_servers,$deploy_osd_servers,$deploy_mds_servers,$deploy_rbd_nodes" | sed 's/,/\n/g' | sort -u | sed 's/\n/ /g'`

echo "start Install ceph $deploy_ceph_version"

for host in $servers
do
    if [ ! -z $host ];then
        ceph_v=`ssh $host ceph -v | grep version`
        if [ ! -z "$ceph_v" ];then 
            echo $host is already installed ceph, $ceph_v
	    continue
        fi
        echo "Install ceph package on $host"
        if [ ! -z ${deploy_ceph_version} ]; then
            param=`echo ${deploy_ceph_version} | awk -F: '{print $1}'`
            version=`echo ${deploy_ceph_version} | awk -F: '{print $2}'`
            case $param in
                release)
                    ceph-deploy install --release ${version} ${host}
                    error_check
                ;;
                dev)
                    ceph-deploy install --dev ${version} ${host}
                    error_check
                ;;
                *)
                    ceph-deploy install --release ${param} ${host}
                    error_check
                ;;
            esac
        fi
    fi
done

echo "finish ceph ($deploy_ceph_version) installation"
