#/bin/bash

file=$1
#echo "start health monitor"
run_blktrace=1;
for ((i=0; i < 999999; i++))
do
#    date >> $file
    health=`ssh gw2 "ceph -s"`
#    echo $health >> $file
    echo "$health"|grep -q "scrubbing"
    if [ $? -eq 0 ]
    then
	date >> $file
	echo $health >> $file
	#ssh gw2 "service ceph -a start osd > /dev/null"
	for sn in ceph-osd1 ceph-osd2 ceph-osd3 ceph-osd4 ceph-osd5
	do
	    ssh $sn "bash blktrace-all.sh"
	    run_blktrace=0;
	done
	break
    fi
    sleep 30
done
