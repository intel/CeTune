#!/bin/bash

bash prepare.sh
echo "start 10M write"
echo "" >> stat.log
echo "start 10M write"
date >> stat.log
bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log

bash run1.sh 10MB-write write_100con_100obj_10MB_
	sleep 30

echo "10M write finished..." >> stat.log
date >> stat.log
bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log
echo "=================================Run Finished=============================="
