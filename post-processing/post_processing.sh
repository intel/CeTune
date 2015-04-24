#!/bin/bash
    echo $disk_list

function get_colume_avg {
    step=1
    input_file=$1
    output_file=$2
    if [ -f $input_file ]; then
        cat $input_file | awk -v step=$step 'BEGIN{for(i=1;i<=NF;i++)sum[i]=0;count=0}{if(count%step==0)for(i=1; i<=NF; i++)sum[i]+=$i;count++}END{for(i=1; i<=NF; i++)if(count!=0)printf("%f\t",sum[i]/count); printf("\n")}' >> $output_file
    fi
}


function get_colume_sum {
    step=1
    input_file=$1
    output_file=$2
    if [ -f $input_file ]; then
        cat $input_file | awk -v step=$step 'BEGIN{for(i=1;i<=NF;i++)sum[i]=0;count=0}{if(count%step==0)for(i=1; i<=NF; i++)sum[i]+=$i;count++}END{for(i=1; i<=NF; i++)printf("%f\t",sum[i]); printf("\n")}' >> $output_file
    fi
}

function tail_sum_avg {
    input_file=$1
    if [ -f $input_file ]; then
        cat $input_file | sed '1d' | awk -v first_column=2 'BEGIN{for(i=first_column;i<=NF;i++)sum[i]=0}{for(i=first_column;i<=NF;i++){sum[i]+=$i}}END{printf("SUM\t"); for(i=first_column;i<=NF;i++)printf("%f\t",sum[i]); printf("\n");printf("AVG\t");for(i=first_column;i<=NF;i++)printf("%f\t",NR!=0?(sum[i]/NR):0); printf("\n")}' >> $input_file
    fi
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
  if [ -f $in_file ]; then
      cat $in_file | awk '{for(i=1;i<=NF;++i){printf("%s,",$i)};printf("\n")}' >> $out_file
  fi
}

function get_nic {
  host=$1
  nic=`echo $list_nic | sed 's/,/\n/g' | grep $host | awk -F: '{print $2}'` 
  echo $nic
}

function get_host_disk_list {
    type=$1
    host=$2

    case "$type" in
        osd)
            disk=$(eval echo \$$host)
            osd_list=`echo $disk | sed 's/,/ /g'`
	    disk=""
            for item in $osd_list
            do
                #disk=$disk" "`echo $item | awk -F: {'print $1'} | sed 's/[0-9]//g' | awk -F/ '{print $3}'`
                disk=$disk" "`echo $item | awk -F: {'print $1'} | awk -F/ '{print $3}'`
            done
	    ;;
	journal)
            disk=$(eval echo \$$host)
            osd_list=`echo $disk | sed 's/,/ /g'`
            disk=""
	    for item in $osd_list
            do
                #disk=$disk" "`echo $item | awk -F: {'print $2'} | sed 's/[0-9]/\n/g' | awk -F/ '{print $3}'`
                disk=$disk" "`echo $item | awk -F: {'print $2'} | awk -F/ '{print $3}'`
            done
            #disk=`echo $disk | sed 's/ /\n/g' | sort -u | sed 's/\n//g'`
	    ;;
        rbd)
	    disk=""
	    disk_list=`echo $run_file | sed 's/,/ /g'`
	    for item in $disk_list
            do
	        #disk=$disk" "`echo $item |  sed 's/[0-9]/\n/g' | awk -F/ '{print $3}'`
	        disk=$disk" "`echo $item |  awk -F/ '{print $3}'`
            done
	    ;;
    esac
    echo $disk
}

