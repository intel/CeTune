#!/bin/bash
. ../conf/common.sh
get_conf

function check_disk {
    host=$1
    vdisk=$2
#`echo $2 | awk -F/ '{print $3}'`
    res=`ssh $host "fdisk -l | grep '$vdisk'"`
    if [ -z "$res" ]; then
	echo $host" does not attached "$vdisk
	exit
    fi
}
 
function dd_init {
    host=$1
    vdisk=$2
    echo "ssh $host \"dd if=/dev/zero of=$vdisk bs=1M &\" &"
    ssh $host "dd if=/dev/zero of=$vdisk bs=1M &"&
}

if [ "`check_fio_rbd`" = "true" ]; then
    rbd ls | while read volume
    do
        rbd_name=${volume}
        echo "fio conf/rbd.fio --output=${volume}_fio.txt &"
        fio conf/rbd.fio --output=${volume}_fio.txt &
    done
    echo "RBD initialization has been started by fio rbd engine,"
    echo "please check 'ceph -s' to see if it is finished"
else
    qemurbd=0
    nodes=`echo ${list_vclient} | sed 's/,/ /g'`
    for vclient in $nodes
    do
        check_disk $vclient $vdisk
    done
    for vclient in $nodes
    do
        echo "==== init rbd volume on vclient ===="
        dd_init $vclient $run_file
        qemurbd=1
    done
    if [ "$qemurbd" = "1" ]; then
        echo "RBD initialization has been started by qemu rbd,"
        echo "please check 'ceph -s' to see if it is finished"
    else
        echo "Can't detect fio rbd engine or vm in your setup,"
        echo "pls download fio rbd engine from https://github.com/axboe/fio"
    fi
fi
