from ..benchmark import *
from collections import OrderedDict
import itertools
import sys

class FioCephFS(Benchmark):
    def load_parameter(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).load_parameter()
	self.cluster["fiocephfs_dir"] = self.all_conf_data.get("fio_for_libcephfs_dir")

    def prepare_result_dir(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #1. prepare result dir
        self.get_runid()
        self.benchmark["section_name"] = "%s-%s-qd%s-%s-%s-%s-fiocephfs" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"])
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
	fio_dir = self.cluster["fiocephfs_dir"]
        common.pdsh(user, nodes, "%s/fio -v" % fio_dir )
        res = common.pdsh(user, nodes, "%s/fio -enghelp | grep cephfs" % fio_dir, option = "check_return")
        if res and not res[0]:
            common.printout("ERROR","FIO cephfs engine not installed",log_level="LVL1")
	    print "You can get the source code of fiocephfs from: https://github.com/noahdesu/fio.git"
            sys.exit()
     
    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).run() 
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]
	fio_dir = self.cluster["fiocephfs_dir"]

        nodes = self.benchmark["distribution"].keys()
        for client in self.benchmark["distribution"]:
	    max_instance_num = self.benchmark["distribution"][client][-1]
            res = common.pdsh(user, [client], "for job_num in `seq 0 %d`; do %s/fio --output %s/`hostname`_${job_num}_fio.txt --write_bw_log=%s/`hostname`_${job_num}_fio --write_lat_log=%s/`hostname`_${job_num}_fio --write_iops_log=%s/`hostname`_${job_num}_fio --section %s --filename=`hostname`.${job_num} %s/fio.conf 2>%s/`hostname`_${job_num}_fio_errorlog.txt & done" % (max_instance_num, fio_dir, dest_dir, dest_dir, dest_dir, dest_dir, self.benchmark["section_name"], dest_dir, dest_dir, ), option = "force")         
            time.sleep(1)
            res = common.pdsh(user, [client], "pgrep -x fio", option = "check_return")
            if res and not len(res[0].split('\n')) >= len(self.benchmark["distribution"][client]):
                common.printout("ERROR","Failed to start FIO process",log_level="LVL1")
                raise KeyboardInterrupt
            common.printout("LOG","%d FIO Jobs starts on %s" % (len(self.benchmark["distribution"][client]), client))
        time.sleep(waittime)
        
    def prepare_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        for client in self.benchmark["distribution"].keys():
            common.scp(user, client, "../conf/fio.conf", dest_dir)
    
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
    
    def testjob_distribution(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        pass

    def cal_run_job_distribution(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        number = int(self.benchmark["instance_number"])
        client_total = len(self.cluster["client"])
	instance_per_client = number/client_total + (number % client_total > 0 )
        self.benchmark["distribution"] = {}
	for client in self.cluster["client"]:
	    self.benchmark["distribution"][client] = range(instance_per_client)

    def generate_benchmark_cases(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        engine = self.all_conf_data.get_list('benchmark_engine')
        if "fiocephfs" not in engine:
            return [[],[]]
        test_config = OrderedDict()
        test_config["engine"] = ["fiocephfs"]
        test_config["vm_num"] = self.all_conf_data.get_list('run_vm_num')
        test_config["rbd_volume_size"] = self.all_conf_data.get_list('run_size')
        test_config["io_pattern"] = self.all_conf_data.get_list('run_io_pattern')
        test_config["record_size"] = self.all_conf_data.get_list('run_record_size')
        test_config["queue_depth"] = self.all_conf_data.get_list('run_queue_depth')
        test_config["warmup_time"] = self.all_conf_data.get_list('run_warmup_time')
        test_config["runtime"] = self.all_conf_data.get_list('run_time')
        test_config["disk"] = ["fiocephfs"]
        testcase_list = []
        for testcase in itertools.product(*(test_config.values())):
            testcase_list.append('%8s\t%4s\t%16s\t%8s\t%8s\t%16s\t%8s\t%8s\t%8s' % ( testcase ))

        fio_list = []
        fio_list.append("[global]")
        fio_list.append("    direct=1")
        fio_list.append("    time_based")
        for element in itertools.product(test_config["engine"], test_config["io_pattern"], test_config["record_size"], test_config["queue_depth"], test_config["rbd_volume_size"], test_config["warmup_time"], test_config["runtime"], test_config["disk"]):
            engine, io_pattern, record_size, queue_depth, rbd_volume_size, warmup_time, runtime, disk = element
            fio_template = []
            fio_template.append("[%s-%s-%s-%s-%s-%s-%s-%s]" % (engine, io_pattern, record_size, queue_depth, rbd_volume_size, warmup_time, runtime, disk))
            fio_template.append("    rw=%s" % io_pattern)
            fio_template.append("    bs=%s" % record_size)
            fio_template.append("    iodepth=%s" % queue_depth)
            fio_template.append("    ramp_time=%s" % warmup_time)
            fio_template.append("    runtime=%s" % runtime)
            fio_template.append("    size=%s" % record_size)
            fio_template.append("    ioengine=cephfs")
            fio_template.append("    thread")
            if io_pattern in ["randread", "randwrite", "randrw"]:
                fio_template.append("    iodepth_batch_submit=1")
                fio_template.append("    iodepth_batch_complete=1")
                fio_template.append("    rate_iops=100")
            if io_pattern in ["seqread", "seqwrite", "readwrite", "rw"]:
                fio_template.append("    iodepth_batch_submit=8")
                fio_template.append("    iodepth_batch_complete=8")
                fio_template.append("    rate=60")
            if io_pattern in ["randrw", "readwrite", "rw"]:
                try:
                    rwmixread = self.all_conf_data.get('rwmixread')
                    fio_template.append("    rwmixread=%s" % rwmixread)
                except Exception,e:
                    common.printout("LOG","<CLASS_NAME:%s> <FUN_NAME : %s> ERR_MSG:%s"%(self.__class__.__name__,sys._getframe().f_code.co_name,e),log_level="LVL2")
                    pass
            fio_list.extend(fio_template)
        return [testcase_list, fio_list]

    def parse_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        p = testcase
        testcase_dict = {
            "instance_number":p[0], "volume_size":p[1], "iopattern":p[2],
            "block_size":p[3], "qd":p[4], "rampup":p[5], 
            "runtime":p[6], "vdisk":p[7]}
