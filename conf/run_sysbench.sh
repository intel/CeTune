#!/bin/bash
host=localhost
port=3306
socket=/var/lib/mysql/mysql.sock
user=root
password=123456
connparams=
test_type=$1
init_rng=$2
#threads=$3
num_thread=$3
oltp_read_only=$4
oltp_dist_type=$5
timeout=$6
max_requests=$7
percentile=$8
resultsdir=$9

function usage_exit {
    echo -e "usage:\n\t $0 test-type init-rng num-threads oltp-read-only oltp-dist-type max-time max-requests percentile resultsdir"
    exit
}

function main {
    # readonly_op=${readonly_op//,/ }
    if [ ! "$socket" == "/var/lib/mysql/mysql.sock" ]; then
        connparams="--mysql-socket=$socket --mysql-user=$user --mysql-password=$password"
    else
        connparams="--mysql-host=$host --mysql-port=$port --mysql-user=$user --mysql-password=$password"
    fi

	sysbench $connparams --test=oltp prepare

    mkdir -p $resultsdir
#    run_num=-1

#   if [ -f "$resultsdir/.run_number" ]; then
#        read run_num < $resultsdir/.run_number
#    fi

#    if [ $run_num -eq -1 ]; then
#        run_num=1
#    fi

#    if [ $run_num -lt 10 ]; then
#        outdir=result-0$run_num
#    else
#        outdir=result-$run_num
#    fi

    mkdir -p $resultsdir

#    run_num=`expr $run_num + 1`
#    echo $run_num > $resultsdir/.run_number

    # Run iostat
    iostat -dx 10 $(($timeout/10+1))  >> $resultsdir/iostat.$num_thread.res &
    
    #preapare
    sysbench $connparams --test=oltp prepare
    # Run sysbench
    sysbench $connparams --test=$test_type --init-rng=$init_rng --num-threads=$num_thread --oltp-read-only=$oltp_read_only --oltp-dist-type=$oltp_dist_type --max-time=$timeout --max-requests=$max_requests --percentile=$percentile run | tee -a $resultsdir/$outdir/sysbench.$num_thread.res
    sleep 10
    #clean
    sysbench $connparams --test=oltp cleanup
}

echo "$0 $1 $2 $3 $4 $5 $6 $7 $8 $9"

if [ "$#" != "9" ]; then
    usage_exit
fi

main $test_type $init_rng $num_thread $oltp_read_only $oltp_dist_type $timeout $max_requests $percentile $resultsdir
