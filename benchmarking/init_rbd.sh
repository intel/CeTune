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

nodes=`echo ${list_vclient} | sed 's/,/ /g'`
for vclient in $nodes
do
    check_disk $vclient $vdisk
done
for vclient in $nodes
do
    echo "==== init rbd volume on vclient ===="
    dd_init $vclient $run_file
done
echo "RBD initialization has been started, please check 'ceph -s' to see if it is finished"
