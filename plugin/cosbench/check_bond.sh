
for sn in ceph-osd1 ceph-osd2 ceph-osd3 ceph-osd4 ceph-osd5
do
	echo "checking $sn"
	ssh $sn "cat /proc/net/bonding/bond0 |grep 1000"
	echo ""
done
