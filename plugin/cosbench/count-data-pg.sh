#!/bin/bash

#pgid=$1
file=$1

cd pg_dist
rm -r $file
mkdir $file
for node in `cat ../osd.lst`
do
	ssh $node "rm $file; bash count-pg.sh $pgid $file "
	scp $node:$file $file/$node
	cat $file/$node >> $file/$file
done
