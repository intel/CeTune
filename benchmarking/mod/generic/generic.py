from ..benchmark import *
from collections import OrderedDict
import itertools
import sys

class Generic(Benchmark):
    def load_parameter(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).load_parameter()
        self.cluster["test_disks"] = self.all_conf_data.get_list("test_disks")

        disk_num_per_client = self.cluster["disk_num_per_client"]
        instance_list = self.cluster["test_disks"]
        self.testjob_distribution(disk_num_per_client, instance_list)

    def prepare_images(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        fio_job_num_total = 0
        for client in self.cluster["testjob_distribution"]:
            common.scp(user, client, "../conf/fio_init.conf", dest_dir)
            test_disks_list = ' '.join(self.cluster["testjob_distribution"][client])
            res = common.pdsh(user, [client], "for disk in %s; do DEVICE=${disk} fio --section init-write-disk %s/fio_init.conf  & done" % (test_disks_list, dest_dir), option = "force")         
            fio_job_num_total += len(self.cluster["testjob_distribution"][client])
        time.sleep(1)
        if not self.check_fio_pgrep(clients, fio_job_num_total):
            common.printout("ERROR","Failed to start FIO process",log_level="LVL1")
            common.pdsh(user, clients, "killall -9 fio", option = "check_return")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            common.printout("ERROR","Planed to run 0 Fio Job, please check all.conf",log_level="LVL1")
            raise KeyboardInterrupt
        common.printout("LOG","%d FIO Jobs starts on %s" % (len(self.cluster["testjob_distribution"][client]), client))

        common.printout("LOG","Wait rbd initialization stop")
        #wait fio finish
        try:
            while self.check_fio_pgrep(self.cluster["testjob_distribution"].keys()):
                time.sleep(5)
        except KeyboardInterrupt:
            clients = self.cluster["testjob_distribution"].keys()
            common.pdsh(user, clients, "killall -9 fio", option = "check_return")
        common.printout("LOG","rbd initialization finished")

    def prepare_result_dir(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #1. prepare result dir
        self.get_runid()
        self.benchmark["section_name"] = "generic-%s-%s-qd%s-%s-%s-%s-generic" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"])
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.cluster["dest_dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])
	
        res = common.pdsh(self.cluster["user"],["%s"%(self.cluster["head"])],"test -d %s" % (self.cluster["dest_dir"]), option = "check_return")
	if not res[1]:
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]),log_level="LVL1")
            sys.exit()

        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))

    def prerun_check(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #1. check is vclient alive
        user = self.cluster["user"]
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "fio -v")
        common.printout("LOG","check if FIO rbd engine installed")
        res = common.pdsh(user, nodes, "fio -enghelp | grep libaio", option = "check_return")
        if res and not res[0]:
            common.printout("ERROR","FIO libaio engine not installed",log_level="LVL1")
            sys.exit()
     
    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]

        #drop page cache
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"]) + self.cluster["run_time_extend"]
        dest_dir = self.cluster["tmp_dir"]
        nodes = self.cluster["osd"]
        nodes.extend(self.benchmark["distribution"].keys())
        common.pdsh(user, nodes, "echo '1' > /proc/sys/vm/drop_caches && sync")

        #send command to ceph cluster
        common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt; echo `date +%s`' interrupt start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "top -c -b -d 1 > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt"  % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A 1 > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))

        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt; echo `date +%s`' interrupt start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "top -c -b -d 1 > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt"  % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A 1 > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))

        common.printout("LOG","This test will run %d secs until finish." % waittime)
        fio_job_num_total = 0
        for client in self.benchmark["distribution"]:
            rbdlist = ' '.join(self.benchmark["distribution"][client])
            res = common.pdsh(user, [client], "for disk in %s; do disk_name=`echo ${disk} | awk -F/ '{for(i=1;i<=NF;i++)if($i!=\"\"&&$i!=\"dev\")printf(\"%s\",$i)}'`;DEVICE=${disk} fio --output %s/`hostname`_${disk_name}_fio.txt --write_bw_log=%s/`hostname`_${disk_name}_fio --write_lat_log=%s/`hostname`_${disk_name}_fio --write_iops_log=%s/`hostname`_${disk_name}_fio --section %s %s/fio.conf 2>%s/`hostname`_${disk_name}_fio_errorlog.txt & done" % (rbdlist, '%s', dest_dir, dest_dir, dest_dir, dest_dir, self.benchmark["section_name"], dest_dir, dest_dir), option = "force")
            fio_job_num_total += len(self.benchmark["distribution"][client])
        self.chkpoint_to_log("fio start")
        time.sleep(1)
        if not self.check_fio_pgrep(self.benchmark["distribution"].keys(), fio_job_num_total):
            common.printout("ERROR","Failed to start FIO process",log_level="LVL1")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            common.printout("ERROR","Planned to start 0 FIO process, seems to be an error",log_level="LVL1")
            raise KeyboardInterrupt
        common.printout("LOG","%d FIO Jobs starts on %s" % ( fio_job_num_total, str(self.benchmark["distribution"].keys())))
        while self.check_fio_pgrep(self.benchmark["distribution"].keys()):
            time.sleep(5)

    def prepare_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        common.printout("LOG","Prepare_run: distribute fio.conf to all clients")
        for client in self.benchmark["distribution"].keys():
            common.scp(user, client, "../conf/fio.conf", dest_dir)
        self.cleanup()
    
    def wait_workload_to_stop(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        common.printout("LOG","Waiting Workload to complete its work")
        user = self.cluster["user"]
        stop_flag = 0
        max_check_times = 30
        cur_check = 0
        while not stop_flag:
            stop_flag = 1
            nodes = self.benchmark["distribution"].keys()
            res = common.pdsh(user, nodes, "pgrep -x fio", option = "check_return")
            if res and not res[1]:
                stop_flag = 0
                common.printout("WARNING","FIO stills run on %s" % str(res[0].split('\n')))
            if stop_flag or cur_check > max_check_times:
                break;
            cur_check += 1
            time.sleep(10)
        common.printout("LOG","Workload completed")

    def stop_workload(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        self.chkpoint_to_log("fio stop")

    def generate_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        fio_capping = self.all_conf_data.get('fio_capping')

        io_pattern = testcase["iopattern"]
        record_size = testcase["block_size"]
        queue_depth = testcase["qd"]
        rbd_volume_size = testcase["volume_size"]
        warmup_time = testcase["rampup"]
        runtime = testcase["runtime"]
        disk = testcase["vdisk"]

        fio_list = []
        fio_list.append("[global]")
        fio_list.append("    direct=1")
        fio_list.append("    time_based")

        io_pattern_fio = io_pattern
        if io_pattern == "seqread":
            io_pattern_fio = "read"
        if io_pattern == "seqwrite":
            io_pattern_fio = "write"

        fio_template = []
        fio_template.append("[%s-%s-%s-qd%s-%s-%s-%s-%s]" % ("generic", io_pattern, record_size, queue_depth, rbd_volume_size, warmup_time, runtime, disk))

        fio_template.append("    rw=%s" % io_pattern_fio)
        fio_template.append("    bs=%s" % record_size)
        fio_template.append("    iodepth=%s" % queue_depth)
        fio_template.append("    ramp_time=%s" % warmup_time)
        fio_template.append("    runtime=%s" % runtime)
        fio_template.append("    ioengine=libaio")
        fio_template.append("    filename=${DEVICE}")
        if io_pattern in ["randread", "randwrite", "randrw"]:
            fio_template.append("    iodepth_batch_submit=1")
            fio_template.append("    iodepth_batch_complete=1")
            if fio_capping != "false":
                fio_template.append("    rate_iops=100")
        if io_pattern in ["seqread", "seqwrite", "readwrite", "rw"]:
            fio_template.append("    iodepth_batch_submit=8")
            fio_template.append("    iodepth_batch_complete=8")
            if fio_capping != "false":
                fio_template.append("    rate=60m")
        if io_pattern in ["randrw", "readwrite", "rw"]:
            try:
                rwmixread = self.all_conf_data.get('rwmixread')
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
            "runtime":p[6], "vdisk":p[7]
        }
        if len(p) >= 10:
            testcase_dict["description"] = p[9]
        else:
            testcase_dict["description"] = ""
        return testcase_dict

    def archive(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).archive() 
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]
        #collect client data
        for node in self.benchmark["distribution"].keys():
            common.pdsh(user, [head], "mkdir -p %s/raw/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*.log" % self.cluster["tmp_dir"])
        common.rscp(user, head, "%s/conf/" % dest_dir, "%s/conf/fio.conf" % self.pwd)
        common.bash("mkdir -p %s/conf/fio_errorlog/;find %s/raw/ -name '*_fio_errorlog.txt' | while read file; do cp $file %s/conf/fio_errorlog/;done" % (dest_dir, dest_dir, dest_dir))
