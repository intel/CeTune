import os
import sys
import socket
import json
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from collections import OrderedDict
from conf import common
import re
import argparse

class TunerConfig():
    def __init__(self, path):
        try:
            self.tuner = common.load_yaml_conf(path) 
        except:
            self.tuner = OrderedDict()
            self.tuner["testjob1"] = OrderedDict()
        self.path = path
        self.tuner_conf = self.format_tuner_to_all(self.tuner)

    def get_group(self, request_type):
        res = {}
        if request_type in self.tuner_conf:
            #for key, value in self.tuner_conf[request_type].items():
                #res.append({"key":key,"value":value,"check":True,"dsc":""})
            res = self.tuner_conf[request_type]
        return res

    def set_config(self, key, value, option="update"):
        level_list = ["testjob1"]
        level_list.extend(key.split('|'))
        current = self.tuner
        for level in level_list[:-1]:
            if level not in current:
                current[level] = OrderedDict()
            current = current[level]
        if option == "delete":
            del current[level_list[-1]]
        elif option == "update":
            current[level_list[-1]] = value
        with open(self.path,"w") as f:
            f.write(json.dumps(self.tuner, indent=4))
        return True

    def group_list(self):
        group_list = {}
        group_list["workflow"] = ["workstages"]
        group_list["system"] = ["version","disk"]
        group_list["ceph_tuning"] = ["pool","global","osd","mon","client","radosgw"]
        group_list["analyzer"] = ["analyzer"]
        return group_list

    def format_tuner_to_all(self, tuner, key=None):
        group_list = self.group_list()
        if not isinstance( tuner, dict ):
            if isinstance( tuner, list ):
                return [key, tuner]
            else:
                return [key, str(tuner)]
        else:
            output = OrderedDict()
            for child_key in tuner:
                find_in_group = False
                for group in group_list:
                    if child_key in group_list[group]:
                        find_in_group = True
                        if group not in output:
                            output[group] = OrderedDict()
                        current = output[group]
                        new_key = child_key
                        break
                if not find_in_group:
                    current = output
                    if not key:
                        current["jobname"] = child_key
                        new_key = None
                    else:
                        new_key = "%s|%s" % (key, child_key)
                res = self.format_tuner_to_all( tuner[child_key], new_key )
                if isinstance(res, list):
                    current[res[0]]=res[1]
                else:
                   current.update(res)
            return output

class Config():
    def __init__(self, conf_path):
        self.conf_data = OrderedDict()
        self.conf_path = conf_path
        cur_conf_section = self.conf_data
        self.group = OrderedDict()
        cur_group = "global"
        self.group[cur_group] = []
        lines = []
        try:
            with open(conf_path, "r") as f:
                lines = f.readlines()
        except:
            print "can't open %s" % conf_path
        if len(lines) > 0:
            for line in lines:
                if re.search('^#', line):
                    if "======" in line:
                        cur_group_re = re.search('\w+', line)
                        if cur_group_re:
                            cur_group = cur_group_re.group(0)
                        self.group[cur_group] = []
                    continue
                section = re.search('^\[(\w+)\]', line)
                if section:
                    self.conf_data[section.group(1)] = {}
                    cur_conf_section = self.conf_data[section.group(1)]
                else:
                    try:
                        key, value = line.split("=")
                        key = key.strip()
                        value = value.strip()
                        if( value[-1] == '\n' ):
                            value = value[:-1]
                        if value != "":
                            value = value.strip('"')
                        self.group[cur_group].append(key)
                        self.conf_data[key] = value
                        if cur_conf_section != self.conf_data:
                            cur_conf_section[key] = value
                    except:
                        pass

    def dump_to_file(self, output, key=""):
        line_list = []
        group_list = self.get_group_list()
        for request_type in group_list:
            line_list.append("#============%s============" % request_type)
            res = self.get_group( request_type )
            for key, value in res.items():
                if value == "":
                    value = '""'
                line_list.append("%s=%s" % (key, value))
        #print "\n".join(line_list)
        with open(output, 'w') as f:
            f.write( "\n".join(line_list) )

    def set_config(self, request_type, key, value, option="update"):
        if request_type not in self.group:
            self.group[request_type] = []
        
        if option == "delete":
            del self.conf_data[key]
            self.group[request_type].remove(key)
        elif option == "update":
            self.conf_data[key] = value
            if request_type not in self.group:
                self.group[request_type] = []
            if key not in self.group[request_type]:
                self.group[request_type].append(key)

        # check if need add new terms


        self.dump_to_file(self.conf_path)
        return True
    
    def get(self, key, dotry=False):
        if key in self.conf_data:
            return self.conf_data[key]
        else:
            if not dotry:
                common.printout("WARNING","%s not defined in all.conf" % key)
                sys.exit()
            else:
                return ""

    def get_list(self,key):
        if key in self.conf_data:
            if re.search(',', self.conf_data[key]):
                return self.conf_data[key].split(",")
            else:
                return [self.conf_data[key]]
        else:
            print "%s not defined in all.conf" % key
            return []

    def get_all(self):
        return self.conf_data

    def get_group(self, request_type):
        res = OrderedDict()
        if request_type in self.group:
            for key in self.group[request_type]:
                res[key] = self.get(key)
        return res

    def get_group_list(self):
        return self.group

