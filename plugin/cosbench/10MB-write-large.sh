#!/bin/bash

#bash prepare.sh
echo "start 10M write large"
echo "start 10M write large" >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log

#bash start-ceph-health.sh ceph-health.w1027.log &
bash run1.sh 10MB-write-large write_10000con_100obj_10MB_
	sleep 30

echo "10M write large finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log
echo "=================================Run Finished=============================="
#killall bash
