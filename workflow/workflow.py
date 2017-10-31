import os,sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import *
from deploy import *
from benchmarking import *
from tuner import *
import os, sys
import time
import pprint
import re
import json
import argparse
import threading

pp = pprint.PrettyPrinter(indent=4)
class Workflow:
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

    def run(self):
        common.printout("LOG","<CLASS_NAME:%s> Test start running function : %s"%(self.__class__.__name__,sys._getframe().f_code.co_name),screen=False,log_level="LVL4")
        user = self.cluster["user"]
        controller = self.cluster["head"]
        osds = self.cluster["osds"]
        pwd = os.path.abspath(os.path.join('..'))
        if len(self.cluster["rgw"]) and self.cluster["rgw_enable"]=="true":
            with_rgw = True
        else:
            with_rgw = False
        for section in self.worksheet:
            for work in self.worksheet[section]['workstages'].split(','):
                if work == "deploy":
                    common.printout("LOG","Check ceph version, reinstall ceph if necessary")
                    tuner.main(['--section', section, 'apply_version'])
                    tuner.main(['--section', section, '--no_check', 'apply_tuning'])
                    common.printout("LOG","Start to redeploy ceph")
                    if with_rgw:
                        run_deploy.main(['--with_rgw','redeploy'])
                    else:
                        run_deploy.main(['redeploy'])
                    tuner.main(['--section', section, 'apply_tuning'])
                elif work == "benchmark":
                    if not common.check_ceph_running( user, controller ):
                        run_deploy.main(['restart'])
                    common.printout("LOG","start to run performance test")
                    if self.cluster["disable_tuning_check"] not in ["true", "True", "TRUE"]:
                        tuner.main(['--section', section, 'apply_tuning'])
                        time.sleep(3)
                    run_cases.main(['--tuning', section])
                else:
                    common.printout("ERROR","Unknown tuner workstage %s" % work,log_level="LVL1")

def main(args):
    parser = argparse.ArgumentParser(description='workflow')
    parser.add_argument(
        '--by_thread',
        default = False,
        action = 'store_true'
        )
    args = parser.parse_args(args)
    workflow = Workflow()
    if args.by_thread:
        print "workflow by thread"
        new_thread = threading.Thread(target=workflow.run, args=())
        new_thread.daemon = True
        new_thread.start()
        return new_thread
    else:
        workflow.run()
        return None

if __name__ == '__main__':
    import sys
    main( sys.argv[1:] )
#tuner.apply_tuning('testjob1')