function get_validate_runtime {
    #below step is used to tackle some scenario that fio is finished before runtime, 
    #so the sys metrics will include some idle data, need to use fio result to get the validate runtime
    #validate_time=`tac $input_file | awk -v dev="$disk_list" 'BEGIN{split(dev,dev_arr," ");for(i in dev_arr){for(j=0;j<=NF;j++){res_arr[i,j]=0;}}}{for(i in dev_arr)if(dev_arr[i]==$1){tmp_sum=0;for(j=2;j<=NF;j++)if(res_arr[i,0]==0){tmp_sum+=$j};if(tmp_sum!=0||res_arr[i,0]!=0){for(j=2;j<=col;j++){res_arr[i,0]=1;}res_arr[i,1]+=1;col=NF}}}END{min=-1;for(i in dev_arr){if(min=-1||$res_arr[i,1]<min)min=$res_arr[i,1];}print(min);}'`
    dst_dir=$1 
    min_validate_time=-1
    for type in vclient client
    do
        eval list_vars=\$list_${type}
        nodes=`echo ${list_vars} | sed 's/,/ /g'`
        for node in $nodes
        do
            if [ ! -d "$dst_dir/${node}" ]; then
                continue
            fi
            for fio_file in `ls $dst_dir/$node/${node}*_fio.txt`
            do
	        if [ ! -f $fio_file ]; then
                    continue
                fi
                validate_time=`grep " *io=.*bw=.*iops=.*runt=.*" $fio_file | awk -F, '{print $4}'` 
                unit=`echo $validate_time | sed -re 's/[^0-9]*([0-9]*)(.*)/\2/;' | awk -F' ' '{print $1}'`
                validate_time=`echo $validate_time | sed -re 's/[^0-9]*([0-9]*)(.*)/\1/;'`
                case $unit in
                    msec)
                        validate_time=`echo "$validate_time / 1000" | bc`
                    ;;
                    usec)
                        validate_time=`echo "$validate_time / 1000 / 1000" | bc`
                    ;;
                    sec)
                    ;;
                    *)
                        validate_time=-1
                    ;;
                esac
                if [ "$validate_time" = "-1" ]; then
                    continue
                fi
                
                if [ "$min_validate_time" = "-1" -o $min_validate_time -gt $validate_time ]; then
                    min_validate_time=$validate_time
                fi
            done
        done
    done

    echo $min_validate_time
}

function deal_interrupts_data {
    input_file_start=$1
    input_file_end=$2
    output_file=$3
    token=","
    if [ -f $input_file_start ] && [ -f $input_file_end ]; then
        awk -v t=$token '{if(FNR==1 || FNR==2){col=NF;printf("%s",t);for(i=1;i<=col;i++)printf("%s%s",$i,t);printf("\n")}else{j=FNR;if(NR==FNR){arr[j,1]=$1;for(i=2;i<=col+1;i++){arr[j,i]=$i;}}else{printf("%s%s",arr[j,1],t);for(i=2;i<=col+1;i++){diff=$i-arr[j,i];printf("%d%s",diff,t)};for(k=col+2;k<=NF;k++){printf("%s%s",$k,t)}printf("\n")}}}' $input_file_start $input_file_end > $output_file
    fi

}

function deal_iostat_data {
    input_file=$1
    output_file=$2
    node=$3
    disk_list=$4
    validate_runtime=$5
    token=,
    if [ -f $input_file ]; then
        cat $input_file | awk -v dev="$disk_list" -v host=$node -v t=$token -v validate_line=$validate_runtime 'BEGIN{split(dev,dev_arr," ");for(i in dev_arr){for(j=0;j<=NF;j++){res_arr[i,j]=0;}}}{for(i in dev_arr)if(dev_arr[i]==$1){if(res_arr[i,0]!=1){for(j=2;j<=NF;j++){res_arr[i,j]+=$j;}res_arr[i,1]+=1;col=NF;if(res_arr[i,1]==validate_line)res_arr[i,0]=1}}}END{for(i in dev_arr){printf("%s-%s%s",host,dev_arr[i],t);for(j=2;j<=col;j++)printf("%f%s",res_arr[i,1]!=0?(res_arr[i,j]/res_arr[i,1]):0,t);printf("\n");}}' >> $output_file
    fi
    
    # for iostat may record some data when ceph is under no io, so need to reduce these data
    # res_arr[i,0] is a flag of identify if we should add this data, 
    # res_arr[i,1] is a colume count, it should match the run_time, ex: when run_time=600, colume_count=600
    #tac $input_file | awk -v dev="$disk_list" -v host=$node -v t=$token 'BEGIN{split(dev,dev_arr," ");for(i in dev_arr){for(j=0;j<=NF;j++){res_arr[i,j]=0;}}}{for(i in dev_arr)if(dev_arr[i]==$1){tmp_sum=0;for(j=2;j<=NF;j++)if(res_arr[i,0]==0){tmp_sum+=$j};if(tmp_sum!=0||res_arr[i,0]!=0){for(j=2;j<=col;j++){res_arr[i,0]=1;res_arr[i,j]+=$j;}res_arr[i,1]+=1;col=NF}}}END{for(i in dev_arr){printf("%s-%s%s",host,dev_arr[i],t);for(j=2;j<=col;j++)printf("%f%s",res_arr[i,j]/res_arr[i,1],t);printf("\n");}}' >> $output_file
    
}

