#!/bin/bash

for node in `cat osd.lst`
do
	ssh $node "slabtop -o > slabtop.6; free -g > mem.6"
done
