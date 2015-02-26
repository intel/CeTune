#!/bin/bash

if [ $# != 1 ];then
   echo "$0 runid"
   exit 1
fi

runid=$1

. ./all.conf

srcdir=${dest_dir}/`ls ${dest_dir} | grep "^$runid-"`
dstdir=${srcdir}/csvs/

list_vclient=${list_vclient:=../conf/vclient.lst}
convert_csv()
{
  if [[ $# != 2 ]];then
     echo "Usage: input_file output_file"
     exit
  fi
  in_file=$1
  out_file=$2
  if [[ -e $out_file ]];then
     rm $out_file
  fi
  cat $in_file | while read line
  do
    echo `echo $line | awk 'BEGIN{ORS=","}{for(i=1;i<=NF;++i){print $i};}'` >> $out_file
  done
}

process_fio_file()
{
    fio_file=$1
    output_file=$2
    echo "process fio file $fio_file"
    echo -n $vclient >> $tmp_file
    iops=`grep " *io=.*bw=.*iops=.*runt=.*" $fio_file | awk -F, '{print $3}'`
    iops=${iops# iops=}
    bw=`grep " *io=.*bw=.*iops=.*runt=.*" $fio_file | awk -F, '{print $2}'`
    bw=${bw# bw=}
    # convert unit to KB/s
    for unit in KB/s MB/s GB/s B/s
    do
        found=`echo $bw | grep -c $unit`
        if [[ $found == 1 ]]
        then
           break
        fi
    done
    bw=${bw%$unit}
    case $unit in
      B/s)
      bw=`echo "scale=2;$bw / 1024" | bc`
      ;;
      MB/s)
      bw=`echo "scale=2;$bw * 1024" | bc`
      ;;
      GB/s)
      bw=`echo "scale=2;$bw * 1024 * 1024" | bc`
      ;;
    esac
    lat=`grep "^ *lat.*min=.*max=.*avg=.*stdev=.*" $fio_file | awk -F, '{print $3}'`
    for lat_unit in usec msec sec
    do
        found=`grep "^ *lat.*min=.*max=.*avg=.*stdev=.*" $fio_file | grep -c $lat_unit`
        if [[ $found != 0 ]];then
           break
        fi
    done
    lat=${lat# avg=}

    case $lat_unit in
      usec)
      lat=`echo "scale=2;$lat / 1000" | bc`
      ;;
      sec)
      lat=`echo "scale=2;$lat * 1000" | bc`
      ;;
    esac
    echo " $iops $bw $lat"
    echo " $iops $bw $lat" >> $output_file
}
dstdir=$dest_dir/$1
tmp_file=$dstdir/vclient/tmp_vclient_fio.tmp
echo "vm    iops   bw(KB/s)  lat(ms)" > $tmp_file

cat $list_vclient | while read vclient
do
    fio_file=$srcdir/$vclient/${vclient}_fio.txt
    process_fio_file $fio_file $tmp_file
done

lines=`wc $tmp_file | awk '{print $1}'`
declare -a sum=(0 0 0)
declare -a avg=(0 0 0)
declare -a num=(0 0 0)

for index in `seq 2 4`
do
    (( i=$index-2 ))
    for line in  `seq 2 $lines`
    do
        data=`sed -n ''$line'p' $tmp_file | awk '{print $'$index'}'`
        if [[ $data != "" ]]
        then
           (( num[$i]=${num[$i]} + 1 ))
        else
            continue
        fi
        sum[$i]=`echo "scale=2;${sum[$i]}+$data" | bc`
    done
done


#compute sum and avg
for i in `seq 0 2`
do
        avg[$i]=`echo "scale=2;${sum[$i]}/${num[$i]}" | bc`
done

sed -i "2i\ sum    ${sum[*]}" $tmp_file
sed -i "3i\ avg    ${avg[*]}" $tmp_file


#convert the tmp file to csv file
echo -e "\n----convert tmp file to csv files----"
now_dir=`pwd`
cd $now_dir
#cd $dst_dir/vclient
for input_file in `ls tmp_*_fio.tmp`
do
        output_file=${input_file#tmp_}
        output_file=${output_file%.tmp}
        output_file=$output_file.csv
        convert_csv $input_file $output_file
#        rm $input_file
done
cd $now_dir

