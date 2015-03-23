#!/bin/bash

#pg_version_old=0
while :
do
	pgmap_str=`ssh gw2 "ceph -s"| grep pgmap`
	pgmap=${pgmap_str#*v}
	pg_version_cur=${pgmap%%:*}
	pg_version_old=`cat pgmap_version`
	echo $pg_version_old
	if [ "$pg_version_cur" = "$pg_version_old" ];then
		break
	fi
	echo $pg_version_cur > pgmap_version
	sleep 60
done
echo "rebalance done"
#bash status-disk.sh > 128K_disk_util.log.2
#bash 128KB-read-large.sh
