
for sn in sn1 sn2 sn3 sn4 sn5
do
	echo "checking $sn"
for disk in sde sdf sdg sdh sdi sdj sdk sdl sdm
do
#	echo 8192 > /sys/block/$disk/queue/read_ahead_kb
	
	echo "checking $disk"
	ssh $sn "cat /sys/block/$disk/queue/read_ahead_kb"
done
done
