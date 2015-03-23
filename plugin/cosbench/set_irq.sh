
for sn in sn1 sn2 sn3 sn4 sn5
do
	scp set_net.sh root@$sn:/
	scp set_mpt.sh root@$sn:/
	ssh root@$sn "cd /; service irqbalance stop; killall irqbalance; bash set_net.sh eth0; bash set_net.sh eth2; bash set_net.sh eth4; bash set_net.sh eth5; bash set_net.sh eth3; bash set_mpt.sh mpt2sas0"
done



