import subprocess
import common
import copy
import os, sys
import time
import re

class Benchmark(object):
    def __init__(self, testcase):
        self.all_conf_data = common.Config("../conf/all.conf")
        self.benchmark = {}
        self.benchmark = copy.deepcopy(testcase)

        self.cluster = {}
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["tmp_dir"] = self.all_conf_data.get("tmp_dir")
        self.cluster["dest_dir"] = self.all_conf_data.get("dest_dir")
        self.cluster["client"] = self.all_conf_data.get_list("list_client")
        self.cluster["osd"] = self.all_conf_data.get_list("list_ceph")
        self.cluster["rbd_num_per_client"] = self.all_conf_data.get_list("rbd_num_per_client")

    def go(self):
        self.prepare_result_dir()
        print common.bcolors.OKGREEN + "RUNID: %d, RESULT_DIR: %s" % (self.runid, self.benchmark["dir"]) + common.bcolors.ENDC

        print common.bcolors.OKGREEN + "[LOG]Prepare Status: Do prerun_check and distribute config files" + common.bcolors.ENDC
        self.cal_run_job_distribution()
        self.prerun_check() 
        self.prepare_run()

        print common.bcolors.OKGREEN + "[LOG]Run Benchmark Status: collect system metrics and run benchmark" + common.bcolors.ENDC
        try:
            self.run()
        except KeyboardInterrupt:
            print common.bcolors.WARNING + "[WARNING]Caught Signal to Cancel this run, killing Workload now, pls wait" + common.bcolors.ENDC
            self.stop_workload()
            self.stop_data_collecters()

        print common.bcolors.OKGREEN + "[LOG]Collect Data Status" + common.bcolors.ENDC
        self.after_run()
        self.archive()
        self.set_runid()

        print common.bcolors.OKGREEN + "[LOG]Post Process Result Data" + common.bcolors.ENDC
        common.bash("cd ../post-processing; bash post_processing.sh %s" % self.benchmark["dir"])
        
    def after_run(self):
        #1. check workload stoped
        self.wait_workload_to_stop()

        #2. stop data collecters process and workload
        self.stop_workload()
        self.stop_data_collecters()
        
        #3. collect after run data
        user = self.cluster["user"]
        nodes = self.cluster["osd"]
        dest_dir = self.cluster["tmp_dir"]
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_end.txt" % (dest_dir))
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_end.txt" % (dest_dir))

    def prepare_run(self):
        self.stop_data_collecters()
        
    def prerun_check(self):
        pass

    def run(self):
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        print common.bcolors.OKGREEN + "[LOG]This test will run %d secs until finish." % waittime + common.bcolors.ENDC
        
        #drop page cache
        user = self.cluster["user"]
        time = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        dest_dir = self.cluster["tmp_dir"]
        nodes = self.cluster["osd"]
        common.pdsh(user, nodes, "echo '1' > /proc/sys/vm/drop_caches && sync")
        
        #send command to ceph cluster
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt" % (dest_dir))
        common.pdsh(user, nodes, "top -c -b -d 1 -n %d > %s/`hostname`_top.txt &" % (time, dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 %d > %s/`hostname`_mpstat.txt &"  % (time, dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 %d > %s/`hostname`_iostat.txt &" % (time, dest_dir))
        common.pdsh(user, nodes, "sar -A 1 %d > %s/`hostname`_sar.txt &" % (time, dest_dir))

        #2. send command to client
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt" % (dest_dir))
        common.pdsh(user, nodes, "top -c -b -d 1 -n %d > %s/`hostname`_top.txt &" % (time, dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 %d > %s/`hostname`_mpstat.txt &" % (time, dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 %d > %s/`hostname`_iostat.txt &" % (time, dest_dir))
        common.pdsh(user, nodes, "sar -A 1 %d > %s/`hostname`_sar.txt &" % (time, dest_dir))
        
    def archive(self):
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.benchmark["dir"]
        #collect all.conf
        
        common.rscp(user, head, "%s/" % (dest_dir), "%s/../conf/all.conf" % os.getcwd())
        #collect osd data
        for node in self.cluster["osd"]:
            common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])
        
        #collect client data
        for node in self.benchmark["distribution"].keys():
            common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])

    def stop_data_collecters(self):
        #2. clean running process
        user = self.cluster["user"]
        nodes = self.cluster["osd"]
        common.pdsh(user, nodes, "killall -9 top", option = "check_return")
        common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar", option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat", option = "check_return")

        #2. send command to client
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "killall -9 top", option = "check_return")
        common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar", option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat", option = "check_return")

    def tuning(self):
        pass

    def get_runid(self):
        self.runid = 0
        try:
            with open(".run_number", "r") as f:
                self.runid = int(f.read())
        except:
            pass

    def set_runid(self):
        if not self.runid:
           self.get_runid()
        self.runid = self.runid + 1
        with open(".run_number", "w") as f:
            f.write(str(self.runid))

    def testjob_distribution(self, rbd_num_per_client, instance_list):
        start_vclient_num = 0
        client_num = 0
        self.cluster["testjob_distribution"] = {}
        for client in self.cluster["client"]:
            vclient_total = int(rbd_num_per_client[client_num])
            end_vclient_num = start_vclient_num + vclient_total
            self.cluster["testjob_distribution"][client] = copy.deepcopy(instance_list[start_vclient_num:end_vclient_num])
            start_vclient_num = end_vclient_num
            client_num += 1 
        print self.cluster["testjob_distribution"]

    def cal_run_job_distribution(self):
         number = int(self.benchmark["instance_number"])
         client_total = len(self.cluster["client"])
         if (number % client_total) > 0:
              volume_max_per_client = number / client_total + 1
         else:
              volume_max_per_client = number / client_total
         
         self.benchmark["distribution"] = {}
	 remained_instance_num = number
         for client in self.cluster["testjob_distribution"]:
             if remained_instance_num < volume_max_per_client:
                 volume_num_upper_bound = remained_instance_num
             else:
                 volume_num_upper_bound = volume_max_per_client
             self.benchmark["distribution"][client] = copy.deepcopy(self.cluster["testjob_distribution"][client][:volume_num_upper_bound])
             remained_instance_num = remained_instance_num - volume_num_upper_bound
         print self.benchmark["distribution"] 
