#!/bin/bash
. ../../conf/common.sh
get_conf

function list_device {
    host=$1
    disk=$2
    ssh $host parted $disk p 2>/dev/null
}

function do_partition_to_dev {
    host=$1
    disk=$2
    partition_count=$3
    partition_size=$4
    no_dd=$5
    part_disk $host $disk $partition_count $partition_size $no_dd
}

function part_disk {
    host=$1
    device=$2
    part_count=$3
    part_size=$4
    no_dd=$5
    if [ "$no_dd" != "1" ]; then
        echo "ssh $host dd if=/dev/zero of=$device bs=4M count=1 oflag=direct"
        ssh $host "dd if=/dev/zero of=$device bs=4M count=1 oflag=direct" 2>/dev/null
        echo "ssh $host parted $device  mklabel gpt &>/dev/null"
        ssh $host "parted $device  mklabel gpt &>/dev/null" 2>/dev/null
        start_pos="1"
        end_pos=$part_size
        for i in `seq 1 $part_count`
        do
            if [ -z $part_size ]; then
                end_pos=`ssh $host "parted $device p"  2>/dev/null | grep "Disk $device" | awk '{print $3}'`
                part_size="0"
            fi
            echo ssh $host "parted $device mkpart data $start_pos $end_pos"
            ssh $host "parted $device mkpart data $start_pos $end_pos &>/dev/null" 2>/dev/null
            start_pos=$end_pos
            end_pos=$(( ${start_pos%%[[:alpha:]]*} + ${part_size%%[[:alpha:]]*} ))${part_size##*[0-9]}
        done
    else
        start_pos=`ssh $host "parted $device p 2>/dev/null" 2>/dev/null | tac |sed -n '2p'| awk '{print $3}'`
        end_pos=$(( ${start_pos%%[[:alpha:]]*} + ${part_size%%[[:alpha:]]*} ))${part_size##*[0-9]}
        for i in `seq 1 $part_count`
        do
             echo ssh $host "parted $device mkpart journal $start_pos $end_pos"
             ssh $host "parted $device mkpart journal $start_pos $end_pos &>/dev/null" 2>/dev/null
             start_pos=$end_pos
             end_pos=$(( ${start_pos%%[[:alpha:]]*} + ${part_size%%[[:alpha:]]*} ))${part_size##*[0-9]}
        done
    fi
}

if [[ $# != 1 ]]
then
        echo "Description:"
        echo "  This script is used to read conf/all.conf then print/format disk partition which will be used as osd and journal, pls always do -l before -w"
        echo "Usage:"
        echo "  $0 [-l][-w]"
        exit
fi

command=$1

echo "deploy_osd_servers: $list_server"
osd_host_list=`echo $list_server | sed 's/,/ /g'`
index=0
for host in $osd_host_list
do
    echo "============start create partition on host $host============"
    index=$(($index + 1))
    #disk=$(eval echo \$deploy_osd_server_$index)
    disk=$(eval echo \$$host)
    osd_list=`echo $disk | sed 's/,/ /g'`
    echo "osd devices:"
    for item in $osd_list
    do
        osd_disk=`echo $item | awk -F: {'print $1'} | sed 's/[0-9]\+$//g'`
        journal_disk=`echo $item | awk -F: {'print $2'} | sed 's/[0-9]\+$//g'`
        if [[ $osd_disk == *"nvme"* ]]; then
            osd_disk=`echo $osd_disk | sed 's/p$//g'`
        fi
        if [[ $journal_disk == *"nvme"* ]]; then
            journal_disk=`echo $journal_disk | sed 's/p$//g'`
        fi
        echo $osd_disk >> tmp.osd
        echo $journal_disk >> tmp.journal
    done
    for osd_disk in `sort -u tmp.osd | sed 's/\n//g'`
    do
        if [ "$osd_partition_count" != "1" ] && [ "$osd_partition_size" = "" ]; then
            echo "pls set the osd_partition_size in conf/all.conf"
            exit
        fi
        case "$command" in
        -l)
            list_device $host $osd_disk
            ;;
        -w)
            do_partition_to_dev $host $osd_disk $osd_partition_count $osd_partition_size
            ;;
        *)
            echo "pls input -l or -w"
            exit
            ;;
    esac
    done

    echo "journal devices:"
    for journal_disk in `sort -u tmp.journal | sed 's/\n//g'`
    do
        #echo $journal_disk
        if [ "$journal_partition_count" != "1" ] && [ "$journal_partition_size" = "" ]; then
            echo "pls set the journal_partition_size in conf/all.conf"
            exit
        fi
        also_osd=`grep $journal_disk tmp.osd`
        if [ ! -z "$also_osd" ]; then
            no_dd=1
        fi
        case "$command" in
        -l)
            list_device $host $journal_disk
            ;;
        -w)
            do_partition_to_dev $host $journal_disk $journal_partition_count $journal_partition_size $no_dd
            ;;
        *)
            echo "pls input -l or -w"
            exit
            ;;
    esac
    done
    rm tmp.osd tmp.journal
done