function deal_iostat_disk_data {
    input_file=$1
    output_file=$2
    node=$3
    disk_list=$4
    validate_runtime=$5
    token=,

    disk_list=`echo $disk_list | sed 's/[0-9]*//g' | sed 's/ /\n/g' | sort -u | sed 's/\n/ /g'`
    if [ -f $input_file ]; then
        cat $input_file | awk -v dev="$disk_list" -v host=$node -v t=$token -v validate_line=$validate_runtime 'BEGIN{split(dev,dev_arr," ");for(i in dev_arr){for(j=0;j<=NF;j++){res_arr[i,j]=0;}}}{for(i in dev_arr)if(dev_arr[i]==$1){if(res_arr[i,0]!=1){for(j=2;j<=NF;j++){res_arr[i,j]+=$j;}res_arr[i,1]+=1;col=NF;if(res_arr[i,1]==validate_line)res_arr[i,0]=1}}}END{for(i in dev_arr){printf("%s-%s%s",host,dev_arr[i],t);for(j=2;j<=col;j++)printf("%f%s",res_arr[i,1]!=0?(res_arr[i,j]/res_arr[i,1]):0,t);printf("\n");}}' >> $output_file
    fi
   
}

function get_iostat_loadline {
    input_file=$1
    output_file=$2
    node=$3
    disk_list=$4
    token=,
    if [ -f $input_file ]; then
        line_count=`cat $input_file | awk -v dev="$disk_list" 'BEGIN{split(dev,dev_arr," ");for(k in dev_arr)count[k]=0}{for(k in dev_arr)if(dev_arr[k]==$1){count[k]+=1;}}END{dev_count=0;total=0;for(k in dev_arr){total+=count[k];dev_count++};print dev_count!=0?(total/dev_count):0}'`
    fi
    #echo $line_count
    if [ -f $input_file ]; then
        cat $input_file | awk -v dev="$disk_list" -v host=$node -v t=$token -v line=$line_count 'BEGIN{split(dev,dev_arr," ");dev_count=0;for(k in dev_arr){count[k]=0;dev_count+=1}for(i=1;i<=line;i++){for(j=1;j<=NF;j++){res_arr[i,j]=0;}}}{for(k in dev_arr)if(dev_arr[k]==$1){cur_line=count[k];for(j=2;j<=NF;j++){res_arr[cur_line,j]+=$j;}count[k]+=1;col=NF}}END{for(i=1;i<=line;i++){printf("%s-osd_avg%s",host,t);for(j=2;j<=col;j++)printf("%f%s",dev_count!=0?(res_arr[i,j]/dev_count):0,t);printf("\n");}}' >> $output_file
    fi
}

