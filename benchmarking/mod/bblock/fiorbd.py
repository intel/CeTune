from ..benchmark import *

class FioRbd(Benchmark):
    def __init__(self, testcase):
        super(self.__class__, self).__init__(testcase)
        self.cluster["rbdlist"] = self.get_rbd_list()

        rbd_num_per_client = self.cluster["rbd_num_per_client"]
        instance_list = self.cluster["rbdlist"]
        self.testjob_distribution(rbd_num_per_client, instance_list)

    def prepare_result_dir(self):
        #1. prepare result dir
        self.get_runid()
        self.benchmark["section_name"] = "%s-%s-qd%s-%s-%s-%s-fiorbd" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"])
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.benchmark["dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])
        if os.path.exists(self.benchmark["dir"]):
            print common.bcolors.FAIL + "[ERROR]Output DIR %s exists" % (self.benchmark["dir"]) + common.bcolors.ENDC
            sys.exit()
        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.benchmark["dir"]))

    def get_rbd_list(self):
        res = common.bash("rbd ls", True)
        if res[1]:
            print common.bcolors.FAIL + "[ERROR]unable get rbd list, return msg: %s" % res[1] + common.bcolors.ENDC
            sys.exit()
        rbd_list_tmp = res[0].split()
        return rbd_list_tmp

    def prerun_check(self):
        #1. check is vclient alive
        user = self.cluster["user"]
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "fio -v")
        res = common.pdsh(user, nodes, "fio -enghelp | grep rbd", option = "check_return")
        if res and not res[0]:
            print common.bcolors.FAIL + "[ERROR]FIO rbd engine not installed" + common.bcolors.ENDC
            sys.exit()
     
    def run(self):
        super(self.__class__, self).run() 
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]

        nodes = self.benchmark["distribution"].keys()
        for client in self.benchmark["distribution"]:
            rbdlist = ' '.join(self.benchmark["distribution"][client])
            res = common.pdsh(user, [client], "for rbdname in %s; do POOLNAME=%s RBDNAME=${rbdname} fio --output %s/`hostname`_${rbdname}_fio.txt --write_bw_log=%s/`hostname`_${rbdname}_fio --write_lat_log=%s/`hostname`_${rbdname}_fio --write_iops_log=%s/`hostname`_${rbdname}_fio --section %s %s/fio.conf 2>%s/`hostname`_${rbdname}_fio_errorlog.txt & done" % (rbdlist, 'rbd', dest_dir, dest_dir, dest_dir, dest_dir, self.benchmark["section_name"], dest_dir, dest_dir), option = "force")         
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
