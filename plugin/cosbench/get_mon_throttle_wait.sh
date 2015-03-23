#!/bin/bash

node=`hostname -s | cut -dd -f2`
for t in `seq 1 60`
do
	ceph --admin-daemon /var/run/ceph/ceph-mon.a.asok perf dump >> ceph-mon.a.perf
    	sleep 5
done
