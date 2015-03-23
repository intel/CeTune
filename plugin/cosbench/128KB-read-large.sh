#!/bin/bash

#bash prepare.sh
echo "start 128K read large"
echo "start 128K read large" >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log

#bash start-ceph-health.sh &
bash start-ceph-health.sh ceph-health.log &
bash run1.sh 128KB-read-large read_10000con_10000obj_128KB_
	sleep 30
echo "128K read large finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log
echo "=========================RUN FINISHED========================"
killall bash
