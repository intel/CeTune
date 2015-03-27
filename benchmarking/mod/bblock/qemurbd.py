from ..benchmark import *

class QemuRbd(Benchmark):
    def __init__(self, testcase):
        super(self.__class__, self).__init__(testcase)
        self.cluster["vclient"] = self.all_conf_data.get("list_vclient")

        rbd_num_per_client = self.cluster["rbd_num_per_client"]
        instance_list = self.cluster["vclient"]
        self.testjob_distribution(rbd_num_per_client, instance_list)

    def prerun_check(self):
        #1. check is vclient alive
        user = self.cluster["user"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "fio -v")
            common.pdsh(user, nodes, "mpstat")
            
    def run(self):
        super(self.__class__, self).run() 
        user = self.cluster["user"]
        time = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]

        #1. send command to vclient
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "fio --output %s/`hostname`_fio.txt --section %s %s/fio.conf" % (dest_dir, self.benchmark["section_name"], dest_dir))
            common.pdsh(user, nodes, "top -c -b -d 1 -n %d > %s/`hostname`_top.txt" % (time, dest_dir))
            common.pdsh(user, nodes, "mpstat -P ALL 1 %d > %s/`hostname`_mpstat.txt" % (time, dest_dir))
            common.pdsh(user, nodes, "iostat -p -dxm 1 %d > %s/`hostname`_iostat.txt" % (time, dest_dir))
            common.pdsh(user, nodes, "sar -A 1 %d > %s/`hostname`_sar.txt" % (time, dest_dir))
        
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
        user = self.cluster["user"]
        stop_flag = 0
        max_check_times = 30
        cur_check = 0
        while not stop_flag:
            stop_flag = 1
            for client in self.benchmark["distribution"]:
                nodes = self.benchmark["distribution"][client]
                res = common.pdsh(user, nodes, "pgrep fio", True)
                if isinstance(res, list) and not res[1]:
                    stop_flag = 0
            if stop_flag:
                break;
            cur_check += 1
            time.sleep(10)

    def stop_data_collecters(self):
        super(self.__class__, self).stop_data_collecters()
        user = self.cluster["user"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "killall -9 sar", True)
            common.pdsh(user, nodes, "killall -9 mpstat", True)
            common.pdsh(user, nodes, "killall -9 iostat", True)
            common.pdsh(user, nodes, "killall -9 top", True)

    def stop_workload(self):
        user = self.cluster["user"]
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            common.pdsh(user, nodes, "killall -9 fio", True)

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
