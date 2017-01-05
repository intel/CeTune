# -*- coding: utf-8 -*
import os,sys
import argparse
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
import common as cn
import os, sys
import time
import pprint
import re
import yaml
from collections import OrderedDict
import json
import numpy
import copy
import config
from multiprocessing import Process
import csv

pp = pprint.PrettyPrinter(indent=4)
class Analyzer:
    def __init__(self, dest_dir,name):
        self.common = cn
        self.common.cetune_log_file = name+"-cetune_process.log"
        self.common.cetune_error_file = name+"-cetune_error.log"
        self.common.cetune_console_file= name+"-cetune_console.log"

        self.dest_dir = dest_dir
        self.cluster = {}
        self.cluster["dest_dir"] = dest_dir
        self.cluster["dest_conf_dir"] = dest_dir
        self.cluster["dest_dir_root"] = dest_dir
        self.all_conf_data = config.Config("all.conf") 
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["diskformat"] = self.all_conf_data.get("disk_format", dotry=True)
        self.cluster["client"] = self.all_conf_data.get_list("list_client")
        self.cluster["osds"] = self.all_conf_data.get_list("list_server")
        self.cluster["mons"] = self.all_conf_data.get_list("list_mon")
        self.cluster["rgw"] = self.all_conf_data.get_list("rgw_server")
        self.cluster["vclient"] = self.all_conf_data.get_list("list_vclient")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["monitor_interval"] = self.all_conf_data.get("monitoring_interval")
        self.cluster["osd_daemon_num"] = 0
        self.cluster["perfcounter_data_type"] = self.all_conf_data.get_list("perfcounter_data_type")
        self.cluster["perfcounter_time_precision_level"] = self.all_conf_data.get("perfcounter_time_precision_level")
        self.cluster["distributed"] = self.all_conf_data.get("distributed")
        self.cluster["tmp_dir"] =self.all_conf_data.get("tmp_dir")
        self.result = OrderedDict()
        self.result["workload"] = OrderedDict()
        self.result["ceph"] = OrderedDict()
        self.result["rgw"] = OrderedDict()
        self.result["client"] = OrderedDict()
        self.result["vclient"] = OrderedDict()
        self.get_validate_runtime()
        self.result["runtime"] = int(float(self.validate_time))
        self.result["status"] = self.getStatus()
        self.result["description"] = self.getDescription()

        self.whoami = name


    def collect_node_ceph_version(self,dest_dir):
        node_list = []
        node_list.extend(self.cluster["osds"])
        node_list.append(self.cluster["head"])
        version_list = {}
        for node in node_list:
            if os.path.exists(os.path.join(dest_dir,node,node+'_ceph_version.txt')):
                data = open(os.path.join(dest_dir,node,node+'_ceph_version.txt'),'r')
                if data:
                    version_list[node] = data.read().strip('\n')
                else:
                    version_list[node] = 'None'
            else:
                version_list[node] = 'None'
        return version_list

    def test_write_json(self,data,file):
        json.dump(data,open(file,'w'))


    def process_data(self):
        process_list = []
        user = self.cluster["user"]
        dest_dir = self.cluster["dest_dir"]
        session_name = self.cluster["dest_dir_root"].split('/')
        if session_name[-1] != '':
            self.result["session_name"] = session_name[-1]
        else:
            self.result["session_name"] = session_name[-2]

        if self.whoami in self.cluster["osds"]:
            self.result["ceph"][self.whoami]={}
            p = Process(target=self._process_data,args=())
            process_list.append(p)
        if self.whoami in self.cluster["rgw"]:
            self.result["rgw"][self.whoami]={}
            p = Process(target=self._process_data,args=())
            process_list.append(p)
        if self.whoami in self.cluster["client"]:
            self.result["client"][self.whoami]={}
            p = Process(target=self._process_data,args=())
            process_list.append(p)
        if self.whoami in self.cluster["vclient"]:
            params = self.result["session_name"].split('-')
            self.cluster["vclient_disk"] = ["/dev/%s" % params[-1]]
            self.result["vclient"][self.whoami]={}
            p = Process(target=self._process_data,args=())
            process_list.append(p)

        for poc in process_list:
            poc.daemon = True
            poc.start()
        poc.join()


        return

        # switch result format for visualizer
        # desired format
        '''
         result = {
             tab1: {
                 table1: { 
                     row1: {
                         column1: [value], column2: [value] , ...
                           }
                     }
                 }
             },
             tab2: {}
             tab3: {}
             ...
             tabn: {}
        }
        '''
        result = self.format_result_for_visualizer( self.result )
        result = self.summary_result( result )
        result["summary"]["Download"] = {"Configuration":{"URL":"<button class='cetune_config_button' href='../results/get_detail_zip?session_name=%s&detail_type=conf'><a>Click TO Download</a></button>" % self.result["session_name"]}}
        node_ceph_version = {}
        if self.collect_node_ceph_version(dest_dir):
            for key,value in self.collect_node_ceph_version(dest_dir).items():
                node_ceph_version[key] = {"ceph_version":value}
        result["summary"]["Node"] = node_ceph_version
        dest_dir = self.cluster["dest_dir_root"]
        self.common.printout("LOG","Write analyzed results into result.json")
        with open('%s/result.json' % dest_dir, 'w') as f:
            json.dump(result, f, indent=4)
        view = visualizer.Visualizer(result, dest_dir)
        output = view.generate_summary_page()

    def format_result_for_visualizer(self, data):
        output_sort = OrderedDict()
        monitor_interval = int(self.cluster["monitor_interval"]) 
        output_sort["summary"] = OrderedDict()
        res = re.search('^(\d+)-(\w+)-(\w+)-(\w+)-(\w+)-(\w+)-(\w+)-(\d+)-(\d+)-(\w+)$',data["session_name"])
        if not res:
            return output_sort
        rampup = int(res.group(8))
        runtime = int(res.group(9))
        diskformat = self.common.parse_disk_format( self.cluster['diskformat'] )
        phase_name_map_for_disk = {}
        for typename in diskformat:
            phase_name_map_for_disk[typename] = "iostat" 
        phase_name_map = {"cpu": "sar", "memory": "sar", "nic": "sar", "vdisk": "iostat" }
        phase_name_map.update( phase_name_map_for_disk )

        for node_type in data.keys():
            if not isinstance(data[node_type], dict):
                output_sort[node_type] = data[node_type]
                continue
            if data[node_type] == {}:
                continue
            output = {}
            output_sort[node_type] = OrderedDict()
            for node in sorted(data[node_type].keys()):
                for field_type in sorted(data[node_type][node].keys()):
                    if field_type == "phase":
                        continue
                    if field_type not in output:
                        output[field_type] = OrderedDict()
                    if "phase" in data[node_type][node].keys() and field_type in phase_name_map.keys():
                        try:
                            start = int(data[node_type][node]["phase"][phase_name_map[field_type]]["benchmark_start"])
                            end = int(data[node_type][node]["phase"][phase_name_map[field_type]]["benchmark_stop"])
                            benchmark_active_time = end - start
                            if benchmark_active_time > (rampup + runtime) or end <= 0:
                                runtime_end = start + rampup + runtime
                            else:
                                runtime_end = end
                            runtime_start = start + rampup
                            output[field_type][node] = OrderedDict()
                            runtime_start = runtime_start / monitor_interval
                            runtime_end = runtime_end / monitor_interval

                            for colume_name, colume_data in data[node_type][node][field_type].items():
                                if isinstance(colume_data, list):
                                    colume_data = colume_data[runtime_start:runtime_end]
                                output[field_type][node][colume_name] = colume_data
                        except:
                            output[field_type][node] = data[node_type][node][field_type]
                    else:
                        output[field_type][node] = data[node_type][node][field_type]
            for key in sorted(output.keys()):
                output_sort[node_type][key] = copy.deepcopy( output[key] )

        return output_sort

    def get_execute_time(self):
        dest_dir = self.dest_dir
        cf = config.Config(dest_dir+"/conf/all.conf")
        head = ''
        head = cf.get("head")
        file_path = os.path.join(dest_dir,"raw",head,head+"_process_log.txt")
        if head != '':
            if os.path.exists(os.path.join(dest_dir,"raw",head)):
                for file_path in os.listdir(os.path.join(dest_dir,"raw",head)):
                    if file_path.endswith("_process_log.txt"):
                        with open("%s/%s" % (os.path.join(dest_dir,"raw",head),file_path), "r") as f:
                            lines = f.readlines()
                if len(lines) != 0 and lines != None:
                    str_time = ''
                    try:
                        str_time = lines[0].replace('CST ','')
                        str_time = str_time.replace('\n','')
                        str_time = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(str_time))
                    except:
                        pass
                    return str_time
            else:
                return ''

    def summary_result(self, data):
        # generate summary
        benchmark_tool = ["fio", "cosbench", "vdbench"]
        data["summary"]["run_id"] = {}
        res = re.search('^(\d+)-(\w+)-(\w+)-(\w+)-(\w+)-(\w+)-(\w+)-(\d+)-(\d+)-(\w+)$',data["session_name"])
        if not res:
            self.common.printout("ERROR", "Unable to get result infomation")
            return data
        data["summary"]["run_id"][res.group(1)] = OrderedDict()
        tmp_data = data["summary"]["run_id"][res.group(1)]
        tmp_data["Timestamp"] = self.get_execute_time()
        tmp_data["Status"] = data["status"]
        tmp_data["Description"] = data["description"]
        tmp_data["Op_size"] = res.group(5)
        tmp_data["Op_Type"] = res.group(4)
        tmp_data["QD"] = res.group(6)
        tmp_data["Driver"] = res.group(3)
        tmp_data["SN_Number"] = 0
        tmp_data["CN_Number"] = 0
        tmp_data["Worker"] = res.group(2)
        if data["runtime"] == 0:
            data["runtime"] = int(res.group(9))
        tmp_data["Runtime"] = "%d" % (data["runtime"])
        tmp_data["IOPS"] = 0
        tmp_data["BW(MB/s)"] = 0
        tmp_data["Latency(ms)"] = 0
        tmp_data["SN_IOPS"] = 0
        tmp_data["SN_BW(MB/s)"] = 0
        tmp_data["SN_Latency(ms)"] = 0
        rbd_count = 0
        osd_node_count = 0
        try:
            read_IOPS = 0
            read_BW = 0
            read_Latency = 0
            write_IOPS = 0
            write_BW = 0
            write_Latency = 0
            for engine_candidate in data["workload"].keys():
                if engine_candidate in benchmark_tool:
                    engine = engine_candidate
            for node, node_data in data["workload"][engine].items():
                rbd_count += 1
                read_IOPS += float(node_data["read_iops"])
                read_BW += float(node_data["read_bw"])
                read_Latency += float(node_data["read_lat"])
                write_IOPS += float(node_data["write_iops"])
                write_BW += float(node_data["write_bw"])
                write_Latency += float(node_data["write_lat"])
            if tmp_data["Op_Type"] in ["randread", "seqread", "read"]:
                tmp_data["IOPS"] = "%.3f" % read_IOPS
                tmp_data["BW(MB/s)"] = "%.3f" % read_BW
                if rbd_count > 0:
                    tmp_data["Latency(ms)"] = "%.3f" % (read_Latency/rbd_count)
            elif tmp_data["Op_Type"] in ["randwrite", "seqwrite", "write"]:
                tmp_data["IOPS"] = "%.3f" % write_IOPS
                tmp_data["BW(MB/s)"] = "%.3f" % write_BW
                if rbd_count > 0:
                    tmp_data["Latency(ms)"] = "%.3f" % (write_Latency/rbd_count)
            elif tmp_data["Op_Type"] in ["randrw", "rw", "readwrite"]:
                tmp_data["IOPS"] = "%.3f, %.3f" % (read_IOPS, write_IOPS)
                tmp_data["BW(MB/s)"] = "%.3f, %.3f" % (read_BW, write_BW)
                if rbd_count > 0:
                    tmp_data["Latency(ms)"] = "%.3f, %.3f" % ((read_Latency/rbd_count), (write_Latency/rbd_count))
        except:
            pass
        read_SN_IOPS = 0
        read_SN_BW = 0
        read_SN_Latency = 0
        write_SN_IOPS = 0
        write_SN_BW = 0
        write_SN_Latency = 0
        diskformat = self.common.parse_disk_format( self.cluster['diskformat'] )
        if len(diskformat):
            typename = diskformat[0]
        else:
            typename = "osd"
        for node, node_data in data["ceph"][typename].items():
            osd_node_count += 1
            read_SN_IOPS += numpy.mean(node_data["r/s"])*int(node_data["disk_num"])
            read_SN_BW += numpy.mean(node_data["rMB/s"])*int(node_data["disk_num"])
            lat_name = "r_await"
            if lat_name not in node_data:
                lat_name = "await"
            read_SN_Latency += numpy.mean(node_data[lat_name])
            write_SN_IOPS += numpy.mean(node_data["w/s"])*int(node_data["disk_num"])
            write_SN_BW += numpy.mean(node_data["wMB/s"])*int(node_data["disk_num"])
            lat_name = "w_await"
            if lat_name not in node_data:
                lat_name = "await"
            write_SN_Latency += numpy.mean(node_data[lat_name])

        if tmp_data["Op_Type"] in ["randread", "seqread", "read"]:
            tmp_data["SN_IOPS"] = "%.3f" % read_SN_IOPS
            tmp_data["SN_BW(MB/s)"] = "%.3f" % read_SN_BW
            if osd_node_count > 0:
                tmp_data["SN_Latency(ms)"] = "%.3f" % (read_SN_Latency/osd_node_count)
        elif tmp_data["Op_Type"] in ["randwrite", "seqwrite", "write"]:
            tmp_data["SN_IOPS"] = "%.3f" % write_SN_IOPS
            tmp_data["SN_BW(MB/s)"] = "%.3f" % write_SN_BW
            if osd_node_count > 0:
                tmp_data["SN_Latency(ms)"] = "%.3f" % (write_SN_Latency/osd_node_count)
        elif tmp_data["Op_Type"] in ["randrw", "readwrite", "rw"]:
            tmp_data["SN_IOPS"] = "%.3f, %.3f" % (read_SN_IOPS, write_SN_IOPS)
            tmp_data["SN_BW(MB/s)"] = "%.3f, %.3f" % (read_SN_BW, write_SN_BW)
            if osd_node_count > 0:
                tmp_data["SN_Latency(ms)"] = "%.3f, %.3f" % (read_SN_Latency/osd_node_count, write_SN_Latency/osd_node_count)

        tmp_data["SN_Number"] = osd_node_count
        try:
            tmp_data["CN_Number"] = len(data["client"]["cpu"])
        except:
            tmp_data["CN_Number"] = 0
        return data

    def _process_data(self):
        result = {}
        fio_log_res = {}
        workload_result = {}
        dest_dir = self.cluster["dest_dir"]
        self.common.printout("LOG","dest_dir:%s"%dest_dir)
        for dir_name in os.listdir(dest_dir):
            if 'smartinfo.txt' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                res = self.process_smartinfo_data( "%s/%s" % (dest_dir, dir_name))
                result.update(res)
            if 'cosbench' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                workload_result.update(self.process_cosbench_data("%s/%s" %(dest_dir,  dir_name), dir_name))
            if '_sar.txt' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                result.update(self.process_sar_data("%s/%s" % (dest_dir, dir_name)))
            if 'totals.html' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                workload_result.update(self.process_vdbench_data("%s/%s" % (dest_dir, dir_name), "%s_%s" % (self.whoami, dir_name)))
            if '_fio.txt' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                workload_result.update(self.process_fio_data("%s/%s" % (dest_dir,  dir_name), dir_name))
            if '_fio_iops.1.log' in dir_name or '_fio_bw.1.log' in dir_name or '_fio_lat.1.log' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                if "_fio_iops.1.log" in dir_name:
                    volume = dir_name.replace("_fio_iops.1.log", "")
                if "_fio_bw.1.log" in dir_name:
                    volume = dir_name.replace("_fio_bw.1.log", "")
                if "_fio_lat.1.log" in dir_name:
                    volume = dir_name.replace("_fio_lat.1.log", "")
                if volume not in fio_log_res:
                    fio_log_res[volume] = {}
                    fio_log_res[volume]["fio_log"] = {}
                fio_log_res[volume]["fio_log"] = self.process_fiolog_data("%s/%s" % (dest_dir,  dir_name), fio_log_res[volume]["fio_log"] )
                workload_result.update(fio_log_res)
            if '_iostat.txt' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                res = self.process_iostat_data( self.whoami, "%s/%s" % (dest_dir,  dir_name))
                result.update(res)
            if '_interrupts_end.txt' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                if os.path.exists("%s/%s" % (dest_dir,  dir_name.replace('end','start'))):
                    interrupt_end = "%s/%s" % (dest_dir,  dir_name)
                    interrupt_start   = "%s/%s" % (dest_dir,  dir_name.replace('end','start'))
                    self.interrupt_diff(dest_dir,self.whoami,interrupt_start,interrupt_end)
            if '_process_log.txt' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                res = self.process_log_data( "%s/%s" % (dest_dir,  dir_name) )
                result.update(res)
            if '.asok.txt' in dir_name:
                self.common.printout("LOG","Processing %s_%s" % (self.whoami, dir_name))
                try:
                    res = self.process_perfcounter_data("%s/%s" % (dest_dir,  dir_name))
                    for key, value in res.items():
                        if dir_name not in workload_result:
                            workload_result[dir_name] = OrderedDict()
                        workload_result[dir_name][key] = value
                except:
                    pass
        self.test_write_json(result,self.whoami+"-system.json")
        self.test_write_json(workload_result,self.whoami+"-workload.json")
        return [result, workload_result]

    def process_smartinfo_data(self, path):
        output = {}
        with open(path, 'r') as f:
            tmp = f.read()
        output.update(json.loads(tmp, object_pairs_hook=OrderedDict))
        return output

    def interrupt_diff(self,dest_dir,node_name,s_path,e_path):
        s_p = s_path
        e_p = e_path
        result_name = node_name+'_interrupt.csv'
        result_path_node = os.path.join(dest_dir,result_name)
        s_l = []
        e_l = []
        diff_list = []
        with open(s_p, 'r') as f:
            s = f.readlines()
        with open(e_p, 'r') as f:
            e = f.readlines()
        for i in s:
            tmp = []
            tmp = i.split(' ')
            while '' in tmp:
                tmp.remove('')
            s_l.append(tmp)
        for i in e:
            tmp = []
            tmp = i.split(' ')
            while '' in tmp:
                tmp.remove('')
            e_l.append(tmp)
        if self.check_interrupt(s_l,e_l):
            for i in range(len(s_l)):
                lines = []
                for j in range(len(s_l[i])):
                    if s_l[i][j].isdigit() and e_l[i][j].isdigit():
                        lines.append(int(e_l[i][j]) - int(s_l[i][j]))
                    else:
                        lines.append(e_l[i][j])
                diff_list.append(lines)
            ##write interrupt to node and conf
            self.common.printout("LOG","write interrput to node and conf.")
            if os.path.exists(result_path_node):
                os.remove(result_path_node)
            output_node = file(result_path_node,'wb')
            interrupt_csv_node = csv.writer(output_node)
            if len(diff_list) != 0:
                diff_list[0][0] = ""
                interrupt_csv_node.writerow(diff_list[0])
                del diff_list[0]
                new_diff_list = self.delete_colon(diff_list)
                for i in new_diff_list:
                    interrupt_csv_node.writerows([i])
                output_node.close()
            else:
                self.common.printout("WARNING","no interrupt.")
        else:
            self.common.printout("ERROR",'interrupt_start lines and interrupt_end lines are different ! can not calculate different value!')

    def delete_colon(self,data_list):
        self.d_list = data_list
        for i in range(len(self.d_list)):
            self.d_list[i][0] = self.d_list[i][0].replace(":","")
            self.d_list[i][-1] = self.d_list[i][-1].strip("\n")
        return self.d_list

    def check_interrupt(self,s_inter,e_inter):
        result = "True"
        if len(s_inter)!=len(e_inter):
            result = "False"
        else:
            for i in range(len(s_inter)):
                if len(s_inter[i])!=len(e_inter[i]):
                    result = "False"
        return result

    def process_log_data(self, path):
        result = {}
        result["phase"] = {}
        with open( path, 'r') as f:
            lines = f.readlines()

        benchmark_tool = ["fio", "cosbench"]
        tmp = {}
        benchmark = {}

        for line in lines:
            try:
                time, tool, status = line.split()
            except:
                continue
            if tool not in tmp:
               tmp[tool] = {}
            if tool in benchmark_tool:
                benchmark[status] = time
            else:
                tmp[tool][status] = time

        for tool in tmp:
            result["phase"][tool] = {}
            result["phase"][tool]["start"] = 0
            try:
                result["phase"][tool]["stop"] = int(tmp[tool]["stop"]) - int(tmp[tool]["start"])
            except:
                result["phase"][tool]["stop"] = None
            try:
                result["phase"][tool]["benchmark_start"] = int(benchmark["start"]) - int(tmp[tool]["start"])
                if result["phase"][tool]["benchmark_start"] < 0:
                    result["phase"][tool]["benchmark_start"] = 0
            except:
                result["phase"][tool]["benchmark_start"] = None
            try:
                result["phase"][tool]["benchmark_stop"] = int(benchmark["stop"]) - int(tmp[tool]["start"])
                if result["phase"][tool]["benchmark_stop"] < 0:
                    result["phase"][tool]["benchmark_stop"] = 0
            except:
                result["phase"][tool]["benchmark_stop"] = None
        return result

    def process_cosbench_data(self, path, dirname):
        result = {}
        result["cosbench"] = OrderedDict()
        result["cosbench"]["cosbench"] = OrderedDict([("read_lat",0), ("read_bw",0), ("read_iops",0), ("write_lat",0), ("write_bw",0), ("write_iops",0), ("lat_unit",'msec'), ('runtime_unit','sec'), ('bw_unit','MB/s')])
        tmp = result
        keys = self.common.bash("head -n 1 %s/%s.csv" %(path, dirname))
        keys = keys.split(',')
        values = self.common.bash('tail -n 1 %s/%s.csv' %(path, dirname) )
        values = values.split(',')
        size = len(keys)
        for i in range(size):
            tmp[keys[i]] = {}
            tmp[keys[i]]["detail"] = {}
            tmp[keys[i]]["detail"]["value"] = values[i]
        tmp = result["cosbench"]["cosbench"]
        io_pattern = result["Op-Type"]["detail"]["value"]
        tmp["%s_lat" % io_pattern] = result["Avg-ResTime"]["detail"]["value"]
        tmp["%s_bw" % io_pattern] = self.common.size_to_Kbytes('%s%s' % (result["Bandwidth"]["detail"]["value"], 'B'), 'MB')
        tmp["%s_iops" % io_pattern] = result["Throughput"]["detail"]["value"]
        return result

    def get_validate_runtime(self):
        self.validate_time = 0
        dest_dir = self.cluster["dest_dir"]
        stdout = self.common.bash('grep " runt=.*" -r %s' % (dest_dir))
        fio_runtime_list = re.findall('runt=\s*(\d+\wsec)', stdout)
        for fio_runtime in fio_runtime_list:
            validate_time = self.common.time_to_sec(fio_runtime, 'sec')
            if validate_time < self.validate_time or self.validate_time == 0:
                self.validate_time = validate_time

    def getStatus(self):
        self.validate_time = 0
        dest_dir = self.cluster["dest_conf_dir"]
        status = "Unknown"
        try:
            with open("%s/status" % dest_dir, 'r') as f:
                status = f.readline()
        except:
            pass
        return status

    def getParameters(self):
        dest_dir = self.cluster["dest_conf_dir"]
        ps = ""
        try:
            with open("%s/vdbench_params.txt" % dest_dir.replace("raw","conf"), 'r') as f:
                ps = f.read()
        except:
            pass
        return ps

    def getDescription(self):
        dest_dir = self.cluster["dest_conf_dir"]
        desc = ""
        try:
            with open("%s/description" % dest_dir, 'r') as f:
                desc = f.readline()
        except:
            pass
        return desc

    def process_fiolog_data(self, path, result):
        if "fio_iops" in path:
            result["iops"] = []
            res = result["iops"]
        if "fio_bw" in path:
            result["bw"] = []
            res = result["bw"]
        if "fio_lat" in path:
            result["lat"] = []
            res = result["lat"]

        time_shift = 1000
        with open( path, "r" ) as f:
            cur_sec = -1
            self.tmp_res = []
            if 'iops' in path:
                self.iops_value = 0
                for line in f.readlines():
                    data = line.split(",")
                    value = int(data[1])
                    timestamp_sec = int(data[0])/time_shift
                    if timestamp_sec > cur_sec:
                        if cur_sec >= 0:
                            self.tmp_res.append( self.iops_value )
                            self.iops_value = 0
                        cur_sec = timestamp_sec
                    self.iops_value += value
                if len(self.tmp_res) != 0:
                    res.extend(self.tmp_res)
            else:
                for line in f.readlines():
                    data = line.split(",")
                    timestamp_sec = int(data[0])/time_shift
                    value = int(data[1])
                    if timestamp_sec > cur_sec:
                        if cur_sec >= 0:
                            res.append(numpy.mean(self.tmp_res))
                        cur_sec = timestamp_sec
                    self.tmp_res.append( value )
                if len(self.tmp_res) != 0:
                    res.append(numpy.mean(self.tmp_res))
        return result


    def process_sar_data(self, path):
        result = {}
        #1. cpu
        stdout = self.common.bash("grep ' *CPU *%' -m 1 "+path+" | awk -F\"CPU\" '{print $2}'; cat "+path+" | grep ' *CPU *%' -A 1 | awk '{flag=0;if(NF<=3)next;for(i=1;i<=NF;i    ++){if(flag==1){printf $i\"\"FS}if($i==\"all\")flag=1};if(flag==1)print \"\"}'")
        result["cpu"] = self.common.convert_table_to_2Dlist(stdout)

        #2. memory
        stdout = self.common.bash("grep 'kbmemfree' -m 1 "+path+" | awk -Fkbmemfree '{printf \"kbmenfree  \";print $2}'; grep \"kbmemfree\" -A 1 "+path+" | awk 'BEGIN{find=0;}    {for(i=1;i<=NF;i++){if($i==\"kbmemfree\"){find=i;next;}}if(find!=0){for(j=find;j<=NF;j++)printf $j\"\"FS;find=0;print \"\"}}'")
        result["memory"] = self.common.convert_table_to_2Dlist(stdout)

        #3. nic
        stdout = self.common.bash("grep 'IFACE' -m 1 "+path+" | awk -FIFACE '{print $2}'; cat "+path+" | awk 'BEGIN{find=0;}{for(i=1;i<=NF;i++){if($i==\"IFACE\"){j=i+1;if($j==    \"rxpck/s\"){find=1;start_col=j;col=NF;for(k=1;k<=col;k++){res_arr[k]=0;}next};if($j==\"rxerr/s\"){find=0;for(k=start_col;k<=col;k++)printf res_arr[k]\"\"FS; print \"\";ne    xt}}if($i==\"lo\")next;if(find){res_arr[i]+=$i}}}'")
        result["nic"] = self.common.convert_table_to_2Dlist(stdout)
        #4. tps
        return result

    def process_iostat_data(self, node, path):
        result = {}
        output_list = []
        dict_diskformat = {}
        if node in self.cluster["osds"]:
            output_list = self.common.parse_disk_format( self.cluster['diskformat'] )
            for i in range(len(output_list)):
                disk_list=[]
                for osd_journal in self.common.get_list(self.all_conf_data.get_list(node)): 
                   tmp_dev_name = osd_journal[i].split('/')[2]
                   if 'nvme' in tmp_dev_name:
                       tmp_dev_name = self.common.parse_nvme( tmp_dev_name )
                   if tmp_dev_name not in disk_list:
                       disk_list.append( tmp_dev_name )
                dict_diskformat[output_list[i]]=disk_list
        elif node in self.cluster["vclient"]:
            vdisk_list = []
            for disk in self.cluster["vclient_disk"]:
                vdisk_list.append( disk.split('/')[2] )
            output_list = ["vdisk"]
        # get total second
        runtime = self.common.bash("grep 'Device' "+path+" | wc -l ").strip()
        for output in output_list:
            if output != "vdisk":
                disk_list = " ".join(dict_diskformat[output])
                disk_num = len(list(set(dict_diskformat[output])))
            else:
                disk_list = " ".join(vdisk_list)
                disk_num = len(vdisk_list)
            stdout = self.common.bash( "grep 'Device' -m 1 "+path+" | awk -F\"Device:\" '{print $2}'; cat "+path+" | awk -v dev=\""+disk_list+"\" -v line="+runtime+" 'BEGIN{split(dev,dev_arr,\" \");dev_count=0;for(k in dev_arr){count[k]=0;dev_count+=1};for(i=1;i<=line;i++)for(j=1;j<=NF;j++){res_arr[i,j]=0}}{for(k in dev_arr)if(dev_arr[k]==$1){cur_line=count[k];for(j=2;j<=NF;j++){res_arr[cur_line,j]+=$j;}count[k]+=1;col=NF}}END{for(i=1;i<=line;i++){for(j=2;j<=col;j++)printf (res_arr[i,j]/dev_count)\"\"FS; print \"\"}}'")
            result[output] = self.common.convert_table_to_2Dlist(stdout)
            result[output]["disk_num"] = disk_num
        return result

    def process_vdbench_data(self, path, dirname):
        result = {}
        vdbench_data = {}
        runtime = int(self.common.bash("grep -o 'elapsed=[0-9]\+' "+path+" | cut -d = -f 2"))
        stdout, stderr = self.common.bash("grep 'avg_2-' "+path, True)
        vdbench_data = stdout.split()
        output_vdbench_data = OrderedDict()
        output_vdbench_data['read_lat'] = vdbench_data[8]
        output_vdbench_data["read_iops"] = vdbench_data[7]
        output_vdbench_data["read_bw"] = vdbench_data[11]
        output_vdbench_data['read_runtime'] = runtime
        output_vdbench_data['write_lat'] = vdbench_data[10]
        output_vdbench_data["write_iops"] = vdbench_data[9]
        output_vdbench_data["write_bw"] = vdbench_data[12]
        output_vdbench_data['write_runtime'] = runtime
        output_vdbench_data['lat_unit'] = 'msec'
        output_vdbench_data['runtime_unit'] = 'sec'
        output_vdbench_data['bw_unit'] = 'MB/s'
        result[dirname] = {}
        result[dirname]["vdbench"] = output_vdbench_data
        return result

    def get_lat_persent_dict(self,fio_str):
        lat_percent_dict = {}
        tmp_list = fio_str.split(',')
        for i in tmp_list:
            li = i.split('=')
            while '' in li:li.remove('')
            if len(li) == 2 and li[1] != '':
                key = re.findall('.*?th',li[0].strip('\n').strip('| ').strip(' ').replace(' ',''),re.S)
                value = re.match(r'\[(.*?)\]',li[1].strip('\n').strip(' ').replace(' ','')).groups()
                if len(key) != 0 and len(value) != 0:
                    lat_percent_dict[key[0]] = value[0]
        return lat_percent_dict

    def process_fio_data(self, path, dirname):
        result = {}
        stdout = self.common.bash("grep \" *io=.*bw=.*iops=.*runt=.*\|^ *lat.*min=.*max=.*avg=.*stdev=.*\" "+path)
        stdout1 = self.common.bash("grep \" *1.00th.*],\| *30.00th.*],\| *70.00th.*],\| *99.00th.*],\| *99.99th.*]\" "+path)
        stdout2 = self.common.bash("grep \" *clat percentiles\" "+path)

        lat_per_dict = {}
        if stdout1 != '':
            lat_per_dict = self.get_lat_persent_dict(stdout1)

        fio_data_rw = {}
        fio_data_rw["read"] = {}
        fio_data_rw["write"] = {}
        for data in re.split(',|\n|:',stdout):
            try:
                key, value = data.split("=")
                if key.strip() not in fio_data:
                    fio_data[key.strip()] = []
                    fio_data[key.strip()].append( value.strip() )
            except:
                if 'lat' in data:
                    res = re.search('lat\s*\((\w+)\)',data)
                    if 'lat_unit' not in fio_data:
                        fio_data['lat_unit'] = []
                    fio_data['lat_unit'].append( res.group(1) )
                if "read" in data:
                    fio_data = fio_data_rw["read"]
                if "write" in data:
                    fio_data = fio_data_rw["write"]

        output_fio_data = OrderedDict()
        output_fio_data['read_lat'] = 0
        output_fio_data['read_iops'] = 0
        output_fio_data['read_bw'] = 0
        output_fio_data['read_runtime'] = 0
        output_fio_data['write_lat'] = 0
        output_fio_data['write_iops'] = 0
        output_fio_data['write_bw'] = 0
        output_fio_data['write_runtime'] = 0
        if len(lat_per_dict) != 0:
            if '99.99th' in lat_per_dict.keys():
                #output_fio_data['99.99%_lat'] = lat_per_dict['99.99th']
                lat_persent_unit = re.findall(r"(?<=[\(])[^\)]+(?=[\)])", stdout2.strip('\n').strip(' ').replace(' ',''))
                if len(lat_persent_unit) != 0:
                    output_fio_data['99.99%_lat'] = float(self.common.time_to_sec("%s%s" % (lat_per_dict['99.99th'], lat_persent_unit[0]),'msec'))
                else:
                    output_fio_data['99.99%_lat'] = 'null'
            else:
                output_fio_data['99.99%_lat'] = 'null'
        output_fio_data['lat_unit'] = 'msec'
        output_fio_data['runtime_unit'] = 'sec'
        output_fio_data['bw_unit'] = 'MB/s'
        for io_pattern in ['read', 'write']:
            if fio_data_rw[io_pattern] != {}:
                first_item = fio_data_rw[io_pattern].keys()[0]
            else:
                continue
            list_len = len(fio_data_rw[io_pattern][first_item])
            for index in range(0, list_len):
                fio_data = fio_data_rw[io_pattern]
                output_fio_data['%s_lat' % io_pattern] += float(self.common.time_to_sec("%s%s" % (fio_data['avg'][index], fio_data['lat_unit'][index]),'msec'))
                output_fio_data['%s_iops' % io_pattern] += int(fio_data['iops'][index])
                res = re.search('(\d+\.*\d*)\s*(\w+)/s',fio_data['bw'][index])
                if res:
                    output_fio_data['%s_bw' % io_pattern] += float( self.common.size_to_Kbytes("%s%s" % (res.group(1), res.group(2)),'MB') )
                output_fio_data['%s_runtime' % io_pattern] += float( self.common.time_to_sec(fio_data['runt'][index], 'sec') )
            output_fio_data['%s_lat' % io_pattern] /= list_len
            output_fio_data['%s_runtime' % io_pattern] /= list_len
        result[dirname] = {}
        result[dirname]["fio"] = output_fio_data
        return result

    def process_lttng_data(self, path):
        pass

    def process_perf_data(self, path):
        pass

    def process_blktrace_data(self, path):
        pass

    def process_perfcounter_data(self, path):
        precise_level = int(self.cluster["perfcounter_time_precision_level"])
