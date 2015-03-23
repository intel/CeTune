#!/bin/bash

log_file=$1
for node in `cat osd.lst`
do
    echo $node >> $log_file
    ssh $node "df -h" >> $log_file
    echo "" >> $log_file
done
