
#bash prepare.sh
echo "start 128K write large"
echo "start 128K write large" >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log

bash run1.sh 128KB-write-large write_10000con_10000obj_128KB_
	sleep 30
echo "128K write large finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
ssh gw2 "ceph -s; ceph df" >> stat.log
echo "=========================RUN FINISHED========================"
