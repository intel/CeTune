#!/bin/bash
. ../conf/common.sh
get_conf

new_conf=ceph.conf.new
cp ceph.conf.tmp $new_conf

for mon in $deploy_mon_servers
do
    echo "[mon."$mon"]" >> $new_conf
    echo "    host = "$mon >> $new_conf
    public_addr=`print_user_ceph_conf | grep "public network\|public_network"`
    if [ ! -z "$public_addr" ]; then
        public_addr=`echo $public_addr | awk -F= '{print $2}'`
        search_kw=`get_subnet $public_addr`
        echo "    mon addr = "`get_host_ip $mon $search_kw` >> $new_conf
    fi
done
index=0
osd_disk_list=`echo $deploy_osd_servers | sed 's/,/ /g'`
for host in $osd_disk_list
do
    disk=$(eval echo \$$host)
    osd_list=`echo $disk | sed 's/,/ /g'`
    for item in $osd_list
    do
        osd_disk=`echo $item | awk -F: {'print $1'}`
        journal_disk=`echo $item | awk -F: {'print $2'}`
        echo "[osd.${index}]" >> $new_conf
	echo "    host = "${host} >> $new_conf
	
        public_addr=`print_user_ceph_conf | grep "public network\|public_network"`
        if [ ! -z "$public_addr" ]; then
            public_addr=`echo $public_addr | awk -F= '{print $2}'`
            search_kw=`get_subnet $public_addr`
            echo "    public addr = "`get_host_ip $host $search_kw` >> $new_conf
        fi
	
        cluster_addr=`print_user_ceph_conf | grep "cluster network\|cluster_network"`
        if [ ! -z "$cluster_addr" ]; then
            cluster_addr=`echo $cluster_addr | awk -F= '{print $2}'`
            search_kw=`get_subnet $cluster_addr`
            echo "    cluster addr = "`get_host_ip $host $search_kw` >> $new_conf
        fi
        
        echo "    osd journal = "$journal_disk >> $new_conf
	echo "    devs = "$osd_disk >> $new_conf
        index=$(($index + 1))
    done    
done

echo "Ceph.conf is generated as deploy/ceph.conf.new, you can copy to /etc/ceph/ceph.conf"
cat ${new_conf}
