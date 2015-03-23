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

mkdir -p $RESULTDIR
#cp xlsm/summary.xlsm $RESULTDIR/
#cp xlsm/summary_new.xlsm $RESULTDIR/

cat NodeList | while read node 
do 
	#skip blank line
	if [ -z "$node" ]; then continue; fi
	# if the first letter is not "#"
	if [ ${node:0:1} = '#' ]; then continue; fi

	mkdir -p $RESULTDIR/$node
	$SCPCMD $node:$OUTPUTDIR/*.csv $RESULTDIR/$node/
	$SCPCMD $node:$OUTPUTDIR/*.txt $RESULTDIR/$node/
	$SCPCMD $node:$OUTPUTDIR/*.log* $RESULTDIR/$node/
	$SCPCMD $node:$OUTPUTDIR/*.dat* $RESULTDIR/$node/
done

cd $RESULTDIR
tar -czf perf.tar.gz *
rm -f $RESULTRT/perf.tar.gz
mv perf.tar.gz $RESULTRT/perf.tar.gz
