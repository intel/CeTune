#/bin/bash

file=$1
#echo "start health monitor"
#rm $file
for ((i=0; i < 99999999; i++))
do
    date >> $file
    health=`ssh gw2 "ceph -s"`
    echo $health >> $file
    echo "$health"|grep -q "40 up, 40 in"
    if [ $? -ne 0 ]
    then
	echo "osd down" >> $file
	#ssh gw2 "service ceph -a start osd > /dev/null"
	ssh gw2 "cd /ceph; ./start-ceph-manual.sh > /dev/null"
    fi
    
#    if [ $i = 600 ]
#    then
#	ssh ceph-osd1 "cd /tmp/multiperf; blktrace -d /dev/sdh -w 1800 -o osd1sdh.log &"
#    fi
    
    sleep 30
done
