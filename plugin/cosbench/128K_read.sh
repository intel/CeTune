
bash prepare.sh
echo "start 128K Read"
bash run1.sh 128KB-read read_100con_100obj_128KB_
	sleep 30
echo "128K read finished..." >> stat.log
date >> stat.log
bash call-swift.sh stat >> stat.log

echo "=================================Run Finished=============================="