function deal_cpu_data {
  # arg1 : input file
  # arg2 : output file
  # arg3 : hostname
  input_file=$1
  output_file=$2
  host=$3
  validate_runtime=$4
  cpu_tmp_file=cpu.tmp
  #add header
  echo -n "$host " >> $output_file
  # filter the all cpu data
  if [ -f $input_file ]; then
    cat $input_file | sed -n '/ *CPU *%/{n;p}' | sed '1d' | sed '$d' | awk -F"all" '{print $2}' | head -$validate_runtime >> $cpu_tmp_file
  fi
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
  validate_runtime=$4
  nic_tmp_file=nic.tmp
  nic=`get_nic $host`
  echo -n "${host}-${nic} " >> $output_file
  # filter the wanted nic data
  #echo $host":"$nic
  if [ -f $input_file ] && [ "$nic" != "" ]; then
    if [ "`cat $input_file | grep $nic | wc -l`" != "0" ]; then
      echo `cat $input_file | grep $nic | wc -l`
      cat $input_file | grep "$nic" | awk -F${nic} -v step=2 'BEGIN{count=0}{if(count%step==0){printf("%s",$2)}else{print $2};count++}' | head -$validate_runtime >> $nic_tmp_file
    fi
  fi
  # calculate the data average
  get_colume_avg $nic_tmp_file $output_file
  rm $nic_tmp_file 2>/dev/null
}

function deal_mem_data {
  # arg1 : input file
  # arg2 : output file
  # arg3 : hostname
  input_file=$1
  output_file=$2
  host=$3
  validate_runtime=$4
  mem_tmp_file=mem.tmp
  echo -n "$host " >> $output_file
  # filter the mem data
  if [ -f $input_file ]; then
    cat $input_file | sed -n '/kbmemfree/{n;p}' | sed '1d' | sed '$d' | awk '{for(i=3;i<=NF;i++) printf $i""FS;print ""}' | head -$validate_runtime >> $mem_tmp_file
  fi
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
  validate_runtime=$4
  tps_tmp_file=tps.tmp
  echo -n "$host " >> $output_file
  # filter the tps data
  if [ -f $input_file ]; then
    cat $input_file | sed -n '/rtps/{n;p}' | sed '1d' | sed '$d' | awk '{for(i=3;i<=NF;i++) printf $i""FS;print ""}' | head -$validate_runtime >> $tps_tmp_file
  fi
  # calculate the tps data average
  get_colume_avg $tps_tmp_file $output_file
  rm $tps_tmp_file
}

function deal_fio_data {
#!/bin/bash
    # arg1 : input file
    # arg2 : output file
    # arg3 : hostname
    fio_file=$1
    output_file=$2
    host=$3
    token=','
    if [ ! -f $fio_file ]; then
        echo "$fio_file not exists"
        return
    fi

    iops=`grep " *io=.*bw=.*iops=.*runt=.*" $fio_file | awk -F, '{print $3}'`
    iops=${iops// iops=/}
    i=0
    for iops_iter in $iops;
    do
	iops_list[$i]=$iops_iter
        i=$(( i + 1 ))
    done
    max_line=$i

    bw=`grep " *io=.*bw=.*iops=.*runt=.*" $fio_file | awk -F, '{print $2}'`
    bw=${bw// bw=/}
    # convert unit to KB/s
    for unit in KB/s MB/s GB/s B/s
    do
        found=`echo $bw | grep -c $unit`
        if [[ $found == 1 ]]; then
           break
        fi
    done
    bw=${bw//$unit/}

    i=0
    for bw_iter in $bw;
    do
        case $unit in
          B/s)
          bw_list[$i]=`echo "scale=2;$bw_iter / 1024" | bc`
          ;;
          MB/s)
          bw_list[$i]=`echo "scale=2;$bw_iter * 1024" | bc`
          ;;
          GB/s)
          bw_list[$i]=`echo "scale=2;$bw_iter * 1024 * 1024" | bc`
          ;;
	  KB/s)
	  bw_list[$i]=${bw_iter}
	  ;;
        esac 
        i=$(( i + 1 ))
    done
    if [ $max_line -lt $i ]; then
        max_line=$i
    fi

    lat=`grep "^ *lat.*min=.*max=.*avg=.*stdev=.*" $fio_file | awk -F, '{print $3}'`
    lat_units=`grep "^ *lat.*min=.*max=.*avg=.*stdev=.*" $fio_file | awk -F' ' '{print $2}'`
