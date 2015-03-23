#!/bin/bash

#change those before you run the scripts

#source ../global.sh
KEY="AQCMroJRSAzvFhAAuJH8OH8OiPn703yysJIEaw=="
SIZE=10
UNIT=MB
DRIVERS=1

CONTAINER=100
OBJECT=100

MON_IP=192.168.4.100

RAMPUP=90
RAMPDOWN=30

RUNTIME=300
TIMEOUT=300000

READ="read"
WRITE="write"

MODE=$READ
rm -rf *.xml
for workers in 5 10 20 40 80 160 320 640 1280 2560
do
	filename=${MODE}_${CONTAINER}con_${OBJECT}obj_${SIZE}${UNIT}_$(($workers*$DRIVERS))w.xml
	echo '<?xml version="1.0" encoding="UTF-8"?>' >> $filename
	echo "<workload name=\"${MODE}_${CONTAINER}con_${OBJECT}obj_${SIZE}${UNIT}_$(($workers*$DRIVERS))w\" description=\"`echo $MODE | tr '[:lower:]' '[:upper:]'`-ONLY\">" >> $filename
		echo "<storage type=\"librados\" config=\"timeout=$TIMEOUT;accesskey=admin;endpoint=$MON_IP;secretkey=$KEY\" />" >> $filename
		echo '<workflow>' >> $filename
			echo '<workstage name="main">' >> $filename
				echo "<work name=\"${SIZE}${UNIT}\" workers=\"$(($workers*$DRIVERS))\" rampup=\"$RAMPUP\" runtime=\"$RUNTIME\" rampdown=\"$RAMPDOWN\">" >> $filename
					echo "<operation type=\"$MODE\" ratio=\"100\" config=\"containers=u(1,${CONTAINER});objects=u(1,${OBJECT});sizes=c($SIZE)$UNIT\"/>" >> $filename
				echo '</work>' >> $filename
			echo '</workstage>' >> $filename
		echo '</workflow>' >> $filename
	echo '</workload>' >> $filename
	echo "$filename generated!"
done

filename=${MODE}_${CONTAINER}con_${OBJECT}obj_${SIZE}${UNIT}_0w.xml
echo '<?xml version="1.0" encoding="UTF-8"?>' >> $filename
echo "<workload name=\"${MODE}_${CONTAINER}con_${OBJECT}obj_${SIZE}${UNIT}_0w\" description=\"`echo $MODE | tr '[:lower:]' '[:upper:]'`-ONLY\">" >> $filename
echo "<storage type=\"librados\" config=\"timeout=$TIMEOUT;accesskey=admin;endpoint=$MON_IP;secretkey=$KEY\" />" >> $filename
echo '<workflow>' >> $filename
echo '<workstage name="prepare">' >> $filename
echo "<work type=\"prepare\" workers=\"$(($DRIVERS*8))\" config=\"containers=r(1,${CONTAINER});objects=r(1,${OBJECT});;sizes=c($SIZE)$UNIT\"/>" >> $filename
echo '</workstage>' >> $filename
echo '</workflow>' >> $filename
echo '</workload>' >> $filename
echo "$filename generated!"
