#!/bin/bash
. ../conf/common.sh
get_conf

pool=rbd

function create_vdb_xml {
    mkdir -p ./vdbs
    index=0
    auth=$1
    nodes=`echo ${list_vclient} | sed 's/,/ /g'`
    for vm in $nodes
    do
        index=$(( $index + 1 ))
        volume=`rbd ls | sed -n "${index}p"`
        echo "<disk type='network' device='disk'>" > ./vdbs/$vm.xml
        echo "    <driver name='qemu' type='raw' cache='none'/>" >> ./vdbs/$vm.xml
	if [ "$auth" != "none" ] ;then
            echo "    <auth username='admin'>" >> ./vdbs/$vm.xml
            echo "        <secret type='ceph' uuid='"$auth"'/>" >> ./vdbs/$vm.xml
            echo "    </auth>" >> ./vdbs/$vm.xml
        fi
	echo -n "    <source protocol='rbd' name='$pool/" >> ./vdbs/$vm.xml
        echo "$volume' />">> ./vdbs/$vm.xml
        echo "    <target dev='vdb' bus='virtio'/>" >> ./vdbs/$vm.xml
        echo "    <serial>009ad738-1a2e-4d9c-bf22-1993c8c67ade</serial>" >> ./vdbs/$vm.xml
        echo "    <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>" >> ./vdbs/$vm.xml
        echo "</disk>" >> ./vdbs/$vm.xml
    done
}

function create_rbd_volume {
	if [ "${rbd_volume_count}" == '' ];then
    	nodes_num=`echo ${list_vclient} | sed 's/,/\n/g' | wc -l`
	else
		nodes_num=${rbd_volume_count}
	fi
    volume_num=`rbd ls | wc -l`
    need_to_create=0
    if [ $nodes_num -gt $volume_num ]; then
        need_to_create=$(( $nodes_num - $volume_num ))
    fi
    if [ $need_to_create -eq 0 ]; then
		echo "Do not need to create new rbd volume, your current rbd volume number is enough."
    else
        for i in `seq 1 $need_to_create`
        do
	    volume="volume-"`uuidgen`
            rbd create -p $pool --size ${volume_size} --image-format 2 $volume
        done
    fi
}

function rm_rbd_volume {
    rbd ls | while read volume
    do
        rbd rm $volume
    done
}

function get_secret {
    ceph_cluster_uuid=`ceph -s | grep cluster | awk '{print $2}'`
    echo $ceph_cluster_uuid
}

function create_secret {
    ceph auth get-or-create client.admin mon 'allow *' osd 'allow *' -o /etc/ceph/ceph.client.admin.keyring
    keyring=`cat /etc/ceph/ceph.client.admin.keyring | grep key | awk '{print $3}'`
    ceph_cluster_uuid=`ceph -s | grep cluster | awk '{print $2}'`
    echo "<secret ephemeral='no' private='no'>" > secret.xml
    echo "   <uuid>$ceph_cluster_uuid</uuid>" >> secret.xml 
    echo "   <usage type='ceph'>" >> secret.xml
    echo "       <name>client.admin secret</name>" >> secret.xml
    echo "   </usage>" >> secret.xml
    echo "</secret>" >> secret.xml
    virsh secret-define --file secret.xml
    virsh secret-set-value $ceph_cluster_uuid $keyring
}

#=================  main  ===================

function usage_exit {
    echo -e "usage:\n\t $0 {-h|create_rbd|remove_rbd|create_disk_xml}"
    exit
}

case $1 in
    -h | --help)
        usage_exit
	;;
    create_rbd)
        create_rbd_volume
	;;        
    remove_rbd)
        rm_rbd_volume
	;;        
    create_disk_xml) 
        echo "If you use CephX, pls make sure the secret.xml locates in vm-scripts"
        select opt in "secret.xml exists, continue with cephx" "help to generate secret.xml first than create volume" "continue with none auth"
        do
            case "$opt" in
                "secret.xml exists, continue with cephx")
                    auth=`get_secret`
        	    create_vdb_xml $auth
        	    break
        	    ;;
        	"help to generate secret.xml first than create volume")
        	    create_secret
                    auth=`get_secret`
        	    create_vdb_xml $auth
        	    break
        	    ;;
        	"continue with none auth")
        	    create_vdb_xml none
        	    break
        	    ;;
        	*) echo invalid option;;
            esac
        done
	;;
    *)
        usage_exit
	;;
esac
