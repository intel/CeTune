#!/bin/bash

for node in `cat osd.lst`
do
	scp $node:~/slabtop.* $node:~/mem.* ../slabtop/$node
	scp -r ../slabtop 192.168.3.101:/data2/yujie/
done
