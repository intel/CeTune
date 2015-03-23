#!/bin/bash

#-------------------------------------------
# Configurable Options
#-------------------------------------------

source ./header.sh

#-------------------------------------------
# Main
#-------------------------------------------

echo "=====================================" >> runid.log
echo "runid $RUNID" >> runid.log
echo "--------------" >> runid.log
echo "Swfit stat:" >> runid.log
#bash call-swift.sh stat >> runid.log

echo "--------------" >> runid.log
for node in `cat osd.lst`
do
	echo "node $node" >> runid.log
	ssh $node "df -h" >> runid.log
	echo "" >> runid.log
	echo "node $node ceph health status:" >> runid.log
	#ssh $node "ceph health -s" >> runid.log
	ssh $node "ceph health" >> runid.log
done

# Update the run number for the next test.
RUNID=`expr $RUNID + 1`
echo $RUNID > .run_number
