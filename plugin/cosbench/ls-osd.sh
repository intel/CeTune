#!/bin/bash

for node in ceph-osd1 ceph-osd2 ceph-osd3 ceph-osd4 ceph-osd5
do
	ssh $node "bash ls-osd.sh"
done
