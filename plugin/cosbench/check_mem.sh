
for sn in ceph-osd1 ceph-osd2 ceph-osd3 ceph-osd4 ceph-osd5
do
	echo "checking $sn"
	ssh $sn "free -g"
	echo ""
done
