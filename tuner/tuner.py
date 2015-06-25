import os,sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import common
from deploy import deploy
from benchmarking import *
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
        self.cluster["osd_daemon_num"] = 0
        for osd in self.cluster["osds"]:
            self.cluster[osd] = []
            for osd_journal in common.get_list( self.all_conf_data.get_list(osd) ):
                self.cluster["osd_daemon_num"] += 1
                self.cluster[osd].append( osd_journal[0] )

    def default_all_conf(self):
        self.cluster = {}
        self.cluster["user"] = self.all_conf_data.get("user")

    def run(self):
        user = self.cluster["user"] 
        controller = self.cluster["head"] 
        osds = self.cluster["osds"] 
        pwd = os.path.abspath(os.path.join('..'))
        for section in self.worksheet:
            for work in self.worksheet[section]['workstages']:
                if work == "deploy":
                    common.printout("LOG","Check ceph version, reinstall ceph if necessary")
                    self.apply_version(section)
                    sys.exit()
                    self.apply_tuning(section, no_check=True)
                    common.printout("LOG","Start to redeploy ceph")
                    deploy.main(['redeploy'])
                elif work == "benchmark":
                    common.printout("LOG","start to run performance test")
                    self.apply_tuning(section)
                    if 'benchmark_engine' in self.worksheet[section]:
                        engine = self.worksheet[section]['benchmark_engine']
                    else:
                        engine = 'fiorbd' 
                    run_cases.main(['--tuning', section, engine])
                else:
                    common.printout("ERROR","Unknown tuner workstage %s" % work)

    def handle_disk(self, option="get", param={'read_ahead_kb':2048, 'max_sectors_kb':512, 'scheduler':'deadline'}, fs_params=""):
        user = self.cluster["user"] 
        osds = self.cluster["osds"] 

        disk_data = {}
        disk_data = common.MergableDict()
        if option == "get":
            for osd in osds:
               for device in self.cluster[osd]:
                   tmp = {}
                   for key, value in param.items():
                       stdout, stderr = common.pdsh(user, [osd], 'echo %s | cut -d"/" -f 3 | sed "s/[0-9]$//" | xargs -I{}  sh -c "cat /sys/block/\'{}\'/queue/%s"' % (device, key), option="check_return")
                       res = common.format_pdsh_return(stdout)
                       tmp[key] = res[osd]
                   stdout, stderr = common.pdsh(user, [osd], 'xfs_info %s' % (device), option="check_return")
                   res = common.format_pdsh_return(stdout)
                   tmp['xfs_info'] = res[osd]
                   disk_data.update(tmp)
                   if option == "get":
                       break
            return disk_data.get()

        if option == "set":
           for osd in osds:
               for device in self.cluster[osd]:
                   for key, value in param.items():
                       stdout, stderr = common.pdsh(user, [osd], 'echo %s | cut -d"/" -f 3 | sed "s/[0-9]$//" | xargs -I{}  sh -c "echo %s > /sys/block/\'{}\'/queue/%s"' % (device, str(value), key), option="check_return")

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
        for node, res in osd_version.items():
            raw_res = res.split()
            version = raw_res[2]
            ceph_version.update(version)
        for node, res in rbd_version.items():
            raw_res = res.split()
            version = raw_res[2]
            ceph_version.update(version)
        for node, res in rados_version.items():
            raw_res = res.split()
            version = raw_res[2]
            ceph_version.update(version)
        return ceph_version.get()

    def get_osd_config(self):
        user = self.cluster["user"] 
        osds = self.cluster["osds"] 

        stdout, stderr = common.pdsh(user, osds, 'path=`find /var/run/ceph -name "*osd*asok" | head -1`; ceph --admin-daemon $path config show', option="check_return") 
        res = common.format_pdsh_return(stdout)
        # merge config diff
        osd_config = common.MergableDict()
        for node in res:
            osd_config.update(res[node])
        return osd_config.get()

    def get_mon_config(self):
        user = self.cluster["user"] 
        mons = self.cluster["mons"] 

        stdout, stderr = common.pdsh(user, mons, 'path=`find /var/run/ceph -name "*mon*asok" | head -1`; ceph --admin-daemon $path config show', option="check_return") 
        res = common.format_pdsh_return(stdout)
        mon_config = common.MergableDict()
        for node in res:
            mon_config.update(res[node])
        return mon_config.get()

    def get_pool_config(self):
        user = self.cluster["user"] 
        controller = self.cluster["head"] 

        stdout, stderr = common.pdsh(user, [controller], 'ceph osd dump | grep pool', option="check_return") 
        res = common.format_pdsh_return(stdout)
        pool_config = {}
        for node in res:
            res_pool = res[node].split('\n')
            for pooldata in res_pool:
                raw_res = pooldata.split()
                name = raw_res[2].replace("'","")
                pool_config[name] = {}
                for index in range(4, len(raw_res),2):
                    pool_config[name][raw_res[index]] = raw_res[index+1]
        return pool_config

    def dump_config(self):
    # check ceph config and os config meet request
        user = self.cluster["user"] 
        controller = self.cluster["head"] 
        mons = self.cluster["mons"] 
        osds = self.cluster["osds"] 
        clients = self.cluster["client"] 

        config = {}
        #get [system] config
        config["disk"] = self.handle_disk(option="get")

        #get [ceph version]
        #config['version'] = self.get_version()

        #get [osd] asok config diff
        #get [mon] asok config diff
        config['global'] = self.get_osd_config()
        config['global'].update(self.get_mon_config())

        #get [pool] information
        config['pool'] = self.get_pool_config()

        return config

    def apply_version(self, jobname):
        user = self.cluster["user"] 
        controller = self.cluster["head"] 
        pwd = os.path.abspath(os.path.join('..'))
        cur_version = self.get_version()
        version_map = {'0.61':'cuttlefish','0.67':'dumpling','0.72':'emperor','0.80':'firefly','0.87':'giant','0.94':'hammer'}
        if 'version' in self.worksheet[jobname]:
            planed_version = self.worksheet[jobname]['version']
        else:
            return
        if not cur_version == {}:
            current_version_group = re.search('(\d+.\d+).\d',cur_version)
            current_version = current_version_group.group(1)
            version_match = False
            if 'version' in self.worksheet[jobname]:
                if current_version in version_map:
                    version_match = ( version_map[current_version] == planed_version )
            else:
                version_match = True
        else:
            version_match = False
        if not version_match:
            common.printout("LOG","Current ceph version not match testjob version, need reinstall")
            deploy.main(['uninstall_binary'])
            deploy.main(['install_binary', '--version', planed_version])

    def check_tuning(self, jobname):
        if not self.cur_tuning:
            self.cur_tuning = self.dump_config()
        tuning_diff = []
        for key in self.worksheet[jobname]:
            tuning = self.worksheet[jobname][key]
            if key in ['workstages', 'benchmark_engine']:
                continue
            if key in ["osd","mon"]:
                key = "global"
            if key in self.cur_tuning:
                res = common.check_if_adict_contains_bdict(self.cur_tuning[key], tuning)
                if not res:
                    tuning_diff.append(key)
            else:
                tuning_diff.append(key)
        for key in tuning_diff:
            common.printout("LOG","Tuning[%s] is not same with current configuration" % (key))
        return tuning_diff

    def apply_tuning(self, jobname, no_check = False):
        #check the diff between worksheet tuning and cur system
        if not no_check:
            common.printout("LOG","Calculate Difference between Current Ceph Cluster Configuration with tuning")
            tmp_tuning_diff = self.check_tuning(jobname)
        else:
            tmp_tuning_diff = ['global']
        for tuning_key in tmp_tuning_diff:
            if tuning_key == 'pool':
                pool_exist = False
                new_poolname = self.worksheet[jobname]['pool'].keys()[0]
                if 'size' in self.worksheet[jobname]['pool'][new_poolname]:
                    replica_size = self.worksheet[jobname]['pool'][new_poolname]['size']
                else:
                    replica_size = 2
                if 'pg_num' not in self.worksheet[jobname]['pool'][new_poolname]:
                    new_pool_pg_num = 100 * self.cluster["osd_daemon_num"]/replica_size
                else:
                    new_pool_pg_num = self.worksheet[jobname]['pool'][new_poolname]['pg_num']
                for cur_tuning_poolname in self.cur_tuning['pool'].keys():
                    if cur_tuning_poolname != new_poolname:
                        self.handle_pool(option = 'delete', param = {'name':cur_tuning_poolname})
                    else:
                        if self.cur_tuning['pool'][cur_tuning_poolname]['pg_num'] != new_pool_pg_num:
                            self.handle_pool(option = 'delete', param = {'name':cur_tuning_poolname})
                        else:
                            pool_exist = True
                if not pool_exist:
                    self.handle_pool(option = 'create', param = {'name':new_poolname, 'pg_num':new_pool_pg_num})
                #after create pool, check pool param
                latest_pool_config = self.get_pool_config()
                for param in self.worksheet[jobname]['pool'][new_poolname]:
                    if param == 'pg_num' or param not in latest_pool_config[new_poolname]:
                        continue
                    if self.worksheet[jobname]['pool'][new_poolname][param] != latest_pool_config[new_poolname][param]:
                        self.handle_pool(option = 'set', param = {'name':new_poolname, param:self.worksheet[jobname]['pool'][new_poolname][param]})
            if tuning_key == 'global':
                tuning = {}
                for section_name, section in self.worksheet[jobname].items():
                    if section_name in ["version","workstages","pool","benchmark_engine"]:
                        continue
                    tuning[section_name] = section
                common.printout("LOG","Apply osd and mon tuning to ceph.conf")
                deploy.main(['--config', str(tuning), 'gen_cephconf'])
                common.printout("LOG","Distribute ceph.conf")
                deploy.main(['distribute_conf'])
                if not no_check:
                    common.printout("LOG","Restart ceph cluster")
                    deploy.main(['restart'])
            if tuning_key == 'disk':
                param = {}
                for param_name, param_data in self.worksheet[jobname]['disk'].items():
                    param[param_name] = param_data
                if param != {}:
                    self.handle_disk( option="set", param=param ) 
                else:
                    self.handle_disk( option="set" ) 

        if no_check:
            return

        #wait ceph health to be OK       
        waitcount = 0
        try:
            while not self.check_health() and waitcount < 300:
                common.printout("WARNING","Applied tuning, waiting ceph to be healthy")
                time.sleep(3)
                waitcount += 3
        except:
            common.printout("WARNING","Caught KeyboardInterrupt, exit")
            sys.exit()
        if waitcount < 300:
            common.printout("LOG","Tuning has applied to ceph cluster, ceph is Healthy now")
        else:
            common.printout("ERROR","ceph is unHealthy after 300sec waiting, please fix the issue manually")
            sys.exit()

    def handle_pool(self, option="set", param = {}):
        user = self.cluster["user"] 
        controller = self.cluster["head"] 
        if option == "create":
            if 'name' in param and 'pg_num' in param:
                common.printout("LOG","create ceph pool %s, pg_num is %s" % (param['name'], str(param['pg_num'])))
                common.pdsh(user, [controller], "ceph osd pool create %s %s %s" % (param['name'], str(param['pg_num']), str(param['pg_num'])),option="check_return")

        if option == "set":
            if 'name' in param:
                for key, value in param.items():
                    if key == 'name':
                        continue
                    common.printout("LOG","set ceph pool %s, %s to %s" % (param['name'], key, str(value)))
                    common.pdsh(user, [controller], "ceph osd pool set %s %s %s" % (param['name'], key, str(value)), option="check_return")

        if option == "delete":
            if 'name' in param:
                pool = param['name']
                common.printout("LOG","delete ceph pool %s" % pool)
                common.pdsh(user, [controller], "ceph osd pool delete %s %s --yes-i-really-really-mean-it" % (pool, pool), option="check_return")
         
        if option == "delete_all":
            cur_pools = get_pool_config()
            for pool in cur_pools:
                common.printout("LOG","delete ceph pool %s" % pool)
                common.pdsh(user, [controller], "ceph osd pool delete %s %s --yes-i-really-really-mean-it" % (pool, pool), option="check_return")
        
    def check_health(self):
        user = self.cluster["user"] 
        controller = self.cluster["head"] 
        check_count = 0
        stdout, stderr = common.pdsh(user, [controller], 'ceph health', option="check_return")
        if "HEALTH_OK" in stdout:
            return True
        else:
            return False

tuner = Tuner()
tuner.run()
