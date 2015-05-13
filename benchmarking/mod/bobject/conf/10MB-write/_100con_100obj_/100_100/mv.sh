
for work in 0 5 10 20 40 80 160 320 640 1280 2560
do
	mv write_100con_100obj_128KB_${work}w.xml write_100con_100obj_10MB_${work}w.xml

done

sed -i 's/128KB/10MB/g' *.xml
