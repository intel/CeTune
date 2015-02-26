#!/bin/bash

if [ "$#" != "1" ]; then
    echo "$0 {auto***/result/latency/ | auto***/result/checkpoint}"
    exit
fi

for file in `find $1/ -name "ceph-osd*.csv"`
do
    python refresh_avg.py $file
done
