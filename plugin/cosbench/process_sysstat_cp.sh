#!/bin/bash

#-------------------------------------------
# Configurable Options
#-------------------------------------------


#-------------------------------------------
# Main 
#-------------------------------------------

if [ ! -f NodeList ]; then 
	echo "No NodeList file";
	exit;
fi
INSTALLDIR="/root/qing/auto"
OUTPUT=/$1

# post-processing
cat NodeList | while read node 
do 
	#skip blank line
	if [ -z "$node" ]; then continue; fi
	# if the first letter is not "#"
	if [ ${node:0:1} = '#' ]; then continue; fi

	echo "post-processing sar/iostat/vmstat data on $node ..."

	sadf -p -T -- -bBrwqWuR -P ALL -n DEV $INTERVAL 0 $OUTPUTDIR/sar_raw.log > $OUTPUTDIR/sar.log
#	$SSHCMD $node "awk '{ print \$1, \$2, \"0\", \$6, \$7, \$8; }' $OUTPUTDIR/sar_f.log > $OUTPUTDIR/sar.log"

	sleep 3 # sync-point 

	perl $INSTALLDIR/tool/sar2csv.pl $OUTPUTDIR/sar.log $OUTPUTDIR/sar.csv
	perl $INSTALLDIR/tool/iostat2csv.pl $OUTPUTDIR/iostat.log $OUTPUTDIR/iostat.csv
	perl $INSTALLDIR/tool/vmstat2csv.pl $OUTPUTDIR/vmstat.log $OUTPUTDIR/vmstat.csv
	perl $INSTALLDIR/tool/vmstat2csv.pl $OUTPUTDIR/vmstat.log $OUTPUTDIR/vmstat.csv
	sleep 3 # sync-point

	perl $INSTALLDIR/tool/csv2avg.pl $OUTPUTDIR/sar.csv $OUTPUTDIR/sar_avg.csv
	perl $INSTALLDIR/tool/csv2avg.pl $OUTPUTDIR/iostat.csv $OUTPUTDIR/iostat_avg.csv  
	perl $INSTALLDIR/tool/csv2avg.pl $OUTPUTDIR/vmstat.csv $OUTPUTDIR/vmstat_avg.csv

	sleep 3 # sync-point

	paste -d ',' $OUTPUTDIR/vmstat.csv $OUTPUTDIR/iostat.csv $OUTPUTDIR/sar.csv > $OUTPUTDIR/sysstat.csv
	cat $OUTPUTDIR/vmstat_avg.csv $OUTPUTDIR/iostat_avg.csv $OUTPUTDIR/sar_avg.csv > $OUTPUTDIR/sysstat_avg.csv
	
	dmesg -ktx > $OUTPUTDIR/dmesg.txt

done
