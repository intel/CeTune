#!/bin/bash

. ../conf/all.conf

list_vclient=${list_vclient:=../conf/vclient.lst}
list_client=${list_client:=../conf/client.lst}
list_ceph=${list_ceph:=../conf/ceph.lst}
list_osd=${list_osd:=../conf/osd.lst}
list_journal=${list_journal:=../conf/journal.lst}
#add proxy
if [ "x$deploy_proxy_http" != "x" ];then
   echo "http_proxy = $deploy_proxy_http" >> /etc/wgetrc
   echo "Acquire::http::proxy "${deploy_proxy_http}"" >> /etc/apt/apt.conf
fi
#wget -q -O- 'https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/release.asc' | sudo apt-key add -
#you can modify the source here
echo "deb http://download.ceph.com/debian-${deploy_ceph_version}/ $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/ceph.list
#apt-get update && apt-get install ceph-deploy

