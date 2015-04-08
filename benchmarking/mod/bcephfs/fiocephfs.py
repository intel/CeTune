from ..benchmark import *

class FioCephFS(Benchmark):
    def __init__(self, testcase):
        super(self.__class__, self).__init__(testcase)
	self.cluster["fiocephfs_dir"] = self.all_conf_data.get("fio_for_libcephfs_dir")

    def prepare_result_dir(self):
        #1. prepare result dir
        self.get_runid()
        self.benchmark["section_name"] = "%s-%s-qd%s-%s-%s-%s-fiocephfs" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"])
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.benchmark["dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])
	
        res = common.pdsh(self.cluster["user"],["%s"%(self.cluster["head"])],"test -d %s" % (self.benchmark["dir"]), option = "check_return")
	if not res[1]:
            print common.bcolors.FAIL + "[ERROR]Output DIR %s exists" % (self.benchmark["dir"]) + common.bcolors.ENDC
            sys.exit()
        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.benchmark["dir"]))

    def prerun_check(self):
        #1. check is vclient alive
        user = self.cluster["user"]
        nodes = self.benchmark["distribution"].keys()
	fio_dir = self.cluster["fiocephfs_dir"]
        common.pdsh(user, nodes, "%s/fio -v" % fio_dir )
        res = common.pdsh(user, nodes, "%s/fio -enghelp | grep cephfs" % fio_dir, option = "check_return")
        if res and not res[0]:
            print common.bcolors.FAIL + "[ERROR]FIO cephfs engine not installed" + common.bcolors.ENDC
	    print "You can get the source code of fiocephfs from: https://github.com/noahdesu/fio.git"
            sys.exit()
     
    def run(self):
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
            res = common.pdsh(user, [client], "pgrep fio", option = "check_return")
            if res and not len(res[0].split('\n')) >= len(self.benchmark["distribution"][client]):
                print common.bcolors.FAIL + "[ERROR]Failed to start FIO process" + common.bcolors.ENDC
                raise KeyboardInterrupt
            print common.bcolors.OKGREEN + "[LOG]%d FIO Jobs starts on %s" % (len(self.benchmark["distribution"][client]), client) + common.bcolors.ENDC
        time.sleep(waittime)
        
    def prepare_run(self):
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        for client in self.benchmark["distribution"].keys():
            common.scp(user, client, "../conf/fio.conf", dest_dir)
    
    def wait_workload_to_stop(self):
        print common.bcolors.OKGREEN + "[LOG]Waiting Workload to complete its work" + common.bcolors.ENDC
        user = self.cluster["user"]
        stop_flag = 0
        max_check_times = 30
        cur_check = 0
        while not stop_flag:
            stop_flag = 1
            nodes = self.benchmark["distribution"].keys()
            res = common.pdsh(user, nodes, "pgrep fio", option = "check_return")
            if res and not res[1]:
                stop_flag = 0
                print common.bcolors.WARNING + "[WARNING]FIO stills run on %s" % str(res[0].split('\n')) + common.bcolors.ENDC
            if stop_flag or cur_check > max_check_times:
                break;
            cur_check += 1
            time.sleep(10)
        print common.bcolors.OKGREEN + "[LOG]Workload completed" + common.bcolors.ENDC

    def stop_workload(self):
        user = self.cluster["user"]
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
    
    def testjob_distribution(self):
        pass

    def cal_run_job_distribution(self):
        number = int(self.benchmark["instance_number"])
        client_total = len(self.cluster["client"])
	instance_per_client = number/client_total + (number % client_total > 0 )
        self.benchmark["distribution"] = {}
	for client in self.cluster["client"]:
	    self.benchmark["distribution"][client] = range(instance_per_client)
