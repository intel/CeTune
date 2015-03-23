
for disk in sde sdf sdg sdh sdi sdj sdk sdl sdm 
do 
fdisk /dev/$disk <<END
d
n
p
1


w
END

done
