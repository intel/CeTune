#!/bin/bash
. ../conf/common.sh
get_conf

function get_runid
{
    # RUNID
    runid=-1
    if [ -f ".run_number" ]; then
    read runid < .run_number
    fi
    if [ $runid -eq -1 ]; then
    runid=0
    fi
    echo $runid
}


function increase_runid
{
    runid=$1
    runid=`expr $runid + 1`
    echo $runid > .run_number
}


function interact
{
    select opt in "yes, start running test" "no, stop test"
    do
        case "$opt" in
            "yes, start running test" )
                echo true
                break
                ;;
            "no, stop test" )
                echo false
            break
                ;;
            *) echo false;;
        esac
    done
}

function run_single_qemu
{
    if [ $# != 9 ] && [ $# != 10 ];then
        echo " "
        echo "Description:"
        echo "   This script attempts to make run "fio" on instance and collect data at the same time."
        echo " "
        echo "usage:"
        echo "    $0 instances_num size operate record_size queue_depth warmup_time run_time disk dest_dir [--force]"
        echo " "
        exit 0
    fi

    #RBD
    number=$1
    size=$2
    operate=$3
    record_size=$4
    qd=$5
    #warmup_time=$run_warmup_time
    warmup_time=$6
    run_time=$7
    disk=$8
    dest_dir=$9
    force=${10}
    runid=`get_runid`
    increase_runid $runid

    fio_conf="../conf/fio.conf"
    check_ceph_health=1
    blk_target=/dev/sdf
    wait_time=50
    post_time=100
    #[ -s $list_vclient ] || (echo "$list_vclient size is ZERO";exit 1)
    #[ -s $list_client ] || (echo "$list_client size is ZERO";exit 1)
    #[ -s $list_ceph ] || (echo "$list_ceph size is ZERO";exit 1)

    list_vclient_tmp=../conf/vclient.lst
    list_client_tmp=../conf/client.lst
    list_ceph_tmp=../conf/ceph.lst

    echo $list_vclient | sed 's/,/\n/g' > $list_vclient_tmp
    echo $list_client | sed 's/,/\n/g' > $list_client_tmp
    echo $list_ceph | sed 's/,/\n/g' > $list_ceph_tmp

    list_vclient=$list_vclient_tmp
    list_client=$list_client_tmp
    list_ceph=$list_ceph_tmp

    echo "date is `date`"
    echo "runid is $runid"


    ###Do some preparation work, as check output directory and drop cache on ceph servers###
    echo "======================Preparing===============================...."
    dd=`echo $disk | sed 's#^/##g' | sed 's#/#-#g'`
    section_name="${operate}-${record_size}-qd${qd}-${size}-${warmup_time}-${run_time}-$dd"
    dir_name=${runid}-${number}instance-$section_name
    dir="/$dest_dir/${dir_name}"
    echo "All results will be saved to $dir"
    if [ -d $dir ]
    then
        echo "$dir already exist, Check it first !"
        exit 1
    fi
    mkdir -p $dir

    echo "----Start to clean cache"
    for ceph in `cat $list_ceph`
    do
       ssh $ceph "echo '1' > /proc/sys/vm/drop_caches && sync"
    done


    ###add prerun-check data in result dir###
    echo "Current system status:"
    bash before_test_check.sh > $dir/prerun-check.log
    cat $dir/prerun-check.log
    #if [ "$force" != "--force" ]; then
    #    if [ "`interact`" != "true" ]; then
    #       exit
    #   fi
    #fi


    ###Run FIO test on specified VMs and collect physical data on clients and servers###
    echo "======================Running===============================...."
    echo "Start FIO on specified number ($number) of VMs..!"
    for vm in `cat $list_vclient | head -n$number`
    do
        echo ">>>> vclient $vm"
        ssh ${vm} "killall -9 dd 2>/dev/null;killall -9 fio 2>/dev/null;killall -9 ./fio.sh  2>/dev/null;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        ssh ${vm} "rm -f /opt/*.txt"
        ssh ${vm} "rm -f /opt/*.log"
        scp $fio_conf root@${vm}:/opt/  > /dev/null
        scp $fio_conf root@${vm}:/opt/  > /dev/null
        scp common.sh root@${vm}:/opt/ > /dev/null
        ssh ${vm} "cd /opt; bash common.sh sys_stat_vclient $section_name $vm $run_time ${wait_time} ${post_time} &" &
    done

    echo "Start data collection on all the clients"
    for client in `cat $list_client`
    do
        ssh ${client} "killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        scp common.sh  root@${client}:/opt/
        ssh ${client}  "cd /opt/; bash common.sh  sys_stat_client ${warmup_time} ${run_time} ${client} ${wait_time} ${post_time} &" &
    done

    echo "start data collection on volume machine"
    for ceph in `cat $list_ceph`
    do
        ssh ${ceph} "killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        scp common.sh root@${ceph}:/opt/
        ssh ${ceph}  " cd /opt/; bash common.sh sys_stat_ceph ${warmup_time} ${run_time} ${ceph} ${blk_target} ${check_ceph_health} ${wait_time} ${post_time} &" &
        check_ceph_health=0
    done


    ###wait test complete###
    sum_wait=$(( ${wait_time} + ${warmup_time} + ${run_time} + ${post_time} ))
    echo "waiting ${sum_wait}s till this single test finishes."
    sleep ${wait_time}
    sleep ${warmup_time}
    sleep $run_time
    sleep ${post_time}


    ###killall aio-stress and get data###
    echo "======================Stopping===============================...."
    for vm in `cat $list_vclient | head -n$number`
    do
        mkdir $dir/${vm}
        ssh ${vm} "killall -9 fio 2>/dev/null;killall -9 ./fio.sh  2>/dev/null;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        stop_flag=0
	#Wait until fio finish
	while [[ $stop_flag == 0 ]]
	do
	    stop_flag=1
	    finish=`ssh ${vm} "cat /opt/${vm}_fio.txt | grep 'Run status' -c"`
	    if [[ $finish == 0 ]]; then
		stop_flag=0
		sleep 10
	    fi
	done

        scp ${vm}:/opt/*.txt $dir/${vm}
        scp ${vm}:/opt/*.log $dir/${vm}
        ssh ${vm} "rm -f /opt/*.txt"
        ssh ${vm} "rm -f /opt/*.log"
    done

    for client in `cat $list_client`
    do
        ssh ${ceph} "cd /opt/; bash common.sh collect_interrupts ${client}_interrupts_end.txt"
        mkdir $dir/$client
        scp ${client}:/opt/*.txt $dir/$client
        ssh ${client} "rm -f /opt/*.txt;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
    done

    for ceph in `cat $list_ceph`
    do
        ssh ${ceph} "cd /opt/; bash common.sh collect_interrupts ${ceph}_interrupts_end.txt"
        mkdir $dir/$ceph
        scp ${ceph}:/opt/*.txt $dir/$ceph
        scp ${ceph}:/opt/*blktrace* $dir/$ceph
        ssh ${ceph} "rm -f /opt/*.txt; rm -f /opt/*blktrace*;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
    done

    cp ../conf/all.conf $dir/

    echo "=================Post Processing==================================="
    cur=`pwd`
    cd ../post-processing
    bash post_processing.sh ${dir}
    cd ../benchmarking

    #cp Ceph_v1.2.xlsm $dir/csvs/Ceph_v1.2.xlsm
}


function run_single_fiorbd
{
    if [ $# != 9 ];then
        echo " "
        echo "Description:"
        echo "   This script attempts to make run "fio" on instance and collect data at the same time."
        echo " "
        echo "usage:"
        echo "    $0 instances_num size operate record_size queue_depth warmup_time run_time disk dest_dir"
        echo " "
        exit 1
    fi

    number=$1
    size=$2
    operate=$3
    record_size=$4
    qd=$5
    #warmup_time=$run_warmup_time
    warmup_time=$6
    run_time=$7
    disk=$8
    dest_dir=$9
    force=${10}
    runid=`get_runid`
    increase_runid $runid

    fio_conf="../conf/fio.conf"
    rbd_conf="../conf/rbd.conf"
    check_ceph_health=1
    blk_target=/dev/sdf
    wait_time=50
    post_time=100
    #[ -s $list_vclient ] || (echo "$list_vclient size is ZERO";exit 1)
    #[ -s $list_client ] || (echo "$list_client size is ZERO";exit 1)
    #[ -s $list_ceph ] || (echo "$list_ceph size is ZERO";exit 1)

    list_client_tmp=../conf/client.lst
    list_ceph_tmp=../conf/ceph.lst

    echo $list_client | sed 's/,/\n/g' > $list_client_tmp
    echo $list_ceph | sed 's/,/\n/g' > $list_ceph_tmp

    list_client=$list_client_tmp
    list_ceph=$list_ceph_tmp

    echo "date is `date`"
    echo "runid is $runid"


    ###Do some preparation work, as check output directory and drop cache on ceph servers###
    echo "======================Preparing===============================...."
    section_name="${operate}-${record_size}-qd${qd}-${size}-${warmup_time}-${run_time}-fiorbd"
    dir_name=${runid}-${number}instance-$section_name
    dir="/$dest_dir/${dir_name}"
    echo "All results will be saved to $dir"
    if [ -d $dir ]
    then
        echo "$dir already exist, Check it first !"
        exit 1
    fi
    mkdir -p $dir

    rbd_conf_flag=0
    if [ ! -f ${rbd_conf} ];then
        bash gen_rbd.sh
        rbd_conf_flag=1
    fi


    echo "----Start to clean cache"
    for ceph in `cat $list_ceph`
    do
       ssh $ceph "echo '1' > /proc/sys/vm/drop_caches && sync"
    done


    ###Run fio+rbd test on all ceph clients and collect physical data on clients and servers###
    echo "======================Running===============================...."
    echo "Start fio+rbd test on all the clients!"
    for client in `cat $list_client`
    do
        echo ">>>> client $client"
        ssh ${client} "killall -9 dd 2>/dev/null;killall -9 fio 2>/dev/null;killall -9 ./fio.sh  2>/dev/null;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        ssh ${client} "rm -f /opt/*.txt"
        ssh ${client} "rm -f /opt/*.log"
        scp $fio_conf root@${client}:/opt/  > /dev/null
        scp $rbd_conf root@${client}:/opt/  > /dev/null
        scp common.sh root@${client}:/opt/  > /dev/null
        ssh ${client} "cd /opt; bash common.sh sys_stat_fiorbd  ${section_name} ${client} ${run_time} ${wait_time} ${post_time} &" &
    done
    if [ ${rbd_conf_flag} -eq 1 ];then
        rm -rf ${rbd_conf} >/dev/null 2>&1
    fi

    echo "start data collection on volume machine"
    for ceph in `cat $list_ceph`
    do
        ssh ${ceph} "killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        scp common.sh root@${ceph}:/opt/
        ssh ${ceph}  " cd /opt/; bash common.sh sys_stat_ceph ${warmup_time} ${run_time} ${ceph} ${blk_target} ${check_ceph_health} ${wait_time} ${post_time} &" &
        check_ceph_health=0
    done


    # wait test complete
    sum_wait=$(( ${wait_time} + ${warmup_time} + ${run_time} + ${post_time} ))
    echo "waiting ${sum_wait}s till this single test finishes."
    sleep ${wait_time}
    sleep ${warmup_time}
    sleep $run_time
    sleep ${post_time}


    # killall aio-stress AND get data
    echo "======================Stopping===============================...."
    for client in `cat $list_client`
    do
        ssh ${ceph} "cd /opt/; bash common.sh collect_interrupts ${client}_interrupts_end.txt"
        mkdir $dir/${client}
        ssh ${client} "killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
	stop_flag=0
	#Wait until fio finish
	while [[ $stop_flag == 0 ]]
	do
	    stop_flag=1
	    sleep 10
	    for nn in `ssh ${client} "ls /opt/${client}_*_fio.txt"`
	    do
		finish=`ssh ${client} "cat ${nn} | grep 'Run status' -c"`
		if [[ $finish == 0 ]]; then
		    stop_flag=0
		fi
	    done
	done

        scp ${client}:/opt/*.txt $dir/${client}
        scp ${client}:/opt/*.log $dir/${client}
        ssh ${client} "rm -f /opt/*.txt"
        ssh ${client} "rm -f /opt/*.log"
    done

    for ceph in `cat $list_ceph`
    do
        ssh ${ceph} "cd /opt/; bash common.sh collect_interrupts ${ceph}_interrupts_end.txt"
        mkdir $dir/$ceph
        scp ${ceph}:/opt/*.txt $dir/$ceph
        scp ${ceph}:/opt/*blktrace* $dir/$ceph
        ssh ${ceph} "rm -f /opt/*.txt; rm -f /opt/*blktrace*;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
    done

    cp ../conf/all.conf $dir/

    echo "=================Post Processing==================================="
    cur=`pwd`
    cd ../post-processing
    bash post_processing.sh ${dir}
    cd ../benchmarking

    #cp Ceph_v1.2.xlsm $dir/csvs/Ceph_v1.2.xlsm
}

function run_single_fiocephfs
{
    if [ $# != 9 ];then
        echo " "
        echo "Description:"
        echo "   This script attempts to make run "fio" on instance and collect data at the same time."
        echo " "
        echo "usage:"
        echo "    $0 instances_num size operate record_size queue_depth warmup_time run_time disk dest_dir"
        echo " "
        exit 1
    fi

    number=$1
    size=$2
    operate=$3
    record_size=$4
    qd=$5
    #warmup_time=$run_warmup_time
    warmup_time=$6
    run_time=$7
    disk=$8
    dest_dir=$9
    runid=`get_runid`
    increase_runid $runid

    fio_conf="../conf/fio.conf"
    check_ceph_health=1
    blk_target=/dev/sdf
    wait_time=50
    #Jesse
    post_time=100
    #[ -s $list_vclient ] || (echo "$list_vclient size is ZERO";exit 1)
    #[ -s $list_client ] || (echo "$list_client size is ZERO";exit 1)
    #[ -s $list_ceph ] || (echo "$list_ceph size is ZERO";exit 1)

    list_client_tmp=../conf/client.lst
    list_ceph_tmp=../conf/ceph.lst

    echo $list_client | sed 's/,/\n/g' > $list_client_tmp
    echo $list_ceph | sed 's/,/\n/g' > $list_ceph_tmp

    list_client=$list_client_tmp
    list_ceph=$list_ceph_tmp

    echo "date is `date`"
    echo "runid is $runid"


    ###Do some preparation work, as check output directory and drop cache on ceph servers###
    echo "======================Preparing===============================...."
    section_name="${operate}-${record_size}-qd${qd}-${size}-${warmup_time}-${run_time}-fiocephfs"
    dir_name=${runid}-${number}instance-$section_name
    dir="/$dest_dir/${dir_name}"
    echo "All results will be saved to $dir"
    if [ -d $dir ]
    then
        echo "$dir already exist, Check it first !"
        exit 1
    fi
    mkdir -p $dir

    echo "----Start to clean cache"
    for ceph in `cat $list_ceph`
    do
       ssh $ceph "echo '1' > /proc/sys/vm/drop_caches && sync"
    done


    ###Run fio+libcephfs test on all ceph clients and collect physical data on clients and servers###
    echo "======================Running===============================...."
    echo "Start fio+libcephfs test on all the clients!"
    for client in `cat $list_client`
    do
        echo ">>>> client $client"
        ssh ${client} "killall -9 dd 2>/dev/null;killall -9 fio 2>/dev/null;killall -9 ./fio.sh  2>/dev/null;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        ssh ${client} "rm -f /opt/*.txt"
        ssh ${client} "rm -f /opt/*.log"
        scp ${fio_conf} root@${client}:/opt/  > /dev/null
        scp common.sh root@${client}:/opt/  > /dev/null
        ssh ${client} "cd /opt; bash common.sh sys_stat_fiocephfs ${number} ${section_name} ${client} ${run_time} ${wait_time} ${post_time}&" &
    done
    echo "start data collection on volume machine"
    for ceph in `cat $list_ceph`
    do
        ssh ${ceph} "killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        scp common.sh root@${ceph}:/opt/
        ssh ${ceph}  " cd /opt/; bash common.sh sys_stat_ceph ${warmup_time} ${run_time} ${ceph} ${blk_target} ${check_ceph_health} ${wait_time} ${post_time} &" &
        check_ceph_health=0
    done


    # wait test complete
    sum_wait=$(( ${wait_time} + ${warmup_time} + ${run_time} + ${post_time} ))
    echo "waiting ${sum_wait}s till this single test finishes."
    sleep ${wait_time}
    sleep ${warmup_time}
    sleep $run_time
    sleep ${post_time}


    # killall aio-stress AND get data
    echo "======================Stopping===============================...."
    for client in `cat $list_client`
    do
        ssh ${ceph} "cd /opt/; bash common.sh collect_interrupts ${client}_interrupts_end.txt"
        mkdir $dir/${client}
        ssh ${client} "killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
        stop_flag=0
	#Wait until fio finish
	while [[ $stop_flag == 0 ]]
	do
	    stop_flag=1
	    sleep 10
	    for nn in `seq 0 $(( number - 1 ))`
	    do
		finish=`ssh ${client} "cat /opt/${client}_${nn}_fio.txt | grep 'Run status' -c"`
		if [[ $finish == 0 ]]; then
		    stop_flag=0
		fi
	    done
	done
        scp ${client}:/opt/*.txt $dir/${client}
        scp ${client}:/opt/*.log $dir/${client}
        ssh ${client} "rm -f /opt/*.txt"
        ssh ${client} "rm -f /opt/*.log"
    done

    for ceph in `cat $list_ceph`
    do
        ssh ${ceph} "cd /opt/; bash common.sh collect_interrupts ${ceph}_interrupts_end.txt"
        mkdir $dir/$ceph
        scp ${ceph}:/opt/*.txt $dir/$ceph
        scp ${ceph}:/opt/*blktrace* $dir/$ceph
        ssh ${ceph} "rm -f /opt/*.txt; rm -f /opt/*blktrace*;killall -9 sar 2>/dev/null;killall -9 iostat 2>/dev/null"
    done

    cp ../conf/all.conf $dir/

    echo "=================Post Processing==================================="
    cur=`pwd`
    cd ../post-processing
    bash post_processing.sh ${dir}
    cd ../benchmarking

    #cp Ceph_v1.2.xlsm $dir/csvs/Ceph_v1.2.xlsm
}

################################Main##############################################
ltype=$1
lengine=$2
check_post_processing
if [ "$ltype" == 'single' ];then
     index=1
     cat ../conf/cases.conf | while read line
     do
         echo "$index) "$line | awk '{printf("%-5s\t%-7s\t%-7s\t%-12s\t%-7s\t%-7s\t%-7s\t%-7s\t%-12s\t%-s\n",$1,$2,$3,$4,$5,$6,$7,$8,$9,$10)}'
         index=$(( $index + 1 ))
     done
     echo -n "Select the number of the case you wanna run: "
     read num
     opt=`cat ../conf/cases.conf | sed -n ${num}'p'`
     if [ "${lengine}" == "qemu" ];then
         run_single_qemu $opt
    elif [ "${lengine}" == "fiorbd" ];then
         run_single_fiorbd $opt
    elif [ "${lengine}" == "fiocephfs" ];then
         run_single_fiocephfs $opt
    fi
elif [ "$ltype" == 'all' ];then
    cases=../conf/cases.conf
    force="--force"
    count=`cat $cases | wc -l`
    for index in `seq 1 ${count}`
    do
        path=`pwd`
        rc=`sed -n ${index}'p' $cases`
        if [ "$lengine" == "qemu" ];then
            run_single_qemu $rc $force
            echo "Sleep for 60 secs to start next run"
            sleep 60
        elif [ "${lengine}" == "fiorbd" ];then
            run_single_fiorbd $rc
            echo "Sleep for 60 secs to start next run"
            sleep 60
        elif [ "${lengine}" == "fiocephfs" ];then
            run_single_fiocephfs $rc
            echo "Sleep for 60 secs to start next run"
            sleep 60
        fi
        cd ${path}
        . ../conf/common.sh
        get_conf
    done
fi
