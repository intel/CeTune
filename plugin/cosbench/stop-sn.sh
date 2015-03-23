for ((i=1;i<=10;i++))
do
	echo "stop sn services on sn$i"
ssh sn$i "cd /etc/swift; ./sn-stop-service.sh" &
done

echo "stoping proxy1 and proxy2"
ssh proxy1 "swift-init proxy stop"
ssh proxy2 "swift-init proxy stop"
