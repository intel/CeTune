#!/bin/bash

. ./all.conf

list_vclient=${list_vclient:=../conf/vclient.lst}
list_client=${list_client:=../conf/client.lst}
list_ceph=${list_ceph:=../conf/ceph.lst}

[ -s $list_vclient ] || (echo "$list_vclient size is ZERO";exit 1)
[ -s $list_client ] || (echo "$list_client size is ZERO";exit 1)
[ -s $list_ceph ] || (echo "$list_ceph size is ZERO";exit 1)

# killall aio-stress AND get data
for vm in `cat $list_vclient | head -n$number`
do
    ssh ${vm} "killall -9 fio;killall -9 ./fio.sh;killall -9 sar;killall -9 iostat"
done

for client in `cat $list_client`
do
    ssh ${client} "killall -9 sar;killall -9 iostat;killall -i fio"
done

for ceph in `cat $list_ceph`
do
    ssh ${ceph} "killall -9 sar;killall -9 iostat"
done

