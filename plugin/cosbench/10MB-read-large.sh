
#bash prepare.sh
echo "start 10M read large"
echo "start 10M read large" >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log

#bash start-ceph-health.sh ceph-health.log & 
bash run1.sh 10MB-read-large read_10000con_100obj_10MB_
	sleep 30
echo "10M read large finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log

echo "=========================RUN FINISHED========================"
#killall bash
