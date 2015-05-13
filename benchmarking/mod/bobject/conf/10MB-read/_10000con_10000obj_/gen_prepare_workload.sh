#!/bin/bash

#change those before you run the scripts


SIZE=10
UNIT=MB
DRIVERS=5

CONTAINER=10000
OBJECT=100

ACCOUNT=cosbench
USER=operator
PASS=intel2012

URL=http://10.4.9.105/auth/v1.0

RAMPUP=90
RAMPDOWN=30

RUNTIME=300
TIMEOUT=300000

READ="read"
WRITE="write"

MODE=$READ

for workers in 0 1 2 3 4 5 6 7 8 9
do
	filename=${MODE}_${CONTAINER}con_${OBJECT}obj_${SIZE}${UNIT}_0${workers}w.xml
	rm $filename;
	echo '<?xml version="1.0" encoding="UTF-8"?>' >> $filename
	echo "<workload name=\"${MODE}_${CONTAINER}con_${OBJECT}obj_${SIZE}${UNIT}_0${workers}w\" description=\"INIT-PREPARE\">" >> $filename
		echo "<storage type=\"swift\" config=\"timeout=$TIMEOUT\" />" >> $filename
		echo "<auth type=\"swauth\" config=\"username=$ACCOUNT:$USER;password=$PASS;url=$URL;retry=9\" />" >> $filename
		echo '<workflow>' >> $filename
			echo '<workstage name="init">' >> $filename
			echo "<work type=\"init\" workers=\"$(($DRIVERS*4))\" config=\"containers=r($(($workers*1000+1)),$(($workers*1000+1000)));cprefix=${SIZE}${UNIT}-${MODE}\"/>" >> $filename
			echo '</workstage>' >> $filename
			echo '<workstage name="prepare">' >> $filename
				echo "<work type=\"prepare\" workers=\"320\" config=\"containers=r($(($workers*1000+1)),$(($workers*1000+1000)));objects=r(1,${OBJECT});cprefix=${SIZE}${UNIT}-${MODE};sizes=c($SIZE)$UNIT\"/>" >> $filename
			echo '</workstage>' >> $filename
		echo '</workflow>' >> $filename
	echo '</workload>' >> $filename
	echo "$filename generated!"
done
