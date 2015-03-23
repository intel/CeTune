
for osd in sn1 sn2 sn3 sn4 sn5
do
	echo "checking $osd"
	ssh $osd "cat /proc/sys/vm/vfs_cache_pressure; echo 1 > /proc/sys/vm/vfs_cache_pressure; cat /proc/sys/vm/vfs_cache_pressure"
done
