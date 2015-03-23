#!/bin/bash

while [ 1 ]
do
	sleep 10
	fin=`ssh ceph-osd2 "ps aux | grep ls"`
	osd="osd"
	echo "$fin"|grep -q "$osd"
	if [ $? -ne 0 ]
	then 
		echo "finish"
		break
	fi
done
