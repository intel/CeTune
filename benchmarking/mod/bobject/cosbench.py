import os
import os.path
import time
lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
this_file_path = os.path.dirname(os.path.abspath(__file__))
from benchmarking.mod.benchmark import *
from conf import common
import itertools
from collections import OrderedDict

class Cosbench(Benchmark):
    def load_parameter(self):
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
        self.cosbench["cosbench_controller"]=self.all_conf_data.get("cosbench_controller")
        self.cosbench["data_dir"]=self.all_conf_data.get("dest_dir")
        self.cosbench["auth_username"] = self.all_conf_data.get("cosbench_auth_username")
        self.cosbench["auth_password"] = self.all_conf_data.get("cosbench_auth_password")
        self.cosbench["auth_url"] = "http://%s/auth/v1.0;retry=9" % self.cosbench["cosbench_controller_cluster_url"]
        self.cosbench["proxy"] = self.all_conf_data.get("cosbench_controller_proxy")
        self.cluster["testjob_distribution"] = copy.deepcopy(self.cosbench["cosbench_driver"])

    def parse_conobj_script(self, string):
        m = re.findall("(\w{1})\((\d+),(\d+)\)", string)
        result = {}
        if m:
            result["method"] = m[0][0]
            result["min"] = m[0][1]
            result["max"] = m[0][2]
            result["complete"] = string
        return result

    def prepare_result_dir(self):
        self.benchmark["container"] = self.parse_conobj_script( self.benchmark["container"] )
        self.benchmark["objecter"] = self.parse_conobj_script( self.benchmark["objecter"] )

        self.benchmark["section_name"] = "cosbench-%s-%scon-%sobj-%s-%sw" % (self.benchmark["iopattern"], self.benchmark["container"]["max"], self.benchmark["objecter"]["max"], self.benchmark["block_size"], self.benchmark["worker"])
        self.benchmark["dirname"] = "%s-%s" % ( str(self.runid), self.benchmark["section_name"])
        self.benchmark["configfile"] = "%s/%s.xml" % (self.cosbench["cosbench_config_dir"], self.benchmark["section_name"])
        self.cluster["dest_dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])

        if common.remote_dir_exist( self.cluster["user"], self.cluster["head"], self.cluster["dest_dir"] ):
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]))
            sys.exit()
        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))

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
        cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
        cosbench_server.extend(self.cosbench["cosbench_controller"])

        # check if cosbench installed
        if not self.check_cosbench_installed(cosbench_server):
            self.deploy_cosbench()

        # check if cosbench is running
        if not self.check_cosbench_runing(cosbench_server):
            sys.exit()

    def check_cosbench_runing(self, cosbench_server):
        user = self.cluster["user"]
        stdout, stderr = common.pdsh( user, [self.cosbench["cosbench_controller"]], "http_proxy=%s;curl -D - -H 'X-Auth-User: %s' -H 'X-Auth-Key: %s' %s" % (self.cosbench["proxy"], self.cosbench["auth_username"], self.cosbench["auth_password"], self.cosbench["auth_url"]), option = "check_return")
        if re.search('(refused|error)', stderr):
            common.printout("ERROR","Cosbench connect to Radosgw Connection Failed")
            return False
        if re.search("AccessDenied", stdout):
            common.printout("[ERROR]","Cosbench connect to Radosgw Auth Failed")
            return False
        return True

    def check_cosbench_installed(self, cosbench_server):
        user = self.cluster["user"]
        # check if cosbench installed
        installed = True
        for client in cosbench_server:
            if common.remote_file_exist(user, client, self.cosbench["cosbench_folder"]+'/cli.sh') is False:
                common.printout("ERROR", "cosbench isn't installed on "+client)
                installed = False

        return installed

    def stop_data_collectors(self):
        user = self.cluster["user"]
        nodes = []
        nodes.append(self.rgw["rgw_server"])
        common.pdsh(user, nodes, "killall -9 top", option = "check_return")
        common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar", option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat", option = "check_return")

    def prepare_run(self):
        super(self.__class__, self).prepare_run()
        self.stop_data_collectors()

        # scp cosbench config dir to remote
        user = self.cluster["user"]
        if not common.remote_file_exist( user, self.cosbench["cosbench_controller"], self.benchmark["configfile"] ):
            common.pdsh( user, self.cosbench["cosbench_controller"], "mkdir -p %s" % self.cosbench["cosbench_config_dir"])
            common.scp( user, self.cosbench["cosbench_controller"], self.benchmark["configfile"], self.benchmark["configfile"])

    def run(self):
        super(self.__class__, self).run()
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]

        #1. send command to radosgw
        nodes = []
        nodes.extend(self.rgw["rgw_server"])

        self.cosbench["run_name"] = {}
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt" % (dest_dir))
        common.pdsh(user, nodes, "top -c -b -d 1 -n %d > %s/`hostname`_top.txt &" % (waittime, dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 %d > %s/`hostname`_mpstat.txt &"  % (waittime, dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 %d > %s/`hostname`_iostat.txt &" % (waittime, dest_dir))
        common.pdsh(user, nodes, "sar -A 1 %d > %s/`hostname`_sar.txt &" % (waittime, dest_dir))
        common.pdsh(user, nodes, "for waittime in `seq 1 %d`; do find /var/run/ceph -name '*osd*asok' | while read path; do filename=`echo $path | awk -F/ '{print $NF}'`;res_file=%s/`hostname`_${filename}.txt; ceph --admin-daemon $path perf dump >> ${res_file}; echo ',' >> ${res_file}; done; sleep 1; done" % (waittime, dest_dir), option="force")

        run_command ="http_proxy=%s; sh %s/cli.sh submit %s " % (self.cosbench["proxy"], self.cosbench["cosbench_folder"], self.benchmark["configfile"])
        stdout, stderr = common.pdsh( user, [self.cosbench["cosbench_controller"]], run_command, option="check_return")
        m = re.search('Accepted with ID:\s*(\w+)', stdout)
        if not m:
            common.printout("ERROR",'Cosbench controller and driver run failed!')
            raise KeyboardInterrupt

        common.printout("LOG", "Cosbench job start, in cosbench scope the job num will be %s" % m.group(1))
        common.printout("LOG", "You can monitor runtime status and results on http://%s:19088/controller" % self.cosbench["cosbench_controller_admin_url"])
        self.cosbench["cosbench_job_id"] = m.group(1)
        while self.check_cosbench_testjob_running( self.cosbench["cosbench_controller"], self.cosbench["cosbench_job_id"] ):
            time.sleep(5)

    def check_cosbench_testjob_running(self, node, runid ):
        user = self.cluster["user"]
        stdout, stderr = common.pdsh(user, [node], "http_proxy=%s; sh %s/cli.sh info 2>/dev/null | grep PROCESSING | awk '{print $1}'" % (self.cosbench["proxy"], self.cosbench["cosbench_folder"]), option="check_return")
        res = common.format_pdsh_return(stdout)
        if node in res:
            if res[node].strip() == "%s" % runid:
                common.printout("LOG", "Cosbench test job w%s is still runing" % runid)
                return True
        return False

    def stop_workload(self):
        user = self.cluster["user"]
        controller = self.cosbench["cosbench_controller"]
        common.pdsh( user, [controller], 'http_proxy=%s; sh %s/cli.sh cancel %s' % (self.cosbench["proxy"], self.cosbench["cosbench_folder"], self.cosbench["cosbench_job_id"]), option="console")

    def wait_workload_to_stop(self):
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
        cosbench_server = copy.deepcopy(self.cosbench["cosbench_driver"])
        cosbench_server.append(self.cosbench["cosbench_controller"])
        ceph_nodes = copy.deepcopy(self.cluster["osd"])
        ceph_nodes.append(self.rgw["rgw_server"])
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        common.pdsh(user, ceph_nodes, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))
        common.pdsh(user, cosbench_server, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))

    def testjob_distribution(self):
        pass

    def cal_run_job_distribution(self):
        self.benchmark["distribution"] = {}
        for driver in self.cosbench["cosbench_driver"]:
            self.benchmark["distribution"][driver] = driver

    def archive(self):
        super(self.__class__, self).archive()
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]

        ceph_nodes = []
        ceph_nodes.extend(self.rgw["rgw_server"])
        for node in ceph_nodes:
            common.pdsh(user, [head], "mkdir -p %s/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])

        cosbench_controller = self.cosbench["cosbench_controller"]
        common.rscp(user, cosbench_controller, "%s/%s/"%(dest_dir, cosbench_controller), "%s/archive/%s-*"%(self.cosbench["cosbench_folder"], self.cosbench["cosbench_job_id"]))

    def parse_benchmark_cases(self, testcase):
        p = testcase
        testcase_dict = {
            "worker":p[0], "container":p[1], "iopattern":p[2],
            "block_size":p[3], "objecter":p[4], "rampup":p[5],
            "runtime":p[6]
        }
        if ":" in testcase_dict["iopattern"]:
            rw_type, rw_ratio = testcase_dict["iopattern"].split(':')
        else:
            rw_type = testcase_dict["iopattern"]
            rw_ratio = 100
        testcase_dict["iopattern"] = rw_type
        testcase_dict["iopattern_ratio"] = rw_ratio
        return testcase_dict

    def generate_benchmark_cases(self):
        engine = self.all_conf_data.get_list('benchmark_engine')
        if "cosbench" not in engine:
            return [[],[]]
        test_config = OrderedDict()
        benchmark = {}
        benchmark["cosbench_config_dir"]=self.all_conf_data.get("cosbench_config_dir")
        benchmark["cosbench_controller"]=self.all_conf_data.get("cosbench_controller")
        benchmark["cosbench_controller_cluster_url"] =  self.all_conf_data.get("cosbench_cluster_ip")
        benchmark["auth_username"] = self.all_conf_data.get("cosbench_auth_username")
        benchmark["auth_password"] = self.all_conf_data.get("cosbench_auth_password")
        benchmark["auth_url"] = "http://%s/auth/v1.0;retry=9" % benchmark["cosbench_controller_cluster_url"]
        test_config["workers"] = self.all_conf_data.get_list("cosbench_workers")
        test_config["contaiter"] = ["".join(self.all_conf_data.get("cosbench_containers"))]
        test_config["cosbench_rw"]=self.all_conf_data.get_list("cosbench_rw")
        test_config["test_size"]=self.all_conf_data.get_list("cosbench_test_size")
        test_config["objecter"] = ["".join(self.all_conf_data.get("cosbench_objects"))]
        test_config["ramp_up"] = self.all_conf_data.get_list("run_warmup_time")
        test_config["run_time"] = self.all_conf_data.get_list("run_time")

        testcase_list = []
        for testcase in itertools.product(*(test_config.values())):
            benchmark["worker"], benchmark["container"], benchmark["iopattern"], benchmark["size"], benchmark["objecter"], benchmark["rampup"], benchmark["runtime"] = testcase
            testcase_string = "%8s\t%4s\t%16s\t%8s\t%8s\t%16s\t%8s\t%8s\tcosbench" % ("cosbench", benchmark["worker"], benchmark["container"], benchmark["iopattern"], benchmark["size"], benchmark["objecter"], benchmark["rampup"], benchmark["runtime"])
            testcase_list.append( testcase_string )
            benchmark["container"] = self.parse_conobj_script( benchmark["container"] )
            benchmark["objecter"] = self.parse_conobj_script( benchmark["objecter"] )
            if ":" in benchmark["iopattern"]:
                rw_type, rw_ratio = benchmark["iopattern"].split(':')
            else:
                rw_type = benchmark["iopattern"]
                rw_ratio = 100
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

            benchmark["section_name"] = "cosbench-%s-%scon-%sobj-%s-%sw" % (benchmark["iopattern"]["type"], benchmark["container"]["max"], benchmark["objecter"]["max"], benchmark["size"]["complete"], benchmark["worker"])
            benchmark["configfile"] = "%s/%s.xml" % (benchmark["cosbench_config_dir"], benchmark["section_name"])

            # check if config dir and config file exists
            if not os.path.exists(benchmark["cosbench_config_dir"]):
                os.makedirs(benchmark["cosbench_config_dir"])
            if os.path.exists(benchmark["configfile"]):
                os.remove(benchmark["configfile"])
            self.replace_conf_xml(benchmark)
        return [testcase_list,[]]

    def replace_conf_xml(self, benchmark):
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

                    match = re.compile("\{\{workers\}\}")
                    line = match.sub("100",line)
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