class BenchmarkConfig():
    def __init__(self):
        self.conf_path = "../conf/cases.conf"
        self.default_conf_path = "../conf/cases.default.conf"
 
    def set_config(self, case_json_list):
        testcase_keys = [
            "benchmark_driver","worker", "container_size", "iopattern",
            "op_size", "object_size/QD", "rampup", "runtime", "device"
        ]
        case_list = []
        for tmp_dict in json.loads(case_json_list):
            tmp = []
            for key in testcase_keys:
                tmp.append(tmp_dict[key])
            if tmp not in case_list:
                case_list.append(tmp)
        if len(case_list):
            with open("../conf/cases.conf","w") as f:
                for case_items in case_list:
                    f.write('%8s\t%4s\t%16s\t%8s\t%8s\t%16s\t%8s\t%8s\t%8s\n' % ( case_items[0],case_items[1], case_items[2], case_items[3], case_items[4], case_items[5], case_items[6], case_items[7], case_items[8] ) )
        #run_cases.main(['--option', "gen_case"])
        return False

    def get_config(self):
        testcase_list = []
        try:
            with open(self.conf_path,"r") as f:
                lines = f.readlines()
            for line in lines:
                p = line.split()
                testcase_list.append( self.parse_benchmark_cases( p ) )
        except:    
            common.bash("cp %s %s" % (self.default_conf_path, self.conf_path))
            with open(self.conf_path,"r") as f:
                lines = f.readlines()
            for line in lines:
                p = line.split()
                testcase_list.append( self.parse_benchmark_cases( p ) )
        return testcase_list
        
    def parse_benchmark_cases(self, testcase):
        p = testcase
        testcase_dict = {
            "benchmark_driver":p[0],"worker":p[1], "container_size":p[2], "iopattern":p[3],
            "op_size":p[4], "object_size/QD":p[5], "rampup":p[6], "runtime":p[7], "device":p[8]
        }
        return testcase_dict

def main(args):
    parser = argparse.ArgumentParser(description='debug')
    parser.add_argument(
    'operation'
    )
    args = parser.parse_args(args)
    benchmarkConfig = BenchmarkConfig()
    if args.operation == "set_config":
        testcase_list = [{"rampup": "0", "iopattern": "seqwrite", "op_size": "64k", "object_size/QD": "64", "device": "/dev/vdb", "benchmark_driver": "qemurbd", "runtime": "100", "worker": "20", "container_size": "40g"},
                        {"rampup": "0", "iopattern": "seqread", "op_size": "64k", "object_size/QD": "64", "device": "/dev/vdb", "benchmark_driver": "qemurbd", "runtime": "100", "worker": "20", "container_size": "40g"},
                        {"rampup": "0", "iopattern": "randwrite", "op_size": "4k", "object_size/QD": "4", "device": "/dev/vdb", "benchmark_driver": "qemurbd", "runtime": "100", "worker": "20", "container_size": "40g"},
                        {"rampup": "0", "iopattern": "randread", "op_size": "4k", "object_size/QD": "4", "device": "/dev/vdb", "benchmark_driver": "qemurbd", "runtime": "100", "worker": "20", "container_size": "40g"}
                        ]
        benchmarkConfig.set_config(testcase_list)
    
    if args.operation == "get_case_conf":
        #myconfig = Config("../conf/cases.conf")
        #myconfig.gen_case_conf()
        get_case_conf()

    if args.operation == "check_case_conf":
        #myconfig = Config("../conf/cases.conf")
        #myconfig.check_case_conf()
        benchmarkConfig.check_case_conf()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
