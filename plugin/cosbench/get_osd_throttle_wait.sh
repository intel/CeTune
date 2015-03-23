#!/bin/bash

node=`hostname -s | cut -dd -f2`
for t in `seq 1 60`
do
    for i in `seq 1 10`
    do
    	osd=$(($node*10+$i-10))
    	ceph --admin-daemon /var/run/ceph/ceph-osd.$osd.asok perf dump >> ceph-osd.$osd.perf
    done
    sleep 5
done
