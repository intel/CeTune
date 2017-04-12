import os
import os.path
import time
lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
this_file_path = os.path.dirname(os.path.abspath(__file__))
from benchmarking.mod.benchmark import *
from conf import *
import itertools
from collections import OrderedDict
from deploy import *
import sys

class Cosbench(Benchmark):
    def load_parameter(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__,self).load_parameter()
        self.rgw={}
        self.rgw["rgw_server"]=self.all_conf_data.get_list("rgw_server")
        self.rgw["rgw_num_per_server"]=self.all_conf_data.get("rgw_num_per_server")
        self.cosbench={}
        self.cosbench["cosbench_folder"]=self.all_conf_data.get("cosbench_folder")
        self.cosbench["cosbench_config_dir"]=self.all_conf_data.get("cosbench_config_dir")
        self.cosbench["cosbench_driver"]=self.all_conf_data.get_list("cosbench_driver")
        self.cosbench["cosbench_controller_admin_url"] = self.all_conf_data.get("cosbench_admin_ip")
        self.cosbench["cosbench_controller_cluster_url"] = self.all_conf_data.get("cosbench_cluster_ip")
        self.cosbench["cosbench_network"] = self.all_conf_data.get("cosbench_network")
        self.cosbench["cosbench_controller"]=self.all_conf_data.get("cosbench_controller")
        self.cosbench["data_dir"]=self.all_conf_data.get("dest_dir")
        self.cosbench["auth_username"] = self.all_conf_data.get("cosbench_auth_username")
        self.cosbench["auth_password"] = self.all_conf_data.get("cosbench_auth_password")
        self.cosbench["auth_url"] = "http://%s/auth/v1.0;retry=9" % self.cosbench["cosbench_controller_cluster_url"]
        self.cosbench["proxy"] = self.all_conf_data.get("cosbench_controller_proxy")
        self.cluster["testjob_distribution"] = copy.deepcopy(self.cosbench["cosbench_driver"])
        self.cosbench["cosbench_version"] = self.all_conf_data.get("cosbench_version")
        self.cluster["client"] = self.cosbench["cosbench_driver"]

    def parse_conobj_script(self, string):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        m = re.findall("(\w{1})\((\d+),(\d+)\)", string)
        result = {}
        if m:
            result["method"] = m[0][0]
            result["min"] = m[0][1]
            result["max"] = m[0][2]
            result["complete"] = string
        return result

    def prepare_result_dir(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        self.benchmark["container"] = self.parse_conobj_script( self.benchmark["container"] )
        self.benchmark["objecter"] = self.parse_conobj_script( self.benchmark["objecter"] )

        self.benchmark["section_name"] = "%s-cosbench-%s-%s-%scon-%sobj-%s-%s-cosbench" % (self.benchmark["worker"], self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["container"]["max"], self.benchmark["objecter"]["max"], self.benchmark["rampup"], self.benchmark["runtime"])
        self.benchmark["dirname"] = "%s-%s" % ( str(self.runid), self.benchmark["section_name"])
        self.benchmark["configfile"] = "%s/%s.xml" % (self.cosbench["cosbench_config_dir"], self.benchmark["section_name"])
        self.cluster["dest_dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])

        if common.remote_dir_exist( self.cluster["user"], self.cluster["head"], self.cluster["dest_dir"] ):
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]),log_level="LVL1")
            sys.exit()
        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))

    def print_all_attributes(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        print "self.cosbench:"
        print self.cosbench
        print "self.rgw"
        print self.rgw
        print "self.cluster"
        print self.cluster

    def produce_cosbench_config(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        controller_config = []
        driver_config = []
        conf = controller_config
        conf.append("[controller]\n")
        conf.append("concurrency=1\n")
        conf.append("drivers=")
        driver_num = (len(self.cosbench["cosbench_driver"]))
        # default each driver has two cosbench instances running
        conf.append(str(driver_num)+"\n")
#        conf.append(str(driver_num*2)+"\n")
        conf.append("log_level=INFO\n")
        conf.append("log_file=log/system.log\n")
        conf.append("archive_dir=archive\n\n")
        index = 0

        conf = driver_config
        while index < driver_num:
            ip_handler = common.IPHandler()
            ip = ip_handler.getIpByHostInSubnet(self.cosbench["cosbench_driver"][index], self.cosbench["cosbench_network"] )
#            name = "driver"+str(2*index+1)
            name = "driver"+str(index+1)
            conf.append("["+name+"]\n")
            conf.append("name="+name+"\n")
            conf.append("url=http://%s:18088/driver\n\n" %(ip))
#            name = "driver"+str(2*index+2)
#            conf.append("["+name+"]\n")
#            conf.append("name="+name+"\n")
#            conf.append("url=http://%s:17088/driver\n\n" %(ip))
            index += 1

        controller_content = "".join(controller_config)+"".join(driver_config)
        driver_content = "".join(driver_config)

        file_path  = (os.path.dirname(os.path.abspath(__file__)) ) + "/.tmp_cosbench_controller_config.conf"
        if os.path.isfile(file_path):
            os.remove(file_path)
        with open(file_path,'w') as conf:
            conf.write(controller_content)
        common.scp(self.cluster["user"],self.cosbench["cosbench_controller"],file_path,self.cosbench["cosbench_folder"]+"/conf/controller.conf")

        file_path  = (os.path.dirname(os.path.abspath(__file__)) ) + "/.tmp_cosbench_driver_config.conf"
        if os.path.isfile(file_path):
            os.remove(file_path)
        with open(file_path,'w') as conf:
            conf.write(driver_content)

        for node in self.cosbench["cosbench_driver"]:
            common.scp(self.cluster["user"],node,file_path,self.cosbench["cosbench_folder"]+"/conf/driver.conf")

    def deploy_cosbench(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        common.printout('LOG', "Start to install cosbench on controllers and clients")
        cosbench_nodes = copy.deepcopy([self.cosbench["cosbench_controller"]])
        cosbench_nodes = common.unique_extend(cosbench_nodes, self.cosbench["cosbench_driver"])
        cosbench_nodes
        # before deploy cosbench, need to check
        # if curl installed
        stdout,stderr = common.pdsh(self.cluster["user"],cosbench_nodes,"curl --version; echo $?",'check_return')
        res = common.format_pdsh_return(stdout)
        need_to_install_curl_nodes = []
        for node, value in res.items():
            if value != 0:
                need_to_install_curl_nodes.append(node)

        # if openjdk-7-jre installed
        stdout,stderr = common.pdsh(self.cluster["user"],cosbench_nodes," java -version; echo $?",'check_return')
        res = common.format_pdsh_return(stdout)
        need_to_install_java_nodes = []
        for node, value in res.items():
            if value != 0:
                need_to_install_java_nodes.append(node)

        if not ( len(need_to_install_curl_nodes) + len(need_to_install_java_nodes) ):
            common.printout("ERROR","Please install curl and openjdk-7-jre on below nodes, curl:%s, java:%s" % (str(need_to_install_curl_nodes), str(need_to_install_java_nodes)),log_level="LVL1")
            sys.exit()

        count = 0
        # check cosbench version and generate url
        tmp_dir = self.cluster["tmp_dir"]
        release_url_prefix = "https://github.com/intel-cloud/cosbench/releases/download/"
        version = self.cosbench["cosbench_version"]
        if version[0] == 'v':
            version = version[1:]
        common.printout('LOG', "Start to download cosbench codes, it may take 5 min, pls wait")
        stdout = common.bash("cd %s; rm -f %s.zip; wget %sv%s/%s.zip; echo $?" % ( tmp_dir, version, release_url_prefix, version, version))
        if int(stdout) == 0:
            common.printout("LOG", "Cosbench version %s downloaded successfully" % version)
        else:
            common.printout("ERROR", "Cosbench version %s downloaded failed" % version,log_level="LVL1")
            sys.exit()

        for node in cosbench_nodes:
            common.printout('LOG', "install cosbench to %s" % node)
            common.scp(self.cluster["user"],node,"%s/%s.zip" %(tmp_dir, version), tmp_dir)
        common.printout('LOG', "Unzip cosbench zip")
        common.pdsh(self.cluster["user"], cosbench_nodes, "cd %s;rm -rf cosbench;" % ( tmp_dir ))
        common.pdsh(self.cluster["user"], cosbench_nodes, "cd %s;unzip %s.zip;" % ( tmp_dir, version ))
        common.pdsh(self.cluster["user"], cosbench_nodes, "cd %s;mv %s %s" % ( tmp_dir, version, self.cosbench["cosbench_folder"]))
        common.printout('LOG', "Succeeded in installing cosbench on controllers and clients")

    def restart_cosbench_daemon(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        # distribute hosts file cosbench nodes
        nodes = []
        nodes.append(self.cosbench["cosbench_controller"])
        nodes.extend(self.cosbench["cosbench_driver"])
        for node in nodes:
            common.scp(self.cluster["user"], node, "/etc/hosts", "/etc/hosts" )

        for driver in self.cosbench["cosbench_driver"]:
            stdout,stderr = common.pdsh(self.cluster["user"],[driver],"cd %s;chmod +x *.sh; ./stop-driver.sh; http_proxy=%s ./start-driver.sh" %( self.cosbench["cosbench_folder"], self.cosbench["proxy"]),'console|check_return')
        stdout,stderr = common.pdsh(self.cluster["user"],[self.cosbench["cosbench_controller"]],"cd %s;chmod +x *.sh; ./stop-controller.sh; http_proxy=%s ./start-controller.sh" %(self.cosbench["cosbench_folder"],self.cosbench["proxy"]),'check_return')

    def prerun_check(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prerun_check()
        cosbench_server = []
        cosbench_server.append(self.cosbench["cosbench_controller"])
        cosbench_server = common.unique_extend( cosbench_server, self.cosbench["cosbench_driver"] )

        # check sysstat
        nodes = []
        nodes.extend(self.rgw["rgw_server"])
        common.printout("LOG","Prerun_check: check if sysstat installed")
        common.pdsh(self.cluster["user"], nodes, "mpstat")

        common.printout("LOG", "check if cosbench installed")
        # check if cosbench installed
        if not self.check_cosbench_installed(cosbench_server):
            self.deploy_cosbench()

        common.printout("LOG", "check if rgw is running")
        # check if rgw is running
        if not self.check_rgw_runing():
            run_deploy.main(['--with_rgw','restart'])
            if not self.check_rgw_runing():
                sys.exit()

        common.printout("LOG", "check if cosbench is running")
        # check if cosbench is running
        if not self.check_cosbench_runing(self.cosbench["cosbench_controller"], self.cosbench["cosbench_driver"]):
            self.produce_cosbench_config()
            self.restart_cosbench_daemon()

    def check_cosbench_runing(self, cosbench_controller, cosbench_driver):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        error_type = []
        stdout,stderr = common.pdsh(self.cluster["user"], [cosbench_controller], "http_proxy=%s sh %s/cli.sh info 2>/dev/null | grep driver" % (self.cosbench["proxy"], self.cosbench["cosbench_folder"]),'check_return')
        res = common.format_pdsh_return(stdout)
        drivers_count = 0
        ip_handler = common.IPHandler()
        planed_driver_ip = []
        for driver in cosbench_driver:
            planed_driver_ip.append(ip_handler.getIpByHostInSubnet(driver, self.cosbench["cosbench_network"]))
        planed_total_driver = 0
        for node, value in res.items():
            if "Connection refused" in value:
                error_type.append("controller_not_started")
            else:
                m = re.findall(r'http://(\d+\.\d+\.\d+\.\d+):', value, re.M)
                if m:
                    for driver in m:
                        planed_total_driver += 1
                        if  driver in planed_driver_ip:
                            planed_driver_ip.remove(driver)
                else:
                    error_type.append("No drivers detected by controller")

        stdout, stderr = common.pdsh(self.cluster["user"], self.cosbench["cosbench_driver"], "ps aux | grep cosbench | grep driver | wc -l", 'check_return')
        res = common.format_pdsh_return(stdout)
        total_driver = 0
        for node, value in res.items():
            total_driver += int(value)
        if total_driver < planed_total_driver:
            error_type.append("No all driver daemon is on")
        if len(planed_driver_ip):
            error_type.append("%s not runing cosbench daemon" % str(planed_driver_ip))

        if len(error_type):
            common.printout("WARNING", "Detect current error: %s" % str(error_type))
            return False
        return True

    def check_rgw_runing(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        stdout, stderr = common.pdsh( user, [self.cosbench["cosbench_controller"]], "http_proxy=%s curl -D - -H 'X-Auth-User: %s' -H 'X-Auth-Key: %s' %s" % (self.cosbench["proxy"], self.cosbench["auth_username"], self.cosbench["auth_password"], self.cosbench["auth_url"]), option = "check_return|console")
        if re.search('(refused|error)', stderr):
            common.printout("ERROR","Cosbench connect to Radosgw Connection Failed",log_level="LVL1")
            return False
        if re.search('Failed', stderr):
            common.printout("ERROR","Cosbench connect to Radosgw Connection Failed",log_level="LVL1")
            return False
        if re.search('Service Unavailable', stdout):
            common.printout("ERROR","Cosbench connect to Radosgw Connection Failed",log_level="LVL1")
            return False
        if re.search('Error', stdout):
            common.printout("ERROR","Cosbench connect to Radosgw Connection Failed",log_level="LVL1")
            return False
        if re.search("AccessDenied", stdout):
            common.printout("[ERROR]","Cosbench connect to Radosgw Auth Failed",log_level="LVL1")
            return False
        return True

    def check_cosbench_installed(self, cosbench_server):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        # check if cosbench installed
        installed = True
        for client in cosbench_server:
            if common.remote_file_exist(user, client, self.cosbench["cosbench_folder"]+'/cli.sh') is False:
                common.printout("WARNING", "cosbench isn't installed on "+client)
                installed = False

        return installed

    def stop_data_collectors(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).stop_data_collecters()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        nodes = []
        nodes.extend(self.rgw["rgw_server"])
        common.pdsh(user, nodes, "killall -9 top;echo `date +%s`' top stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 mpstat;echo `date +%s`' mpstat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar;echo `date +%s`' sar stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat;echo `date +%s`' iostat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_stop.txt; echo `date +%s`' interrupt stop' >> %s/`hostname`_process_log.txt;" % (dest_dir, '%s', dest_dir))

    def prepare_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prepare_run()
        self.stop_data_collectors()

        # scp cosbench config dir to remote
        user = self.cluster["user"]
        if not common.remote_file_exist( user, self.cosbench["cosbench_controller"], self.benchmark["configfile"] ):
            common.pdsh( user, self.cosbench["cosbench_controller"], "mkdir -p %s" % self.cosbench["cosbench_config_dir"])
            common.scp( user, self.cosbench["cosbench_controller"], self.benchmark["configfile"], self.benchmark["configfile"])
        self.cleanup()

    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).run()
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]
        monitor_interval = self.cluster["monitoring_interval"]

        #1. send command to radosgw
        nodes = []
        nodes.extend(self.rgw["rgw_server"])

        self.cosbench["run_name"] = {}
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt; echo `date +%s`' interrupt start' >> %s/`hostname`_process_log.txt;" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "top -c -b -d %s > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt;" % (monitor_interval,dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL %s > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt;"  % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm %s > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt;" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A %s > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt;" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "echo `date +%s`' perfcounter start' >> %s/`hostname`_process_log.txt; for i in `seq 1 %d`; do find /var/run/ceph -name '*osd*asok' | while read path; do filename=`echo $path | awk -F/ '{print $NF}'`;res_file=%s/`hostname`_${filename}.txt; echo `ceph --admin-daemon $path perf dump`, >> ${res_file} & done; sleep %s; done; echo `date +%s`' perfcounter stop' >> %s/`hostname`_process_log.txt;" % ('%s', dest_dir, waittime, dest_dir, monitor_interval, '%s', dest_dir), option="force")

        run_command ="http_proxy=%s sh %s/cli.sh submit %s " % (self.cosbench["proxy"], self.cosbench["cosbench_folder"], self.benchmark["configfile"])
        stdout, stderr = common.pdsh( user, [self.cosbench["cosbench_controller"]], run_command, option="check_return")
        m = re.search('Accepted with ID:\s*(\w+)', stdout)
        if not m:
            common.printout("ERROR",'Cosbench controller and driver run failed!',log_level="LVL1")
            raise KeyboardInterrupt

        common.printout("LOG", "Cosbench job start, in cosbench scope the job num will be %s" % m.group(1))
        common.printout("LOG", "You can monitor runtime status and results on http://%s:19088/controller" % self.cosbench["cosbench_controller_admin_url"])
        self.chkpoint_to_log("cosbench start")
        self.cosbench["cosbench_job_id"] = m.group(1)
        while self.check_cosbench_testjob_running( self.cosbench["cosbench_controller"], self.cosbench["cosbench_job_id"] ):
            time.sleep(5)

    def chkpoint_to_log(self, log_str):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).chkpoint_to_log(log_str)
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        nodes = []
        nodes.extend(self.rgw["rgw_server"])
        common.pdsh(user, nodes, "echo `date +%s`' %s' >> %s/`hostname`_process_log.txt" % ('%s', log_str, dest_dir))

    def check_cosbench_testjob_running(self, node, runid ):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        stdout, stderr = common.pdsh(user, [node], "http_proxy=%s sh %s/cli.sh info 2>/dev/null | grep PROCESSING | awk '{print $1}'" % (self.cosbench["proxy"], self.cosbench["cosbench_folder"]), option="check_return")
        res = common.format_pdsh_return(stdout)
        if node in res:
            if res[node].strip() == "%s" % runid:
                common.printout("LOG", "Cosbench test job w%s is still runing" % runid)
                return True
        return False

    def stop_workload(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        controller = self.cosbench["cosbench_controller"]
        common.pdsh( user, [controller], 'http_proxy=%s sh %s/cli.sh cancel %s' % (self.cosbench["proxy"], self.cosbench["cosbench_folder"], self.cosbench["cosbench_job_id"]), option="console")
        self.chkpoint_to_log("cosbench stop")

    def wait_workload_to_stop(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        common.printout("LOG","Waiting Workload to complete its work")
        max_check_times = 30
        cur_check = 0
        while self.check_cosbench_testjob_running(self.cosbench["cosbench_controller"], self.cosbench["cosbench_job_id"]):
            if cur_check > max_check_times:
                break
            time.sleep(10)
            cur_check += 1
        common.printout("LOG","Workload completed")

    def cleanup(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).cleanup()
        cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
        cosbench_server.append(self.cosbench["cosbench_controller"])
        ceph_nodes = copy.deepcopy(self.cluster["osd"])
        ceph_nodes.extend(self.rgw["rgw_server"])
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        common.pdsh(user, ceph_nodes, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))
        common.pdsh(user, cosbench_server, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))

    def testjob_distribution(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        pass

    def cal_run_job_distribution(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        self.benchmark["distribution"] = {}
        for driver in self.cosbench["cosbench_driver"]:
            self.benchmark["distribution"][driver] = driver

    def archive(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).archive()
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]

        ceph_nodes = []
        ceph_nodes.extend(self.rgw["rgw_server"])
        for node in ceph_nodes:
            common.bash("mkdir -p %s/raw/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])

        cosbench_controller = self.cosbench["cosbench_controller"]
        common.rscp(user, cosbench_controller, "%s/raw/%s/"%(dest_dir, cosbench_controller), "%s/archive/%s-*"%(self.cosbench["cosbench_folder"], self.cosbench["cosbench_job_id"]))

    def parse_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        p = testcase
        testcase_dict = {
            "worker":p[0], "container":p[1], "iopattern":p[2],
            "block_size":p[3], "objecter":p[4], "rampup":p[5],
            "runtime":p[6]
        }
        if len(p) == 9:
            testcase_dict["description"] = p[8]
        else:
            testcase_dict["description"] = ""
        return testcase_dict

    def generate_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        benchmark = {}
        benchmark["cosbench_config_dir"]=self.all_conf_data.get("cosbench_config_dir")
        benchmark["cosbench_controller"]=self.all_conf_data.get("cosbench_controller")
        benchmark["cosbench_driver"]=self.all_conf_data.get_list("cosbench_driver")
        benchmark["cosbench_controller_cluster_url"] =  self.all_conf_data.get("cosbench_cluster_ip")
        benchmark["auth_username"] = self.all_conf_data.get("cosbench_auth_username")
        benchmark["auth_password"] = self.all_conf_data.get("cosbench_auth_password")
        benchmark["auth_url"] = "http://%s/auth/v1.0;retry=9" % benchmark["cosbench_controller_cluster_url"]

        benchmark["worker"] = testcase["worker"]
        benchmark["container"] = testcase["container"]
        benchmark["iopattern"]= testcase["iopattern"]
        benchmark["size"] = testcase["block_size"]
        benchmark["objecter"] = testcase["objecter"]
        benchmark["rampup"] = testcase["rampup"]
        benchmark["runtime"] = testcase["runtime"]

        testcase_string = "%8s\t%4s\t%16s\t%8s\t%8s\t%16s\t%8s\t%8s\tcosbench" % ("cosbench", benchmark["worker"], benchmark["container"], benchmark["iopattern"], benchmark["size"], benchmark["objecter"], benchmark["rampup"], benchmark["runtime"])
        benchmark["container"] = self.parse_conobj_script( benchmark["container"] )
        benchmark["objecter"] = self.parse_conobj_script( benchmark["objecter"] )

        if ":" in benchmark["iopattern"]:
            rw_type, rw_ratio = benchmark["iopattern"].split(':')
        else:
            rw_type = benchmark["iopattern"]
            rw_ratio = "100"
        benchmark["iopattern"] = {}
        benchmark["iopattern"]["type"] = rw_type
        benchmark["iopattern"]["ratio"] = rw_ratio

        m = re.search("(\d+)([a-zA-Z]+)", benchmark["size"])
        size_complete = benchmark["size"]
        benchmark["size"] = {}
        benchmark["size"]["complete"] = size_complete
        if m:
            benchmark["size"]["size_value"] = m.group(1)
            benchmark["size"]["size_unit"] = m.group(2)
        else:
            benchmark["size"]["size_value"] = "128"
            benchmark["size"]["size_unit"] = KB

        benchmark["section_name"] = "%s-cosbench-%s-%s-%scon-%sobj-%s-%s-cosbench" % (benchmark["worker"], benchmark["iopattern"]["type"], benchmark["size"]["complete"], benchmark["container"]["max"], benchmark["objecter"]["max"], benchmark["rampup"], benchmark["runtime"])
        benchmark["configfile"] = "%s/%s.xml" % (benchmark["cosbench_config_dir"], benchmark["section_name"])

        # check if config dir and config file exists
        if not os.path.exists(benchmark["cosbench_config_dir"]):
            os.makedirs(benchmark["cosbench_config_dir"])
        if os.path.exists(benchmark["configfile"]):
            os.remove(benchmark["configfile"])
        self.replace_conf_xml(benchmark)
        return True

    def replace_conf_xml(self, benchmark):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        with open(lib_path+"/benchmarking/mod/bobject/.template_config.xml",'r') as infile:
            with open(benchmark["configfile"],'w+') as outfile:
                line = infile.read()

                # Using worker to identify if it is prepare stage
                # for workers more than 0
                if benchmark["worker"] == "0":
                    match = re.compile("\{\{description\}\}")
                    line = match.sub("INIT-PREPARE",line)

                    match = re.compile("<workstage name=\"main\">\n.*\n.*\n.*\n</workstage>\n")
                    line = match.sub('',line)

                    worker_count = len(benchmark["cosbench_driver"]) * 40 * 2
                    match = re.compile("\{\{workers\}\}")
                    line = match.sub(str(worker_count),line)
                else:
                    match = re.compile("\{\{description\}\}")
                    line = match.sub( "%s-%s" % (benchmark["iopattern"]["type"], benchmark["iopattern"]["ratio"]),line)
                    match = re.compile("<workstage name=\"init\">\n.*\n</workstage>\n")
                    line = match.sub('',line)
                    match = re.compile("<workstage name=\"prepare\">\n.*\n</workstage>\n")
                    line = match.sub('',line)


                match = re.compile("\{\{section_name\}\}")
                line = match.sub(benchmark["section_name"],line)
                match = re.compile("\{\{auth_username\}\}")
                line = match.sub(benchmark["auth_username"],line)
                match = re.compile("\{\{auth_passwd\}\}")
                line = match.sub(benchmark["auth_password"],line)
                match = re.compile("\{\{cluster_ip\}\}")
                line = match.sub(benchmark["cosbench_controller_cluster_url"],line)
                match = re.compile("\{\{size\}\}")
                line = match.sub(benchmark["size"]["complete"],line)
                match = re.compile("\{\{workers\}\}")
                line = match.sub(benchmark["worker"],line)
                match = re.compile("\{\{rampup\}\}")
                line = match.sub(benchmark["rampup"],line)
                match = re.compile("\{\{runtime\}\}")
                line = match.sub(benchmark["runtime"],line)
                match = re.compile("\{\{rw\}\}")
                line = match.sub(benchmark["iopattern"]["type"],line)
                match = re.compile("\{\{rw_ratio\}\}")
                line = match.sub(benchmark["iopattern"]["ratio"],line)
                match = re.compile("\{\{containers\}\}")
                line = match.sub(benchmark["container"]["complete"],line)
                match = re.compile("\{\{objects\}\}")
                line = match.sub(benchmark["objecter"]["complete"],line)
                match = re.compile("\{\{size_value\}\}")
                line = match.sub(benchmark["size"]["size_value"],line)
                match = re.compile("\{\{size_unit\}\}")
                line = match.sub(benchmark["size"]["size_unit"],line)

                outfile.write(line)
