from ..benchmark import *
from collections import OrderedDict
import itertools
from plugin import *
import sys

class Hook(Benchmark):
    def load_parameter(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).load_parameter()
        self.custom_script = self.all_conf_data.get("custom_script", True )

    def prepare_result_dir(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #1. prepare result dir
        self.get_runid()
        self.benchmark["section_name"] = "hook-%s-%s-qd%s-%s-%s-%s-hook" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"])
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.cluster["dest_dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])

        res = common.pdsh(self.cluster["user"],["%s"%(self.cluster["head"])],"test -d %s" % (self.cluster["dest_dir"]), option = "check_return")
	if not res[1]:
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]),log_level="LVL1")
            sys.exit()

        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))

    def prepare_run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        self.cleanup()

    def wait_workload_to_stop(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        pass

    def stop_workload(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        pass

    def generate_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        if self.benchmark["description"] != "":
            custom_script = self.all_conf_data.get("%s|custom_script" % self.benchmark["description"], True )
            self.custom_script = custom_script
        return True

    def parse_benchmark_cases(self, testcase):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        p = testcase
        testcase_dict = {
            "instance_number":p[0], "volume_size":p[1], "iopattern":p[2],
            "block_size":p[3], "qd":p[4], "rampup":p[5],
            "runtime":p[6], "vdisk":p[7]
        }
        if len(p) == 9:
            testcase_dict["description"] = p[8]
        else:
            testcase_dict["description"] = ""
        return testcase_dict

    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        super(self.__class__, self).run()
        common.printout("LOG", "custom_script: %s" % self.custom_script)
        waittime = int(self.benchmark["runtime"]) + int(self.benchmark["rampup"]) + self.cluster["run_time_extend"]
        if self.custom_script:
            common.bash( self.custom_script )
        plugin.main()
        for wait in range(1, waittime):
            time.sleep(1)

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

    def cal_run_job_distribution(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        self.cluster["testjob_distribution"] = {}
        self.benchmark["distribution"] = {}
        for node in self.cluster["client"]:
            self.cluster["testjob_distribution"][node] = []
            self.benchmark["distribution"][node] = []
