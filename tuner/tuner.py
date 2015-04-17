import os,sys
lib_path = os.path.abspath(os.path.join('../conf/'))
sys.path.append(lib_path)
import common
import os, sys
import time
import pprint
import re

pp = pprint.PrettyPrinter(indent=4)
class Tuner:
    def __init__(self):
        self.cur_tuning = {}
        self.all_conf_data = common.Config("../conf/all.conf")
        self.worksheet = common.load_yaml_conf("../conf/tuner.yaml")
        self.cluster = {}
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["client"] = self.all_conf_data.get_list("list_client")
        self.cluster["osds"] = self.all_conf_data.get_list("list_ceph")
        self.cluster["mons"] = self.all_conf_data.get_list("list_mon") 
        for osd in self.cluster["osds"]:
            self.cluster[osd] = []
            for osd_journal in common.get_list( self.all_conf_data.get_list(osd) ):
                self.cluster[osd].append( osd_journal[0] )
        pp.pprint(self.worksheet)

    def run(self):
        user = self.cluster["user"] 
        controller = self.cluster["head"] 
        osds = self.cluster["osds"] 
        for section in self.worksheet:
            for work in self.worksheet[section][workstages]:
                if work == "install":
                    common.pdsh(user, [controller], "bash deploy-ceph.sh purge")
                    common.pdsh(user, [controller], "bash deploy-ceph.sh install")
                elif work == "deploy":
                    common.pdsh(user, [controller], "bash deploy-ceph.sh redeploy")
                elif work == "benchmark":
                    self.check_tuning(self.worksheet[section])
                    self.apply_tuning(self.worksheet[section])
                    common.pdsh(user, [controller], "bash benchmarking-ceph.sh run")
                else:
                    print common.bcolors.FAIL + "[ERROR] Unknown tuner workstage %s" % work + common.bcolors.ENDC

    def handle_disk(self, option="get", param={'read_ahead_kb':2048, 'max_sectors_kb':512, 'scheduler':'deadline'}, fs_params=""):
        user = self.cluster["user"] 
        osds = self.cluster["osds"] 

        disk_data = {}
        disk_data = common.MergableDict()
        for osd in osds:
           for device in self.cluster[osd]:
               tmp = {}
               for key, value in param.items():
                   if option == "get":
                       stdout, stderr = common.pdsh(user, [osd], 'echo %s | cut -d"/" -f 3 | sed "s/[0-9]$//" | xargs -I{} sudo sh -c "cat /sys/block/\'{}\'/queue/%s"' % (device, key), option="check_return")
                   if option == "set":
                       stdout, stderr = common.pdsh(user, [osd], 'echo %s | cut -d"/" -f 3 | sed "s/[0-9]$//" | xargs -I{} sudo sh -c "echo %s > /sys/block/\'{}\'/queue/%s"' % (device, str(value), key), option="check_return")
                   res = common.format_pdsh_return(stdout)
                   tmp[key] = res[osd]
               stdout, stderr = common.pdsh(user, [osd], 'xfs_info %s' % (device), option="check_return")
               res = common.format_pdsh_return(stdout)
               tmp['xfs_info'] = res[osd]
               disk_data.update(tmp)
               if option == "get":
                   break
        return disk_data.get()

    def get_version(self):
        user = self.cluster["user"] 
        osds = self.cluster["osds"] 
        clients = self.cluster["client"] 

        stdout, stderr = common.pdsh(user, osds, 'ceph -v', option="check_return") 
        res = common.format_pdsh_return(stdout)
        osd_version = res
        stdout, stderr = common.pdsh(user, clients, 'rbd -v', option="check_return") 
        res = common.format_pdsh_return(stdout)
        rbd_version = res
        stdout, stderr = common.pdsh(user, clients, 'rados -v', option="check_return") 
        res = common.format_pdsh_return(stdout)
        rados_version = res
        # merge config diff
        ceph_version = common.MergableDict()
        version = {}
        for node, res in osd_version.items():
            raw_res = res.split()
            version['ceph_version'] = raw_res[2]
            ceph_version.update(version)
        for node, res in rbd_version.items():
            raw_res = res.split()
            version['rbd_version'] = raw_res[2]
            ceph_version.update(version)
        for node, res in rados_version.items():
            raw_res = res.split()
            version['rados_version'] = raw_res[2]
            ceph_version.update(version)
        return ceph_version.get()

    def get_osd_config(self):
        user = self.cluster["user"] 
        osds = self.cluster["osds"] 

        stdout, stderr = common.pdsh(user, osds, 'path=`find /var -name "*osd*asok" | head -1`; ceph --admin-daemon $path config diff', option="check_return") 
        res = common.format_pdsh_return(stdout)
        # merge config diff
        osd_config = common.MergableDict()
        for node in res:
            osd_config.update(res[node]['diff']['current'])
        return osd_config.get()

    def get_mon_config(self):
        user = self.cluster["user"] 
        mons = self.cluster["mons"] 

        stdout, stderr = common.pdsh(user, mons, 'path=`find /var -name "*mon*asok" | head -1`; ceph --admin-daemon $path config diff', option="check_return") 
        res = common.format_pdsh_return(stdout)
        mon_config = common.MergableDict()
        for node in res:
            mon_config.update(res[node]['diff']['current'])
        return mon_config.get()

    def get_pool_config(self):
        user = self.cluster["user"] 
        controller = self.cluster["head"] 

        stdout, stderr = common.pdsh(user, [controller], 'ceph osd dump | grep pool', option="check_return") 
        res = common.format_pdsh_return(stdout)
        pool_config = common.MergableDict()
        for node in res:
            pool = {}
            raw_res = res[node].split()
            name = raw_res[2].replace("'","")
            pool[name] = {}
            for index in range(4, len(raw_res),2):
                pool[name][raw_res[index]] = raw_res[index+1]
            pool_config.update(pool)
        return pool_config.get()

    def dump_config(self):
    # check ceph config and os config meet request
        user = self.cluster["user"] 
        controller = self.cluster["head"] 
        mons = self.cluster["mons"] 
        osds = self.cluster["osds"] 
        clients = self.cluster["client"] 

        config = {}
        #get [system] config
        #config["Disk"] = self.handle_disk(option="get")

        #get [ceph version]
        config['version'] = self.get_version()

        #get [osd] asok config diff
        config['osd'] = self.get_osd_config()

        #get [mon] asok config diff
        config['mon'] = self.get_mon_config()

        #get [pool] information
        config['pool'] = self.get_pool_config()

        return config

    def check_tuning(self, jobname):
        if not self.cur_tuning:
            self.cur_tuning = self.dump_config()
        pp.pprint(self.cur_tuning)
        tuning_diff = []
        for key, tuning in self.worksheet[jobname].items():
            if key in ['workstages', 'benchmark_engine']:
                continue
           # if key in self.cur_tuning:
           #     if not tuning == self.cur_tuning[key]:
           #         print
        return tuning_diff

    def apply_tuning(self, jobname):
    # apply tuning
         #check the diff between worksheet tuning and cur system
         #for tuning_key in self.check_tuning(jobname):
         #    if tuning_key == 
         #do tuning
         #apply osd config
         #apply pool config
         pass        

tuner = Tuner()
tuner.check_tuning('testjob1')
