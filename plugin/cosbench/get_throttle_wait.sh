#!/bin/bash

source ./header.sh

for node in ceph-osd1 ceph-osd2 ceph-osd3 ceph-osd4
do
	$SSHCMD $node "sleep $RAMPUP; bash get_osd_throttle_wait.sh"
done 

$SSHCMD gw2 "cd /ceph; sleep $RAMPUP; bash get_mon_throttle_wait.sh"
