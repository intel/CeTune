
bash prepare.sh
echo "start 128K Write"
date >> stat.log
bash call-swift.sh stat >> stat.log
bash run1.sh 128KB-write write_100con_100obj_128KB_
	sleep 30
echo "128K write finished..." >> stat.log
date >> stat.log
bash call-swift.sh stat >> stat.log

echo "======================Run Finished========================"
