
#bash prepare.sh
date >> stat.log
echo "start librados 10M read large"
ssh gw2 "rados df" >> stat.log
bash run1.sh 10MB-read-large read_1000con_1000obj_10MB_
	sleep 30
echo "librados 10M read large finished..." >> stat.log
ssh gw2 "rados df" >> stat.log
date >> stat.log

#bash call-swift.sh stat >> stat.log

if false; then
#bash prepare.sh
date >> stat.log
echo "start 10M write large"
bash run1.sh 10MB-write-large write_1000con_1000obj_10MB_
	sleep 30
echo "10M write large finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
fi
echo "=================================Run Finished=============================="
