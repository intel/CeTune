from ..benchmark import * 
from collections import OrderedDict 
import itertools
import sys

class VdBench(Benchmark):
    def __init__(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        print "try try"
        self.bench_type = "vdbench"
        super(self.__class__, self).__init__()
        self.cluster["bench_dir"] = "%s/%s/" % (self.all_conf_data.get("tmp_dir"), self.bench_type)
        # Format default output dir: vdbench/output/
        self.cluster["format_output_dir"] = "%s/output/" % (self.cluster["bench_dir"])
        # Run results dir: vdbench/results/
        self.cluster["result_dir"] = "%s/results/" % (self.cluster["bench_dir"])
        common.printout("LOG","bench dir: %s, format output dir: %s, result dir: %s" % (self.cluster["bench_dir"], self.cluster["format_output_dir"], self.cluster["result_dir"]))

    def load_parameter(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).load_parameter()
        self.custom_script = self.all_conf_data.get("custom_script", True )
        self.cluster["vclient"] = self.all_conf_data.get_list("list_vclient")
        disk_num_per_client = self.cluster["disk_num_per_client"]
        self.disk_num_per_client = disk_num_per_client
        self.volume_size = self.all_conf_data.get("volume_size")
        self.instance_list = self.cluster["vclient"]
        self.testjob_distribution(disk_num_per_client, self.instance_list)

    def cal_run_job_distribution(self):
         common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
         number = int(self.benchmark["instance_number"])
         client_total = len(self.cluster["client"])
         # Assume number is always 50 here
         self.benchmark["distribution"] = {}
         client_num = 0
         for client in self.cluster["testjob_distribution"]:
             vclient_total = int(self.disk_num_per_client[client_num])
             self.benchmark["distribution"][client] = copy.deepcopy(self.cluster["testjob_distribution"][client][:vclient_total])
             client_num  += 1
         nodes = []
         for client in self.benchmark["distribution"]:
             nodes.extend(self.benchmark["distribution"][client])
         self.cluster["nodes_distribution"] = nodes

    def prepare_result_dir(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #1. prepare result dir
        self.get_runid()
        vdisk = self.benchmark["vdisk"].split('/')[-1]
        self.benchmark["section_name"] = "%s-%s-%s-qd%s-%s-%s-%s-%s" % (self.bench_type, self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"], vdisk)
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.cluster["dest_dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])

        res = common.pdsh(self.cluster["user"],["%s"%(self.cluster["head"])],"test -d %s" % (self.cluster["dest_dir"]), option = "check_return")
        if not res[1]:
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]),log_level="LVL1")
            sys.exit()

        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))

    def cleanup(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).cleanup()
        #1. clean the tmp res dir
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        common.pdsh(user, nodes, "rm -rf %s/*" % self.cluster["format_output_dir"])
        common.pdsh(user, nodes, "rm -rf %s/*" % self.cluster["result_dir"])

    def check_run_success(self, check_file, max_time, run_type="format"):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        cur_check = 0
        sleep_sec = 2
        max_check = max_time / sleep_sec
        while cur_check < max_check:
            common.printout("LOG", "checking... %s" % cur_check)
            stdout, stderr = common.pdsh(user, nodes, "grep completed %s" % check_file, option="check_return")
            res = common.format_pdsh_return(stdout)
            if len(nodes) != len(res.keys()):
                time.sleep(sleep_sec)
            else:
                common.printout("LOG", "checking done,all nodes execute %s completely" % run_type)
                return
            cur_check += 1
        common.printout("ERROR","Checking run in %s failed" % check_file,log_level="LVL1")
        stdout, stderr = common.pdsh(user, nodes, "grep -q completed %s; if [ $? -ne 0 ]; then echo Run is not completed successfully; fi" % check_file, option="check_return")
    	sys.exit()
    	
    def format_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        common.printout("LOG", "Start Formatting!")
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        common.pdsh(user, nodes, "cd %s; ./vdbench -f format.cfg -o %s" % (self.cluster["bench_dir"], self.cluster["format_output_dir"]))
        check_file = "%s/summary.html" % self.cluster["format_output_dir"]
        self.check_run_success(check_file, 100)
        
    def prepare_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        self.cleanup()
        # format
        self.format_run()
        
    #Add new method to check vdbench
    def check_vdbench_pgrep(self, nodes, vdbench_node_num = 1, check_type="jobnum"):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user =  self.cluster["user"]
        stdout, stderr = common.pdsh(user, nodes, "pgrep -x java", option = "check_return")
        res = common.format_pdsh_return(stdout)
        if res:
            vdbench_running_job_num = 0
            vdbench_running_node_num = 0
            for node in res:
                vdbench_running_node_num += 1
                vdbench_running_job_num += len(str(res[node]).strip().split('\n'))
            if (check_type == "jobnum" and vdbench_running_job_num >= vdbench_node_num) or (check_type == "nodenum" and vdbench_running_node_num >= vdbench_node_num):
                common.printout("WARNING","%d vdbench job still runing" % vdbench_running_job_num)
                return True
            else:
                if check_type == "nodenum":
                    common.printout("WARNING","Expecting %d nodes run vdbench, detect %d node runing" % (vdbench_node_num, vdbench_running_node_num))
                if check_type == "jobnum":
                    common.printout("WARNING","Expecting %d nodes run vdbench, detect %d node runing" % (vdbench_node_num, vdbench_running_job_num))
                return False
        common.printout("WARNING","Detect no vdbench job runing")
        return False
    
   #Updated wait_workload_to_stop and stop_workload
    def wait_workload_to_stop(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        common.printout("LOG","Waiting Workload to complete its work")
        nodes = self.cluster["nodes_distribution"]
        max_check_times = 30
        cur_check = 0
        while self.check_vdbench_pgrep(nodes):
            if cur_check > max_check_times:
                break
            time.sleep(10)
            cur_check += 1
        common.printout("LOG","Workload completed")
        
   #Add Stop_data_collecters
    def stop_data_collecters(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).stop_data_collecters()
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        common.pdsh(user, nodes, "killall -9 sar", option = "check_return")
        common.pdsh(user, nodes, "killall -9 mpstat", option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat", option = "check_return")
        common.pdsh(user, nodes, "killall -9 top", option = "check_return")
    
    def chkpoint_to_log(self, log_str):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).chkpoint_to_log(log_str)
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        common.pdsh(user, nodes, "echo `date +%s`' %s' >> %s/`hostname`_process_log.txt" % ('%s', log_str, dest_dir))
	 
    def stop_workload(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        common.pdsh(user, nodes, "killall -9 java", option = "check_return")
        common.printout("LOG","Workload stopped, detaching rbd volume from vclient")
        self.chkpoint_to_log("vdbench stop")
        try:
            self.detach_images()
        except KeyboardInterrupt:
            common.printout("WARNING","Caught KeyboardInterrupt, stop detaching",log_level="LVL1")
            
    #end
    def generate_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        io_pattern = testcase["iopattern"]
        block_size = testcase["block_size"]
        queue_depth = testcase["qd"]
        rbd_volume_size = testcase["volume_size"]
        warmup_time = testcase["rampup"]
        runtime = int(testcase["runtime"])
        disk = testcase["vdisk"]
        custom_params = testcase["custom_parameters"]
        for str in custom_params.split(','):
            str2 = str.split('=')
            if len(str2) != 2:
                continue
            if str2[0] == "width":
                width = int(str2[1]);
            elif str2[0] == "depth":
                depth = int(str2[1]);
            elif str2[0] == "files":
                files_num = int(str2[1]);
            elif str2[0] == "threads":
                threads_num = int(str2[1]);
            elif str2[0] == "rdpct":
                read_percentage = int(str2[1]);

        if int(re.findall(r"\d", block_size)[0]) * depth * width > int(re.findall(r"\d", rbd_volume_size)[0]) * 1024 * 1024:
            common.printout("ERROR","Files total size is too big, bigger than volume size!",log_level="LVL1")
            raise KeyboardInterrupt

        if io_pattern in ["randread", "randwrite", "randrw"]:
            fileio = "random"
        if io_pattern in ["seqread", "seqwrite", "readwrite", "rw"]:
            fileio = "sequential"
        if io_pattern == "randread":
            read_percentage = 100
        if io_pattern == "randwrite":
            read_percentage = 0

        format_cfg = []
        format_cfg.append("fsd=fsd1,anchor=/mnt/,depth=%d,width=%d,files=%d,size=%s" % (depth, width, files_num, block_size))
        format_cfg.append("fwd=default")
        format_cfg.append("fwd=fwd1,fsd=fsd1")
        format_cfg.append("rd=rd0,fwd=fwd1,fwdrate=max,format=only")
        with open("../conf/format.cfg", "w+") as f:
            f.write("\n".join(format_cfg)+"\n")

        case_cfg = []
        case_cfg.append("fsd=fsd1,anchor=/mnt/,depth=%d,width=%d,files=%d,size=%s" % (depth, width, files_num, block_size))
        case_cfg.append("fwd=default,xfersize=4k,fileio=%s,fileselect=random,threads=%d" % (fileio, threads_num))
        case_cfg.append("fwd=fwd1,fsd=fsd1,rdpct=%d" % read_percentage)
        case_cfg.append("rd=rd1,fwd=fwd1,fwdrate=max,format=no,elapsed=%d,interval=1" % runtime)
        with open("../conf/vdbench_test.cfg", "w+") as f:
            f.write("\n".join(case_cfg)+"\n")

        params_list = []
        params_list.append("depth=%d,width=%d,files=%d,threads=%d,rdpct=%d" % (depth, width, files_num, threads_num, read_percentage))
        with open("../conf/vdbench_params.txt", "w+") as f:
            f.write("\n".join(params_list)+"\n")
        return True

    def parse_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        p = testcase
        testcase_dict = {
            "instance_number":p[0], "volume_size":p[1], "iopattern":p[2],
            "block_size":p[3], "qd":p[4], "rampup":p[5],
            "runtime":p[6], "vdisk":p[7], "custom_parameters":p[8]
        }
        if len(p) == 10:
            testcase_dict["description"] = p[9]
        elif len(p) > 10:
            common.printout("ERROR","Too much columns found for test case ",log_level="LVL1")
            sys.exit()
        else:
            testcase_dict["description"] = ""

        return testcase_dict

    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).run()
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        dest_dir = self.cluster["tmp_dir"]
        monitor_interval = self.cluster["monitoring_interval"]
        common.printout("LOG", "Start Running VdBench!")
	common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.printout("LOG","Start system data collector under %s " % nodes)
        common.pdsh(user, nodes, "top -c -b -d %s > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL %s > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt"  % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm %s > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A %s > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "cd %s; ./vdbench -f vdbench_test.cfg -o %s" % (self.cluster["bench_dir"], self.cluster["result_dir"]))
       
        self.chkpoint_to_log("vdbench start")       
        check_file = "%s/summary.html" % self.cluster["result_dir"]
        self.check_run_success(check_file, 100, "test")

    def archive(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).archive()
        user = self.cluster["user"]
        nodes = self.cluster["nodes_distribution"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]
        common.cp("%s/conf/vdbench_params.txt" % self.pwd, "%s/conf/" % dest_dir)
        #collect client data
        for node in nodes:
            common.bash("mkdir -p %s/raw/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*" % self.cluster["result_dir"])


    def prepare_images(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user =  self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        controller =  self.cluster["head"]
        rbd_count = len(self.instance_list)
        rbd_size = self.all_conf_data.get("volume_size")
        if rbd_count and rbd_size:
            super(self.__class__, self).create_image(rbd_count, rbd_size, 'rbd')
        else:
            common.printout("ERROR","need to set rbd_volume_count and volune_size in all.conf",log_level="LVL1")

        #create image xml
        common.printout("LOG","create rbd volume vm attach xml")
        common.scp(user, controller, "%s/vm-scripts" % (self.pwd), "/opt/");
        common.scp(user, controller, "%s/conf" % (self.pwd), "/opt/");
        common.pdsh(user, [controller], "cd /opt/vm-scripts; echo 3 | bash create-volume.sh create_disk_xml", "check_return")
        common.rscp(user, controller, "%s/vm-scripts/" % (self.pwd), "/opt/vm-scripts/vdbs/");
        common.printout("LOG","Distribute vdbs xml")
        for client in self.cluster["testjob_distribution"]:
            common.scp(user, client, "../vm-scripts/vdbs", dest_dir)

        #attach to vm
        self.attach_images(self.cluster["testjob_distribution"])

        #start to init
        common.printout("LOG","rbd initialization finished")

    def prepare_case(self, user, nodes):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        stdout, stderr = common.pdsh(user, nodes, "test -d %s" % self.cluster["bench_dir"], option="check_return")
        if stderr:
            common.printout("LOG","Distribute vdbench benchmark execution file")
            for node in nodes:
                common.scp(user, node, '../conf/%s.tar.gz' % self.bench_type, '%s' % self.cluster["tmp_dir"])
            common.pdsh(user, nodes, 'cd %s; tar xzf %s.tar.gz' % (self.cluster["tmp_dir"], self.bench_type))

        common.pdsh(user, nodes, "mkdir -p  %s" % self.cluster["result_dir"])
        for node in nodes:
            common.scp(user, node, "../conf/format.cfg", "%s" % self.cluster["bench_dir"])
            common.scp(user, node, "../conf/vdbench_test.cfg", "%s" % self.cluster["bench_dir"])

    def prerun_check(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prerun_check()
        #1. check is vclient alive
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        nodes = self.cluster["nodes_distribution"]
        planed_space = str(len(self.instance_list) * int(self.volume_size)) + "MB"
        common.printout("LOG","Prerun_check: check if rbd volume be intialized")
        if not self.check_rbd_init_completed(planed_space):
            common.printout("WARNING","rbd volume initialization has not be done")
            self.prepare_images()

        common.printout("LOG","Distribution nodes: %s" % nodes)
        self.prepare_case(user, nodes)

        common.printout("LOG","Prerun_check: check if rbd volume attached")
        need_to_attach = False
        stdout, stderr = common.pdsh(user, nodes, "fdisk -l %s" % vdisk, option="check_return")
        res = common.format_pdsh_return(stdout)
        if len(nodes) != len(res.keys()):
            need_to_attach = True
        if need_to_attach:
            common.printout("WARNING","vclients are not attached with rbd volume")
            self.attach_images()
            common.printout("WARNING","vclients attached rbd volume now")
        common.printout("LOG","Prerun_check: check if sysstat installed on %s" % nodes)
        common.pdsh(user, nodes, "mpstat")
        common.pdsh(user, nodes, "killall -9 java", option = "check_return")

    def attach_images(self, to_attach_dict = None):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        dest_dir = self.cluster["tmp_dir"]
        if not to_attach_dict:
            to_attach_dict = self.benchmark["distribution"]
        for client in to_attach_dict:
            nodes = to_attach_dict[client]
            for node in nodes:
                common.printout("LOG","Attach rbd image to %s" % node)
                stdout, stderr = common.pdsh(user, [node], "fdisk -l %s" % vdisk, option="check_return")
                res = common.format_pdsh_return(stdout)
                if node not in res:
                   common.pdsh(user, [client], "cd %s/vdbs; virsh attach-device %s %s.xml" % (dest_dir, node, node), except_returncode=1)
                   common.pdsh(user, [node], "mount | grep /dev/vdb1; if [ $? ne 0]; then parted -s -a optimal /dev/vdb mklabel gpt -- mkpart primary ext4 1 100%; mkfs -t ext4 /dev/vdb1; mount /dev/vdb1 /mnt; fi")

    def detach_images(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        tmp_vdisk = re.search('/dev/(\w+)',vdisk)
        vdisk_suffix = tmp_vdisk.group(1)
        #for client in self.cluster["testjob_distribution"]:
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            for node in nodes:
                common.printout("LOG","Detach rbd image from %s" % node)
                stdout, stderr = common.pdsh(user, [node], "df %s" % vdisk, option="check_return")
                if not stderr:
                   common.pdsh(user, [client], "virsh detach-disk %s %s" % (node, vdisk_suffix), except_returncode=1)

