if false;then
#bash prepare.sh
echo "start 128K Read"
date >> stat.log
#bash call-swift.sh stat >> stat.log
bash run1.sh 128KB-read read_100con_100obj_128KB_
	sleep 30
echo "128K read finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
#bash restart.sh
#fi

#if false; then
#bash prepare.sh
echo "start 128K Write"
date >> stat.log
bash call-swift.sh stat >> stat.log
bash run1.sh 128KB-write write_100con_100obj_128KB_
	sleep 30
echo "128K write finished..." >> stat.log
date >> stat.log
bash call-swift.sh stat >> stat.log
#bash restart.sh
fi

#if false; then
#bash prepare.sh
echo "start 10M read"
date >> stat.log
#bash call-swift.sh stat >> stat.log
bash run1.sh 10MB-read read_100con_100obj_10MB_
	sleep 30
echo "10M read finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
#bash restart.sh

if false;then
#bash prepare.sh
echo "start 10M write"
date >> stat.log
#bash call-swift.sh stat >> stat.log
bash run1.sh 10MB-write write_100con_100obj_10MB_
	sleep 30
echo "10M write finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
fi
echo "=================================Run Finished=============================="
