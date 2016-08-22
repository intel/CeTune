import os
import sys
import socket
import json
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from collections import OrderedDict
from conf import config
from conf import description
import re
import argparse

class ConfigHandler():
    def __init__(self):
        self.all_conf = config.Config("../conf/all.conf")
        self.tuner_conf = config.TunerConfig("../conf/tuner.yaml")
        self.cases_conf = config.BenchmarkConfig()
        self.required_lists = self.list_required_config()
        for request_type in self.required_lists:
            self.get_group( request_type )

    def get_help(self):
        formated_report = {}
        output = []
        #output.append("<table class='help_table_class'>")
        #output.append(" <thead>")
        #output.extend( self.getDescriptionTitle() )
        #output.append(" </thead>")
        dict_desc = description.Description.get_all_description()
        first_char = 'A'
        output.append("</table><p id = 'label_id' class = 'left_style'>------------> A <-----------</p><table class='help_table_class'>")
        output.append(" <thead>")
        output.extend( self.getDescriptionTitle() )
        output.append(" </thead>")
        output.append(" <tbody>")
        for key in dict_desc.keys():
            if str(key)[0].upper() != first_char:
                first_char = str(key)[0].upper()
                output.append("</tbody></table><p id = 'label_id' class = 'left_style'>------------> "+first_char+" <------------</p><tbody><table class='help_table_class'>")
                output.append(" <thead>")
                output.extend( self.getDescriptionTitle() )
                output.append(" </thead>")
            tr_data = " <tr><td class = 'left_style'>"+key+" </td><td id='mid_style'>"+description.DefaultValue.get_defaultvalue_by_key(key)+"</td><td id = 'td_right_id' class='right_style'>"+dict_desc[key]+" </td> </tr>"
            output.append(tr_data)
        output.append(" </tbody></table>")
        output.append("<script>")
        output.append("$('.cetune_table tr').dblclick(function(){var path=$(this).attr('href'); window.location=path})")
        output.append("</script>")
        return "".join(output)

    def getDescriptionTitle(self):
        output = []
        output.append(" <tr>")
        output.append(" <th>Item</th>")
        output.append(" <th>Default Value</th>")
        output.append(" <th>Description</th>")
        output.append(" </tr>")
        return output

    def get_group(self, request_type):
        res = []
        tmp_res = OrderedDict()

        all_conf = self.all_conf.get_group(request_type)
        tmp_res.update( all_conf )

        tuner_conf = self.tuner_conf.get_group(request_type)
        tmp_res.update( tuner_conf )

        if request_type == "testcase":
            cases_conf = self.cases_conf.get_config()
            return cases_conf

        for key, value in tmp_res.items():
	    self.desc = ""
	    if key != "":
		self.desc = description.Description.get_description_by_key(key)
            res.append({"key":key,"value":value,"check":True,"dsc":self.desc})

        if request_type in self.required_lists:
            for required_key in self.required_lists[request_type]:
                 if required_key not in tmp_res:
                     value = self.required_lists[request_type][required_key]
                     res.append({"key":required_key, "value":value, "check":False, "dsc":"please check or complete"})
                     self.set_config(request_type, required_key, value)
        return res

    def set_config(self, request_type, key, value):
        conf_type = self.get_corresponde_config(request_type)
        if conf_type == "tuner":
            res = self.tuner_conf.set_config(key, value)
        elif conf_type == "all":
            res = self.all_conf.set_config(request_type, key, value)
        if conf_type == "cases":
            res = self.cases_conf.set_config(value)
        return res

    def check_testcase(self):
        request_type = "benchmark"
        benchmark_config = self.all_conf.get_group(request_type)
        res = []
        tmp_res = OrderedDict()
        required = OrderedDict()

        #testcase_conf = BenchmarkConfig()
        testcase_list = self.cases_conf.get_config()
        engine_list = []
        for testcase in testcase_list:
            if testcase["benchmark_driver"] not in engine_list:
                required.update( self.check_engine(testcase["benchmark_driver"]) )
            if testcase["description"] != "":
                if testcase["benchmark_driver"] == "hook":
                    required["%s|%s" % (testcase["description"], "custom_script")] = ""
                if testcase["iopattern"] in ["readwrite", "rw", "randrw"]:
                    required["%s|%s" % (testcase["description"], "rwmixread")] = "100"

        for required_key in required:
             if required_key not in benchmark_config.keys():
                 value = required[required_key]
                 res.append({"key":required_key, "value":value, "check":False, "dsc":"please check or complete"})
                 self.set_config(request_type, required_key, value)
        return res

    def check_engine(self, engine):
        required = OrderedDict()
        if engine == "qemurbd":
            required["list_vclient"] = "vclient01,vclient02..."
            required["fio_capping"] = "false"
            required["enable_zipf"] = "false"
            required["fio_randrepeat"] = "false"
            required["volume_size"] = "40960"
            required["rbd_volume_count"] = "1"
            required["disk_num_per_client"] = "35,35,35,35"
            required["rwmixread"] = 100
        if engine == "fiorbd":
            required["fio_capping"] = "false"
            required["enable_zipf"] = "false"
            required["fio_randrepeat"] = "false"
            required["volume_size"] = "40960"
            required["rbd_volume_count"] = "1"
            required["disk_num_per_client"] = "35,35,35,35"
            required["rwmixread"] = 100
        if engine == "cosbench":
            required["cosbench_version"] = "v0.4.2.c2"
            required["cosbench_controller"] = ""
            required["cosbench_driver"] = ""
            required["cosbench_folder"] = "/opt/cosbench"
            required["cosbench_config_dir"] = "/opt/cosbench_config"
            required["cosbench_cluster_ip"] = "10.10.5.5"
            required["cosbench_admin_ip"] = "192.168.5.1"
            required["cosbench_network"] = "192.168.5.0/24"
        if engine == "generic":
            required["test_disks"] = ""
            required["fio_capping"] = "false"
            required["disk_num_per_client"] = "35,35,35,35"
        if engine == "hook":
            required["custom_script"] = ""

        return required

    def del_config(self, request_type, key):
        conf_type = self.get_corresponde_config(request_type)
        if conf_type == "tuner":
            res = self.tuner_conf.set_config(key, "", option="delete")
        elif conf_type == "all":
            res = self.all_conf.set_config(request_type, key, "", option="delete")
        return res

    def get_group_config(self, request_type):
        config_type = self.get_corresponde_conf( request_type )
        if config_type == "tuner":
            res = self.tuner_conf.get_group(request_type)
        elif config_type == "all":
            res = self.all_conf.get_group(request_type)

    def get_corresponde_config(self, request_type):
        key_to_file = {}
        key_to_file["tuner"] = ["workflow","system","ceph_tuning","analyzer"]
        key_to_file["all"] = ["cluster","ceph_hard_config","benchmark"]
        key_to_file["cases"] = ["testcase"]
        for key, value in key_to_file.items():
            if request_type in value:
                return key
        return None

    def check_config_correction(self):
        pass

    def check_required_config(self):
        pass

    def list_required_config(self):
        required_list = {}
        required_list["cluster"] = OrderedDict()
        required_list["cluster"]["clean_build"] = "true"
        required_list["cluster"]["head"] = socket.gethostname()
        required_list["cluster"]["user"] = "root"
        required_list["cluster"]["list_server"] = ""
        required_list["cluster"]["list_client"] = ""
        required_list["cluster"]["list_mon"] = ""
        required_list["cluster"]["enable_rgw"] = "false"
        required_list["cluster"]["disk_format"] = "osd:journal"
        required_list["ceph_hard_config"] = OrderedDict()
        required_list["ceph_hard_config"]["public_network"] = ""
        required_list["ceph_hard_config"]["cluster_network"] = ""
        required_list["ceph_hard_config"]["osd_objectstore"] = "filestore"
        required_list["benchmark"] = OrderedDict()
        required_list["benchmark"]["disable_tuning_check"] = "false"
        required_list["benchmark"]["tmp_dir"]="/opt/"
        required_list["benchmark"]["dest_dir"]="/mnt/data/"
        required_list["benchmark"]["cache_drop_level"]=1
        required_list["benchmark"]["monitoring_interval"]=1
        required_list["benchmark"]["collector"]="blktrace,strace,fatrace,lttng,perfcounter"
        required_list["benchmark"]["perfcounter_data_type"]="osd,filestore"
        required_list["benchmark"]["perfcounter_time_precision_level"]=6

        required_list["workflow"] = OrderedDict()
        required_list["workflow"]["workstages"] = ["deploy","benchmark"]
        required_list["system"] = OrderedDict()
        required_list["system"]["disk|read_ahead_kb"] = 2048
        required_list["ceph_tuning"] = OrderedDict()
        required_list["ceph_tuning"]["pool|rbd|size"] = 2
        required_list["ceph_tuning"]["global|mon_pg_warn_max_per_osd"] = 1000
        required_list["analyzer"] = OrderedDict()
        required_list["analyzer"]["analyzer"] = "all"

        return required_list
        
