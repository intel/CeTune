import header
import os
import os.path
import time
lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
this_file_path = os.path.dirname(os.path.abspath(__file__))
from benchmarking.mod.benchmark import *
from conf import common

class Cosbench(Benchmark):
    def load_parameter(self):
        super(self.__class__,self).load_parameter()
        self.rgw={}
        self.rgw["rgw_server"]=self.all_conf_data.get("rgw_server")
        self.rgw["rgw_num_per_server"]=self.all_conf_data.get("rgw_num_per_server")
        self.cosbench={}
        self.cosbench["cosbench_folder"]=self.all_conf_data.get("cosbench_folder")
        self.cosbench["timeout"]=self.all_conf_data.get("timeout")
        self.cosbench["cosbench_driver"]=self.all_conf_data.get("cosbench_driver")
        self.cosbench["cosbench_controller"]=self.all_conf_data.get("cosbench_controller")
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
        #first_id = 1+int(header.read_test_id(".test_id"))
        stdout,stderr = common.pdsh(self.cluster['user'],[self.cosbench['cosbench_controller']],'tail -1 %s/stop' %(self.cosbench['cosbench_folder']),'check_return')
        res = common.format_pdsh_return(stdout)
        if self.cosbench['cosbench_controller'] in res:
            first_id = int(res[self.cosbench['cosbench_controller']].strip()[1:]) + 1
        else:
            common.printout('ERROR','no run id record in cosbench_folder/stop')
            sys.exit()
        self.cosbench["cosbench_run_id"] = [str(test_id+first_id) for test_id in range(num_tests)]
        header.update_test_id(".test_id",str(first_id - 1))
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
        file_path  = (os.path.dirname(os.path.abspath(__file__)) ) + "/.tmp_cosbench_controller_config.conf"

        if os.path.isfile(file_path):
            os.remove(file_path)
        with open(file_path,'w') as conf:
            conf.write("[controller]\n")
            conf.write("concurrency=1\n")
            conf.write("drivers=")
            driver_num = (len(self.cosbench["cosbench_driver"]))
            # default each driver has two cosbench instances running
            conf.write(str(driver_num*2)+"\n")
            conf.write("log_level=INFO\n")
            conf.write("log_file=log/system.log\n")
            conf.write("archive_dir=archive\n\n")
            index = 0

            while index < driver_num:
                # default instance number per cosbench driver is two
                ip = common.pdsh(self.cluster["user"],[self.cosbench["cosbench_controller"]],"cat /etc/hosts | grep '\s%s' | head -n 1 | awk '{print $1}'"  %(self.cosbench["cosbench_driver"][index]),"check_return")[0].split(':')[1]
                ip = ip.strip()
                ip = ip.replace("\s","")
                ip = ip.replace("#","")
                print "ip is %s" %ip
                name = "driver"+str(2*index+1)
                conf.write("["+name+"]\n")
                conf.write("name="+name+"\n")
                conf.write("url=http://%s:18088/driver\n\n" %(ip))
                name = "driver"+str(2*index+2)
                conf.write("["+name+"]\n")
                conf.write("name="+name+"\n")
                conf.write("url=http://%s:17088/driver\n\n" %(ip))
                index += 1
        config_result = common.bash("cat %s" %(file_path),True)[0]
        print config_result
        continue_or_not = raw_input("This is the config of Cosbench Controller, is it correct? [y|n] ")
        if continue_or_not != "y":
            sys.exit()
        common.scp(self.cluster["user"],self.cosbench["cosbench_controller"],file_path,self.cosbench["cosbench_folder"]+"/conf/controller.conf")

    def deploy_cosbench(self):
        cosbench_nodes = copy.deepcopy([self.cosbench["cosbench_controller"]])
        cosbench_nodes.extend(self.cosbench["cosbench_driver"])
        count = 0
        print "installing dependencites on cosbench controller and driver: "+','.join(cosbench_nodes)
        print "installing git and curl..."
        #stdout,stderr = common.pdsh(self.cluster["user"],cosbench_nodes,"sudo apt-get update ")
        for software in ['git','curl']:
            stdout,stderr = common.pdsh(self.cluster["user"],cosbench_nodes,"%s --version 2>&1 | head -n 1 " %(software),'check_return')
            for arg_node in stdout.split('\n'):
                if arg_node is '':
                    continue
                if (re.search('[0-9]+\.[0-9]+\.[0-9]+',arg_node)) is None:
                    print "%s arg_node is %s" %(software,arg_node)
                    sys.stdout.flush()

                    print "Install %s on node %s" %(software,arg_node.split()[0][:-1])
                    stdout, stderr = common.pdsh(self.cluster["user"],[arg_node.split()[0][:-1]],"apt-get -y install %s 2>&1" %(software), 'check_return')
                else:
                    print "%s has already been installed on %s" %(software,arg_node.split()[0][:-1])
        print "installing java"
        stdout,stderr = common.pdsh(self.cluster["user"],cosbench_nodes," java -showversion 2>&1  |  head -n 1 | awk '{print $3}'",'check_return')
        print stdout.split('\n')
        for arg_node in stdout.split('\n'):
            if arg_node is '':
                continue
            if re.search('[0-9]+\.[0-9]+\.[0-9]+',arg_node) == None:
                node = arg_node.split()[0][:-1]
                print "Install java environment on node %s" %(node)
                try:
                    common.pdsh(self.cluster["user"],[node],"apt-get -y install openjdk-7-jre", 'error_check')
                except:
                    common.pdsh(self.cluster["user"],[node],"apt-get -f install", 'error_check')
                    common.pdsh(self.cluster["user"],[node],"apt-get -y install openjdk-7-jre", 'error_check')

            else:
                print "java environment has already been installed on %s" %(arg_node.split()[0][:-1])

        stdout,stderr = common.pdsh(self.cluster["user"],cosbench_nodes,"mkdir -p %s" %(self.cosbench['cosbench_folder']),'check_return' )
        for node in cosbench_nodes:
            common.scp(self.cluster["user"],node,"%s/cosbench" %(this_file_path),os.path.dirname(self.cosbench["cosbench_folder"]))
        common.printout('LOG', "Push cosbench to controllers and clients")

        # stdout,stderr = common.pdsh(self.cluster["user"],cosbench_nodes,"cd /cosbench; sh pack.sh "+self.cosbench["cosbench_folder"],'check_return')
        # common.printout("LOG",stdout)
        # TODO: add the function and template to change controller.conf
        print "configure cosbench..."
        self.produce_cosbench_config()

        print "run cosbench..."
        stdout,stderr = common.pdsh(self.cluster["user"],[self.cosbench["cosbench_controller"]],"cd %s; sh start-controller.sh" %(self.cosbench["cosbench_folder"]),'check_return')
        common.printout("LOG",stdout)
        # assume that # of driver is more than one
        for driver in self.cosbench["cosbench_driver"]:
            stdout,stderr = common.pdsh(self.cluster["user"],[driver],"cd %s; sh start-driver.sh" %(self.cosbench["cosbench_folder"]),'console|check_return')
            common.printout("LOG",stdout)

    def prerun_check(self):
        # check if cosbench is running
        print "check whether cosbench is running on clients..."
        cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
        cosbench_server.append(self.cosbench["cosbench_controller"])
        installed = True
        for client in cosbench_server:
            if header.remote_file_exist(client,self.cosbench["cosbench_folder"]+'/cli.sh') is False:
                common.printout("ERROR", "cosbench isn't installed on "+client)
                installed = False
                break
        if installed is False:
            install_or_not = raw_input("Install Cosbench? [y|n] ")
            if install_or_not is not "y":
                sys.exit()
            else:
                self.deploy_cosbench()
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
        config_path=os.path.dirname(__file__) + "/configs/"
        if not os.path.exists(config_path):
            print "mkdir configs/"
            os.makedirs(config_path)
        for workers in (test_worker_list):
            config_file_name = self.cosbench["cosbench_rw"]+config_middle+self.cosbench["test_size"]+"_"+workers+config_suffix
            if os.path.exists(config_path+config_file_name) == True:
                os.remove(config_path+config_file_name)
            header.replace_conf_xml(self.cosbench["cosbench_rw"],self.cosbench["test_size"],workers,config_middle,self.cosbench["cluster_ip"])
            common.bash("cat %s" %(config_path+config_file_name),option='console')
            #print "The config file content is:"
            #print config_content
            yn = raw_input( "This is the config file %s, is it correct? [y|n] " %(config_path+config_file_name))
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
        elif self.cosbench['size'] == '128KB':
            config_middle = "_10000con_10000obj_"
        else:
            config_middle = '_100con_10000obj_'
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

        count = 1
        self.cosbench["run_name"] = {}
        for workers in self.cosbench["test_worker_list"]:
            test_id_this_worker = str(header.read_test_id(".test_id")+1)
            print  "test_id_this_worker is "+ test_id_this_worker
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

            local_config = self.cosbench["cosbench_rw"]+config_middle+self.cosbench["test_size"]+"_"+workers
            local_config_file = local_config+config_suffix
            local_config_path = config_path+local_config_file
            common.bash("cat %s" %(local_config_path))
            remote_config_path = "/tmp/"+local_config_file
            print "cosbench xml file: local_config_path is " + local_config_path
            print "cosbench xml remote file is "+remote_config_path
            #./cli.sh submit /tmp/write_100con_100obj_128KB_160w.xml 2>/dev/null > /tmp/curl.cosbench && cat /tmp/curl.cosbench | awk '{print $4}'
            run_command =" sh "+self.cosbench["cosbench_folder"]+"/cli.sh submit "+remote_config_path +" 2>/dev/null | awk  '{print $4}'"
            common.scp("root",self.cosbench["cosbench_controller"],local_config_path,remote_config_path)
            try:
                self.runid = int((common.pdsh("root",list([self.cosbench["cosbench_controller"]]),run_command,"check_return")[0]).split()[1][1:]) 
            except:
                common.printout("ERROR",'Cosbench controller and driver run failed!')
                sys.exit()
            header.update_test_id(".test_id",test_id_this_worker)
            self.cosbench['run_name'][test_id_this_worker] = 'w%s-%sw' %(test_id_this_worker,local_config)
            common.pdsh("root",list([self.cosbench["cosbench_controller"]]),"rm -f %s" %(remote_config_path),"error_check")
        print "Cosbench[run_name ] is "
        print self.cosbench["run_name"]
        self.runid =  (header.read_test_id(".test_id"))

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
            still_running,stderr = (common.pdsh("root",list([self.cosbench["cosbench_controller"]]),"grep %s %s/stop" %(int(self.cosbench['cosbench_run_id'][-1]),self.cosbench["cosbench_folder"] ),"check_return"))
            res = common.format_pdsh_return(still_running)
            if not self.cosbench['cosbench_run_id'][-1] in res[self.cosbench['cosbench_controller']]:
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
            dest_dir_test_id = "%s/%s" %(dest_dir, run_id)
            common.pdsh(user,list([head]),"mkdir -p %s; mkdir -p %s/cosbench" %(dest_dir_test_id,dest_dir_test_id))
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
                #common.rrscp(user, node,  "%s/*.txt" % self.cluster["tmp_dir"], head,"%s/%s/" % (dest_dir_test_id, node))
                common.rscp(user,node,'%s/%s' %(dest_dir_test_id,node),'%s/*.txt' %(self.cluster['tmp_dir']))
            cosbench_summary_stat = self.cosbench["run_name"][run_id]
            common.rscp(user,self.cosbench['cosbench_controller'],"%s/cosbench/_cosbench.csv"%(dest_dir_test_id),"%s/archive/%s/%s.csv"%(self.cosbench["cosbench_folder"],cosbench_summary_stat,cosbench_summary_stat))
            #common.rrscp(user,self.cosbench["cosbench_controller"],"%s/archive/%s/%s.csv"%(self.cosbench["cosbench_folder"],cosbench_summary_stat,cosbench_summary_stat),head,"%s/cosbench/_cosbench.csv"%(dest_dir_test_id))

            #collect client data
            for node in cosbench_server:
                common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir_test_id, node))
                #common.rrscp(user, node, "%s/*.txt" % self.cluster["tmp_dir"], head, "%s/%s/" % (dest_dir_test_id, node) )
                common.pdsh(user,node, "%s/%s/" % (dest_dir_test_id, node),"%s/*.txt" % self.cluster["tmp_dir"] )
            #save real runtime
            #if self.real_runtime:
            #    with open("%s/real_runtime.txt" % dest_dir, "w") as f:
            #        f.write(str(int(self.real_runtime)))
