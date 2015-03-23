
#echo "Restarting cosbench and proxy..."
#echo "stop-csobench"
#./stop-cosbench-cluster.sh
#./killjava.sh 
#./killjava.sh
#sleep 5

if false; then
echo "stop ceph cluster"
bash stop-ceph-manual.sh
sleep 10
echo "start ceph cluster"
bash start-ceph-manual.sh
sleep 30
fi
#echo "restart proxy"
#./proxy.sh
#sleep 5
echo "start cosbench"
bash start-cosbench-cluster.sh
sleep 10
#bash status-cosbench-cluster.sh