#        precise_level = 6
        self.common.printout("LOG","loading %s" % path)
        perfcounter = []
        with open(path,"r") as fd:
            data = fd.readlines()
        for tmp_data in data:
            if ',' == tmp_data[-2]:
                tmp_data = tmp_data[:-2]
            try:
                perfcounter.append(json.loads(tmp_data, object_pairs_hook=OrderedDict))
            except:
                perfcounter.append({})
        if not len(perfcounter) > 0:
            return False
        result = self.common.MergableDict()
        lastcounter = perfcounter[0]
        for counter in perfcounter[1:]:
            result.update(counter, dedup=False, diff=False)
        result = result.get()
        output = OrderedDict()
#        for key in ["osd", "filestore", "objecter", "mutex-JOS::SubmitManager::lock"]:
        for key in self.cluster["perfcounter_data_type"]:
            result_key = key
            find = True
            if key != "librbd" and key not in result:
                continue
            if key == "librbd":
                find = False
                for result_key in result.keys():
                    if key in result_key:
                        find = True
                        break
            if not find:
                continue
            output["perfcounter_"+key] = {}
            current = output["perfcounter_"+key]
            for param, data in result[result_key].items():
                if isinstance(data, list):
                    if not param in current:
                        current[param] = []
                    current[param].extend( data )
                if isinstance(data, dict) and 'avgcount' in data and 'sum' in data:
                    if not isinstance(data['sum'], list):
                        continue
                    if not param in current:
                        current[param] = []
                    last_sum = data['sum'][0]
                    last_avgcount = data['avgcount'][0]
                    for i in range(1, len(data['sum'])):
                        try:
                            current[param].append( round((data['sum'][i]-last_sum)/(data['avgcount'][i]-last_avgcount),precise_level) )
                        except:
                            current[param].append(0)
                        last_sum = data['sum'][i]
                        last_avgcount = data['avgcount'][i]
        return output

def main(args):
    parser = argparse.ArgumentParser(description='Analyzer tool')
    parser.add_argument(
        'operation',
        )
    parser.add_argument(
        '--path',
        )
    parser.add_argument(
        '--path_detail',
        )
    parser.add_argument(
        '--node',
        )
    parser.add_argument(
        '--name',
        )
    args = parser.parse_args(args)
    process = Analyzer(args.path,args.name)
    if args.operation == "process_data":
        process.process_data()
    else:
        func = getattr(process, args.operation)
        if func:
            func(args.path_detail)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
