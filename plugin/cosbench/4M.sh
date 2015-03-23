#!/bin/bash

#-------------------------------------------
# Configurable Options
#-------------------------------------------

COSBENCH="/cosbench/current"

RUN_ID=w0
TIME_OUT=99999999

CONFIG_DIR="./conf/4MB-read/10_10"
CONFIG_PREFIX=read_10con_10obj_4MB_
CONFIG_SUFFIX=w.xml
#CONFIG_LIST="0 5 10 20 40 80" #1280 2560"
#CONFIG_LIST="1280"
CONFIG_LIST="0"
#CONFIG_LIST="$CONFIG_LIST $CONFIG_LIST $CONFIG_LIST"

REMOTE_SERV=192.168.3.101
REMOTE_USER=root
REMOTE_DIR=/data2/yujie/data

#-------------------------------------------
# Helper
#-------------------------------------------

function do_clean()
{
    bash stop_sysstat.sh
    bash clean_sysstat.sh
}

function do_start()
{
    bash run_sysstat.sh
}

function do_submit_workload()
{
    config=$CONFIG_DIR/${CONFIG_PREFIX}${run}${CONFIG_SUFFIX}
    echo "using workload config: $config"

    RUN_ID=`sh $COSBENCH/cli.sh submit $config | awk -F: '/Accept/{print $2}'`
    echo "workload id: $RUN_ID"

    if [ -z "$RUN_ID" ]; then
        echo "!!!ERROR SUBMITTING WORKLOAD!!!"
        exit 1
    fi
}

function do_wait()
{    
    echo "waiting for $RUN_ID in $COSBENCH/stop file"

    cnt=0
    while [ 1 ]
    do
        sleep 1
        cnt=`expr $cnt + 1`
        echo -n .
        grep $RUN_ID $COSBENCH/stop
        if [ $? -eq 0 ]
        then
            echo "found $RUN_ID"
            break
        fi
        if [ $cnt -gt $TIME_OUT ];
        then
            echo "!!!TIMEOUT!!!"
            sh $COSBENCH/cli.sh cancel $RUN_ID >> /dev/null
            echo "workload $RUN_ID has been cancelled"
        fi
    done
}

function do_stop()
{
    bash stop_sysstat.sh
    bash process_sysstat.sh
    bash remote_copy.sh
}

function do_archive()
{
    dir=`pwd`
    cd $COSBENCH/archive

    fullid=`ls ${RUN_ID}-* -d`

    rm -f result.tar.gz
    tar -czf result.tar.gz $fullid
    scp result.tar.gz $REMOTE_USER@$REMOTE_SERV:$REMOTE_DIR/
    scp workloads.csv $REMOTE_USER@$REMOTE_SERV:$REMOTE_DIR/
    ssh $REMOTE_USER@$REMOTE_SERV "cd $REMOTE_DIR; tar -xzf result.tar.gz -C ."
    rm -f result.tar.gz

    cd /var/cache/multiperf
    scp perf.tar.gz $REMOTE_USER@$REMOTE_SERV:$REMOTE_DIR/
    ssh $REMOTE_USER@$REMOTE_SERV "cd $REMOTE_DIR; tar -xzf perf.tar.gz -C $REMOTE_DIR/$fullid"
    rm -f perf.tar.gz
    cd $dir
}

#-------------------------------------------
# Main
#-------------------------------------------

echo $CONFIG_LIST

echo "sleep 5 seconds ..."
sleep 5

echo "job starts in 3 seconds ... "

sleep 1

echo "job starts in 2 seconds ... "

sleep 1

echo "job starts in 1 seconds ... "

sleep 1

echo "==========================================="

unset http_proxy

bash install.sh

for run in $CONFIG_LIST
do
    do_clean
    do_start
    do_submit_workload
    do_wait
    do_stop
    do_archive    
    bash inc_runid.sh
    bash clean_sysstat.sh
done
