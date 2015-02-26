#!/bin/bash

echo `date+%Y-%m-%d %H:%M:%S` >> autorun.log
echo bash ceph-deploy.sh purge >> autorun.log
bash ceph-deploy.sh purge 
sleep 100

echo bash ceph-deploy.sh install >> autorun.log
bash ceph-deploy.sh install
sleep 100

echo bash ceph-deploy.sh deploy mon >> autorun.log
bash ceph-deploy.sh deploy mon
sleep 30

echo bash ceph-deploy.sh deploy osd >> autorun.log
bash ceph-deploy.sh deploy osd
sleep 30

echo ceph osd pool set rbd pg_num 512 >> autorun.log
ceph osd pool set rbd pg_num 512
sleep 30

echo ceph osd pool set rbd pgp_num 512 >> autorun.log
ceph osd pool set rbd pgp_num 512
sleep 100

echo ceph osd pool set rbd size 1 >> autorun.log
ceph osd pool set rbd size 1
sleep 180

echo ceph osd pool set rbd size 2 >> autorun.log
ceph osd pool set rbd size 2

ceph -v >> autorun.log
ceph -s >> autorun.log