#    for lat_unit in usec msec sec
#    do
#        found=`grep "^ *lat.*min=.*max=.*avg=.*stdev=.*" $fio_file | grep -c $lat_unit`
#        if [[ $found != 0 ]];then
#           break
#        fi
#    done
    lat=${lat// avg=/}
    i=0
    for lat_iter in $lat;
    do
	jj=0
	for u in $lat_units
	do	
		if [ $i -eq $jj ]; then
			break
		fi
		jj=$(( jj + 1 ))
	done

	for lat_unit in usec msec sec
	do
		found=`echo $u|grep -c $lat_unit`
		if [[ $found == 1 ]]; then
			break
		fi
	done
	
        case $lat_unit in
          usec)
          lat_list[$i]=`echo "scale=3;$lat_iter / 1000" | bc`
          ;;
          sec)
          lat_list[$i]=`echo "scale=3;$lat_iter * 1000" | bc`
          ;;
	  msec)
	  lat_list[$i]=$lat_iter
	  ;;
        esac
	i=$(( i + 1 ))
    done
    if [ $max_line -lt $i ]; then
        max_line=$i
    fi
    i=$(( max_line - 1 ))

    for j in `seq 0 $i`;
    do
    	echo -e "${host}_job${j}${token}${iops_list[$j]}${token}${bw_list[$j]}${token}${lat_list[$j]}" >> $output_file
    done
    cat $output_file
}

