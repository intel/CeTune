import subprocess
from conf import *
import copy
import os, sys
import time
import re
import uuid
from analyzer import *
lib_path = ( os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Benchmark(object):
    def __init__(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        self.runid = 0
        self.all_conf_data = config.Config(lib_path+"/conf/all.conf")
        self.benchmark = {}
        self.cluster = {}
        self.pwd = os.path.abspath(os.path.join('..'))

    def go(self, testcase, tuning):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        try:
            common.clean_process_log(os.path.join(self.pwd,'log'))
            cancel_file = open("../conf/execute_op_type.conf","r")
            execute_op_type = cancel_file.read().strip("\n")
            if execute_op_type != "cancel_all":
                common.bash("rm -f %s/conf/%s" % (self.pwd, common.cetune_log_file))
                common.bash("rm -f %s/conf/%s" % (self.pwd, common.cetune_error_file))
                user = self.all_conf_data.get("user")
                controller = self.all_conf_data.get("head")
                common.wait_ceph_to_health( user, controller )
                self.benchmark = self.parse_benchmark_cases(testcase)
                self.load_parameter()
                self.get_runid()
                self.set_runid()

                if not self.generate_benchmark_cases(self.benchmark):
                    common.printout("ERROR", "Failed to generate Fio/cosbench configuration file.",log_level="LVL1")
                    sys.exit()
                self.benchmark["tuning_section"] = tuning

                self.prepare_result_dir()
                common.printout("LOG","RUNID: %d, RESULT_DIR: %s" % (self.runid, self.cluster["dest_dir"]))
                self.cal_run_job_distribution()
                self.prerun_check()
                self.prepare_run()

                common.printout("LOG","Run Benchmark Status: collect system metrics and run benchmark")
                test_start_time = time.time()
                interrupted_flag = False
                try:
                    self.run()
                except KeyboardInterrupt:
                    interrupted_flag = True
                    self.setStatus("Interrupted")
                    common.printout("WARNING","Caught Signal to Cancel this run, killing Workload now, pls wait",log_level="LVL1")
                    self.real_runtime = time.time() - test_start_time
                    self.stop_workload()
                    self.stop_data_collecters()

                self.real_runtime = time.time() - test_start_time
                self.after_run()
                common.printout("LOG","Collecting Data, this will takes quite long time depends on the network")
                self.archive()
                if not interrupted_flag:
                    self.setStatus("Completed")

                common.printout("LOG","Post Process Result Data")
                try:
                    analyzer.main(['--path', self.cluster["dest_dir"], 'process_data'])
                except:
                    common.printout("ERROR","analyzer failed, pls try cd analyzer; python analyzer.py --path %s process_data " % self.cluster["dest_dir"],log_level="LVL1")
        except:
            common.printout("ERROR","The test has been stopped.",log_level="LVL1")

    def create_image(self, volume_count, volume_size, poolname):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        rbd_list = self.get_rbd_list(poolname)
        need_to_create = 0
        if not len(rbd_list) >= int(volume_count):
            need_to_create = int(volume_count) - len(rbd_list)
        if need_to_create != 0:
            for i in range(0, need_to_create):
                volume = 'volume-%s' % str(uuid.uuid4())
                common.pdsh(user, [controller], "rbd create -p %s --size %s %s --image-format 2" % (poolname, str(volume_size), volume))
            common.printout("LOG","%d RBD Image Created" % need_to_create)

    def get_rbd_list(self, poolname):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        stdout, stderr = common.pdsh(user, [controller], "rbd ls -p %s" % poolname, option="check_return")
        if stderr:
            common.printout("ERROR","unable get rbd list, return msg: %s" % stderr,log_level="LVL1")
            #sys.exit()
        res = common.format_pdsh_return(stdout)
        if res != {}:
            rbd_list_tmp = (res[controller]).split()
        else:
            rbd_list_tmp = []
        return rbd_list_tmp

    def after_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
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
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
#        self.stop_workload()
        self.stop_data_collecters()

    def cleanup(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        nodes = self.cluster["osd"]
        dest_dir = self.cluster["tmp_dir"]
        clients = self.cluster["client"]
        common.pdsh(user, nodes, "rm -rf %s/*.txt; rm -rf %s/*.log; rm %s/*blktrace*; rm -rf %s/lttng-traces/*" % (dest_dir, dest_dir, dest_dir, dest_dir), except_returncode=1)
        common.pdsh(user, clients, "rm -rf %s/*.txt; rm -rf %s/*.log" % (dest_dir, dest_dir), option="check_return")
        common.printout("LOG","Cleaned original data under %s " % dest_dir)

    def prerun_check(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        nodes = self.cluster["osd"]
        common.printout("LOG","Prerun_check: check if sysstat installed " % nodes)
        common.pdsh(user, nodes, "mpstat")

        if "fatrace" in self.cluster["collector"]:
            common.printout("LOG","Prerun_check: check if fatrace installed " % nodes)
            common.pdsh(user, nodes, "fatrace -h")

        if "blktrace" in self.cluster["collector"]:
            common.printout("LOG","Prerun_check: check if blktrace installed " % nodes)
            common.pdsh(user, nodes, "blktrace -v")

        if "strace" in self.cluster["collector"]:
            common.printout("LOG","Prerun_check: check if strace installed " % nodes)
            common.pdsh(user, nodes, "strace -V")

        if "lttng" in self.cluster["collector"]:
            common.printout("LOG","Prerun_check: check if lttng installed " % nodes)
            common.pdsh(user, nodes, "lttng -V")

    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"])
        common.printout("LOG","This test will run %d secs until finish." % waittime)

        #drop page cache
        user = self.cluster["user"]
        time_tmp = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"]) + self.cluster["run_time_extend"]
        dest_dir = self.cluster["tmp_dir"]
        nodes = self.cluster["osd"]
        monitor_interval = self.cluster["monitoring_interval"]
        #nodes.extend(self.benchmark["distribution"].keys())
        common.pdsh(user, nodes, "sync && echo '%s' > /proc/sys/vm/drop_caches" % self.cluster["cache_drop_level"])

        #send command to ceph cluster
        common.pdsh(user, nodes, "for i in `seq 1 %d`;do echo `date \"+%s\"` `ceph health` >> %s/`hostname`_ceph_health.txt; sleep %s;done" % (time_tmp/int(monitor_interval)+1, "%Y_%m_%d %H:%M:%S", dest_dir, monitor_interval), option="force")
        common.pdsh(user, nodes, "ps aux | grep ceph-osd | grep -v 'grep' > %s/`hostname`_ps.txt" % (dest_dir))
        common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.printout("LOG","Start system data collector under %s " % nodes)
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt; echo `date +%s`' interrupt start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "top -c -b -d %s > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "mpstat -P ALL %s > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt"  % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "iostat -p ALL -dxm %s > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "sar -A %s > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "ceph -v > %s/`hostname`_ceph_version.txt" % (dest_dir))
        if "perfcounter" in self.cluster["collector"]:
            common.printout("LOG","Start perfcounter data collector under %s " % nodes)
            self.create_admin_daemon_dump_script(dest_dir, time_tmp, monitor_interval)
            for node in nodes:
                common.scp(user, node, "ceph_admin.bash", dest_dir);
            common.pdsh(user, nodes, "echo `date +%s`' perfcounter start' >> %s/`hostname`_process_log.txt; bash %s/ceph_admin.bash; echo `date +%s`' perfcounter stop' >> %s/`hostname`_process_log.txt; rm -rf %s/ceph_admin.bash" % ('%s', dest_dir, dest_dir, '%s', dest_dir, dest_dir), option="force")
        if "blktrace" in self.cluster["collector"]:
            for node in nodes:
                common.printout("LOG","Start blktrace data collector under %s " % node)
                for osd_dev in self.cluster[node]["osds"]:
                    common.pdsh(user, [node], "cd %s; blktrace -d %s -o `hostname`_osd_%s 2>&1 > %s/`hostname`_blktrace_%s.log" % (dest_dir, osd_dev, osd_dev.replace("/","_"), dest_dir, osd_dev.replace("/","_")), option="force")
                for journal_dev in self.cluster[node]["journals"]:
                    common.pdsh(user, [node], "cd %s; blktrace -d %s -o `hostname`_journal_%s 2>&1 > %s/`hostname`_blktrace_%s.log" % (dest_dir, journal_dev, journal_dev.replace("/","_"), dest_dir, journal_dev.replace("/","_")), option="force")
            common.printout("LOG","Sleep 15s due to high cpu utilization when blktrace finish")
            time.sleep(15)
        if "fatrace" in self.cluster["collector"]:
            common.printout("LOG","Start fatrace data collector under %s " % nodes)
            time.sleep(15)
            common.pdsh(user, nodes, "fatrace -o %s/`hostname`_fatrace.txt &" % (dest_dir))
        if "strace" in self.cluster["collector"]:
            common.printout("LOG","Start strace data collector under %s " % nodes)
            common.pdsh(user, nodes, "ps aux | grep ceph-osd | grep -v 'grep' | awk '{print $2}' | while read pid;do strace -ttt -T -e trace=desc -p ${pid} -o %s/`hostname`_strace_${pid}.txt 2>&1 > %s/`hostname`_strace_${pid}.log & done" % (dest_dir, dest_dir), option="force")
        if "lttng" in self.cluster["collector"]:
            common.printout("LOG","Start lttng data collector under %s " % nodes)
            common.pdsh(user, nodes, "export HOME='%s'; lttng destroy 2>/dev/null; lttng create zipkin; lttng enable-channel channel0 -u --buffers-pid; lttng enable-event -c channel0 --userspace zipkin:*; lttng start;" % (dest_dir))
        need_smart_dict = {}
        for node in nodes:
            nvme_devs = []
            for osd_journal in common.get_list(self.all_conf_data.get_list(node)):
                if 'nvme' in osd_journal[0]:
                    nvme_dev = common.parse_nvme( osd_journal[0] )
                    if nvme_dev not in nvme_devs:
                        nvme_devs.append(nvme_dev)
                if 'nvme' in osd_journal[1]:
                    nvme_dev = common.parse_nvme( osd_journal[1] )
                    if nvme_dev not in nvme_devs:
                        nvme_devs.append(nvme_dev)

            if node not in need_smart_dict:
                need_smart_dict[node] = nvme_devs
        for node, nvme_list in need_smart_dict.items():
            common.scp(user, node, '../conf/nvme-pack/', '/opt/')
            for nvme_dev in nvme_list:
                if nvme_dev[-1] == '/':
                    nvme_dev = nvme_dev[:-1]
                common.pdsh(user, [node], 'cd /opt/nvme-pack/; python nvme-parser.py --tool_path ./ --output /opt/%s_%s_smartinfo.txt %s' % (node, nvme_dev.split('/')[-1], nvme_dev))

        #2. send command to client
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "for i in `seq 1 %d`;do echo `date \"+%s\"` `ceph health` >> %s/`hostname`_ceph_health.txt; sleep %s;done" % (time_tmp/int(monitor_interval)+1, "%Y_%m_%d %H:%M:%S", dest_dir, monitor_interval), option="force")
        common.pdsh(user, nodes, "date > %s/`hostname`_process_log.txt" % (dest_dir))
        common.printout("LOG","Start system data collector under %s " % nodes)
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_start.txt; echo `date +%s`' interrupt start' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "ps -fe|grep top |grep -v grep; if [ $? -ne 0 ]; then top -c -b -d %s > %s/`hostname`_top.txt & echo `date +%s`' top start' >> %s/`hostname`_process_log.txt; fi" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "ps -fe|grep mpstat |grep -v grep; if [ $? -ne 0 ]; then mpstat -P ALL %s > %s/`hostname`_mpstat.txt & echo `date +%s`' mpstat start' >> %s/`hostname`_process_log.txt; fi"  % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "ps -fe|grep iostat |grep -v grep; if [ $? -ne 0 ]; then iostat -p -dxm %s > %s/`hostname`_iostat.txt & echo `date +%s`' iostat start' >> %s/`hostname`_process_log.txt; fi" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "ps -fe|grep sar |grep -v grep; if [ $? -ne 0 ]; then sar -A %s > %s/`hostname`_sar.txt & echo `date +%s`' sar start' >> %s/`hostname`_process_log.txt; fi" % (monitor_interval, dest_dir, '%s', dest_dir))
        common.pdsh(user, nodes, "ceph -v > %s/`hostname`_ceph_version.txt" % (dest_dir))
        if "perfcounter" in self.cluster["collector"]:
            common.printout("LOG","Start perfcounter data collector under %s " % nodes)
            self.create_admin_daemon_dump_script(dest_dir, time_tmp, monitor_interval)
            for node in nodes:
                common.scp(user, node, "ceph_admin.bash", dest_dir);
            common.pdsh(user, nodes, "echo `date +%s`' perfcounter start' >> %s/`hostname`_process_log.txt; bash %s/ceph_admin.bash; echo `date +%s`' perfcounter stop' >> %s/`hostname`_process_log.txt; rm -rf %s/ceph_admin.bash" % ('%s', dest_dir, dest_dir, '%s', dest_dir, dest_dir), option="force")

    def archive(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]
        #collect all.conf
        try:
            common.bash("mkdir -p %s/conf" % (dest_dir))
            common.bash("mkdir -p %s/log" % (dest_dir))
            common.cp("%s/conf/all.conf" % self.pwd, "%s/conf/" % dest_dir)
            common.cp("%s/conf/%s" % (self.pwd, common.cetune_log_file), "%s/conf/" % dest_dir)
            common.cp("%s/conf/%s" % (self.pwd, common.cetune_error_file), "%s/conf/" % dest_dir)
            common.bash("rm -f %s/conf/%s" % (self.pwd, common.cetune_log_file))
            common.bash("rm -f %s/conf/%s" % (self.pwd, common.cetune_error_file))
        except Exception,e:
            common.printout("LOG","<CLASS_NAME:%s> <FUN_NAME : %s> ERR_MSG:%s"%(self.__class__.__name__,sys._getframe().f_code.co_name,e),log_level="LVL2")
            pass
        #collect tuner.yaml
        worksheet = common.load_yaml_conf("%s/conf/tuner.yaml" % self.pwd)
        if self.benchmark["tuning_section"] in worksheet:
            common.write_yaml_file( "%s/conf/tuner.yaml" % dest_dir, {self.benchmark["tuning_section"]:worksheet[self.benchmark["tuning_section"]]})
        else:
            common.cp("%s/conf/tuner.yaml" % (dest_dir), "%s/conf/tuner.yaml" % (self.pwd) )
        #write description to dir
        with open( "%s/conf/description" % dest_dir, 'w+' ) as f:
            f.write( self.benchmark["description"] )
        #collect osd data
        for node in self.cluster["osd"]:
            common.bash("mkdir -p %s/raw/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])
            common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*.csv" % self.cluster["tmp_dir"])
            common.rscp(user, node, "%s/conf/" % (dest_dir), "%s/*.csv" % self.cluster["tmp_dir"])
            if "blktrace" in self.cluster["collector"]:
                common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*blktrace*" % self.cluster["tmp_dir"])
            if "lttng" in self.cluster["collector"]:
                common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/lttng-traces" % self.cluster["tmp_dir"])

        #collect client data
        for node in self.benchmark["distribution"].keys():
            common.bash( "mkdir -p %s/raw/%s" % (dest_dir, node))
            common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*.txt" % self.cluster["tmp_dir"])
            common.rscp(user, node, "%s/raw/%s/" % (dest_dir, node), "%s/*.csv" % self.cluster["tmp_dir"])
            common.rscp(user, node, "%s/conf/" % (dest_dir), "%s/*.csv" % self.cluster["tmp_dir"])

        #save real runtime
        if self.real_runtime:
            with open("%s/real_runtime.txt" % dest_dir, "w") as f:
                f.write(str(int(self.real_runtime)))

        common.bash("cp %s/log/* %s/log/" %(self.pwd,dest_dir))
        common.bash("rm -f %s/log/*" %self.pwd)

    def stop_data_collecters(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #2. clean running process
        user = self.cluster["user"]
        nodes = self.cluster["osd"]
        dest_dir = self.cluster["tmp_dir"]
        if "lttng" in self.cluster["collector"]:
            common.pdsh(user, nodes, "export HOME=%s; lttng stop; lttng destroy;" % dest_dir, option = "check_return")
        if "perfcounter" in self.cluster["collector"]:
            common.pdsh(user, nodes, "echo `date +%s`' perfcounter stop' >> %s/`hostname`_process_log.txt; ps aux | grep ceph_admin | grep -v 'grep' | awk '{print $2}' | while read pid;do kill $pid;done" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 top; echo `date +%s`' top stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar; echo `date +%s`' sar stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat; echo `date +%s`' iostat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 mpstat; echo `date +%s`' mpstat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        if "fatrace" in self.cluster["collector"]:
            common.pdsh(user, nodes, "killall -9 fatrace;", option = "check_return")
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_end.txt; echo `date +%s`' interrupt stop' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))
        if "blktrace" in self.cluster["collector"]:
            common.pdsh(user, nodes, "killall -9 blktrace;", option = "check_return")
        if "strace" in self.cluster["collector"]:
            common.pdsh(user, nodes, "killall -9 strace;", option = "check_return")

        #2. send command to client
        nodes = self.benchmark["distribution"].keys()
        if "perfcounter" in self.cluster["collector"]:
            common.pdsh(user, nodes, "echo `date +%s`' perfcounter stop' >> %s/`hostname`_process_log.txt; ps aux | grep ceph_admin | grep -v 'grep' | awk '{print $2}' | while read pid;do kill $pid;done" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 top; echo `date +%s`' top stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 sar; echo `date +%s`' sar stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 iostat; echo `date +%s`' iostat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "killall -9 mpstat; echo `date +%s`' mpstat stop' >> %s/`hostname`_process_log.txt" % ('%s', dest_dir), option = "check_return")
        common.pdsh(user, nodes, "cat /proc/interrupts > %s/`hostname`_interrupts_end.txt; echo `date +%s`' interrupt stop' >> %s/`hostname`_process_log.txt" % (dest_dir, '%s', dest_dir))

    def tuning(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        pass

    def get_runid(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        if self.runid != 0:
            return
        try:
            with open("%s/.run_number" % lib_path, "r") as f:
                self.runid = int(f.read())
        except Exception,e:
            common.printout("LOG","<CLASS_NAME:%s> <FUN_NAME : %s> ERR_MSG:%s"%(self.__class__.__name__,sys._getframe().f_code.co_name,e),log_level="LVL2")
            pass

    def set_runid(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        if not self.runid:
           self.get_runid()
        with open("%s/.run_number" % lib_path, "w") as f:
            f.write(str(self.runid+1))

    def testjob_distribution(self, disk_num_per_client, instance_list):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        start_vclient_num = 0
        client_num = 0
        self.cluster["testjob_distribution"] = {}
        for client in self.cluster["client"]:
            vclient_total = int(disk_num_per_client[client_num])
            end_vclient_num = start_vclient_num + vclient_total
            self.cluster["testjob_distribution"][client] = copy.deepcopy(instance_list[start_vclient_num:end_vclient_num])
            start_vclient_num = end_vclient_num
            client_num += 1

    def cal_run_job_distribution(self):
         common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
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

    def check_fio_pgrep(self, nodes, fio_node_num = 1, check_type="jobnum"):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user =  self.cluster["user"]
        stdout, stderr = common.pdsh(user, nodes, "pgrep -x fio", option = "check_return")
        res = common.format_pdsh_return(stdout)
        if res != []:
            fio_running_job_num = 0
            fio_running_node_num = 0
            for node in res:
                fio_running_node_num += 1
                fio_running_job_num += len(str(res[node]).strip().split('\n'))
            if (check_type == "jobnum" and fio_running_job_num >= fio_node_num) or (check_type == "nodenum" and fio_running_node_num >= fio_node_num):
                common.printout("WARNING","%d fio job still runing" % fio_running_job_num)
                return True
            else:
                if check_type == "nodenum":
                    common.printout("WARNING","Expecting %d nodes run fio, detect %d node runing" % (fio_node_num, fio_running_node_num))
                if check_type == "jobnum":
                    common.printout("WARNING","Expecting %d nodes run fio, detect %d node runing" % (fio_node_num, fio_running_job_num))
                return False
        common.printout("WARNING","Detect no fio job runing" % (fio_node_num, fio_running_node_num),log_level="LVL1")
        return False

    def check_rbd_init_completed(self, planed_space, pool_name="rbd"):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user =  self.cluster["user"]
        controller =  self.cluster["head"]
        stdout, stderr = common.pdsh(user, [controller], "ceph df | grep %s | awk '{print $3}'" % pool_name, option = "check_return")
        res = common.format_pdsh_return(stdout)
        if controller not in res:
            common.printout("ERROR","cannot get ceph space, seems to be a dead error",log_level="LVL1")
            #sys.exit()
        cur_space = common.size_to_Kbytes(res[controller])
        planned_space = common.size_to_Kbytes(planed_space)
        common.printout("WARNING","Ceph cluster used data occupied: %s KB, planned_space: %s KB " % (cur_space, planned_space))
        if cur_space < planned_space:
            return False
        else:
            return True

    def create_admin_daemon_dump_script(self, dest_dir, total_count, monitor_interval):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        with open('ceph_admin.bash', 'w') as f:
            f.write("for i in `seq 1 %d`; do find /var/run/ceph -name '*osd*asok' | while read path; do filename=`echo $path | awk -F/ '{print $NF}'`;res_file=%s/`hostname`_${filename}.txt; echo `ceph --admin-daemon $path perf dump`, >> ${res_file} & done; sleep %s; done;" % (total_count, dest_dir, monitor_interval))

    def generate_benchmark_cases(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        return [[],[]]

    def parse_benchmark_cases(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        pass

    def load_parameter(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["tmp_dir"] = self.all_conf_data.get("tmp_dir")
        self.cluster["dest_dir"] = self.all_conf_data.get("dest_dir")
        self.cluster["client"] = self.all_conf_data.get_list("list_client")
        self.cluster["osd"] = self.all_conf_data.get_list("list_server")
        for node in self.cluster["osd"]:
            self.cluster[node] = {}
            self.cluster[node]["osds"] = []
            self.cluster[node]["journals"] = []
            for osd_journal in common.get_list(self.all_conf_data.get_list(node)):
                self.cluster[node]["osds"].append(osd_journal[0])
                self.cluster[node]["journals"].append(osd_journal[1])
        self.cluster["disk_num_per_client"] = self.all_conf_data.get_list("disk_num_per_client")
        self.cluster["cache_drop_level"] = self.all_conf_data.get("cache_drop_level")
        self.cluster["monitoring_interval"] = self.all_conf_data.get("monitoring_interval")
        self.cluster["run_time_extend"] = 100
        self.cluster["collector"] = self.all_conf_data.get_list("collector")

    def chkpoint_to_log(self, log_str):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        dest_dir = self.cluster["tmp_dir"]
        user = self.cluster["user"]
        nodes = []
        nodes.extend(self.cluster["osd"])
        nodes.extend(self.benchmark["distribution"].keys())
        common.pdsh(user, nodes, "echo `date +%s`' %s' >> %s/`hostname`_process_log.txt" % ('%s', log_str, dest_dir))

    def setStatus(self, status):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        head = self.cluster["head"]
        dest_dir = self.cluster["dest_dir"]
        common.bash("mkdir -p %s/conf" % (dest_dir))
        common.bash("echo %s > %s/conf/status" % (status, dest_dir))

    def prepare_result_dir(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        res = common.pdsh(self.cluster["user"],["%s"%(self.cluster["head"])],"test -d %s" % (self.cluster["dest_dir"]), option = "check_return")
	if not res[1]:
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]),log_level="LVL1")
            sys.exit()

        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))
        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s/conf/" % (self.cluster["dest_dir"]))
        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s/raw/" % (self.cluster["dest_dir"]))
