import os,sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import *
from deploy import *
import os, sys
import time
import pprint
import re
import json
import argparse
import threading

pp = pprint.PrettyPrinter(indent=4)
class Tuner:
    def __init__(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        self.cur_tuning = {}
        self.all_conf_data = config.Config("../conf/all.conf")
        self.worksheet = common.load_yaml_conf("../conf/tuner.yaml")
        self.cluster = {}
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["client"] = self.all_conf_data.get_list("list_client")
        self.cluster["osds"] = self.all_conf_data.get_list("list_server")
        self.cluster["mons"] = self.all_conf_data.get_list("list_mon")
        self.cluster["rgw"] = self.all_conf_data.get_list("rgw_server")
        self.cluster["rgw_enable"] = self.all_conf_data.get("enable_rgw")
        self.cluster["disable_tuning_check"] = self.all_conf_data.get("disable_tuning_check")
        self.cluster["osd_daemon_num"] = 0
        for osd in self.cluster["osds"]:
            self.cluster[osd] = []
            for osd_journal in common.get_list( self.all_conf_data.get_list(osd) ):
                self.cluster["osd_daemon_num"] += 1
                self.cluster[osd].append( osd_journal[0] )
                if osd_journal[1] not in self.cluster[osd]:
                    self.cluster[osd].append( osd_journal[1] )

    def default_all_conf(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        self.cluster = {}
        self.cluster["user"] = self.all_conf_data.get("user")

    def handle_disk(self, option="get", param={'read_ahead_kb':2048, 'max_sectors_kb':512, 'scheduler':'deadline'}, fs_params=""):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        osds = self.cluster["osds"]

        disk_data = {}
        disk_data = common.MergableDict()
        if option == "get":
            for osd in osds:
               for device in self.cluster[osd]:
                   parsed_device_name = common.parse_device_name(device)
                   tmp = {}
                   for key, value in param.items():
                       stdout, stderr = common.pdsh(user, [osd], 'sh -c "cat /sys/block/%s/queue/%s"' % (parsed_device_name, key), option="check_return")
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
                   parsed_device_name = common.parse_device_name(device)
                   for key, value in param.items():
                       stdout, stderr = common.pdsh(user, [osd], 'sh -c "echo %s > /sys/block/%s/queue/%s"' % (str(value), parsed_device_name, key), option="check_return")

    def get_version(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        osds = self.cluster["osds"]
        clients = self.cluster["client"]

        version_dict = {}
        stdout, stderr = common.pdsh(user, osds, 'ceph -v', option="check_return")
        res = common.format_pdsh_return(stdout)
        version_dict["osd_version"] = res
        stdout, stderr = common.pdsh(user, clients, 'rbd -v', option="check_return")
        res = common.format_pdsh_return(stdout)
        version_dict["rbd_version"] = res
        stdout, stderr = common.pdsh(user, clients, 'rados -v', option="check_return")
        res = common.format_pdsh_return(stdout)
        version_dict["rados_version"] = res

        # merge config diff
        ceph_version = common.MergableDict()
        for node in osds:
            version_type = "osd_version"
            if node in version_dict[version_type]:
                res = version_dict[version_type][node]
                raw_res = res.split()
                version = raw_res[2]
            else:
                version = "" 
            ceph_version.update(version)
        for node in clients:
            for version_type in ["rbd_version", "rados_version"]:
                if node in version_dict[version_type]:
                    res = version_dict[version_type][node]
                    raw_res = res.split()
                    version = raw_res[2]
                else:
                    print version_type
                    version = "" 
                ceph_version.update(version)
        return ceph_version.get()

    def get_osd_config(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        osds = self.cluster["osds"]

        stdout, stderr = common.pdsh(user, osds, 'path=`find /var/run/ceph -name "*osd*asok" | head -1`; timeout 5 ceph --admin-daemon $path config show', option="check_return",loglevel="LVL6")
        res = common.format_pdsh_return(stdout)
        # merge config diff
        osd_config = common.MergableDict()
        for node in res:
            osd_config.update(res[node])
        return osd_config.get()

    def get_mon_config(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        mons = self.cluster["mons"]

        stdout, stderr = common.pdsh(user, mons, 'path=`find /var/run/ceph -name "*mon*asok" | head -1`; timeout 5 ceph --admin-daemon $path config show', option="check_return",loglevel="LVL6")
        res = common.format_pdsh_return(stdout)
        mon_config = common.MergableDict()
        for node in res:
            mon_config.update(res[node])
        return mon_config.get()

    def get_pool_config(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        controller = self.cluster["head"]

        stdout, stderr = common.pdsh(user, [controller], 'timeout 5 ceph osd dump | grep pool', option="check_return")
        res = common.format_pdsh_return(stdout)
        pool_config = {}
        for node in res:
            res_pool = res[node].split('\n')
            for pooldata in res_pool:
                raw_res = pooldata.split()
                name = raw_res[2].replace("'","")
                pool_config[name] = {}
                for index in range(4, len(raw_res),2):
                    try:
                        pool_config[name][raw_res[index]] = raw_res[index+1]
                    except Exception,e:
                        common.printout("LOG","<CLASS_NAME:%s> <FUN_NAME : %s> ERR_MSG:%s"%(self.__class__.__name__,sys._getframe().f_code.co_name,e),log_level="LVL2")
                        pass
        return pool_config

    def dump_config(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
    # check ceph config and os config meet request
        user = self.cluster["user"]
        controller = self.cluster["head"]
        mons = self.cluster["mons"]
        osds = self.cluster["osds"]
        clients = self.cluster["client"]

        config = {}
        #get [system] config
        try:
            config["disk"] = self.handle_disk(option="get")
        except Exception,e:
            common.printout("LOG","<CLASS_NAME:%s> <FUN_NAME : %s> ERR_MSG:%s"%(self.__class__.__name__,sys._getframe().f_code.co_name,e),log_level="LVL2")
            pass

        #get [ceph version]
        #config['version'] = self.get_version()

        #get [osd] asok config diff
        #get [mon] asok config diff
        config['osd'] = self.get_osd_config()
        config['mon'] = self.get_mon_config()

        #get [pool] information
        config['pool'] = self.get_pool_config()

        return config

    def apply_version(self, jobname):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        controller = self.cluster["head"]
        pwd = os.path.abspath(os.path.join('..'))
        cur_version = self.get_version()
        version_map = {'0.61':'cuttlefish','0.67':'dumpling','0.72':'emperor','0.80':'firefly','0.87':'giant','0.94':'hammer','9.1':'infernalis','9.2':'infernalis','10.2':'jewel'}
        if 'version' in self.worksheet[jobname]:
            planed_version = self.worksheet[jobname]['version']
        else:
            return
        if not cur_version == {}:
            if not isinstance(cur_version, list):
                cur_version = [cur_version]
            for cur_version_tmp in cur_version:
                current_version_group = re.search('(\d+.\d+).\d',cur_version_tmp)
                if not current_version_group:
                    version_match = False
                    break
                current_version = current_version_group.group(1)
                version_match = False
                if 'version' in self.worksheet[jobname]:
                    if current_version in version_map:
                        version_match = ( version_map[current_version] == planed_version )
                else:
                    version_match = True
                if not version_match:
                    break
        else:
            version_match = False
        if not version_match:
            common.printout("LOG","Current ceph version not match testjob version, need reinstall")
            run_deploy.main(['install_binary', '--version', planed_version])

    def check_tuning(self, jobname):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        if not self.cur_tuning:
            self.cur_tuning = self.dump_config()
        tuning_diff = []
        key_list = {}
        for key in self.worksheet[jobname]:
            if key == "global":
                key_list["osd"] = "try"
                key_list["mon"] = "try"
            elif key not in ['workstages', 'benchmark_engine']:
                key_list[key] = key
        try_count = 0
        if not len(key_list.keys()):
            tuning_diff.append("global")
        for key in key_list.keys():
            if key_list[key] == 'try':
                tuning = self.worksheet[jobname]["global"]
            else:
                tuning = self.worksheet[jobname][key]
            if key in self.cur_tuning:
                res = common.check_if_adict_contains_bdict(self.cur_tuning[key], tuning)
                if not res and key not in tuning_diff:
                    if key_list[key] != "try":
                        tuning_diff.append(key)
                    else:
                        try_count += 1
            else:
                tuning_diff.append(key)
            if try_count >= 1:
                tuning_diff.append("global")
        tuning_diff_unique = []
        for key in tuning_diff:
            if key not in tuning_diff_unique:
                tuning_diff_unique.append(key)
                common.printout("LOG","Tuning[%s] is not same with current configuration" % (key))
        return tuning_diff

    def apply_tuning(self, jobname, no_check = False):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        #check the diff between worksheet tuning and cur system
        if not no_check:
            common.printout("LOG","Calculate Difference between Current Ceph Cluster Configuration with tuning")
            tmp_tuning_diff = self.check_tuning(jobname)
        else:
            tmp_tuning_diff = ['global']

        if 'disk' in tmp_tuning_diff:
            param = {}
            for param_name, param_data in self.worksheet[jobname]['disk'].items():
                param[param_name] = param_data
            try:
                if param != {}:
                    self.handle_disk( option="set", param=param )
                else:
                    self.handle_disk( option="set" )
            except Exception,e:
                common.printout("LOG","<CLASS_NAME:%s> <FUN_NAME : %s> ERR_MSG:%s"%(self.__class__.__name__,sys._getframe().f_code.co_name,e),log_level="LVL2")
                pass
        if 'global' in tmp_tuning_diff or 'osd' in tmp_tuning_diff or 'mon' in tmp_tuning_diff:
            if self.cluster["rgw_enable"]=="true" and len(self.cluster["rgw"]):
                with_rgw = True
            else:
                with_rgw = False
            tuning = {}
            for section_name, section in self.worksheet[jobname].items():
                if section_name in ["version","workstages","pool","benchmark_engine"]:
                    continue
                tuning[section_name] = section
            common.printout("LOG","Apply osd and mon tuning to ceph.conf")
            if with_rgw:
                run_deploy.main(['--config', json.dumps(tuning), '--with_rgw',  'gen_cephconf'])
            else:
                run_deploy.main(['--config', json.dumps(tuning), 'gen_cephconf'])
            common.printout("LOG","Distribute ceph.conf")
            if with_rgw:
                run_deploy.main(['--with_rgw','distribute_conf'])
            else:
                run_deploy.main(['distribute_conf'])
            if not no_check:
                common.printout("LOG","Restart ceph cluster")
                if with_rgw:
                    run_deploy.main(['--with_rgw','restart'])
                else:
                    run_deploy.main(['restart'])
        if 'pool' in tmp_tuning_diff:
            pool_exist = False
            new_poolname = self.worksheet[jobname]['pool'].keys()[0]
            if 'size' in self.worksheet[jobname]['pool'][new_poolname]:
                replica_size = int(self.worksheet[jobname]['pool'][new_poolname]['size'])
            else:
                replica_size = 2
            if 'pg_num' not in self.worksheet[jobname]['pool'][new_poolname]:
                new_pool_pg_num = 100 * self.cluster["osd_daemon_num"]/replica_size
            else:
                new_pool_pg_num = self.worksheet[jobname]['pool'][new_poolname]['pg_num']
            for cur_tuning_poolname in self.cur_tuning['pool'].keys():
                if cur_tuning_poolname != new_poolname:
#                        self.handle_pool(option = 'delete', param = {'name':cur_tuning_poolname})
                    continue
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

        if no_check:
            return

        user = self.cluster["user"]
        controller = self.cluster["head"]
        common.wait_ceph_to_health( user, controller )

    def handle_pool(self, option="set", param = {}):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
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

def main(args):
    print args
    tuner_parser = argparse.ArgumentParser(description='Tuner.')
    tuner_parser.add_argument(
        'operation',
    )
    tuner_parser.add_argument(
        '--section',
    )
    tuner_parser.add_argument(
        '--no_check',
        default = False,
        action = 'store_true'
    )
    args = tuner_parser.parse_args(args)
    tuner = Tuner()
    if args.operation == "apply_tuning":
        tuner.apply_tuning( args.section, args.no_check )
    if args.operation == "apply_version":
        tuner.apply_version( args.section )

if __name__ == '__main__':
    import sys
    main( sys.argv[1:] )
#tuner.apply_tuning('testjob1')
