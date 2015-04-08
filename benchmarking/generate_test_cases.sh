#!/bin/bash

. ../conf/common.sh
get_conf

check_parameters()
{
  para=$1
  if [ "x$para" = "x" ];then
     return 0
  fi
  return 1
}

generate_cases()
{
  vm_num=$1
  size=$2
  io_pattern=$3
  record_size=$4
  queue_depth=$5
  warmup_time=$6
  run_time=$7
  disk=$8
  dest=$9
  for vn in `echo $vm_num | sed 's/,/ /g'`
  do
      for s in `echo $size | sed 's/,/ /g'`
      do
          for ip in `echo $io_pattern | sed 's/,/ /g'`
          do
              for rs in `echo $record_size | sed 's/,/ /g'`
              do
                  for qd in `echo $queue_depth | sed 's/,/ /g'`
                  do
                      for wt in `echo $warmup_time | sed 's/,/ /g'`
                      do
                          for rt in `echo $run_time | sed 's/,/ /g'`
                          do
                              for d in `echo $disk | sed 's/,/ /g'`
                              do
                                  printf "%-7s\t%-7s\t%-12s\t%-7s\t%-7s\t%-7s\t%-7s\t%-12s\t%-s\n" $vn $s $ip $rs $qd $wt $rt $d $dest >> ../conf/cases.conf
                              done
                          done
                      done
                  done
              done
          done
      done
  done
}


generate_fio_config()
{
  size=$1
  io_pattern=$2
  record_size=$3
  queue_depth=$4
  warmup_time=$5
  run_time=$6
  disk=$7
  thread_num=$8
  cat <<EOF >> ../conf/fio.conf
[global]
  direct=1
  time_based
EOF

  for d in `echo $disk | sed 's/,/ /g'` fiorbd fiocephfs
  do
    for s in `echo $size | sed 's/,/ /g'`
    do
      for io in `echo $io_pattern | sed 's/,/ /g'`
      do
        case $io in
          "seqwrite")
            ip=write
            ibs=8
            ibc=8
            capping="rate=60m"
            ;;
          "seqread")
            ip=read
            ibs=8
            ibc=8
            capping="rate=60m"
            ;;
          "randwrite")
            ip=randwrite
            ibs=1
            ibc=1
            capping="rate_iops=100"
            ;;
          "randread")
            ip=randread
            ibs=1
            ibc=1
            capping="rate_iops=100"
            ;;
          *)
            echo "operation $io is forbidden"
            exit 0
          esac
          for rs in `echo $record_size | sed 's/,/ /g'`
          do
            for qd in `echo $queue_depth | sed 's/,/ /g'`
            do
              for wt in `echo $warmup_time | sed 's/,/ /g'`
              do
                for rt in `echo $run_time | sed 's/,/ /g'`
                  do
                    dd=`echo $d | sed 's#^/##g' | sed 's#/#-#g'`
                    section_name="$io-$rs-qd$qd-$s-$wt-$rt-$dd"
cat <<EOF >> ../conf/fio.conf
[$section_name]
  rw=$ip
  bs=$rs
  iodepth=$qd
  ramp_time=$wt
  runtime=$rt
  iodepth_batch_submit=$ibs
  iodepth_batch_complete=$ibc
EOF
if [ ${dd} == 'fiorbd' ];then
    ioengine=rbd
    cat <<EOF >>../conf/fio.conf
  $capping
  ioengine=$ioengine
  clientname=admin
  pool=\${POOLNAME}
  rbdname=\${RBDNAME}
EOF
elif [ ${dd} == 'fiocephfs' ];then
    ioengine=cephfs
    cat << EOF >> ../conf/fio.conf
  size=$s
  ioengine=$ioengine
  thread
EOF
else
    ioengine=libaio
    cat <<EOF >>../conf/fio.conf
  $capping
  size=$s
  ioengine=${ioengine}
  filename=$disk
EOF
fi

                  done
                done
              done
            done
        done
      done
    done
}


check_parameters $run_vm_num
if [ $? -eq 0 ];then
   echo "run_vm_num is NONE"
   exit 0
fi
check_parameters $run_size
if [ $? -eq 0 ];then
   echo "run_size is NONE"
   exit 0
fi
check_parameters $run_io_pattern
if [ $? -eq 0 ];then
   echo "run_io_pattern is NONE"
   exit 0
fi
check_parameters $run_record_size
if [ $? -eq 0 ];then
   echo "run_record_szie is NONE"
   exit 0
fi
check_parameters $run_queue_depth
if [ $? -eq 0 ];then
   echo "run_queue_depth is NONE"
   exit 0
fi
check_parameters $run_warmup_time
if [ $? -eq 0 ];then
   echo "run_warmup_time is NONE"
   exit 0
fi
check_parameters $run_time
if [ $? -eq 0 ];then
   echo "run_time is NONE"
   exit 0
fi
check_parameters $dest_dir
if [ $? -eq 0 ];then
   dest_dir=/mnt
fi
check_parameters $run_file
if [ $? -eq 0 ];then
   run_file=/dev/vdb
fi


[ -f ../conf/cases.conf ] && > ../conf/cases.conf
generate_cases $run_vm_num $run_size $run_io_pattern $run_record_size $run_queue_depth $run_warmup_time $run_time $run_file $dest_dir
echo conf/cases.conf generated
[ -f ../conf/fio.conf ] && > ../conf/fio.conf
generate_fio_config $run_size $run_io_pattern $run_record_size $run_queue_depth $run_warmup_time $run_time $run_file $rum_vm_num
echo conf/fio.conf generated
