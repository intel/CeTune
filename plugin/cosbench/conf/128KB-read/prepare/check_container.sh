#!/bin/bash

SWIFT="ssh proxy /root/qing/ceph/call-swift.sh"

for con in `$SWIFT list`
do
    objs=`$SWIFT list $con | wc -l`
	if [ $objs -ne 1000 ]; then
        echo $con $objs objects
	fi
done
