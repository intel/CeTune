from ..benchmark import *

class FioRbd(Benchmark):
    def __init__(self, testcase):
        super(self.__class__, self).__init__(testcase)
        self.cluster["rbdlist"] = self.get_rbd_list()
        if self.cluster["rbdlist"] == []:
            self.prepare_images()

        rbd_num_per_client = self.cluster["rbd_num_per_client"]
        instance_list = self.cluster["rbdlist"]
        self.volume_size = self.all_conf_data.get("volume_size")
        self.testjob_distribution(rbd_num_per_client, instance_list)

    def prepare_images(self):
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        rbd_count = self.all_conf_data.get("rbd_volume_count")
        rbd_size = self.all_conf_data.get("volume_size")
        print common.bcolors.OKGREEN + "[LOG]Creating rbd volume" + common.bcolors.ENDC
        if rbd_count and rbd_size:
            super(self.__class__, self).create_image(rbd_count, rbd_size, 'rbd')
        else:
            print common.bcolors.FAIL + "[ERROR]need to set rbd_volume_count and volune_size in all.conf" + common.bcolors.ENDC
        #start to init 
        dest_dir = self.cluster["tmp_dir"]
        rbd_num_per_client = self.cluster["rbd_num_per_client"]
        self.cluster["rbdlist"] = self.get_rbd_list()
        instance_list = self.cluster["rbdlist"]
        self.testjob_distribution(rbd_num_per_client, instance_list)
        fio_job_num_total = 0
        clients = self.cluster["testjob_distribution"].keys()
        for client in self.cluster["testjob_distribution"]:
            common.scp(user, client, "../conf/fio_init.conf", dest_dir)
            rbdlist = ' '.join(self.cluster["testjob_distribution"][client])
            res = common.pdsh(user, [client], "for rbdname in %s; do POOLNAME=%s RBDNAME=${rbdname} fio --section init-write %s/fio_init.conf  & done" % (rbdlist, 'rbd', dest_dir), option = "force")         
            fio_job_num_total += len(self.cluster["testjob_distribution"][client])
        time.sleep(1)
        if not self.check_fio_pgrep(clients, fio_job_num_total):
            print common.bcolors.FAIL + "[ERROR]Failed to start FIO process" + common.bcolors.ENDC
            common.pdsh(user, clients, "killall -9 fio", option = "check_return")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            print common.bcolors.FAIL + "[ERROR]Planed to run 0 Fio Job, please check all.conf" + common.bcolors.ENDC
            raise KeyboardInterrupt
        print common.bcolors.OKGREEN + "[LOG]%d FIO Jobs starts on %s" % (len(self.cluster["testjob_distribution"][client]), client) + common.bcolors.ENDC

        print common.bcolors.OKGREEN + "[LOG]Wait rbd initialization stop" + common.bcolors.ENDC
        #wait fio finish
        try:
            while self.check_fio_pgrep(self.cluster["testjob_distribution"].keys()):
                time.sleep(5)
        except KeyboardInterrupt:
            clients = self.cluster["testjob_distribution"].keys()
            common.pdsh(user, clients, "killall -9 fio", option = "check_return")
        print common.bcolors.OKGREEN + "[LOG]rbd initialization finished" + common.bcolors.ENDC

    def prepare_result_dir(self):
        #1. prepare result dir
        self.get_runid()
        self.benchmark["section_name"] = "%s-%s-qd%s-%s-%s-%s-fiorbd" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"])
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
        common.pdsh(user, nodes, "fio -v")
        print common.bcolors.OKGREEN + "[LOG]check if FIO rbd engine installed" + common.bcolors.ENDC
        res = common.pdsh(user, nodes, "fio -enghelp | grep rbd", option = "check_return")
        if res and not res[0]:
            print common.bcolors.FAIL + "[ERROR]FIO rbd engine not installed" + common.bcolors.ENDC
            sys.exit()
        planed_space = str(len(self.cluster["rbdlist"]) * int(self.volume_size)) + "MB"
        print common.bcolors.OKGREEN + "[LOG]check if rbd volume fully initialized" + common.bcolors.ENDC
        if not self.check_rbd_init_completed(planed_space):
            print common.bcolors.WARNING + "[WARN]rbd volume initialization has not be done" + common.bcolors.ENDC
            self.prepare_images()
     
    def run(self):
        super(self.__class__, self).run() 
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]

        nodes = self.benchmark["distribution"].keys()
        fio_job_num_total = 0
        for client in self.benchmark["distribution"]:
            rbdlist = ' '.join(self.benchmark["distribution"][client])
            res = common.pdsh(user, [client], "for rbdname in %s; do POOLNAME=%s RBDNAME=${rbdname} fio --output %s/`hostname`_${rbdname}_fio.txt --write_bw_log=%s/`hostname`_${rbdname}_fio --write_lat_log=%s/`hostname`_${rbdname}_fio --write_iops_log=%s/`hostname`_${rbdname}_fio --section %s %s/fio.conf 2>%s/`hostname`_${rbdname}_fio_errorlog.txt & done" % (rbdlist, 'rbd', dest_dir, dest_dir, dest_dir, dest_dir, self.benchmark["section_name"], dest_dir, dest_dir), option = "force")         
            fio_job_num_total += len(self.benchmark["distribution"][client])
        time.sleep(1)
        if not self.check_fio_pgrep(self.benchmark["distribution"].keys(), fio_job_num_total):
            print common.bcolors.FAIL + "[ERROR]Failed to start FIO process" + common.bcolors.ENDC
            raise KeyboardInterrupt
        if not fio_job_num_total:
            print common.bcolors.FAIL + "[ERROR]Planned to start 0 FIO process, seems to be an error" + common.bcolors.ENDC
            raise KeyboardInterrupt
        print common.bcolors.OKGREEN + "[LOG]%d FIO Jobs starts on %s" % ( fio_job_num_total, str(self.benchmark["distribution"].keys())) + common.bcolors.ENDC

        while self.check_fio_pgrep(self.benchmark["distribution"].keys()):
            time.sleep(5)
        
    def prepare_run(self):
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        print common.bcolors.OKGREEN + "[LOG]Prepare_run: distribute fio.conf to all clients" + common.bcolors.ENDC
        for client in self.benchmark["distribution"].keys():
            common.scp(user, client, "../conf/fio.conf", dest_dir)
        self.cleanup()
    
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
