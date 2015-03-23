#!/bin/bash
a=0
#ssh gw2 "service ceph -a start osd"
for ((i=0; i < 10; i++))
do
	if [ $a = 0 ]
	then
		echo $i
		a=1
	fi
	#i=$i-1;
done
