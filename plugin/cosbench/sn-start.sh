for ((i=1;i<=10;i++))
do
	echo "start sn$i"
ssh sn$i "cd /etc/swift; ./sn-start-service.sh" 
done