function process_sar_data {
    type=$1
    dst_dir=$2
    validate_runtime=$3
    mkdir -p $dst_dir/$type

    tmp_all_cpu=$dst_dir/$type/tmp_all_${type}_cpu_sar.tmp
    tmp_all_nic=$dst_dir/$type/tmp_all_${type}_nic_sar.tmp
    tmp_all_mem=$dst_dir/$type/tmp_all_${type}_mem_sar.tmp
    tmp_all_tps=$dst_dir/$type/tmp_all_${type}_iops_sar.tmp
    
    echo -e "CPU\t%usr\t%nice\t%sys\t%iowait\t%irq\t%soft\t%steal\t%guest\t%gnice\t%idle" >> $tmp_all_cpu
    echo -e "IFACE\trxpck/s\ttxpck/s\trxkB/s\ttxkB/s\trxcmp/s\ttxcmp/s\trxmcst/s\trxerr/s\ttxerr/s\tcoll/s\trxdrop/s\ttxdrop/s\ttxcarr/s\trxfram/s\trxfifo/s\ttxfifo/s" >> $tmp_all_nic
    echo -e "MEM\tkbmemfree\tkbmemused\t%memused\tkbbuffers\tkbcached\tkbcommit\t%commit\tkbactive\tkbinact" >> $tmp_all_mem
    echo -e "NETWORK\ttps\trtps\twtps\tbread/s\tbwrtn/s" >> $tmp_all_tps
    
    eval list_vars=\$list_${type}
    nodes=`echo ${list_vars} | sed 's/,/ /g'`
    for node in $nodes
    #for node in `ls $dst_dir | grep $type | grep -v $type'$'`
    do
        sar_file=$dst_dir/$node/${node}_sar.txt
	if [ -f $sar_file ]; then
            deal_cpu_data $sar_file $tmp_all_cpu $node $validate_runtime
            deal_nic_data $sar_file $tmp_all_nic $node $validate_runtime
            deal_mem_data $sar_file $tmp_all_mem $node $validate_runtime
            deal_tps_data $sar_file $tmp_all_tps $node $validate_runtime
        fi
    done
    
    tail_sum_avg $tmp_all_cpu
    tail_sum_avg $tmp_all_nic
    tail_sum_avg $tmp_all_mem
    tail_sum_avg $tmp_all_tps

    echo "======================== $type sar data output ========================"
    now_dir=`pwd`
    cd $dst_dir/$type
    for input_file in `ls tmp_all_${type}_*.tmp`
    do
        output_file=${input_file#tmp_all_}
        output_file=${output_file%.tmp}
        output_file=$output_file.csv
        convert_csv $input_file $output_file
        rm $input_file
        echo "*****  $output_file  *****"
	cat $output_file
    done
    cd $now_dir

}

function process_interrupts_data {
    type=$1
    dst_dir=$2
    mkdir -p $dst_dir/$type
   
    #======== process interrupts raw data ========= 
    eval list_vars=\$list_${type}
    nodes=`echo ${list_vars} | sed 's/,/ /g'`
    for node in $nodes
    do
        if [ ! -d "${dst_dir}/${node}" ]; then
            continue
        fi
        output=$dst_dir/$type/${node}_interrupts.csv
    	interrupt_start=${dst_dir}/${node}/${node}_interrupts_start.txt
    	interrupt_end=${dst_dir}/${node}/${node}_interrupts_end.txt
	if [ -f $interrupt_start -a -f $interrupt_end ]; then
            deal_interrupts_data $interrupt_start $interrupt_end $output
        fi
    done
}

function process_iostat_data {
    type=$1
    dst_dir=$2
    validate_runtime=$3
    mkdir -p $dst_dir/$type
    token=','
   
    case $type in
        ceph)
	    disk_types="osd journal"
	    ;;
	vclient)
	    disk_types="rbd"
	    ;;
    esac 
    
    for disk_type in $disk_types
    do
        iostat_tmp=$dst_dir/$type/${type}_all_${disk_type}_iostat.tmp
        iostat_extra_tmp=$dst_dir/$type/${type}_all_${disk_type}_iostat_extra.tmp
        iostat=$dst_dir/$type/${type}_all_${disk_type}_iostat.csv
        iostat_extra=$dst_dir/$type/${type}_all_${disk_type}_iostat_extra.csv
        iostat_loadline=$dst_dir/$type/${type}_all_${disk_type}_iostat_loadline.csv

        #======== process iostat raw data ========= 
        eval list_vars=\$list_${type}
        nodes=`echo ${list_vars} | sed 's/,/ /g'`
        for node in $nodes
        do
            if [ ! -d "${dst_dir}/${node}" ]; then
                continue
            fi
            disk_list=`get_host_disk_list $disk_type $node`
    	    iostat_file=${dst_dir}/${node}/${node}_iostat.txt
    	    if [ -f $iostat_file ]; then
                title=`grep Device $iostat_file | head -1 | awk -v t=$token 'END{for(i=1;i<=NF;i++)printf("%s%s",$i,t);printf("\n")}'`
                deal_iostat_data $iostat_file $iostat_tmp ${node} "${disk_list}" $validate_runtime
                deal_iostat_disk_data $iostat_file $iostat_extra_tmp ${node} "${disk_list}" $validate_runtime
                get_iostat_loadline $iostat_file $iostat_loadline ${node} "${disk_list}"
    	    fi
        done
        #======== output to file ========
	echo $title > $iostat
        if [ -f $iostat_tmp ]; then
            cat $iostat_tmp | awk -F, -v t=$token 'BEGIN{count=0;for(i=2;i<=NF;i++)sum[i]=0}{for(i=2;i<=NF;i++){sum[i]+=$i;}count++;col=NF}END{printf("sum%s",t);for(i=2;i<=col;i++)printf("%f%s",sum[i],t);printf("\navg%s",t);for(i=2;i<=col;i++)printf("%f%s",count!=0?(sum[i]/count):0,t);printf("\n")}' >> $iostat
            cat $iostat_tmp >> $iostat
	    rm $iostat_tmp    
        fi
	
        echo $title > $iostat_extra
        if [ -f $iostat_extra_tmp ]; then
            cat $iostat_extra_tmp | awk -F, -v t=$token 'BEGIN{count=0;for(i=2;i<=NF;i++)sum[i]=0}{for(i=2;i<=NF;i++){sum[i]+=$i;}count++;col=NF}END{printf("sum%s",t);for(i=2;i<=col;i++)printf("%f%s",sum[i],t);printf("\navg%s",t);for(i=2;i<=col;i++)printf("%f%s",count!=0?(sum[i]/count):0,t);printf("\n")}' >> $iostat_extra
            cat $iostat_extra_tmp >> $iostat_extra
	    rm $iostat_extra_tmp    
        fi
    done

    #======= output to screen ========
    echo "======================== $type iostat data output ========================"
    find $dst_dir/$type -name "${type}_all_*_iostat.csv" | while read file
    do
	echo "*****  $file  *****"
	cat $file 
    done
}

