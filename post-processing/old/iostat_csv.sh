#!/bin/bash

processing_iostat_data()
{
  #arg1 (vclient , client , ceph)
  #arg2 (null before_run)
  class=$1
  which_iostat=$2
  subdir=""
  if [[ $which_iostat != "" ]];then
     subdir=/$which_iostat
     which_iostat=${which_iostat}_
  fi
  num_of_items=`echo ${care_items[*]} | wc | awk '{print $2}'`
  case $class in 
    vclient)
    list_file=$list_vclient
    ;;
    client)
    list_file=$list_client
    ;;
    ceph)
    list_file=$list_ceph
    ;;
    *)
    echo "wrong type"
    exit 1
  esac
  tmp_file_iostat=$dst_dir/tmp_iostat.txt
  tmp_file_iostat_avg=$dst_dir/tmp_iostat_avg.csv
  cat $list_file | while read host
  do
      iostat_file=${src_dir}/${host}/${host}_iostat.txt
      perl ./iostat_csv.pl $iostat_file $tmp_file_iostat
      perl ./csv2avg.pl $tmp_file_iostat $tmp_file_iostat_avg
      for disk in ${care_disks[*]}
      do
          tmp_file_disk_iostat=$dst_dir/${class}${subdir}/tmp_${class}_${which_iostat}${disk}_iostat.tmp
          if [[ ! -e $dst_dir/${class}${subdir} ]];then
             mkdir -p $dst_dir/${class}${subdir}
          fi
	  if [[ ! -e $tmp_file_disk_iostat ]];then
	     echo "host ${care_items[*]}" >  $tmp_file_disk_iostat
	  fi
          echo -n "$host " >> $tmp_file_disk_iostat
	  for item in ${care_items[*]}
	  do
	      echo -n " `grep -A $num_of_items $disk $tmp_file_iostat_avg | grep -E "^(|$disk)$item" \
	      | awk -F, '{print $2}'`" >> $tmp_file_disk_iostat
	  done
	  echo "" >> $tmp_file_disk_iostat
      done
  done  
  rm $tmp_file_iostat $tmp_file_iostat_avg

  #count sum and avg
  for host_disk_iostat in `ls $dst_dir/${class}${subdir}/tmp_${class}_${which_iostat}*_iostat.tmp`
  do
      ./sum_avg.sh $host_disk_iostat 1
  done
}

sum_avg_osd_or_journal()
{
  deal_dir=$1
  disk_file=$2
  given_name=$3
  #variables depends: ceph_nodes
  if [[ $given_name != "" ]];then
     given_name=${given_name}_
  fi
  all_file=$dst_dir/ceph/tmp_ceph_${given_name}all_${which_disks}_iostat.tmp
  echo "disk ${care_items[*]}" > $all_file
  cat $list_ceph | while read host
  do
      out_file=$dst_dir/ceph/tmp_ceph_${given_name}${host}_${which_disks}_iostat.tmp
      echo "disk ${care_items[*]}" > $out_file
      disk_num=`grep $host ${disk_file} | awk '{print $2}'`
      for disk in `grep -A $disk_num $host ${disk_file}`
      do
          disk_iostat_file=`ls $deal_dir | grep "tmp_ceph_.*${disk}.*_iostat.tmp"`
          if [[ $disk_iostat_file ]];then
             echo `sed -n "s/$host/$disk/p" $deal_dir/$disk_iostat_file` >> $out_file
             echo `sed -n "s/$host/${host}-$disk/p" $deal_dir/$disk_iostat_file` >> $all_file
          fi
      done
     ./sum_avg.sh $out_file 1
  done
  ./sum_avg.sh $all_file 1
}

collect_care_items()
{
}

if [ $# != 1 ];then
   echo "$0 runid"
   exit 1
fi

src_dir=${dest_dir}/`ls ${dest_dir} | grep "^$runid-"`
dst_dir=${src_dir}/csvs/

. ./all.conf

list_osd=${list_osd:=../conf/osd.lst}
list_journal=${list_journal:=../conf/journal.lst}
list_vclient=${list_vclient:=../conf/vclient.lst}
list_client=${list_client:=../conf/client.lst}
list_ceph=${list_ceph:=../conf/ceph.lst}


