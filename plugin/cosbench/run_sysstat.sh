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

#start sysstat monitoring
cat NodeList | while read node 
do 
	#skip blank line
	if [ -z "$node" ]; then continue; fi
	# if the first letter is not "#"
	if [ ${node:0:1} = '#' ]; then continue; fi

	i=$INTERVAL
	c=$(( $RUNTIME / $INTERVAL ))

	echo "collecting sar/iostat/vmstat on $node ..."

	$SSHCMD $node "dmesg -C; dmesg -c >> /dev/null"
#	num_processors=`$SSHCMD $node cat /proc/cpuinfo | grep processor | wc -l`
#	if [ $num_processors -eq 1 ]; then
#	        $SSHCMD $node "sar -bBrwqWuR -o ${OUTPUTDIR}/sar_raw.log $INTERVAL > /dev/null &"
#	else
	$SSHCMD $node "sleep $RAMPUP; sar -bBrwqWuR -P ALL -n DEV -o ${OUTPUTDIR}/sar_raw.log $i $c > /dev/null &"
#	fi

	$SSHCMD $node "sleep $RAMPUP; iostat -d -k -t -x $i $c > ${OUTPUTDIR}/iostat.log &"
	$SSHCMD $node "sleep $RAMPUP; vmstat -n $i $c > ${OUTPUTDIR}/vmstat.log &"
	$SSHCMD $node "sleep $RAMPUP; mpstat -P ALL $i $c > ${OUTPUTDIR}/mpstat.log &"

#	$SSHCMD $node "sleep $RAMPUP; cd $INSTALLDIR/tool; bash collect_interrupt.sh $OUTPUTDIR &"
#	$SSHCMD $node "sleep $RAMPUP; cd $INSTALLDIR/tool; bash collect_softirq.sh $OUTPUTDIR &"
done

