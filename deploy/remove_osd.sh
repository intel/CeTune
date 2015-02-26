#!/bin/bash
. ../conf/common.sh
get_conf

function remove_osd {
    index=0
    osd_id=0
    admin_host=`echo $osd_host_list | awk '{print $1}'`
    osd_host_list=`echo $deploy_osd_servers | sed 's/,/ /g'`
    for host in $osd_host_list
    do
        echo "============start remove osds from host $host============"
        index=$(($index + 1))
        disk=$(eval echo \$$host)
        osd_list=`echo $disk | sed 's/,/ /g'`
        #check if mon is alive first, if not skip stop osd gracefully
        timeout 3 ceph -s
        if [ "$?" = "0" ]; then       
            for item in $osd_list
            do
                ssh $host ceph osd out $osd_id
                ssh $host stop ceph-osd id=$osd_id
                ssh $host ceph osd crush remove osd.$osd_id
                ssh $host ceph auth del osd.$osd_id
                ssh $host ceph osd rm $osd_id
                osd_id=$(($osd_id + 1))
            done
        fi
        echo "rm -r /var/lib/ceph/osd"
        ssh $host rm -rf /var/lib/ceph/osd/*
        ssh $host killall ceph-osd
        ssh $host umount /var/lib/ceph/osd/*
        ssh $host rm -rf /var/lib/ceph/*
        ssh $host rm -f /etc/ceph/ceph.client.admin.keyring*
        rm_uuid_from_fstab $host
    done
    echo "============finish removing osd============"
}

function remove_mon {
    osd_host_list=`echo $deploy_osd_servers | sed 's/,/ /g'`
    index=0
    osd_id=0
    admin_host=`echo $osd_host_list | awk '{print $1}'`
    
    echo "============start remove mon from host $admin_host============"
    mon_host_list=`echo $deploy_mon_servers | sed 's/,/ /g'`
    for mon_host in $mon_host_list
    do
        ceph-deploy mon destroy $mon_host
    done   
    for mon_host in $mon_host_list
    do
        ssh $mon_host kill `ps aux | grep ceph | awk '{print $2}'`
        echo "rm -r /var/lib/ceph/mon"
        ssh $mon_host rm -f /etc/ceph/*
        ssh $mon_host rm -rf /var/lib/ceph/*
    done
    echo "============finish removing mon============"
    rm ceph.log
}

function remove_mds {
    mds_c=`echo $deploy_mds_servers | awk -F"," '{print NF}'`
    
    timeout 3 ceph -s
    if [ "$?" = "0" ]; then       
        for idx in `seq 1 ${mds_c}`
        do
            mds_s=`echo $deploy_mds_servers | awk -F"," '{print $'$idx'}'`
            ceph-deploy mds destroy $mds_s
            error_check
        done
    fi
    ssh $host killall ceph-mds
    ssh $host rm -rf /var/lib/ceph/bootstrap-mds/
    ssh $host rm -rf /var/lib/ceph/mds/
}

function forgetkeys {
    echo "ceph-deploy forgetkeys"
    ceph-deploy forgetkeys
    rm -f /etc/ceph/*
    rm -rf /var/lib/ceph/*
}


case $1 in
    mon)
	remove_mon
        forgetkeys
    ;;
    osd)
	remove_osd
    ;;
    mds)
	remove_mds
    ;;
    all)
	remove_osd
	remove_mds
	remove_mon
        forgetkeys
    ;;
    *)
        echo "You can only remove mon/osd/mds/all"
        exit
    ;;
esac
