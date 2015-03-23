
#bash prepare.sh
echo "start 10M read"
bash run1.sh 10MB-read read_100con_100obj_10MB_
	sleep 30
echo "10M read finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log

echo "==================RUN FINISHED=================="
