#!/bin/bash

. ../conf/common.sh
get_conf

function install-ceph-dev-pkg {
    host=$1
    release_type=$2
    case $release_type in
        CentOS)
            ssh $host "yum -y install librados-devel librbd-devel"
        ;;
        Ubuntu)
            ssh $host "apt-get -y install librados-dev librbd-dev"
        ;;
    esac
}

function install-sysmetrics-collecter-pkg {
    host=$1
    release_type=$2
    case $release_type in
        CentOS)
            ssh $host "yum -y install sysstat"
        ;;
        Ubuntu)
            ssh $host "apt-get -y install sysstat"
        ;;
    esac
}

#create a cluster so that you can use ceph-deploy to install ceph
servers=`echo "$deploy_mon_servers,$deploy_osd_servers,$deploy_mds_servers,$deploy_rbd_nodes" | sed 's/,/\n/g' | sort -u | sed 's/\n/ /g'`
if [ "$#" != "0" ]; then
    deploy_ceph_version=$1
fi
echo "start Install ceph $deploy_ceph_version"

for host in $servers
do
    if [ ! -z $host ];then
        if [  -z ${deploy_ceph_version} ]; then
            continue
        fi
        ceph_v=`ssh $host ceph -v | grep version`
        if [ ! -z "$ceph_v" ];then 
            echo $host is already installed ceph, $ceph_v
        else
            echo "Install ceph package on $host"
            is_client=`echo $deploy_rbd_nodes | grep $host`
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
                    version=${param}
                    param="release"
                    ceph-deploy install --release ${version} ${host}
                    error_check
                ;;
            esac
        fi
	release_type=`lsb_release -i | awk -F: '{print $2}'`
        if [ ! -z "$is_client" ];then 
	    release_codename=`lsb_release -c | awk -F: '{print $2}'`
            install-ceph-dev-pkg $host $release_type
        fi
        install-sysmetrics-collecter-pkg $host $release_type
    fi
done

echo "finish ceph ($deploy_ceph_version) installation"
