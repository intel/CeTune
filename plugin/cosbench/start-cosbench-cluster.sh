cd /cosbench/current
sh stop-controller.sh; sh start-controller.sh 
ssh root@c1 "cd /cosbench/current; sh start-driver.sh" 
ssh root@c2 "cd /cosbench/current; sh start-driver.sh" 
ssh root@c3 "cd /cosbench/current; sh start-driver.sh" 
ssh root@c4 "cd /cosbench/current; sh start-driver.sh"
ssh root@c1 "cd /cosbench/cosbench; sh start-driver.sh" 
ssh root@c2 "cd /cosbench/cosbench; sh start-driver.sh" 
ssh root@c3 "cd /cosbench/cosbench; sh start-driver.sh" 
ssh root@c4 "cd /cosbench/cosbench; sh start-driver.sh" 
 
