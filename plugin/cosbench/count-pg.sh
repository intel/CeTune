#!/bin/bash

pgid=$1
file=$2
node=`hostname -s | cut -dd -f2`
for i in `seq 1 12`
do
    osd=$(($node*12+$i-12))
    echo -n "ceph-$osd " >> $file
    ls /var/lib/ceph/osd/ceph-$osd/current| grep ^$pgid.*head$ |wc -l >> $file
    #echo "" >> $file
done


