#/bin/bash
file=test.log
REMOTE_SERV=192.168.3.101
REMOTE_USER=root
REMOTE_DIR=/data2/yujie/firefly/librados
FAILURE_NAME=disk_down

bash install.sh

bash stop_sysstat.sh
bash clean_sysstat.sh

#if false;then
ssh gw2 "ceph -w" >> $FAILURE_NAME.log &
sleep 3

for ((i=0; i < 99999999; i++))
do
    tail -n 3 $FAILURE_NAME.log | grep -q "13248 active+clean"
    #health=`ssh gw2 "ceph -s"`
    #echo $health >> $file
    #echo "$health"|grep -q "13248 active+clean"
    if [ $? -ne 0 ]
    then
        break
    fi
    sleep 1
done
#fi

bash run_sysstat.sh

for ((i=0; i < 99999999; i++))
do
    tail -n 1 $FAILURE_NAME.log | grep -q "13248 active+clean"
    #health=`ssh gw2 "ceph -s"`
    #echo $health >> $file
    #echo "$health"|grep -q "13248 active+clean$"
    if [ $? -eq 0 ]
    then
       tail -n 1 $FAILURE_NAME.log | grep -q "avail$"
       if [ $? -eq 0 ]
       then
           pid=`ps aux|grep "ssh gw2 ceph -w" | awk 'NR<=1 {print $2}'`
           kill -9 $pid
           break
       fi
    fi
    sleep 1
done 

bash stop_sysstat.sh
bash process_sysstat.sh
bash remote_copy.sh

dir=`pwd`
cd /var/cache/multiperf
scp perf.tar.gz $REMOTE_USER@$REMOTE_SERV:$REMOTE_DIR/
ssh $REMOTE_USER@$REMOTE_SERV "cd $REMOTE_DIR; mkdir -p $FAILURE_NAME; tar -xzf perf.tar.gz -C $REMOTE_DIR/$FAILURE_NAME"
rm -f perf.tar.gz
cd $dir
scp $FAILURE_NAME.log $REMOTE_USER@$REMOTE_SERV:$REMOTE_DIR/$FAILURE_NAME
echo "failure test: $FAILURE_NAME done"
