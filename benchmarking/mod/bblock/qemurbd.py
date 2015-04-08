from ..benchmark import *

class QemuRbd(Benchmark):
    def __init__(self, testcase):
        super(self.__class__, self).__init__(testcase)
        self.cluster["vclient"] = self.all_conf_data.get("list_vclient")
        self.benchmark["vdisk"] = self.all_conf_data.get("run_file")

        rbd_num_per_client = self.cluster["rbd_num_per_client"]
        instance_list = self.cluster["vclient"]
        self.testjob_distribution(rbd_num_per_client, instance_list)

    def prepare_result_dir(self):
        #1. prepare result dir
        self.get_runid()
        vdisk = re.sub(r'/dev/',r'dev-',self.benchmark["vdisk"])
        self.benchmark["section_name"] = "%s-%s-qd%s-%s-%s-%s-%s" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"], vdisk)
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.benchmark["dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])
        if os.path.exists(self.benchmark["dir"]):
            print common.bcolors.FAIL + "[ERROR]Output DIR %s exists" % (self.benchmark["dir"]) + common.bcolors.ENDC
            sys.exit()
        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.benchmark["dir"]))

    def prerun_check(self):
        #1. check is vclient alive
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "fio -v")
            res = common.pdsh(user, nodes, "df %s" % vdisk)
            common.pdsh(user, nodes, "mpstat")
            
    def run(self):
        super(self.__class__, self).run() 
        user = self.cluster["user"]
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]

        #1. send command to vclient
        nodes = []
        for client in self.benchmark["distribution"]:
            nodes.extend(self.benchmark["distribution"][client])
        common.pdsh(user, nodes, "top -c -b -d 1 -n %d > %s/`hostname`_top.txt &" % (waittime, dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 %d > %s/`hostname`_mpstat.txt &" % (waittime, dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 %d > %s/`hostname`_iostat.txt &" % (waittime, dest_dir))
        common.pdsh(user, nodes, "sar -A 1 %d > %s/`hostname`_sar.txt &" % (waittime, dest_dir))

        for node in nodes:
            common.pdsh(user, [node], "fio --output %s/`hostname`_fio.txt --section %s %s/fio.conf > /dev/null" % (dest_dir, self.benchmark["section_name"], dest_dir), option = "force")

        time.sleep(1)
        res = common.pdsh(user, nodes, "pgrep fio", option = "check_return")
        if res and not len(res[0].split('\n')) >= 2*len(nodes):
            print common.bcolors.FAIL + "[ERROR]Failed to start FIO process" + common.bcolors.ENDC
            raise KeyboardInterrupt
            print common.bcolors.OKGREEN + "[LOG]FIO Jobs starts on %s" % str(nodes) + common.bcolors.ENDC
        time.sleep(waittime)
        
    def cleanup(self):
        super(self.__class__, self).cleanup()
        #1. clean the tmp res dir
        user = self.cluster["user"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "rm -f %s/*.txt" % self.cluster["tmp_dir"])
            common.pdsh(user, nodes, "rm -f %s/*.log" % self.cluster["tmp_dir"])

    def prepare_run(self):
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        for client in self.benchmark["distribution"]:
            for vclient in self.benchmark["distribution"][client]:
                common.scp(user, vclient, "../conf/fio.conf", self.cluster["tmp_dir"])
    
    def wait_workload_to_stop(self):
        print common.bcolors.OKGREEN + "[LOG]Waiting Workload to complete its work" + common.bcolors.ENDC
        user = self.cluster["user"]
        stop_flag = 0
        max_check_times = 30
        cur_check = 0
        while not stop_flag:
            stop_flag = 1
            for client in self.benchmark["distribution"]:
                nodes = self.benchmark["distribution"][client]
                res = common.pdsh(user, nodes, "pgrep fio", option = "check_return")
                if not res[1]:
                    stop_flag = 0
                    print common.bcolors.WARNING + "[WARNING]FIO stills run on %s" % str(res[0].split('\n')) + common.bcolors.ENDC
            if stop_flag or cur_check > max_check_times:
                break;
            cur_check += 1
            time.sleep(10)
        print common.bcolors.OKGREEN + "[LOG]Workload completed" + common.bcolors.ENDC

    def stop_data_collecters(self):
        super(self.__class__, self).stop_data_collecters()
        user = self.cluster["user"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "killall -9 sar", option = "check_return")
            common.pdsh(user, nodes, "killall -9 mpstat", option = "check_return")
            common.pdsh(user, nodes, "killall -9 iostat", option = "check_return")
            common.pdsh(user, nodes, "killall -9 top", option = "check_return")

    def stop_workload(self):
        user = self.cluster["user"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "killall -9 fio", option = "check_return")

    def archive(self):
        super(self.__class__, self).archive()
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.benchmark["dir"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            for node in nodes:
                common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir, node))
                common.rscp(user, node, "%s/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])
