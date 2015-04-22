#!/bain/bash

. ../../conf/all.conf
get_conf

#check the ceph-deploy
ceph-deploy --version

servers=`echo "$deploy_mon_servers,$deploy_osd_servers,$deploy_mds_servers,$deploy_rbd_nodes" | sed 's/,/\n/g' | sort -u | sed 's/\n//g'`

for host in $servers
do
    echo "============Settings on $host============"
    echo "/etc/wgetrc"
#   ssh $host cat /etc/wgetrc | sed '/^$/d' | grep -v "#"
    i=`ssh $host "ls -l index.html* | wc -l"`
    ssh $host wget ceph.com
    if [ $i == 0 ]
        then
        a=`ssh $host "grep "Home Ceph" index.html"`
    else
        a=`ssh $host "grep "Home Ceph" index.html.$i"`
    fi
    if [ $a == "" ]
    then
        echo "Sorry, the proxy in $host is unavailiable!!!"
	#echo "Congratulations!, the proxy in $host is availiable"
    else
        echo $a
       # echo "Sorry, the proxy in $host is unavailiable!!!"
	echo "Congratulations!, the proxy in $host is availiable"
    ssh $host rm index.html*
    fi
done

