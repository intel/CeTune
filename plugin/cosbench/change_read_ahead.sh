
for osd in sn1 sn2 sn3 sn4 sn5
do
	ssh $osd "bash read_ahead.sh $1"
done
