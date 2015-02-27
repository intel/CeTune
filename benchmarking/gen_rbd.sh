#!/bin/bash

. ../conf/common.sh
get_conf

if [ $# -eq 0 ];then
    rm -rf ../conf/rbd.conf >/dev/null 2>null
    client_num=0
    rbd_line=0
    for i in `echo $list_client | sed 's/,/\n/g'`
    do
        let "client_num+=1"
        rbd_num=`echo ${rbd_num_per_client} | cut -d ',' -f ${client_num}`
        if [ ${rbd_num} -gt 0 ];then
            rbd_line=$(( rbd_line + rbd_num ))
            rbd ls | head -${rbd_line} | tail -${rbd_num} | while read line
            do
                printf "%-18s\t%-8s\t%-s\n" $i 'rbd' $line >> ../conf/rbd.conf
            done
        fi
    done
elif [ $# -eq 1 -a $1 == '-h' ];then
    echo -e "Usage:\n\tbash gen_rbd.sh\n\tbash gen_rbd.sh  client pool rbd_num"
else
    echo -e 'Wrong parameters! Please check your input!'
    exit 1
fi
