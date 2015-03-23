#!/bin/bash

for node in ceph-osd2 ceph-osd1 ceph-osd4 ceph-osd5
do
	ssh $node reboot
done
