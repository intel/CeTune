#!/bin/bash

function collect_interrupts
{
    dest=$1
    echo `date` > ${dest}
    cat /proc/interrupts >> ${dest}
}

function collect_mpstat
{
    time=$1
    dest=$2
    mpstat -P ALL 1 ${time} >${dest}
}


function collect_iostat
{
    time=$1
    dest=$2
    iostat -p -dxm 1 ${time} >${dest}
}


function collect_sar
{
    time=$1
    dest=$2
    sar -A 1 ${time} >${dest}
}


function collect_top
{
    time=$1
    dest=$2
    top -c -b -d 1 -n ${time} >${dest}
}


function collect_blktrace
{
    disk=$1
    time=$2
    dest=$3
    blktrace -d $disk -w {$time} -o - | blkparse -o ${dest} -i -
}


function check_health
{
    if [ $# != 2 ];then
            echo "Usage: ./check_cephHeath.sh <runtime> <interval>"
            exit
    fi
    runtime=$1
    interval=$2
    runCount=$[ $runtime / $interval ]
    echo ${runCount}

    for i in `seq 1 ${runCount}`
    do
            echo "============="`date +%Y%m%d_%H:%M:%S`"==============="
            ceph -s
            sleep ${interval}
    done
}


function sys_stat_ceph
{
    if [ $# != 7 ] ; then
        echo " "
        echo "[WRONG] missing parameter: $0 warmup_time run_time ceph_host disk check_health wait_time post_time"
        echo " "
        exit 1
    fi

    warmup_time=$1
    run_time=$2
    ceph=$3
    disk=$4
    check_health=$5
    wait_time=$6
    post_time=$7

    sleep ${wait_time}

    collect_mpstat  ${run_time}   before_run_ceph_${ceph}_mpstat.txt  &
    collect_iostat  ${wait_time}  before_run_ceph-${ceph}_iostat.txt &
    collect_sar     ${wait_time}  before_run_ceph-${ceph}_sar.txt    &
    collect_top     ${run_time}   before_run_ceph-${ceph}_top.txt    &

    sleep ${warmup_time}

    # data collection
    if [ ${check_health} -eq 1 ] ; then
        check_health  ${run_time} 5 >ceph_health.txt &
    fi

    blk_target=`echo $disk | sed 's#^/##' | sed 's#/#_#g'`

    collect_interrupts ${ceph}_interrupts_start.txt
    collect_mpstat    ${run_time}  ${ceph}_mpstat.txt  &
    collect_iostat    ${run_time}  ${ceph}_iostat.txt  &
    collect_sar       ${run_time}  ${ceph}_sar.txt     &
    collect_top       ${run_time}  ${ceph}_top.txt     &
    collect_blktrace  $disk        ${run_time}  ${ceph}_${blk_target}.blktrace  &

    sleep ${post_time}
}


function sys_stat_client
{
    if [ $# != 5 ] ; then
        echo "    [WRONG] missing parameter: $0 warmup_time run_time client wait_time post_time"
        exit 1
    fi

    warmup_time=$1
    run_time=$2
    client=$3
    wait_time=$4
    post_time=$5

    sleep ${wait_time}
    sleep ${warmup_time}

    collect_interrupts ${client}_interrupts_start.txt
    collect_iostat  ${run_time}  ${client}_iostat.txt &
    collect_sar     ${run_time}  ${client}_sar.txt    &
    collect_top     ${run_time}  ${client}_top.txt    &
    collect_mpstat  ${run_time}  ${client}_mpstat.txt &

    sleep ${post_time}
}


function sys_stat_vclient
{
    if [ $# != 5 ] ; then
        echo " "
        echo "[WRONG] missing parameter: $0 section_name vclient run_time wait_time post_time"
        echo " "
        exit 1
    fi

    section_name=$1
    vclient=$2
    run_time=$3
    wait_time=$4
    post_time=$5
    
    sleep ${wait_time}
    fio --output /opt/${vclient}_fio.txt --section ${section_name} fio.conf &

    sleep ${warm_time}
    collect_top       ${run_time}  /opt/${vclient}_top.txt    &
    collect_mpstat    ${run_time}  /opt/${vclient}_mpstat.txt &
    collect_iostat    ${run_time}  /opt/${vclient}_iostat.txt &
    collect_sar       ${run_time}  /opt/${vclient}_sar.txt    &

    sleep ${post_time}
}


function sys_stat_fiorbd
{
    if [ $# != 7 ] ; then
        echo " "
        echo "[WRONG] missing parameter: $0 end_num total_num section_name client run_time wait_time post_time"
        echo " "
        exit 1
    fi

    end_num=$1
    total_num=$2
    section_name=$3
    client=$4
    run_time=$5
    wait_time=$6
    post_time=$7

    sleep ${wait_time}
    collect_interrupts ${client}_interrupts_start.txt
    rbd ls | head -${end_num} | tail -${total_num} | while read line
    do
        #RBDNAME=${line} fio --output /opt/${client}_${line}_fio.txt --section ${section_name} fio.conf 2>/opt/${client}_${line}_fio_errorlog.txt &
        RBDNAME=${line} fio --output /opt/${client}_${line}_fio.txt --write_bw_log=/opt/${client}_${line}_fio --write_lat_log=/opt/${client}_${line}_fio --write_iops_log=/opt/${client}_${line}_fio --section ${section_name} fio.conf 2>/opt/${client}_${line}_fio_errorlog.txt &
    done

    sleep ${warm_time}
    collect_sar       ${run_time}  /opt/${client}_sar.txt &
    collect_top       ${run_time}  /opt/${client}_top.txt &
    collect_mpstat    ${run_time}  /opt/${client}_mpstat.txt &
    sleep ${run_time}
    sleep ${post_time}
}

function sys_stat_fiocephfs
{
    if [ $# != 6 ] ; then
        echo " "
        echo "[WRONG] missing parameter: $0 job_num section_name client run_time wait_time post_time"
        echo " "
        exit 1
    fi
    job_num=$1
    section_name=$2
    client=$3
    run_time=$4
    wait_time=$5
    post_time=$6

    sleep ${wait_time}
    collect_interrupts ${client}_interrupts_start.txt
    for i in `seq 0 $(( job_num - 1 ))`
    do
        /opt/fio --output /opt/${client}_${i}_fio.txt --write_bw_log=/opt/${client}_${i}_fio --write_lat_log=/opt/${client}_${i}_fio --write_iops_log=/opt/${client}_${i}_fio --section ${section_name}  --filename=${client}.${i} fio.conf 2>/opt/${client}_${i}_fio_errorlog.txt &
    done

    sleep ${warm_time}
    collect_sar       ${run_time}  /opt/${client}_sar.txt &
    collect_top       ${run_time}  /opt/${client}_top.txt &
    collect_mpstat    ${run_time}  /opt/${client}_mpstat.txt &
    sleep ${run_time}
    sleep ${post_time}
}




##############################Main########################################################
if [ "$1" == "sys_stat_vclient" ];then
    if [ "$#" -ne 6 ];then
        echo "Wrong paramters for 'bash common.sh sys_stat_vclient'!"
        exit 1
    fi
    section_name=$2
    vm=$3
    run_time=$4
    wait_time=$5
    post_time=$6
    sys_stat_vclient ${section_name} $vm ${run_time} ${wait_time} ${post_time} &
elif [ "$1" == "sys_stat_client" ];then
    if [ "$#" -ne 6 ];then
        echo "Wrong paramters for 'bash common.sh sys_stat_client'!"
        exit 1
    fi
    warmup_time=$2
    run_time=$3
    client=$4
    wait_time=$5
    post_time=$6
    sys_stat_client ${warmup_time} ${run_time} ${client} ${wait_time} ${post_time} &
elif [ "$1" == "sys_stat_ceph" ];then
    if [ "$#" -ne 8 ];then
        echo "Wrong paramters for 'bash common.sh sys_stat_ceph'!"
        exit 1
    fi
    warmup_time=$2
    run_time=$3
    ceph=$4
    blk_target=$5
    check_ceph_health=$6
    wait_time=$7
    post_time=$8
    sys_stat_ceph ${warmup_time} ${run_time} ${ceph} ${blk_target} ${check_ceph_health} ${wait_time} ${post_time} &
elif [ "$1" == "sys_stat_fiorbd" ];then
    if [ "$#" -ne 8 ];then
        echo "Wrong paramters for 'bash common.sh sys_stat_fiorbd'!"
        exit 1
    fi
    rnum2=$2
    rnum3=$3
    section_name=$4
    client=$5
    run_time=$6
    wait_time=$7
    post_time=$8
    sys_stat_fiorbd ${rnum2} ${rnum3} ${section_name} ${client} ${run_time} ${wait_time} ${post_time} &
elif [ "$1" == "collect_interrupts" ];then
    if [ "$#" -ne 2 ];then
        echo "Wrong paramters for 'bash common.sh collect_interrupts'!"
        exit 1
    fi
    collect_interrupts $2
elif [ "$1" == "sys_stat_fiocephfs" ];then
    if [ "$#" -ne 7 ];then
        echo "Wrong paramters for 'bash common.sh sys_stat_fiocephfs'!"
        exit 1
    fi
    job_num=$2
    section_name=$3
    client=$4
    run_time=$5
    wait_time=$6
    post_time=$7
    sys_stat_fiocephfs ${job_num} ${section_name} ${client} ${run_time} ${wait_time} ${post_time} &
else
    echo -e "Wrong parameters! Please check your input!"
    exit 1
fi
