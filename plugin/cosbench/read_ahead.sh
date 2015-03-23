
for disk in sde sdf sdg sdh sdi sdj sdk sdl sdm
do
	echo $1 > /sys/block/$disk/queue/read_ahead_kb
done
