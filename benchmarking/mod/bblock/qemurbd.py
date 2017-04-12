from ..benchmark import *
from collections import OrderedDict
import itertools
import sys

class QemuRbd(Benchmark):
    def load_parameter(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).load_parameter()
        self.cluster["vclient"] = self.all_conf_data.get_list("list_vclient")

        disk_num_per_client = self.cluster["disk_num_per_client"]
        self.volume_size = self.all_conf_data.get("volume_size")
        self.instance_list = self.cluster["vclient"]
        self.testjob_distribution(disk_num_per_client, self.instance_list)

    def prepare_result_dir(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #1. prepare result dir
        self.get_runid()
        vdisk = self.benchmark["vdisk"].split('/')[-1]
        self.benchmark["section_name"] = "qemurbd-%s-%s-qd%s-%s-%s-%s-%s" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"], vdisk)
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.cluster["dest_dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])

        if common.remote_dir_exist( self.cluster["user"], self.cluster["head"], self.cluster["dest_dir"] ):
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]),log_level="LVL1")
            sys.exit()

        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))

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
        fio_job_num_total = 0
        nodes = []
        for client in self.cluster["testjob_distribution"]:
            vclients = self.cluster["testjob_distribution"][client]
            for vclient in vclients:
                common.scp(user, vclient, "../conf/fio_init.conf", dest_dir)
                common.pdsh(user, [vclient], "fio --output %s/`hostname`_fio.txt --section init-write-vdb %s/fio_init.conf > /dev/null" % (dest_dir, dest_dir), option = "force")
            fio_job_num_total += len(self.cluster["testjob_distribution"][client])
            nodes.extend(vclients)
        time.sleep(1)
        if not self.check_fio_pgrep(nodes, fio_job_num_total, check_type = "nodenum"):
            common.printout("ERROR","Failed to start FIO process",log_level="LVL1")
            common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            common.printout("ERROR","Planed to run 0 Fio Job, please check all.conf",log_level="LVL1")
            raise KeyboardInterrupt
        common.printout("LOG","FIO Jobs starts on %s" % (nodes))

        common.printout("LOG","Wait rbd initialization stop")
        #wait fio finish
        try:
            while self.check_fio_pgrep(nodes):
                time.sleep(5)
        except KeyboardInterrupt:
            common.printout("WARNING","Caught KeyboardInterrupt, stop check fio pgrep.",log_level="LVL1")
            common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        common.printout("LOG","rbd initialization finished")

    def prerun_check(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prerun_check()
        #1. check is vclient alive
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        planed_space = str(len(self.instance_list) * int(self.volume_size)) + "MB"
        common.printout("LOG","Prerun_check: check if rbd volume be intialized")
        if not self.check_rbd_init_completed(planed_space):
            common.printout("WARNING","rbd volume initialization has not be done")
            self.prepare_images()

        nodes = []
        for client in self.benchmark["distribution"]:
            nodes.extend( self.benchmark["distribution"][client] )

        common.printout("LOG","Prerun_check: check if fio installed in vclient")
        common.pdsh(user, nodes, "fio -v")
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

    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).run()
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]
        monitor_interval = self.cluster["monitoring_interval"]

        #1. send command to vclient
        nodes = []
        for client in self.benchmark["distribution"]:
            nodes.extend(self.benchmark["distribution"][client])
        common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.printout("LOG","Start system data collector under %s " % nodes)
        common.pdsh(user, nodes, "top -c -b -d %s > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL %s > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt"  % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm %s > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A %s > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))

        fio_job_num_total = 0
        for node in nodes:
            common.pdsh(user, [node], "fio --output %s/`hostname`_fio.txt --section %s %s/fio.conf 2>%s/`hostname`_fio_errorlog.txt > /dev/null" % (dest_dir, self.benchmark["section_name"], dest_dir, dest_dir), option = "force")
            fio_job_num_total += 1

        self.chkpoint_to_log("fio start")
        time.sleep(5)
        if not self.check_fio_pgrep(nodes, fio_job_num_total, check_type = "nodenum"):
            common.printout("ERROR","Failed to start FIO process",log_level="LVL1")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            common.printout("ERROR","Planned to start 0 FIO process, seems to be an error",log_level="LVL1")
            raise KeyboardInterrupt

        common.printout("LOG","FIO Jobs starts on %s" % str(nodes))

        while self.check_fio_pgrep(nodes):
            time.sleep(5)

    def chkpoint_to_log(self, log_str):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).chkpoint_to_log(log_str)
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        nodes = []
        for client in self.benchmark["distribution"]:
            nodes.extend(self.benchmark["distribution"][client])
        common.pdsh(user, nodes, "echo `date +%s`' %s' >> %s/`hostname`_process_log.txt" % ('%s', log_str, dest_dir))

    def cleanup(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).cleanup()
        #1. clean the tmp res dir
        user = self.cluster["user"]
        nodes = []
        for client in self.benchmark["distribution"]:
            nodes.extend(self.benchmark["distribution"][client])
        common.pdsh(user, nodes, "rm -f %s/*.txt" % self.cluster["tmp_dir"])
        common.pdsh(user, nodes, "rm -f %s/*.log" % self.cluster["tmp_dir"])

    def prepare_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        common.printout("LOG","Prepare_run: distribute fio.conf to vclient")
        for client in self.benchmark["distribution"]:
            for vclient in self.benchmark["distribution"][client]:
                common.scp(user, vclient, "../conf/fio.conf", self.cluster["tmp_dir"])
        self.cleanup()
    
    def wait_workload_to_stop(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        common.printout("LOG","Waiting Workload to complete its work")
        nodes = []
        for client in self.benchmark["distribution"]:
            nodes.extend(self.benchmark["distribution"][client])
        max_check_times = 30
        cur_check = 0
        while self.check_fio_pgrep(nodes):
            if cur_check > max_check_times:
                break
            time.sleep(10)
            cur_check += 1
        common.printout("LOG","Workload completed")

    def stop_data_collecters(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).stop_data_collecters()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "killall -9 sar; echo `date +%s`' sar stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
            common.pdsh(user, nodes, "killall -9 mpstat; echo `date +%s`' mpstat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
            common.pdsh(user, nodes, "killall -9 iostat; echo `date +%s`' iostat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
            common.pdsh(user, nodes, "killall -9 top; echo `date +%s`' top stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")

    def stop_workload(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        common.printout("LOG","Workload stopped, detaching rbd volume from vclient")
        self.chkpoint_to_log("fio stop")
        try:
            self.detach_images()
        except KeyboardInterrupt:
            common.printout("WARNING","Caught KeyboardInterrupt, stop detaching",log_level="LVL1")

    def archive(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).archive()
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            for node in nodes:
                common.bash("mkdir -p %s/raw/%s" % (dest_dir, node))
                common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])
        common.cp("%s/conf/fio.conf" % self.pwd, "%s/conf/" % dest_dir )
        common.cp("/etc/ceph/ceph.conf", "%s/conf/" % dest_dir)
        common.bash("mkdir -p %s/conf/fio_errorlog/;find %s/raw/ -name '*_fio_errorlog.txt' | while read file; do cp $file %s/conf/fio_errorlog/;done" % (dest_dir, dest_dir, dest_dir))

    def generate_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        fio_capping = self.all_conf_data.get('fio_capping')
        enable_zipf = self.all_conf_data.get ('enable_zipf')
        fio_randrepeat = self.all_conf_data.get('fio_randrepeat')
        io_pattern = testcase["iopattern"]
        record_size = testcase["block_size"]
        queue_depth = testcase["qd"]
        rbd_volume_size = testcase["volume_size"]
        warmup_time = testcase["rampup"]
        runtime = testcase["runtime"]
        disk = testcase["vdisk"]
        description = testcase["description"]

        fio_list = []
        fio_list.append("[global]")
        fio_list.append("    direct=1")
        fio_list.append("    time_based")

        io_pattern_fio = io_pattern
        if io_pattern == "seqread":
            io_pattern_fio = "read"
        if io_pattern == "seqwrite":
            io_pattern_fio = "write"
        disk_name = disk.split('/')[-1]

        fio_template = []
        fio_template.append("[qemurbd-%s-%s-qd%s-%s-%s-%s-%s]" % (io_pattern, record_size, queue_depth, rbd_volume_size, warmup_time, runtime, disk_name))
        fio_template.append("    rw=%s" % io_pattern_fio)
        fio_template.append("    bs=%s" % record_size)
        fio_template.append("    iodepth=%s" % queue_depth)
        fio_template.append("    ramp_time=%s" % warmup_time)
        fio_template.append("    runtime=%s" % runtime)
        fio_template.append("    size=%s" % rbd_volume_size)
        fio_template.append("    filename=%s" % disk)
        fio_template.append("    ioengine=libaio")
        if io_pattern in ["randread", "randwrite", "randrw"]:
            fio_template.append("    iodepth_batch_submit=1")
            fio_template.append("    iodepth_batch_complete=1")
            fio_template.append("    norandommap")
            if fio_randrepeat == "false":
                fio_template.append("    randrepeat=0")
            if fio_capping != "false":
                fio_template.append("    rate_iops=100")
            if enable_zipf != "false":
                fio_zipf = self.all_conf_data.get('random_distribution')
                fio_template.append("    random_distribution=%s" % (fio_zipf))
        if io_pattern in ["seqread", "seqwrite", "readwrite", "rw"]:
            fio_template.append("    iodepth_batch_submit=8")
            fio_template.append("    iodepth_batch_complete=8")
            if fio_capping != "false":
                fio_template.append("    rate=60m")
        if io_pattern in ["randrw", "readwrite", "rw"]:
            if description != "":
                key_name = "%s|rwmixread" % description
            else:
                key_name = "rwmixread"
            try:
                rwmixread = self.all_conf_data.get(key_name)
                fio_template.append("    rwmixread=%s" % rwmixread)
            except Exception,e:
                common.printout("LOG","<CLASS_NAME:%s> <FUN_NAME : %s> ERR_MSG:%s"%(self.__class__.__name__,sys._getframe().f_code.co_name,e),log_level="LVL2")
                pass

        fio_list.extend(fio_template)
        with open("../conf/fio.conf", "w+") as f:
            f.write("\n".join(fio_list)+"\n")
        return True

    def parse_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        p = testcase
        testcase_dict = {
            "instance_number":p[0], "volume_size":p[1], "iopattern":p[2],
            "block_size":p[3], "qd":p[4], "rampup":p[5], 
            "runtime":p[6], "vdisk":p[7], "poolname":p[8]
        }
        if len(p) >= 10:
            testcase_dict["description"] = p[9]
        else:
            testcase_dict["description"] = ""

        return testcase_dict
