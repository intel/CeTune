import os
import sys
import socket
import json
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from collections import OrderedDict
try:
    from conf import common
    from conf import description
except:
    import common 
    import description
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
        config_helper = ConfigHelper()
        return config_helper._check_config(key, value)

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
#                        res = re.search('(\w+)=(.*)', line)
#                        key = res.group(1)
#                        value = res.group(2)
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
                        print "except: %s" % (line)

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
        res = self._set_config(request_type, key, value, option)
        self.dump_to_file(self.conf_path)
        return res

    def _set_config(self, request_type, key, value, option="update"):
        if request_type not in self.group:
            self.group[request_type] = []
        
        if option == "delete":
            del self.conf_data[key]
            self.group[request_type].remove(key)
            return {}

        if option == "update":
            # check if need to add new terms
            res = self.check_config( key, value )
            if not res["check"]:
                return res
    
            # if check is right, then add addition and set_config
            tmp = []
            for add_key, add_value in res["addition"].items():
                if add_key not in self.group[request_type]:
                    tmp.append( self._set_config( request_type, add_key, description.DefaultValue.get_defaultvalue_by_key(add_key), option="update" ) )
            res["addition"] = tmp

            self.conf_data[key] = value
            if value in self.conf_data.keys():
                self.conf_data[value] = description.DefaultValue.get_defaultvalue_by_key(value)
            if request_type not in self.group:
                self.group[request_type] = []
            if key not in self.group[request_type]:
                self.group[request_type].append(key)
        return res
    
    def check_config(self, key, value):
        required = {}
        required["head"] = {"type":"node"}
        required["user"] = {"type":"static:root"}
        required["list_server"] = {"type":"node_list", "addition":"value_to_key"}
        required["osd_journal"] = {"type":"osd_journal_list"}
        required["list_client"] = {"type":"node_list"}
        required["list_mon"] = {"type":"node_list"}
        required["enable_rgw"] = {"if":"true", "type":"bool", "addition":{"rgw_server":"","rgw_start_index":1, "rgw_num_per_server":5, "cosbench_auth_username":"cosbench:operator", "cosbench_auth_password":"intel2012", "cosbench_controller_proxy":""}}
        required["rgw_server"] = {"type":"node_list"}
        required["rgw_num_per_server"] = {"type":"int"}
        required["rgw_start_index"] = {"type":"int"}

        required["public_network"] = {"type": "network"}
        required["cluster_network"] = {"type": "network"}

        required["fio_capping"] = {"type":"bool"}
        required["enable_zipf"] = {"if":"true", "type":"bool", "addition":{"random_distribution":"zipf:1.2"}}
        required["perfcounter_time_precision_level"] = {"type":"int"}
        required["Description"] = {"type":"parameters"}
        required["cosbench_controller"] = {"type":"node_list"}
        required["cosbench_driver"] = {"type":"node_list"}
        required["cosbench_cluster_ip"] = {"type":"ip"}
        required["cosbench_admin_ip"] = {"type":"ip"}
        required["cosbench_network"] = {"type":"network"}
        required["disk_num_per_client"] = {"type":"int_list"}
        required["list_vclient"] = {"type":"node_list"}
        required["monitoring_interval"] = {"type":"int"}
        required["disk_format"] = {"type":"diskformat"}
        required["disable_tuning_check"] = {"type":"bool"}
        required["distributed_data_process"] = {"type":"bool"}

        helper = ConfigHelper()
        if key in required:
            output = helper._check_config( key, value, required[key] )
        elif key in self.get_list("list_server"):
            output = helper._check_config( key, value, required["osd_journal"] )
        else:
            output = helper._check_config( key, value )
        return output

    def get(self, key, dotry=False,loglevel="LVL3"):
        if key in self.conf_data:
            return self.conf_data[key]
        else:
            if not dotry:
                common.printout("WARNING","%s not defined in all.conf" % key,log_level=loglevel)
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
            "op_size", "object_size/QD", "rampup", "runtime", "device", "parameter", "desc","additional_option"
        ]
        case_list = []
        for tmp_dict in json.loads(case_json_list):
            tmp = []
            for key in testcase_keys:
                if tmp_dict[key] == "":
                    tmp_dict[key] = "NULL"
                tmp.append(tmp_dict[key])
            if tmp not in case_list:
                case_list.append(tmp)
        output = ""
        for case_items in case_list:
            output += '%8s\t%4s\t%16s\t%8s\t%8s\t%16s\t%8s\t%8s\t%8s\t%8s\t%s\t%6s\n' % ( case_items[0],case_items[1], case_items[2], case_items[3], case_items[4], case_items[5], case_items[6], case_items[7], case_items[8], case_items[9] ,case_items[10],case_items[11])
        with open("../conf/cases.conf","w") as f:
            f.write( output )
        return False

    def get_config(self):
        testcase_list = []
        try:
            with open(self.conf_path,"r") as f:
                lines = f.readlines()
            for line in lines:
                p = line.split()
                if len(p) != 0 and p!="\n":
                    testcase_list.append( self.parse_benchmark_cases( p ) )
        except:
            common.bash("cp %s %s" % (self.default_conf_path, self.conf_path))
            with open(self.conf_path,"r") as f:
                lines = f.readlines()
            for line in lines:
                p = line.split()
                if len(p) != 0 and p!="\n":
                    testcase_list.append( self.parse_benchmark_cases( p ) )
        return testcase_list

    def parse_benchmark_cases(self, testcase):
        p = testcase
        testcase_dict = {
            "benchmark_driver":p[0],"worker":p[1], "container_size":p[2], "iopattern":p[3],
            "op_size":p[4], "object_size/QD":p[5], "rampup":p[6], "runtime":p[7], "device":p[8]
        }

        if len(p) == 12:
            testcase_dict["parameter"] = p[9]
            testcase_dict["description"] = p[10]
            testcase_dict["additional_option"] = p[11]
        else:
            option_list = ['restart','redeploy']
            if len(p) == 9:
                testcase_dict["parameter"] = ""
                testcase_dict["description"] = ""
                testcase_dict["additional_option"] = ""
            elif len(p) == 10:
                if self.check_parameter_style(p[9]):
                    testcase_dict["parameter"] = p[9]
                    testcase_dict["description"] = ""
                    testcase_dict["additional_option"] = ""
                elif p[9] in option_list:
                    testcase_dict["parameter"] = ""
                    testcase_dict["description"] = ""
                    testcase_dict["additional_option"] = p[9]
                else:
                    testcase_dict["parameter"] = ""
                    testcase_dict["description"] = p[9]
                    testcase_dict["additional_option"] = ""

            elif len(p) == 11:
                if p[10] in option_list:
                    if self.check_parameter_style(p[9]):
                        testcase_dict["parameter"] = p[9]
                        testcase_dict["description"] = ""
                        testcase_dict["additional_option"] = p[10]
                    else:
                        testcase_dict["parameter"] = ""
                        testcase_dict["description"] = p[9]
                        testcase_dict["additional_option"] = p[10]
                else:
                    testcase_dict["parameter"] = p[9]
                    testcase_dict["description"] = p[10]
                    testcase_dict["additional_option"] = ""

        return testcase_dict
    
    def check_parameter_style(self,paras):
        if paras != "":
            for i in paras.split(','):
                if len(i.split('=')) != 2:
                    return False
            return True
        else:
            return False

