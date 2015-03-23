#!/bin/bash
for node in `cat mon.lst osd.lst`
do 
    echo $node
    ssh $node "echo 3 > /proc/sys/vm/drop_caches; free -g"
done
