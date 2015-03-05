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
    volume_total=`rbd ls | wc -l`
    client_total=`echo $list_client | sed 's/,/\n/g' | wc -l `
    res=`expr ${volume_total} % ${client_total}`
    if [ "$res" != "0" ]; then
      max_init_volume_num=`expr $volume_total / $client_total + 1`
    else
      max_init_volume_num=`expr $volume_total / $client_total`
    fi
    inited_volume=0
    client_inited_volume=0
    volumes=`rbd ls | sed 's/\n/ /g'`
    clients=`echo $list_client | sed 's/,/ /g'`
    for client in $clients
    do
        scp -q ../conf/rbd.fio $client:/opt/
        while [ $client_inited_volume -le $max_init_volume_num ]; do
            inited_volume=`expr $inited_volume + 1`
            volume=`echo ${volumes} | sed 's/ /\n/g' | sed -n ${inited_volume}'p'`
            echo "ssh $client rbd_name=${volume} fio /opt/rbd.fio --output=/opt/${volume}_fio.txt &"
            ssh $client "rbd_name=${volume} fio /opt/rbd.fio --output=/opt/${volume}_fio.txt &"&
            client_inited_volume=`expr $client_inited_volume + 1`
        done
        client_inited_volume=0
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