class ConfigHelper():
    def _check_config( self, key, value, requirement=None):
        output = {}
        output["key"] = key
        output["value"] = value
        output["dsc"] = ""
        if not requirement:
            output["check"] = True
            output["addition"] = {}
            return output
        output["check"], output["dsc"] = self.check_type(key, value, requirement["type"])
        if "addition" not in requirement or ("if" in requirement and requirement["if"] != value):
            output["addition"] = {}
        else:
            output["addition"] = self.addition_eval(requirement["addition"], value)
        return output
    
    def check_type( self, key, value, value_type):
        if value_type == "parameters":
            for i in value.split(","):
                tmp = i.split('=')
                while '' in tmp:
                    tmp.remove('')
                if len(tmp) != 2:
                    return [ False, "value type is invalid !" ]
            return [ True, "" ]
        if value_type == "node_list":
            if not isinstance( value.split(','), list ):
                return [ False, "Value is a %s, format %s" % (value_type, self.type_example(value_type)) ]
            # check if node exists and can be ssh
            error_node = []
            for node in value.split(','):
                if not common.try_ssh(node):
                    error_node.append( node )
            if len(error_node):
                return [ False, "Nodes:%s are not set in /etc/hosts or can't be auto ssh" % error_node ]
            else:
                return [ True, "" ]

        if value_type == "int_list":
            if not isinstance( value.split(','), list ):
                return [ False, "Value is a %s, format %s" % (value_type, "10,10,10,10") ]
            else:
                try:
                    for subdata in value.split(','):
                        int( subdata )
                    return [ True, "" ]
                except:
                    return [ False, "Value is a %s, format %s" % (value_type, "10,10,10,10") ]

        if value_type == "bool":
            if value in ["true", "false"]:
                return [ True, "" ]
            else:
                return [ False, "Value is a %s, format %s" % (value_type, self.type_example(value_type)) ]

        if "static" in value_type:
            static_value = value_type.split(":")[1]
            if value == static_value:
                return [ True, "" ]
            else:
                return [ False, "Value is a static, only can set to be %s" % static_value ]

        if value_type == "int":
            try:
                int(value)
                return [ True, "" ]
            except:
                return [ False, "Value is a %s, format %s" % (value_type, self.type_example(value_type)) ]

        if value_type == "osd_journal_list":
            try:
                error_disk = []
                disk_list = value.split(',')
                print disk_list
                for substr in disk_list:
                    res = common.get_list(substr)[0]
                    if len(res) > 4:
                        raise
                    device_index = 1
                    for device in res:
                        if not common.try_disk(key, device):
                            error_disk.append(device)
                        if device_index == len(res):
                            print "device_%s: %s " % (device_index, device)
                        else:
                            print "device_%s: %s " % (device_index, device),
                        device_index += 1
                if not len(error_disk):
                    return [ True, "" ]
                else:
                    return [ False, "Disks:%s are not exists or it is boot device." % error_disk ]
            except:
                return [ False, "Value is a %s, format %s" % (value_type, self.type_example(value_type)) ]
     
	if value_type == "diskformat":
            try:
                if ',' not in value:
		    return [ True, "" ]
		else:
                    return [ False, "Please use [:] split."]
            except:
                return [ False, "Value is a %s, format %s" % (value_type, self.type_example(value_type)) ]

        if value_type == "network":
            try:
                ip, netmask = value.split('/')
                if int(netmask) < 32 and len(ip.split('.')) == 4:
                    return [ True , "" ]
                else:
                    return [ False, "Value is a %s, format %s" % (value_type, "192.168.5.0/24") ]

            except:
                return [ False, "Value is a %s, format %s" % (value_type, "192.168.5.0/24") ]

        if value_type == "ip":
            try:
                count = 0
                for subip in value.split('.'):
                    count += 1
                    if int(subip) >= 255:
                        return [ False, "Value is a %s, format %s" % (value_type, "192.168.5.1") ]
                if count == 4:
                    return [ True , "" ]
                else:
                    return [ False, "Value is a %s, format %s" % (value_type, "192.168.5.1") ]
            except:
                return [ False, "Value is a %s, format %s" % (value_type, "192.168.5.1") ]

        return [ True, "" ]
    
    def addition_eval( self, requirement, value ):
        if isinstance(requirement, dict):
            return requirement
        if isinstance(requirement, str):
            func = getattr(self, requirement)
            if func:
                return func( value )

    def value_to_key( self, value ):
        output = {}
        for key in value.split(','):
            output[key] = ""
        return output

    def type_example( self, value_type ):
	if value_type == "diskformat":
            return "osd:journal"
        if value_type == "node_list":
            return "node01,node02,node03,..."
        if value_type == "bool":
            return "false/true"
        if value_type == "osd_journal_list":
            return "/dev/hdd1:/dev/ssd1,/dev/hdd2:/dev/ssd2 or number of devices more than 4"

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