function draw_fio_loadline {
    dst_dir=$1
    type=$2
    mkdir -p $dst_dir/$type
    cur_path=`pwd`

    eval list_vars=\$list_${type}
    nodes=`echo ${list_vars} | sed 's/,/ /g'`
    for node in $nodes
    do
        if [ -d "$dst_dir/$node/" ]; then
            #fio_generate_plots can only handle filename as *_bw.log, but fio may generate log name as *_bw.1.log, so format name here
            for fio_file in `ls $dst_dir/$node/${node}*_fio_*.txt`
            do
                format_file=`echo $fio_file | sed 's/\.[0-9]*\././'`
                mv -f $fio_file $format_file 2>/dev/null
            done
            cd $dst_dir/$node/
            fio_generate_plots $node > $node_fio_generate_plots_errorlog.txt 2>&1 
            mv *.svg $dst_dir/${type}/ 2>/dev/null
            cd $cur_path
        fi
    done
}

function process_fio_data {
    token=','
    dst_dir=$1
    type=$2 
    mkdir -p $dst_dir/$type

    tmp_all_fio=$dst_dir/${type}/${type}_fio.csv
    echo -e "vm${token}iops${token}bw(KB/s)${token}lat(ms)" > $tmp_all_fio

    eval list_vars=\$list_${type}
    nodes=`echo ${list_vars} | sed 's/,/ /g'`

    for node in $nodes
    do
        if [ ! -d "$dst_dir/$node" ]; then
            continue
        fi
        for fio_file in `ls $dst_dir/$node/${node}*_fio.txt`
        do
	    node_label=${fio_file#$dst_dir/$node/}
	    node_label=${node_label%"_fio.txt"}
	    if [ -f $fio_file ]; then
                echo "deal_fio_data $fio_file $tmp_all_fio $node_label"
                deal_fio_data $fio_file $tmp_all_fio $node_label
	    fi
        done
    done
    cat $tmp_all_fio | awk -F, 'BEGIN{for(i=1;i<=NF;i++)res[i]=0;}{for(i=2;i<=NF;i++)res[i]+=$i;col=NF}END{printf("result,");for(i=2;i<col;i++)printf("%f,",res[i]);printf("%f\n",(NR-1)!=0?(res[col]/(NR-1)):0);printf("result-avg,");for(i=2;i<=col;i++)printf("%f,",(NR-1)!=0?(res[i]/(NR-1)):0);}' >> $tmp_all_fio
    echo "======================== $type fio data output ========================"
    cat $tmp_all_fio
    echo ""

}

#==============================  main  ================================
dst_dir=$1

. ../conf/common.sh
get_conf $1/all.conf

validate_runtime=`get_validate_runtime $dst_dir`
process_sar_data vclient $dst_dir $validate_runtime
process_sar_data client $dst_dir $validate_runtime
process_sar_data ceph $dst_dir $validate_runtime

process_fio_data $dst_dir vclient 
process_fio_data $dst_dir client 

process_iostat_data ceph $dst_dir $validate_runtime
process_iostat_data vclient $dst_dir $validate_runtime

process_interrupts_data ceph $dst_dir 

#echo "Process fio loadline, this is a little slow..."
#draw_fio_loadline $dst_dir client
#draw_fio_loadline $dst_dir vclient

mkdir -p $dst_dir/csvs
rm -rf $dst_dir/csvs/*
mv $dst_dir/vclient $dst_dir/client $dst_dir/ceph $dst_dir/csvs/

echo "========================Generating Excel================================="
python wrexcel.py $dest_dir $dst_dir

echo "========================Archiving================================="
scp -rq ${dst_dir} ${dest_dir_remote_bak}
scp -q ${dest_dir}/history.csv ${dest_dir_remote_bak}/
