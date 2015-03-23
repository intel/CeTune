


echo "start 10M read"
bash run1.sh 10M read_10con_10obj_10MB_
	sleep 30
echo "10M read finished..." >> stat.log
date >> stat.log
bash call-swift.sh stat >> stat.log

