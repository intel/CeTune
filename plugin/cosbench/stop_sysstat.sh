#!/bin/bash

#-------------------------------------------
# Configurable Options
#-------------------------------------------

source ./header.sh

#-------------------------------------------
# Main 
#-------------------------------------------

if [ ! -f NodeList ]; then 
	echo "No NodeList file";
	exit;
fi

# stop sysstat monitoring
cat NodeList | while read node 
do 
	#skip blank line
	if [ -z "$node" ]; then continue; fi
	# if the first letter is not "#"
	if [ ${node:0:1} = '#' ]; then continue; fi

	echo "closing sar/iostat/vmstat on $node..."

	$SSHCMD $node "killall -q sleep"
	$SSHCMD $node "killall -q sar sadc iostat vmstat mpstat blktrace"
done

#$SSHCMD ceph-osd1 "killall -q blktrace"
