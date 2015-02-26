#!/bin/bash
. ../conf/common.sh
get_conf

function check_ceph_space {
   volume_num=`echo $list_vclient | sed 's/,/\n/g' | wc -l` 
   total_size=$(( $volume_num * $volume_size / 1024 ))
   ceph_space=`ceph -s | grep pgmap | awk '{print $7}'`
   echo "Current ceph used data: $ceph_space GB, RBD volumes total expects size: $total_size GB"
}

function check_ps {
    host=$1
    ps_name=$2
    res=`ssh $host "ps aux | grep $ps_name" | grep -v "grep"`
    if [ ! -z "$res" ]; then
        echo $ps_name" is running"
        exit
    fi
}

function check_disk {
    disk=$1
    host=$2
    echo $disk" read_ahead_kb: "`ssh $host cat /sys/block/${disk}/queue/read_ahead_kb`
    echo "    max_sectors_kb: "`ssh $host cat /sys/block/${disk}/queue/max_sectors_kb`
    echo "    scheduler: "`ssh $host cat /sys/block/${disk}/queue/scheduler`
    echo "   "`ssh $host hdparm -W /dev/${disk} | grep caching `
    echo ""
}

function get_nic_from_conf {
    host=$1
    nic=`echo ${list_nic} | awk -F[:/,] -v var=$host '{for(i=1;i<=NF;i++)if($i==var){i++;print $i}}'`
    echo $nic
}

if [ $# -eq 1 ];then
    engine=$1
else
    engine='none'
fi

nodes=`echo ${list_vclient} | sed 's/,/ /g'`
vdisk=`echo $run_file | awk -F/ '{print $3}'`
for vclient in $nodes
do
    echo "==================== check on vm node $vclient ===================="
    res=`ssh $vclient "fio -v"`
    if [ ! -z "`echo  $res | grep not`" ]; then
        echo [ERROR]$vclient not installed fio yet
        exit
    else
        echo [LOG]$vclient fio check yes
    fi
    res=`ssh $vclient "fdisk -l | grep $vdisk 2>/dev/null"`
    if [ -z "$res" ]; then
        echo [ERROR]$vclient attaches no rbd volume
        exit
    else
        echo [LOG]$vclient rbd volume attachment check yes
    fi
    res=`ssh $vclient mpstat`
    if [ ! -z "`echo  $res | grep not`" ]; then
        echo [ERROR]$vclient not installed sysstat yet
        exit
    else
        echo [LOG]$vclient sysstat check yes
    fi
    check_ps $vclient "fio"
    check_ps $vclient "iostat"
    echo ""
done

nodes=`echo ${list_client} | sed 's/,/ /g'`
for client in $nodes
do
    echo "==================== check on client node $client ===================="
    nic=`get_nic_from_conf ${client}`
    echo "$nic "`ssh $client ifconfig $nic | grep MTU | awk '{print $5}'`
    res=`ssh $client "fio --enghelp | grep rbd"`
    if [ -z "$res" ]; then
        echo [ERROR]$client not installed fio-rbd yet
        exit
    else
        echo [LOG]$client fio-rbd check yes
    fi
    echo ""
    if [ ${engine} == 'cephfs' ];then
        res=`ssh $client "/opt/fio --enghelp | grep cephfs"`
        if [ -z "$res"  ]; then
        echo [ERROR]$client not installed fio-cephfs yet
            exit
        else
            echo [LOG]$client fio-cephfs check yes
        fi
        echo ""
    fi
    res=`ssh $client mpstat`
    if [ ! -z "`echo  $res | grep not`" ]; then
        echo [ERROR]$vclient not installed sysstat yet
        exit
    else
        echo [LOG]$vclient sysstat check yes
    fi
    echo ""
done

nodes=`echo ${list_ceph} | sed 's/,/ /g'`
for ceph in $nodes
do
    echo "==================== check on ceph node $ceph ===================="
    nic=`get_nic_from_conf ${ceph}`
    echo "$nic "`ssh $ceph ifconfig $nic | grep MTU | awk '{print $5}'`
    res=`ssh $ceph mpstat`
    if [ ! -z "`echo  $res | grep not`" ]; then
        echo [ERROR]$vclient not installed sysstat yet
        exit
    else
        echo [LOG]$vclient sysstat check yes
    fi
    check_ps $vclient "iostat"

    disk=$(eval echo \$$ceph)
    osd_list=`echo $disk | sed 's/,/ /g'`
    osd_disk=""
    journal_disk=""
    for item in $osd_list
    do
        osd_disk=$osd_disk" "`echo $item | awk -F: '{print $1}' | awk -F\/ '{print $3}'| sed 's/[0-9]//g'`
        journal_disk=$journal_disk" "`echo $item | awk -F: '{print $2}' | awk -F\/ '{print $3}' | sed 's/[0-9]//g'`
    done
    journal_disk=`echo ${journal_disk} | sed 's/ /\n/g' | sort -u | sed 's/\n/ /g'`
    echo "*****  osd devices:  *****"
    for disk in $osd_disk
    do
        check_disk $disk $ceph
    done
    echo "*****  journal disk:  *****"
    for disk in $journal_disk
    do
        check_disk $disk $ceph
    done
    echo ""
done
echo "==================== check ceph health ===================="
ceph -s
check_ceph_space

#check can ssh to all clients, ceph and vm
#check all ceph disk setting
#check all clients and ceph network

#check vm all attach vdb
#check ceph healthy

#check runid and dir
#check if in screen
