from ..benchmark import *
from collections import OrderedDict
import itertools

class FioRbd(Benchmark):
    def load_parameter(self):
        super(self.__class__, self).load_parameter()
        self.cluster["rbdlist"] = self.get_rbd_list()
        if len(self.cluster["rbdlist"]) < int(self.all_conf_data.get("rbd_volume_count")):
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
        common.printout("LOG","Creating rbd volume")
        if rbd_count and rbd_size:
            super(self.__class__, self).create_image(rbd_count, rbd_size, 'rbd')
        else:
            common.printout("ERROR","need to set rbd_volume_count and volune_size in all.conf")
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
            common.printout("ERROR","Failed to start FIO process")
            common.pdsh(user, clients, "killall -9 fio", option = "check_return")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            common.printout("ERROR","Planed to run 0 Fio Job, please check all.conf")
            raise KeyboardInterrupt
        common.printout("LOG","%d FIO Jobs starts on %s" % (len(self.cluster["testjob_distribution"][client]), client))

        common.printout("LOG","Wait rbd initialization stop")
        #wait fio finish
        try:
            while self.check_fio_pgrep(self.cluster["testjob_distribution"].keys()):
                time.sleep(5)
        except KeyboardInterrupt:
            clients = self.cluster["testjob_distribution"].keys()
            common.pdsh(user, clients, "killall -9 fio", option = "check_return")
        common.printout("LOG","rbd initialization finished")

    def prepare_result_dir(self):
        #1. prepare result dir
        self.get_runid()
        self.benchmark["section_name"] = "fiorbd-%s-%s-qd%s-%s-%s-%s-fiorbd" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"])
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.cluster["dest_dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])
	
        res = common.pdsh(self.cluster["user"],["%s"%(self.cluster["head"])],"test -d %s" % (self.cluster["dest_dir"]), option = "check_return")
	if not res[1]:
            common.printout("ERROR","Output DIR %s exists" % (self.cluster["dest_dir"]))
            sys.exit()

        common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.cluster["dest_dir"]))

    def prerun_check(self):
        #1. check is vclient alive
        user = self.cluster["user"]
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "fio -v")
        common.printout("LOG","check if FIO rbd engine installed")
        res = common.pdsh(user, nodes, "fio -enghelp | grep rbd", option = "check_return")
        if res and not res[0]:
            common.printout("ERROR","FIO rbd engine not installed")
            sys.exit()
        planed_space = str(len(self.cluster["rbdlist"]) * int(self.volume_size)) + "MB"
        common.printout("LOG","check if rbd volume fully initialized")
        if not self.check_rbd_init_completed(planed_space):
            common.printout("WARNING","rbd volume initialization has not be done")
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
            common.printout("ERROR","Failed to start FIO process")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            common.printout("ERROR","Planned to start 0 FIO process, seems to be an error")
            raise KeyboardInterrupt
        common.printout("LOG","%d FIO Jobs starts on %s" % ( fio_job_num_total, str(self.benchmark["distribution"].keys())))
        self.chkpoint_to_log("fio start")
        while self.check_fio_pgrep(self.benchmark["distribution"].keys()):
            time.sleep(5)

    def prepare_run(self):
        super(self.__class__, self).prepare_run()
        user = self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        common.printout("LOG","Prepare_run: distribute fio.conf to all clients")
        for client in self.benchmark["distribution"].keys():
            common.scp(user, client, "../conf/fio.conf", dest_dir)
        self.cleanup()
    
    def wait_workload_to_stop(self):
        common.printout("LOG","Waiting Workload to complete its work")
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
                common.printout("WARNING","FIO stills run on %s" % str(res[0].split('\n')))
            if stop_flag or cur_check > max_check_times:
                break;
            cur_check += 1
            time.sleep(10)
        common.printout("LOG","Workload completed")

    def stop_workload(self):
        user = self.cluster["user"]
        nodes = self.benchmark["distribution"].keys()
        common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        self.chkpoint_to_log("fio stop")

    def generate_benchmark_cases(self):
        engine = self.all_conf_data.get_list('benchmark_engine')
        if "fiorbd" not in engine:
            return [[],[]]
        test_config = OrderedDict()
        test_config["engine"] = ["fiorbd"]
        test_config["vm_num"] = self.all_conf_data.get_list('run_vm_num')
        test_config["rbd_volume_size"] = self.all_conf_data.get_list('run_size')
        test_config["io_pattern"] = self.all_conf_data.get_list('run_io_pattern')
        test_config["record_size"] = self.all_conf_data.get_list('run_record_size')
        test_config["queue_depth"] = self.all_conf_data.get_list('run_queue_depth')
        test_config["warmup_time"] = self.all_conf_data.get_list('run_warmup_time')
        test_config["runtime"] = self.all_conf_data.get_list('run_time')
        test_config["disk"] = ["fiorbd"]
        testcase_list = []
        for testcase in itertools.product(*(test_config.values())):
            testcase_list.append('%8s\t%4s\t%16s\t%8s\t%8s\t%16s\t%8s\t%8s\t%8s' % ( testcase ))

        fio_list = []
        fio_list.append("[global]")
        fio_list.append("    direct=1")
        fio_list.append("    time_based")
        for element in itertools.product(test_config["engine"], test_config["io_pattern"], test_config["record_size"], test_config["queue_depth"], test_config["rbd_volume_size"], test_config["warmup_time"], test_config["runtime"], test_config["disk"]):
            engine, io_pattern, record_size, queue_depth, rbd_volume_size, warmup_time, runtime, disk = element
            io_pattern_fio = io_pattern
            if io_pattern == "seqread":
                io_pattern_fio = "read"
            if io_pattern == "seqwrite":
                io_pattern_fio = "write"
            fio_template = []
            fio_template.append("[%s-%s-%s-qd%s-%s-%s-%s-%s]" % (engine, io_pattern, record_size, queue_depth, rbd_volume_size, warmup_time, runtime, disk))
            fio_template.append("    rw=%s" % io_pattern_fio)
            fio_template.append("    bs=%s" % record_size)
            fio_template.append("    iodepth=%s" % queue_depth)
            fio_template.append("    ramp_time=%s" % warmup_time)
            fio_template.append("    runtime=%s" % runtime)
            fio_template.append("    ioengine=rbd")
            fio_template.append("    clientname=admin")
            fio_template.append("    pool=${POOLNAME}")
            fio_template.append("    rbdname=${RBDNAME}")
            if io_pattern in ["randread", "randwrite", "randrw"]:
                fio_template.append("    iodepth_batch_submit=1")
                fio_template.append("    iodepth_batch_complete=1")
                fio_template.append("    rate_iops=100")
            if io_pattern in ["seqread", "seqwrite", "readwrite", "rw"]:
                fio_template.append("    iodepth_batch_submit=8")
                fio_template.append("    iodepth_batch_complete=8")
                fio_template.append("    rate=60m")
            if io_pattern in ["randrw", "readwrite", "rw"]:
                try:
                    rwmixread = self.all_conf_data.get('rwmixread')
                    fio_template.append("    rwmixread=%s" % rwmixread)
                except:
                    pass
            fio_list.extend(fio_template)
        return [testcase_list, fio_list]

    def parse_benchmark_cases(self, testcase):
        p = testcase
        testcase_dict = {
            "instance_number":p[0], "volume_size":p[1], "iopattern":p[2],
            "block_size":p[3], "qd":p[4], "rampup":p[5], 
            "runtime":p[6], "vdisk":p[7]
        }
        return testcase_dict
