#!/bin/bash
. ../../conf/common.sh
get_conf

function list_device {
    host=$1
    disk=$2
    echo ssh $host parted $disk p 2>/dev/null
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

if [ $# -ne 5 ] && [ $# -ne 3 ] && [ $# -ne 5 ]
then
        echo $#
        echo "Description:"
        echo "  This script is used to read conf/all.conf then print/format disk partition which will be used as osd and journal, pls always do -l before -w"
        echo "Usage:"
        echo "  $0 [-l] hostname [disk,disk,...] or $0 [-w] hostname [disk,disk,...] partition_number partition_size [-a]"
        exit
fi

command=$1
osd_host_list=$2
disk=$3
osd_partition_count=$4
osd_partition_size=$5
index=0
for host in $osd_host_list
do
    index=$(($index + 1))
    #disk=$(eval echo \$deploy_osd_server_$index)
    osd_list=`echo $disk | sed 's/,/ /g'`
    echo "osd devices:"
    for item in $osd_list
    do
        if [[ $item == *"nvme"* ]]; then
            osd_disk=`echo $item | sed 's/p$//g'`
        else
            osd_disk=`echo $item | sed 's/[0-9]\+$//g'`
        fi
        echo "/dev/"$osd_disk >> tmp.osd
    done
    case "$command" in
    -l)
        echo "============start list partition on host $host============"
        ;;
    -w)
        echo "============start create partition on host $host============"
        ;;
    *)
        echo "pls input -l or -w"
        exit
        ;;
    esac
    for osd_disk in `sort -u tmp.osd | sed 's/\n//g'`
    do
        case "$command" in
        -l)
            list_device $host $osd_disk
            ;;
        -w)
            if [[ "$6" == "1" ]]
            then
                do_partition_to_dev $host $osd_disk $osd_partition_count $osd_partition_size 1
            else
                do_partition_to_dev $host $osd_disk $osd_partition_count $osd_partition_size
            fi
            ;;
    esac
    done

    rm tmp.osd
done
