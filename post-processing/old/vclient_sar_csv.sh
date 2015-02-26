#!/bin/bash

source ../conf/all.conf

function get_colume_avg {
    step=1
    input_file=$1
    output_file=$2
    cat $input_file | awk -v step=$step 'BEGIN{for(i=1;i<=NF;i++)sum[i]=0;count=0}{if(count%step==0)for(i=1; i<=NF; i++)sum[i]+=$i;count++}END{for(i=1; i<=NF; i++)printf("%f\t",sum[i]/count); printf("\n")}' >> $output_file
}


function get_colume_sum {
    step=1
    input_file=$1
    output_file=$2
    cat $input_file | awk -v step=$step 'BEGIN{for(i=1;i<=NF;i++)sum[i]=0;count=0}{if(count%step==0)for(i=1; i<=NF; i++)sum[i]+=$i;count++}END{for(i=1; i<=NF; i++)printf("%f\t",sum[i]); printf("\n")}' >> $output_file
}

function tail_sum_avg {
    input_file=$1
    cat $input_file | sed '1d' | awk -v first_column=2 'BEGIN{for(i=first_column;i<=NF;i++)sum[i]=0}{for(i=first_column;i<=NF;i++){sum[i]+=$i}}END{printf("SUM:\t"); for(i=first_column;i<=NF;i++)printf("%f\t",sum[i]); printf("\n");printf("AVG:\t");for(i=first_column;i<=NF;i++)printf("%f\t",sum[i]/NR); printf("\n")}' >> $input_file
}

function convert_csv {
  if [[ $# != 2 ]];then
     echo "Usage: input_file output_file"
     exit
  fi
  in_file=$1
  out_file=$2
  if [[ -e $out_file ]];then
     rm $out_file
  fi
  cat $in_file | awk '{for(i=1;i<=NF;++i){printf("%f",$i)};printf("\n")}' >> $out_file
}

function get_nic {
  host=$1
  nic=`echo $list_nic | sed 's/,/\n/g' | grep $host | awk -F: '{print $2}'` 
  echo $nic
}

function deal_cpu_data {
  # arg1 : input file
  # arg2 : output file
  # arg3 : hostname
  input_file=$1
  output_file=$2
  host=$3
  cpu_tmp_file=cpu.tmp
  #add header
  echo -e "CPU\t%usr\t%nice\t%sys\t%iowait\t%steal\t%irq\t%soft\t%guest\t%idle\n" >> $output_file
  echo -n "$host " >> $output_file
  # filter the all cpu data
  cat $input_file | sed -n '/ *CPU *%/{n;p}' | sed '1d' | sed '$d' | awk -F"all" '{print $2}' >> $cpu_tmp_file
  # calculate the data average
  get_colume_avg $cpu_tmp_file $output_file
  rm $cpu_tmp_file
}

function deal_nic_data {
  # arg1 : input file
  # arg2 : output file
  # arg3 : hostname
  input_file=$1
  output_file=$2
  host=$3
  nic_tmp_file=nic.tmp
  nic=`get_nic $host`
  echo -e "IFACE\trxpck/s\ttxpck/s\trxkB/s\ttxkB/s\trxcmp/s\ttxcmp/s\trxmcst/s\trxerr/s\ttxerr/s\tcoll/s\trxdrop/s\ttxdrop/s\ttxcarr/s\trxfram/s\trxfifo/s\ttxfifo/s\n" >> $output_file
  echo -n "${host}-${nic} " >> $output_file
  # filter the wanted nic data
  cat $input_file | grep "$nic" | awk -F${nic} -v step=2 'BEGIN{count=0}{if(count%step==0){printf("%s",$2)}else{print $2};count++}' >> $nic_tmp_file
  # calculate the data average
  get_colume_avg $nic_tmp_file $output_file
  rm $nic_tmp_file
}

function deal_mem_data {
  # arg1 : input file
  # arg2 : output file
  # arg3 : hostname
  input_file=$1
  output_file=$2
  host=$3
  mem_tmp_file=mem.tmp
  echo -e "kbmemfree\tkbmemused\t%memused\tkbbuffers\tkbcached\tkbcommit\t%commit\tkbactive\tkbinact\n" >> $output_file
  echo -n "$host " >> $output_file
  # filter the mem data
  cat $input_file | sed -n '/kbmemfree/{n;p}' | sed '1d' | sed '$d' | awk '{for(i=3;i<=NF;i++) printf $i""FS;print ""}' >> $mem_tmp_file
  # calculate the mem data average
  get_colume_avg $mem_tmp_file $output_file
  rm $mem_tmp_file
}

function deal_tps_data {
  # arg1 : input file
  # arg2 : output file
  # arg3 : hostname
  input_file=$1
  output_file=$2
  host=$3
  tps_tmp_file=tps.tmp
  echo -e "tps\trtps\twtps\tbread/s\tbwrtn/s\n" >> $output_file
  echo -n "$host " >> $output_file
  # filter the tps data
  cat $input_file | sed -n '/rtps/{n;p}' | sed '1d' | sed '$d' | awk '{for(i=3;i<=NF;i++) printf $i""FS;print ""}' >> $tps_tmp_file
  # calculate the tps data average
  get_colume_avg $tps_tmp_file $output_file
  rm $tps_tmp_file
}

#======================================   main   ===========================================
dst_dir=$dest_dir/$1

mkdir -p $dst_dir/vclient

tmp_all_cpu=$dst_dir/vclient/tmp_all_vclient_cpu_sar.tmp
tmp_all_nic=$dst_dir/vclient/tmp_all_vclient_nic_sar.tmp
tmp_all_mem=$dst_dir/vclient/tmp_all_vclient_mem_sar.tmp
tmp_all_tps=$dst_dir/vclient/tmp_all_vclient_iops_sar.tmp

list_vclient=`echo $list_vclient | sed 's/,/ /g'`
for vclient in $list_vclient
do
    sar_file=$dst_dir/$vclient/${vclient}_sar.txt
    deal_cpu_data $sar_file $tmp_all_cpu $vclient
    deal_nic_data $sar_file $tmp_all_nic $vclient
    deal_mem_data $sar_file $tmp_all_mem $vclient
    deal_tps_data $sar_file $tmp_all_tps $vclient
done

tail_sum_avg $tmp_all_cpu
tail_sum_avg $tmp_all_nic
tail_sum_avg $tmp_all_mem
tail_sum_avg $tmp_all_tps

echo "******CPU******"
head -1 $tmp_all_cpu; tail -2 $tmp_all_cpu
echo "******NIC******"
head -1 $tmp_all_nic; tail -2 $tmp_all_nic
echo "******MEM******"
head -1 $tmp_all_mem; tail -2 $tmp_all_mem
echo "******TPS******"
head -1 $tmp_all_tps; tail -2 $tmp_all_tps

#convert the tmp file to csv file
echo -e "\n----convert tmp file to csv files----"
now_dir=`pwd`
cd $now_dir
cd $dst_dir/vclient
for input_file in `ls tmp_all_vclient_*.tmp`
do
        output_file=${input_file#tmp_all_}
        output_file=${output_file%.tmp}
        output_file=$output_file.csv
        convert_csv $input_file $output_file
        rm $input_file
done
cd $now_dir

