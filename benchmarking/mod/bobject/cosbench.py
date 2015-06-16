import header
import os
import os.path
import time
lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
this_file_path = os.path.dirname(os.path.abspath(__file__))
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
        #self.cosbench["data_user"]=self.all_conf_data.get("data_user")
        self.cosbench["data_dir"]=self.all_conf_data.get("dest_dir")
        
        self.cosbench["test_size"]=self.all_conf_data.get("test_size")
        self.cosbench["test_scale"]=self.all_conf_data.get("test_scale")
        self.cosbench["cosbench_rw"]=self.all_conf_data.get("cosbench_rw")
        self.cosbench["data_processing_scripts"]="/var/lib/multiperf"
        self.cosbench["data_on_nodes"]="/tmp/multiperf"
        self.cosbench["cluster_ip"]=self.all_conf_data.get("cluster_ip")
        workers = self.all_conf_data.get("test_worker_list")
        if type(workers) is list:
            self.cosbench["test_worker_list"]=workers
        else:
            self.cosbench["test_worker_list"]= list([workers])
        num_tests = len(self.cosbench["test_worker_list"])
        first_id = 1+int(header.read_test_id(".test_id"))
        self.cosbench["cosbench_run_id"] = [str(test_id+first_id) for test_id in range(num_tests)]
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

    def produce_cosbench_config(self):
        file_path  = (os.path.dirname(os.path.abspath(__file__)) ) + "/.tmp_config_file"

        if os.path.isfile(file_path):
            os.remove(file_path)
        with open(file_path,'w+') as conf:
            conf.write("[controller]\n")
            conf.write("concurrency=1\n")
            conf.write("drivers=")
            driver_num = (len(self.cosbench["cosbench_driver"]))
            conf.write(str(driver_num)+"\n")
            conf.write("log_level=INFO\n")
            conf.write("log_file=log/system.log\n")
            conf.write("archive_dir=archive\n\n")
            
            for index in range((driver_num)):
                name = "driver"+str(index+1)
                conf.write("["+name+"]\n")
                conf.write("name="+name+"\n")
                ip = bash("grep %s /etc/hosts | awk '{print $1}'" %(self.cosbench["cosbench_driver"][index]))
                conf.write("url=http://%s:18088/driver\n\n" %(ip))
        common.scp(self.cluster["user"],file_path,self.cosbench["cosbench_folder"]+"/conf/controller.conf")

    '''
    def deploy_cosbench(self):
        cosbench_nodes = copy.deepcopy(list([self.cosbench["cosbench_controller"]]))
        cosbench_nodes.extend(self.cosbench["cosbench_driver"])
        print "downloading cosbench from git..."
        common.pdsh(self.cluster["user"],cosbench_nodes,"git clone https://github.com/intel-cloud/cosbench.git")
        
        print "installing dependencites on cosbench controller and driver..."
        pdsh(self.cluster["user"],cosbench_nodes,"sudo apt-get update && sudo apt-get install openjdk-7-jre")
        stdout,stderr = pdsh(self.cluster["user"],cosbench_nodes," java -showversion 2>&1  |  head -1 | awk '{print $1}'",check_return)
        if stdout != "java":
            print bcolors.FAIL + "[ERROR]: java environment installation failed "+client+bcolors.ENDC
                sys.exit()
        pdsh(self.cluster["user"],cosbench_nodes,"sudo apt-get install curl ")
        stdout,stderr = pdsh(self.cluster["user"],cosbench_nodes," curl --version 2>&1  |  head -1 | awk '{print $1}'",check_return)
        if stdout != "curl":
            print bcolors.FAIL + "[ERROR]: curl installation failed "+client+bcolors.ENDC
                sys.exit()
        common.pdsh(self.cluster["user"],cosbench_nodes,"sh cosbench/pack.sh "+self.cosbench["cosbench_folder"])

        # TODO: add the function and template to change controller.conf
        print "configure cosbench..."
        self.produce_cosbench_config()

        print "run cosbench..."
        common.pdsh(self.cluster["user"],list([self.cosbench["cosbench_controller"]]),"sh %s/start-controller.sh")
        common.pdsh(self.cluster["user"],self.cosbench["cosbench_driver"],"sh %s/start-driver.sh")        
    '''
    def prerun_check(self):
        # check if cosbench is running
        print "check whether cosbench is running on clients..."
        cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
        cosbench_server.append(self.cosbench["cosbench_controller"])
        for client in cosbench_server:
            if header.remote_file_exist(client,self.cosbench["cosbench_folder"]) == False:
                common.printout("ERROR", "cosbench isn't installed on "+client)
                sys.exit()
        print "Cosbench works well" 
        # check if radosgw is running
        print "check whether radosgw is running..."
        output =  common.bash("curl "+ self.rgw["rgw_server"],True)
        if re.search('amazon',output[0]) == None:
            common.printout("ERROR","radosgw doesn't work")
        else:
            print "radosgw is running"

    def update_config(self,config_middle,test_worker_list):
        config_suffix = "w.xml"
        

        for workers in (test_worker_list):
            config_file_name = self.cosbench["cosbench_rw"]+config_middle+self.cosbench["test_size"]+"_"+workers+config_suffix
            config_path=os.path.dirname(__file__) + "/configs/"
            if os.path.exists(config_path+config_file_name) == True:
                os.remove(config_path+config_file_name)
            header.replace_conf_xml(self.cosbench["cosbench_rw"],self.cosbench["test_size"],workers,config_middle,self.cosbench["cluster_ip"])
            
            config_content = common.bash("cat %s" %(config_path+config_file_name))
            print "The config file content is:"
            print config_content
            yn = raw_input( "This is the config file %s, is it correct? [y|n] " %(config_file_name))
            print " "
            if yn != "y":
                sys.exit()

    def stop_data_collectors(self):
        ceph_nodes = copy.deepcopy(self.cluster["osd"])
        ceph_nodes.append(self.rgw["rgw_server"]) 
        ceph_nodes.extend(self.cosbench["cosbench_driver"])
        print "Kill sleep, sar, sadc, iostat, vmstat, mpstat, blktrace on each ceph osd. Clean up data on node:" + ','.join(ceph_nodes)
        common.pdsh("root",ceph_nodes,"killall -q sleep; killall -q sar sadc iostat vmstat mpstat blktrace","force")

       
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
        runtime = self.cosbench["run_time"]
        user = self.cluster["user"]
        
        #ramp_up = "100"
        time = int(ramp_up) + int(runtime)
        dest_dir = self.cluster["tmp_dir"]
    
        count = 0
        for workers in self.cosbench["test_worker_list"]:
            test_id_this_worker = str(header.read_test_id(".test_id")+count)
            dest_dir_this_worker = "%s/%s_cosbench" %(dest_dir,test_id_this_worker)
            count += 1
            common.pdsh(user,ceph_nodes,"dmesg -C; dmesg -c >> /dev/null")
            common.pdsh(user, ceph_nodes, "echo '1' > /proc/sys/vm/drop_caches && sync")
        
            #send command to ceph cluster
            # TODO: Question: do we have to sleep for a rampup time before starting collecting data?
            common.pdsh(user,ceph_nodes,"mkdir -p %s" %(dest_dir_this_worker))
            common.pdsh(user, ceph_nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt" % (dest_dir_this_worker))
            common.pdsh(user, ceph_nodes, "top -c -b -d 1 -n %d > %s/`hostname`_top.txt &" % (time, dest_dir_this_worker))
            common.pdsh(user, ceph_nodes, "mpstat -P ALL 1 %d > %s/`hostname`_mpstat.txt &"  % (time, dest_dir_this_worker))
            common.pdsh(user, ceph_nodes, "iostat -p -dxm 1 %d > %s/`hostname`_iostat.txt &" % (time, dest_dir_this_worker))
            common.pdsh(user, ceph_nodes, "sar -A 1 %d > %s/`hostname`_sar.txt &" % (time, dest_dir_this_worker))
        
            local_config_file = self.cosbench["cosbench_rw"]+config_middle+self.cosbench["test_size"]+"_"+workers+config_suffix
            local_config_path = config_path+local_config_file
            common.bash("cat %s" %(local_config_path))
            remote_config_path = "/tmp/"+local_config_file
            print "cosbench xml file: local_config_path is " + local_config_path
            print "cosbench xml remote file is "+remote_config_path
            #./cli.sh submit /tmp/write_100con_100obj_128KB_160w.xml 2>/dev/null > /tmp/curl.cosbench && cat /tmp/curl.cosbench | awk '{print $4}'
            run_command =" sh "+self.cosbench["cosbench_folder"]+"/cli.sh submit "+remote_config_path +" 2>/dev/null | awk  '{print $4}'"
            common.scp("root",self.cosbench["cosbench_controller"],local_config_path,remote_config_path)
            self.runid = int((common.pdsh("root",list([self.cosbench["cosbench_controller"]]),run_command,"check_return")[0]).split()[1][1:]) 
            header.update_test_id(".test_id",test_id_this_worker)
            
            common.pdsh("root",list([self.cosbench["cosbench_controller"]]),"rm -f %s" %(remote_config_path),"error_check")

    def after_run(self):
        print "[cosbench] waiting for the workload to stop..."
        self.wait_workload_to_stop()
        self.stop_data_collectors()
        
    def cleanup(self):
        cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
        cosbench_server.append(self.cosbench["cosbench_controller"])
        ceph_nodes = copy.deepcopy(self.cluster["osd"])
        ceph_nodes.append(self.rgw["rgw_server"])
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        common.pdsh(user, ceph_nodes, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))
        common.pdsh(user, cosbench_server, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))



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
            still_running = (common.pdsh("root",list([self.cosbench["cosbench_controller"]]),"grep %s %s/stop" %(int(self.runid),self.cosbench["cosbench_folder"] ),"force"))
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
        print "The test ID we are going to do is:"+ ','.join(self.cosbench["cosbench_run_id"]) 
        print "scale:" + self.cosbench["test_scale"]
        print "size:" + self.cosbench["test_size"]
        

    def archive(self):
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cosbench["data_dir"]
       
        for run_id in self.cosbench["cosbench_run_id"]:
            dest_dir_test_id = "%s/%s_cosbench" %(dest_dir, run_id)
            common.pdsh(user,list([head]),"mkdir -p %s" %(dest_dir_test_id))
            #collect all.conf
            common.scp(user, head, "%s/conf/all.conf" % self.pwd,  "%s/all.conf" % (dest_dir_test_id))
        
            #collect osd data
            cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
            #cosbench_server.append(self.cosbench["cosbench_controller"])
            ceph_nodes = copy.deepcopy(self.cluster["osd"])
            ceph_nodes.append(self.rgw["rgw_server"])

            #print "collect data from cosbench controller..."
            #common.rrscp(user, self.cosbench["cosbench_controller"],"%s/%s/archieve/" self.cosbench["cosbench_folder"]
        
            print "collect data from osd and rgw..."
            for node in ceph_nodes:
                common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir_test_id, node))
                common.rrscp(user, node,  "%s/*.txt" % self.cluster["tmp_dir"], head,"%s/%s/" % (dest_dir_test_id, node))
        
            #collect client data
            for node in cosbench_server:
                common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir_test_id, node))
                common.rrscp(user, node, "%s/*.txt" % self.cluster["tmp_dir"], head, "%s/%s/" % (dest_dir_test_id, node) )

            #save real runtime
            #if self.real_runtime:
            #    with open("%s/real_runtime.txt" % dest_dir, "w") as f:
            #        f.write(str(int(self.real_runtime)))
