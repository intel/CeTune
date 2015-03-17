#!/bin/bash

. ../conf/common.sh
get_conf

if [ $# -eq 1 ] && [ $1 != '-h' ];then
    cmd="rbd ls"
    if [ "$1" = "qemu" ]; then
        `echo $list_vclient | sed 's/,/\n/g' > ../conf/vclient.lst`
        cmd="cat ../conf/vclient.lst" 
    fi
    rm -rf ../conf/rbd.conf >/dev/null 2>null
    client_num=0
    rbd_line=0
    for i in `echo $list_client | sed 's/,/\n/g'`
    do
        let "client_num+=1"
        rbd_num=`echo ${rbd_num_per_client} | cut -d ',' -f ${client_num}`
        if [ ${rbd_num} -gt 0 ];then
            rbd_line=$(( rbd_line + rbd_num ))
            ${cmd} | head -${rbd_line} | tail -${rbd_num} | while read line
            do
                printf "%-18s\t%-8s\t%-s\n" $i 'rbd' $line >> ../conf/rbd.conf
            done
        fi
    done
elif [ $# -eq 1 ] && [ $1 = '-h' ];then
    echo -e "Usage:\n\tbash gen_rbd.sh\n\tbash gen_rbd.sh [qemu/fiorbd] client pool rbd_num"
else
    echo -e 'Wrong parameters! Please check your input!'
    exit 1
fi
