#!/bin/bash

SWIFT="ssh proxy /root/qing/ceph/call-swift.sh"

id=0
prefix=myobjects_

rm -f list
$SWIFT list $1 > list

echo `wc -l < list` objects

while [ $id -lt 1000 ]
do
	id=$(($id + 1))
	grep $prefix$id list >> /dev/null
	if [ $? -ne 0 ]
	then
		echo missing $prefix$id
	fi
done
