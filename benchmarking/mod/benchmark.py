import subprocess
from conf import common
import copy
import os, sys
import time
import re
import uuid
from analyzer import *
lib_path = ( os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Benchmark(object):
    def __init__(self):
        self.all_conf_data = common.Config(lib_path+"/conf/all.conf")
        self.benchmark = {}
        self.cluster = {}
        self.pwd = os.path.abspath(os.path.join('..'))

    def go(self, testcase, tuning):
        self.load_parameter()
        self.get_runid()

        self.benchmark = self.parse_benchmark_cases(testcase)
        self.benchmark["tuning_section"] = tuning

        self.prepare_result_dir()
        common.printout("LOG","RUNID: %d, RESULT_DIR: %s" % (self.runid, self.cluster["dest_dir"]))
        self.cal_run_job_distribution()
        self.prerun_check()
        self.prepare_run()

        common.printout("LOG","Run Benchmark Status: collect system metrics and run benchmark")
        test_start_time = time.time()
        try:
            self.run()
        except KeyboardInterrupt:
            common.printout("WARNING","Caught Signal to Cancel this run, killing Workload now, pls wait")
            self.real_runtime = time.time() - test_start_time
            self.stop_workload()
            self.stop_data_collecters()

        self.real_runtime = time.time() - test_start_time
        common.printout("LOG","Collecting Data")
        self.after_run()
        self.archive()
        self.set_runid()

        common.printout("LOG","Post Process Result Data")
        try:
            analyzer.main(['--path', self.cluster["dest_dir"], 'process_data'])
        except:
            common.printout("ERROR","analyzer failed, pls try cd analyzer; python analyzer.py --path %s process_data " % self.cluster["dest_dir"])

    def create_image(self, volume_count, volume_size, poolname):
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        rbd_list = self.get_rbd_list()
        need_to_create = 0
        if not len(rbd_list) >= int(volume_count):
            need_to_create = int(volume_count) - len(rbd_list)
        if need_to_create != 0:
            for i in range(0, need_to_create):
                volume = 'volume-%s' % str(uuid.uuid4())
                common.pdsh(user, [controller], "rbd create -p %s --size %s --image-format 2 %s" % (poolname, str(volume_size), volume))
            common.printout("LOG","%d RBD Image Created" % need_to_create)

    def get_rbd_list(self):
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        poolname = "rbd"
        stdout, stderr = common.pdsh(user, [controller], "rbd ls -p %s" % poolname, option="check_return")
        if stderr:
            common.printout("ERROR","unable get rbd list, return msg: %s" % stderr)
            #sys.exit()
        res = common.format_pdsh_return(stdout)
        if res != {}:
            rbd_list_tmp = (res[controller]).split()
        else:
            rbd_list_tmp = []
        return rbd_list_tmp

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

    def cleanup(self):
        user = self.cluster["user"]
        nodes = self.cluster["osd"]
        dest_dir = self.cluster["tmp_dir"]
        clients = self.cluster["client"]
        common.pdsh(user, nodes, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))
        common.pdsh(user, clients, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir))

    def prerun_check(self):
        pass

    def run(self):
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        common.printout("LOG","This test will run %d secs until finish." % waittime)

        #drop page cache
        user = self.cluster["user"]
        time = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"]) + self.cluster["run_time_extend"]
        dest_dir = self.cluster["tmp_dir"]
        nodes = self.cluster["osd"]
        common.pdsh(user, nodes, "echo '3' > /proc/sys/vm/drop_caches && sync")

        #send command to ceph cluster
        common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt; echo `date +%s`' interrupt start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "top -c -b -d 1 > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt"  % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A 1 > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "echo `date +%s`' perfcounter start' >> %s/`hostname`_process_log.txt; for i in `seq 1 %d`; do find /var/run/ceph -name '*osd*asok' | while read path; do filename=`echo $path | awk -F/ '{print $NF}'`;res_file=%s/`hostname`_${filename}.txt; echo `ceph --admin-daemon $path perf dump`, >> ${res_file} & done; sleep 1; done; echo `date +%s`' perfcounter stop' >> %s/`hostname`_process_log.txt;" % ('%s', dest_dir, time, dest_dir, '%s', dest_dir), option="force")

        #2. send command to client
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt; echo `date +%s`' interrupt start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "top -c -b -d 1 > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL 1 > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt"  % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p -dxm 1 > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A 1 > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))

    def archive(self):
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]
        #collect all.conf
        try:
            common.rscp(user, head, "%s/" % (dest_dir), "%s/conf/all.conf" % self.pwd)
            common.rscp(user, head, "%s/" % (dest_dir), "%s/conf/%s" % (self.pwd, common.cetune_log_file) )
            common.rscp(user, head, "%s/" % (dest_dir), "%s/conf/%s" % (self.pwd, common.cetune_error_file) )
            common.bash("rm -f %s/conf/%s" % (self.pwd, common.cetune_log_file))
            common.bash("rm -f %s/conf/%s" % (self.pwd, common.cetune_error_file))
        except:
            pass
        #collect tuner.yaml
        worksheet = common.load_yaml_conf("%s/conf/tuner.yaml" % self.pwd)
        if self.benchmark["tuning_section"] in worksheet:
            common.write_yaml_file( "%s/tuning.yaml" % dest_dir, {self.benchmark["tuning_section"]:worksheet[self.benchmark["tuning_section"]]})
        #collect osd data
        for node in self.cluster["osd"]:
            common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])

        #collect client data
        for node in self.benchmark["distribution"].keys():
            common.pdsh(user, ["%s@%s" % (user, head)], "mkdir -p %s/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])

        #save real runtime
        if self.real_runtime:
            with open("%s/real_runtime.txt" % dest_dir, "w") as f:
                f.write(str(int(self.real_runtime)))

    def stop_data_collecters(self):
        #2. clean running process
        user = self.cluster["user"]
        nodes = self.cluster["osd"]
        dest_dir = self.cluster["tmp_dir"]
        stdout, stderr = common.pdsh(user, nodes, "echo `date +%s`' perfcounter stop' >> %s/`hostname`_process_log.txt; ps aux | grep asok |awk '{print $2}'| while read pid;do kill $pid;done" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 top; echo `date +%s`' top stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar; echo `date +%s`' sar stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat; echo `date +%s`' iostat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 mpstat; echo `date +%s`' mpstat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_end.txt; echo `date +%s`' interrupt stop' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))

        #2. send command to client
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "killall -9 top; echo `date +%s`' top stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar; echo `date +%s`' sar stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat; echo `date +%s`' iostat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 mpstat; echo `date +%s`' mpstat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_end.txt; echo `date +%s`' interrup stop' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))

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
             if not remained_instance_num:
                 break
             if remained_instance_num < volume_max_per_client:
                 volume_num_upper_bound = remained_instance_num
             else:
                 volume_num_upper_bound = volume_max_per_client
             self.benchmark["distribution"][client] = copy.deepcopy(self.cluster["testjob_distribution"][client][:volume_num_upper_bound])
             remained_instance_num = remained_instance_num - volume_num_upper_bound

    def check_fio_pgrep(self, nodes, fio_job_num = 1):
        user =  self.cluster["user"]
        stdout, stderr = common.pdsh(user, nodes, "pgrep fio", option = "check_return")
        res = common.format_pdsh_return(stdout)
        if res != []:
            fio_running_job_num = 0
            for node in res:
                fio_running_job_num += len(str(res[node]).split('\n'))
            if fio_running_job_num >= fio_job_num:
                common.printout("WARNING","%d fio job still runing" % fio_running_job_num)
                return True
            else:
                return False
        return False

    def check_rbd_init_completed(self, planed_space):
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        stdout, stderr = common.pdsh(user, [controller], "ceph -s | grep pgmap | awk '{print $7 $8}'", option = "check_return")
        res = common.format_pdsh_return(stdout)
        if controller not in res:
            common.printout("ERROR","cannot get ceph space, seems to be a dead error")
            #sys.exit()
        cur_space = common.size_to_Kbytes(res[controller])
        planned_space = common.size_to_Kbytes(planed_space)
        common.printout("WARNING","Ceph cluster used data occupied: %s KB, planned_space: %s KB " % (cur_space, planned_space))
        if cur_space < planned_space:
            return False
        else:
            return True

    def generate_benchmark_cases(self):
        return [[],[]]

    def parse_benchmark_cases(self):
        pass

    def load_parameter(self):
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["tmp_dir"] = self.all_conf_data.get("tmp_dir")
        self.cluster["dest_dir"] = self.all_conf_data.get("dest_dir")
        self.cluster["client"] = self.all_conf_data.get_list("list_client")
        self.cluster["osd"] = self.all_conf_data.get_list("list_ceph")
        self.cluster["rbd_num_per_client"] = self.all_conf_data.get_list("rbd_num_per_client")
        self.cluster["run_time_extend"] = 100

    def chkpoint_to_log(self, log_str):
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        nodes = []
        nodes.extend(self.cluster["osd"])
        nodes.extend(self.benchmark["distribution"].keys())
        common.pdsh(user, nodes, "echo `date +%s`' %s' >> %s/`hostname`_process_log.txt" % ('%s', log_str, dest_dir))
