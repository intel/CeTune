#!/bin/bash

#1. generate a vm xml
function set_vm_xml {
    vmxml=$1
    vclient_name=$2
    cpuset=$3
    img_path=$4
    mac_address=$5

    echo '<domain type="kvm">' > $vmxml
    echo '    <name>'${vclient_name}'</name>' >> $vmxml
    echo '    <memory>524288</memory>' >> $vmxml
    echo '    <vcpu>1</vcpu>' >> $vmxml
    echo '    <cputune>' >> $vmxml
    echo '        <vcpupin vcpu="0" cpuset="'${cpuset}'"/>' >> $vmxml
    echo '    </cputune>' >> $vmxml
    echo '    <os>' >> $vmxml
    echo '        <type>hvm</type>' >> $vmxml
    echo '        <boot dev="hd"/>' >> $vmxml
    echo '    </os>' >> $vmxml
    echo '    <features>' >> $vmxml
    echo '        <acpi/>' >> $vmxml
    echo '    </features>' >> $vmxml
    echo '    <clock offset="utc">' >> $vmxml
    echo '        <timer name="pit" tickpolicy="delay"/>' >> $vmxml
    echo '        <timer name="rtc" tickpolicy="catchup"/>' >> $vmxml
    echo '    </clock>' >> $vmxml
    echo '    <cpu mode="host-model" match="exact"/>' >> $vmxml
    echo '    <devices>' >> $vmxml
    echo '        <disk type="file" device="disk">' >> $vmxml
    echo '            <driver name="qemu" type="raw" cache="none"/>' >> $vmxml
    echo '            <source file="'${img_path}'" />' >> $vmxml
    echo '            <target bus="virtio" dev="vda"/>' >> $vmxml
    echo '        </disk>' >> $vmxml
    echo '        <interface type="bridge" >' >> $vmxml
    echo '            <source bridge ="br0"/>' >> $vmxml
    echo '            <mac address ="'$mac_address'"/>' >> $vmxml
    echo '        </interface>' >> $vmxml
    echo '        <serial type="pty"/>' >> $vmxml
    echo '        <input type="tablet" bus="usb"/>' >> $vmxml
    echo '        <graphics type="vnc" autoport="yes" keymap="en-us" listen="0.0.0.0"/>' >> $vmxml
    echo '    </devices>' >> $vmxml
    echo '</domain>' >> $vmxml
}


function usage_exit {
    echo -e "usage:\n\t $0 cpuset_start vm_num_per_client img_path_dir ip_prefix ip_fix"
    exit
}

function main {
    mac_address_fix=01
    mac_address_prefix="52:54:00:b2:3c:"
    vm_num=0
    
    mkdir -p $img_path_prefix"/tmp"
    mkdir -p vmxml
    
    if [ ! -f vclient.tmp.img ]; then
        echo " Download the vclient.tmp.img from 10.239.34.45 "
        scp $vm_image_locate_server:/home/xuechendi/remote_access/vclient.tmp.img vclient.tmp.img
        if [ "$?" != "0" ]; then
            echo "Downloading failed"
            exit
        fi
    fi
    nodes=`echo ${list_vclient} | sed 's/,/ /g'`
    for node in $nodes
    do
        echo "create $node xml"
    #====== create vm xml ======
        vmxml=$node".xml"
        vmname=$node
        img_path=$img_path_prefix"/"$node".img"
        mac_address=$mac_address_prefix$mac_address_fix
        set_vm_xml "vmxml/${vmxml}" $vmname $cpuset $img_path $mac_address
        cpuset=$(( $cpuset + 1 ))
        vm_num=$(( vm_num + 1 ))
        if [ "$vm_num" = "$vm_num_per_client" ];then
            vm_num=0
            cpuset=$cpuset_start
        fi
        mac_address_fix=$(( $mac_address_fix + 1 ))
        if [ "$mac_address_fix" = "100" ];then
            mac_address_prefix="52:54:00:b2:3b:"
            mac_address_fix=01
        fi

        echo "copy tmp.img as $node"
    #===== edit vm img ======
        cp vclient.tmp.img $img_path
        echo "edit $node img"
        img_path_tmp=${img_path_prefix}"/tmp"
        mount -o loop,offset=1048576 ${img_path} ${img_path_tmp}

        echo ${node} > ${img_path_tmp}/etc/hostname
        ip=$ip_prefix"."$ip_fix
        echo "auto eth0" >> ${img_path_tmp}/etc/network/interfaces
        echo "iface eth0 inet static" >> ${img_path_tmp}/etc/network/interfaces
        echo "address "${ip} >> ${img_path_tmp}/etc/network/interfaces
        echo "netmask 255.255.255.0" >> ${img_path_tmp}/etc/network/interfaces
        ip_fix=$(( $ip_fix + 1 ))
    
        umount ${img_path_tmp}
    
    #===== add to client /etc/hosts ======
    done
}

echo "$0 $1 $2 $3 $4 $5"

if [ "$#" != "5" ]; then
    usage_exit
fi

cpuset=$1
vm_num_per_client=$2
img_path_prefix=$3
ip_prefix=$4
cpuset_start=$cpuset
if [ -z "$5" ]; then
    ip_fix=201
fi
. ../conf/common.sh
get_conf
main $cpuset_start $vm_num_per_client $img_path_dir $ip_prefix $ip_fix
