#!/bin/bash

for node in ceph-osd1 ceph-osd2 ceph-osd3 ceph-osd4 ceph-osd5
do
	ssh $node "echo 100 > /proc/sys/vm/vfs_cache_pressure"
done
