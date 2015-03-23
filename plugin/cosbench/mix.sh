if false;then
#bash prepare.sh
echo "start 128K Mix-load"
date >> stat.log
#bash call-swift.sh stat >> stat.log
bash run1.sh 128KB-mix mix_100con_100obj_128KB_
	sleep 30
echo "128K mix-load finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
#bash restart.sh
fi

#if false; then
#bash prepare.sh
echo "start 10M Mix"
date >> stat.log
#bash call-swift.sh stat >> stat.log
bash run1.sh 10MB-mix mix_100con_100obj_10MB_
	sleep 30
echo "10M mix finished..." >> stat.log
date >> stat.log
#bash call-swift.sh stat >> stat.log
#bash restart.sh
echo "=================================Run Finished=============================="
