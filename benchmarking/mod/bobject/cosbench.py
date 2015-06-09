import header
import os
import os.path
import time
lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
from benchmarking.mod.benchmark import *
from conf import common

class Cosbench(Benchmark):
    def __init__(self,testcase):
        super(self.__class__,self).__init__(testcase)
        self.rgw={}
        self.rgw["rgw_server"]=self.all_conf_data.get("rgw_server")
        self.rgw["rgw_num_per_server"]=self.all_conf_data.get("rgw_num_per_server")
        self.cosbench={}
        self.cosbench["cosbench_folder"]=self.all_conf_data.get("cosbench_folder")
        self.cosbench["timeout"]=self.all_conf_data.get("timeout")
        self.cosbench["cosbench_driver"]=self.all_conf_data.get("cosbench_driver")
        self.cosbench["cosbench_controller"]=self.all_conf_data.get("cosbench_controller")
        self.cosbench["data_user"]=self.all_conf_data.get("data_user")
        self.cosbench["data_dir"]=self.all_conf_data.get("data_dir")
        self.cosbench["test_worker_list"]=self.all_conf_data.get("test_worker_list")
        self.cosbench["test_size"]=self.all_conf_data.get("test_size")
        self.cosbench["test_scale"]=self.all_conf_data.get("test_scale")
        self.cosbench["cosbench_rw"]=self.all_conf_data.get("cosbench_rw")
        self.cosbench["data_processing_scripts"]="/var/lib/multiperf"
        self.cosbench["data_on_nodes"]="/tmp/multiperf"
        self.cosbench["cluster_ip"]=self.all_conf_data.get("cluster_ip")
        num_tests = len(self.cosbench["test_worker_list"])
        first_id = 1+int(header.read_test_id(".test_id"))
        self.cosbench_run_id = [str(test_id+first_id) for test_id in range(num_tests)]
        self.runid = first_id
        self.cosbench["run_time"] = self.all_conf_data.get("run_time")
        self.cosbench["ramp_up"] = self.all_conf_data.get("run_warmup_time")
        


    def prepare_result_dir(self):
        pass


    def print_all_attributes(self):
        print "self.cosbench:"        
        print self.cosbench
        print "self.rgw"        
        print self.rgw
        print "self.cluster"
        print self.cluster

    def prerun_check(self):
        # check if cosbench is running
        print "check whether cosbench is running on clients..."
        cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
        cosbench_server.append(self.cosbench["cosbench_controller"])
        for client in cosbench_server:
            if header.remote_file_exist(client,self.cosbench["cosbench_folder"]) == False:
                print bcolors.FAIL + "[ERROR]: cosbench isn't installed on "+client+bcolors.ENDC
                sys.exit()
        print "Cosbench works well" 
        # check if radosgw is running
        print "check whether radosgw is running..."
        output =  common.bash("curl "+ self.rgw["rgw_server"],True)
        if re.search('amazon',output[0]) == None:
            print common.bcolors.FAIL + "[ERROR]: radosgw doesn't workd" + common.bcolors.ENDC
        else:
            print "radosgw is running"

    def update_config(self,config_middle,test_worker_list):
        config_suffix = "w.xml"
        for workers in test_worker_list:
            config_file_name = self.cosbench["cosbench_rw"]+config_middle+self.cosbench["test_size"]+"_"+workers+config_suffix
            config_path=os.path.dirname(__file__) + "/configs/"
            if os.path.exists(config_path+config_file_name) == True:
                os.remove(config_path+config_file_name)
            header.replace_conf_xml(self.cosbench["cosbench_rw"],self.cosbench["test_size"],workers,config_middle,self.cosbench["cluster_ip"])

    def stop_data_collectors(self):
        ceph_nodes = copy.deepcopy(self.cluster["osd"])
        ceph_nodes.append(self.rgw["rgw_server"]) 
        for node in ceph_nodes:
            print "Kill sleep, sar, sadc, iostat, vmstat, mpstat, blktrace on each ceph osd. Clean up data on node:" + node
            common.pdsh("root",node,"killall -q sleep; killall -q sar sadc iostat vmstat mpstat blktrace","check_return")

       
    def prepare_run(self):
        print "[cosbench] prepare_run"
        self.print_all_attributes()
        self.stop_data_collectors()
        # kill sleep, sar, sadc, iostat, vmstat, mpstat, blktrace on each ceph osd.
        print "unset proxy on cosbench controller and drivers..."
        # Unset http_proxy for each cosbench node
        common.pdsh("root",self.cosbench["cosbench_driver"],"unset http_proxy","error_check")
        common.pdsh("root",[self.cosbench["cosbench_controller"]],"unset http_proxy","error_check")
        
    def run(self):
        print "[cosbench] starting workloads..."
        config_prefix = self.cosbench["cosbench_rw"]
        config_suffix = "w.xml"
        config_path=os.path.dirname(__file__) + "/configs/"
        if self.cosbench["test_scale"]== "small":
            config_middle = "_100con_100obj_"
        else:
            config_middle = "_10000con_10000obj_"
        self.update_config(config_middle,self.cosbench["test_worker_list"])
        print "start system statistics..."
        ceph_nodes = copy.deepcopy(self.cluster["osd"])
        ceph_nodes.append(self.rgw["rgw_server"])
        ceph_nodes.extend(self.cosbench["cosbench_driver"])
        ramp_up = self.cosbench["ramp_up"]
        interval = 5
        # TODO: replace this with the config from all.conf
        #runtime = self.cosbench["run_time"]
        #user = self.cluster["user"]
        runtime = "300"
        ramp_up = "100"
        time = int(ramp_up) + int(runtime)
        dest_dir = self.cluster["tmp_dir"]
           
        for workers in self.cosbench["test_worker_list"]:
            common.pdsh(user,ceph_nodes,"dmesg -C; dmesg -c >> /dev/null")
            common.pdsh(user, ceph_nodes, "echo '1' > /proc/sys/vm/drop_caches && sync")
        
            #send command to ceph cluster
            # TODO: Question: do we have to sleep for a rampup time before starting collecting data?
            common.pdsh(user, ceph_nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt" % (dest_dir))
            common.pdsh(user, ceph_nodes, "top -c -b -d 1 -n %d > %s/`hostname`_top.txt &" % (time, dest_dir))
            common.pdsh(user, ceph_nodes, "mpstat -P ALL 1 %d > %s/`hostname`_mpstat.txt &"  % (time, dest_dir))
            common.pdsh(user, ceph_nodes, "iostat -p -dxm 1 %d > %s/`hostname`_iostat.txt &" % (time, dest_dir))
            common.pdsh(user, ceph_nodes, "sar -A 1 %d > %s/`hostname`_sar.txt &" % (time, dest_dir))
        
            local_config_file = self.cosbench["cosbench_rw"]+config_middle+self.cosbench["test_size"]+"_"+workers+config_suffix
            local_config_path = config_path+local_config_file
            remote_config_path = "/tmp/"+local_config_file
            print local_config_path
            run_command =" sh "+self.cosbench["cosbench_folder"]+"/cli.sh submit "+remote_config_path +"| awk  '{print $4}'"
            
            common.scp("root",self.cosbench["cosbench_controller"],local_config_path,remote_config_path)
            self.runid = int((common.pdsh("root",list([self.cosbench["cosbench_controller"]]),run_command,"check_return")[0]).split()[1][1:]) 
            header.update_test_id(".test_id",str(self.runid))
            common.pdsh("root",list([self.cosbench["cosbench_controller"]]),"rm -f %s" %(remote_config_path),"error_check")
            
    
    def after_run(self):
        print "[cosbench] waiting for the workload to stop..."
        self.wait_workload_to_stop()
        self.stop_data_collectors()
        
    def get_curr_workload(self):
        pass
        # TODO: get current work id

    def stop_workload(self):
        pass
        # TODO: stop cosbench workload



    def wait_workload_to_stop(self):
        curr_time = 0
        while True:
            time.sleep(1)
            curr_time += 1
            print ".",
            if curr_time % 20 == 0:
                print ""
            still_running = (common.pdsh("root",list([self.cosbench["cosbench_controller"]]),"grep %s %s/stop" %(int(self.runid),self.cosbench["cosbench_folder"] ),"check_return")[0])
            if still_running == '':
                if curr_time == int(self.cosbench["timeout"]):
                    break
            else:
                break
        print "w"+str(self.runid)+" ends"
            
            
    def post_processing(self):
        return

        

    def testjob_distribution(self):
        pass

    def cal_run_job_distribution(self):
        print "The test ID we are going to do is:"+ ','.join(self.cosbench_run_id) 
        print "scale:" + self.cosbench["test_scale"]
        print "size:" + self.cosbench["test_size"]
        

    def archive(self):
        pass
