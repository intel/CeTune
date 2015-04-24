from ..benchmark import *

class QemuRbd(Benchmark):
    def __init__(self, testcase):
        super(self.__class__, self).__init__(testcase)
        self.cluster["vclient"] = self.all_conf_data.get("list_vclient")
        self.benchmark["vdisk"] = self.all_conf_data.get("run_file")

        rbd_num_per_client = self.cluster["rbd_num_per_client"]
        self.volume_size = self.all_conf_data.get("volume_size")
        self.instance_list = self.cluster["vclient"]
        self.testjob_distribution(rbd_num_per_client, self.instance_list)

    def prepare_result_dir(self):
        #1. prepare result dir
        self.get_runid()
        vdisk = re.sub(r'/dev/',r'dev-',self.benchmark["vdisk"])
        self.benchmark["section_name"] = "%s-%s-qd%s-%s-%s-%s-%s" % (self.benchmark["iopattern"], self.benchmark["block_size"], self.benchmark["qd"], self.benchmark["volume_size"],self.benchmark["rampup"], self.benchmark["runtime"], vdisk)
        self.benchmark["dirname"] = "%s-%s-%s" % (str(self.runid), str(self.benchmark["instance_number"]), self.benchmark["section_name"])
        self.benchmark["dir"] = "/%s/%s" % (self.cluster["dest_dir"], self.benchmark["dirname"])

        res = common.pdsh(self.cluster["user"],["%s"%(self.cluster["head"])],"test -d %s" % (self.benchmark["dir"]), option = "check_return")
	if not res[1]:
            print common.bcolors.FAIL + "[ERROR]Output DIR %s exists" % (self.benchmark["dir"]) + common.bcolors.ENDC
            sys.exit()
      
	common.pdsh(self.cluster["user"] ,["%s" % (self.cluster["head"])], "mkdir -p %s" % (self.benchmark["dir"]))

    def prepare_images(self):
        user =  self.cluster["user"]
        dest_dir = self.cluster["tmp_dir"]
        controller =  self.cluster["head"]
        rbd_count = len(self.instance_list)
        rbd_size = self.all_conf_data.get("volume_size")
        if rbd_count and rbd_size:
            super(self.__class__, self).create_image(rbd_count, rbd_size, 'rbd')
        else:
            print common.bcolors.FAIL + "[ERROR]need to set rbd_volume_count and volune_size in all.conf" + common.bcolors.ENDC

        #create image xml
        print common.bcolors.OKGREEN + "[LOG]create rbd volume vm attach xml" + common.bcolors.ENDC
        common.pdsh(user, [controller], "cd %s/vm-scripts; echo 3 | bash create-volume.sh create_disk_xml" % (self.pwd), "check_return")
        print common.bcolors.OKGREEN + "[LOG]Distribute vdbs xml" + common.bcolors.ENDC
        for client in self.cluster["testjob_distribution"]:
            common.scp(user, client, "../vm-scripts/vdbs", dest_dir)

        #attach to vm
        self.attach_images()

        #start to init 
        fio_job_num_total = 0
        nodes = []
        for client in self.cluster["testjob_distribution"]:
            vclients = self.cluster["testjob_distribution"][client]
            for vclient in vclients:
                common.scp(user, vclient, "../conf/fio_init.conf", dest_dir)
                common.pdsh(user, [vclient], "fio --output %s/`hostname`_fio.txt --section init-write-vdb %s/fio_init.conf > /dev/null" % (dest_dir, dest_dir), option = "force")
            fio_job_num_total += len(self.cluster["testjob_distribution"][client])
            nodes.extend(vclients)
        time.sleep(1)
        if not self.check_fio_pgrep(nodes, fio_job_num_total):
            print common.bcolors.FAIL + "[ERROR]Failed to start FIO process" + common.bcolors.ENDC
            common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
            raise KeyboardInterrupt
        if not fio_job_num_total:
            print common.bcolors.FAIL + "[ERROR]Planed to run 0 Fio Job, please check all.conf" + common.bcolors.ENDC
            raise KeyboardInterrupt
        print common.bcolors.OKGREEN + "[LOG]FIO Jobs starts on %s" % (nodes) + common.bcolors.ENDC

        print common.bcolors.OKGREEN + "[LOG]Wait rbd initialization stop" + common.bcolors.ENDC
        #wait fio finish
        try:
            while self.check_fio_pgrep(nodes):
                time.sleep(5)
        except KeyboardInterrupt:
            common.pdsh(user, nodes, "killall -9 fio", option = "check_return")
        print common.bcolors.OKGREEN + "[LOG]rbd initialization finished" + common.bcolors.ENDC

    def prerun_check(self):
        #1. check is vclient alive
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        planed_space = str(len(self.instance_list) * int(self.volume_size)) + "MB"
        print common.bcolors.OKGREEN + "[LOG]Prerun_check: check if rbd volume be intialized" + common.bcolors.ENDC
        if not self.check_rbd_init_completed(planed_space):
            print common.bcolors.WARNING + "[WARN]rbd volume initialization has not be done" + common.bcolors.ENDC
            self.prepare_images()

        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            print common.bcolors.OKGREEN + "[LOG]Prerun_check: check if fio installed in vclient" + common.bcolors.ENDC
            common.pdsh(user, nodes, "fio -v")
            print common.bcolors.OKGREEN + "[LOG]Prerun_check: check if rbd volume attached" + common.bcolors.ENDC
            stdout, stderr = common.pdsh(user, nodes, "df %s" % vdisk, option="check_return")
            if stderr:
                common.bcolors.WARNING + "[WARN]vclients are not attached with rbd volume" + common.bcolors.ENDC
                self.attach_images()
                common.bcolors.WARNING + "[WARN]vclients attached rbd volume now" + common.bcolors.ENDC
            print common.bcolors.OKGREEN + "[LOG]Prerun_check: check if sysstat installed" + common.bcolors.ENDC
            common.pdsh(user, nodes, "mpstat")

    def attach_images(self):
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        dest_dir = self.cluster["tmp_dir"]
        #for client in self.cluster["testjob_distribution"]:
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            for node in nodes:
                print common.bcolors.OKGREEN + "[LOG]Attach rbd image to %s" % node + common.bcolors.ENDC
                stdout, stderr = common.pdsh(user, [node], "df %s" % vdisk, option="check_return")
                if stderr:
                   common.pdsh(user, [client], "cd %s/vdbs; virsh attach-device %s %s.xml" % (dest_dir, node, node))

    def detach_images(self):
        user = self.cluster["user"]
        vdisk = self.benchmark["vdisk"]
        tmp_vdisk = re.search('/dev/(\w+)',vdisk)
        vdisk_suffix = tmp_vdisk.group(1)
        #for client in self.cluster["testjob_distribution"]:
        for client in self.benchmark["distribution"]:
            nodes = self.benchmark["distribution"][client]
            for node in nodes:
                print common.bcolors.OKGREEN + "[LOG]Detach rbd image from %s" % node + common.bcolors.ENDC
                stdout, stderr = common.pdsh(user, [node], "df %s" % vdisk, option="check_return")
                if not stderr:
                   common.pdsh(user, [client], "virsh detach-disk %s %s" % (node, vdisk_suffix))

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

        fio_job_num_total = 0
        for node in nodes:
            common.pdsh(user, [node], "fio --output %s/`hostname`_fio.txt --section %s %s/fio.conf > /dev/null" % (dest_dir, self.benchmark["section_name"], dest_dir), option = "force")
            fio_job_num_total += 1

        time.sleep(1)
        if not self.check_fio_pgrep(nodes, fio_job_num_total):
            print common.bcolors.FAIL + "[ERROR]Failed to start FIO process" + common.bcolors.ENDC
            raise KeyboardInterrupt
        if not fio_job_num_total:
            print common.bcolors.FAIL + "[ERROR]Planned to start 0 FIO process, seems to be an error" + common.bcolors.ENDC
            raise KeyboardInterrupt
        
        print common.bcolors.OKGREEN + "[LOG]FIO Jobs starts on %s" % str(nodes) + common.bcolors.ENDC
        while self.check_fio_pgrep(nodes):
            time.sleep(5)
        
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
        print common.bcolors.OKGREEN + "[LOG]Prepare_run: distribute fio.conf to vclient" + common.bcolors.ENDC
        for client in self.benchmark["distribution"]:
            for vclient in self.benchmark["distribution"][client]:
                common.scp(user, vclient, "../conf/fio.conf", self.cluster["tmp_dir"])
        self.cleanup()
    
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
            common.pdsh(user, nodes, "killall -9 dd", option = "check_return")
        print common.bcolors.OKGREEN + "[LOG]Workload stopped, detaching rbd volume from vclient" + common.bcolors.ENDC
        try:
            self.detach_images()
        except KeyboardInterrupt:
            print common.bcolors.WARNING + "[WARN]Caught KeyboardInterrupt, stop detaching" + common.bcolors.ENDC

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
