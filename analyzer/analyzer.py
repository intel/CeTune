# -*- coding: utf-8 -*
import os,sys
import argparse
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import *
from visualizer import *
import os, sys
import time
import pprint
import re
import yaml
from collections import OrderedDict
import json
import numpy
import copy
import getpass
from multiprocessing import Process, Lock, Queue
import multiprocessing
import threading
import csv

pp = pprint.PrettyPrinter(indent=4)
class Analyzer:
    def __init__(self, dest_dir):
        self.dest_dir = dest_dir
        self.cluster = {}
        if os.path.isdir('%s/%s' % ( dest_dir, 'conf' )):
            self.cluster["dest_conf_dir"] = '%s/%s' % ( dest_dir, 'conf' )
        else:
            self.cluster["dest_conf_dir"] = dest_dir
        if os.path.isdir('%s/%s' % ( dest_dir, 'raw' )):
            self.cluster["dest_dir"] = '%s/%s' % ( dest_dir, 'raw' )
        else:
            self.cluster["dest_dir"] = dest_dir
        self.cluster["dest_dir_root"] = dest_dir
        self.all_conf_data = config.Config("%s/all.conf" % self.cluster["dest_conf_dir"])
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
        self.cluster["distributed"] = self.all_conf_data.get("distributed_data_process")
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
        self.workpool = WorkPool(common)

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

    def _process_remote(self,node,use_tmp):
        if not use_tmp:
            common.printout("LOG","scp %s/%s/ to %s:/%s" % (self.cluster["dest_dir"], node, node, self.cluster["tmp_dir"]))
            common.pdsh(self.cluster['user'], [node], "cd %s; rm -rf %s;" % (self.cluster["tmp_dir"], node),'check_return' )
            common.scp(self.cluster['user'], node, "%s/%s/" % (self.cluster["dest_dir"], node), self.cluster["tmp_dir"] )
        else:
            files = " ".join(os.listdir("%s/%s" % (self.cluster["dest_dir"], node)))
            common.pdsh(self.cluster['user'], [node], "cd %s; rm -rf %s; mkdir -p %s; mv %s %s/;" % (self.cluster["tmp_dir"], node, node, files, node),'check_return' )
        common.pdsh(self.cluster['user'], [node], "cd "+ self.cluster["tmp_dir"] +";python analyzer_remote.py --path "+self.cluster["tmp_dir"] +" --name "+ node +" process_data" )

    def _process_remote_data(self,process_file):
        node_result = json.load(open(process_file,'r'))
        return node_result

    def print_remote_log(self,node_log,node):
        try:
            get_log = ""
            get_line = "wc -l "+ self.cluster["tmp_dir"] +node+"-cetune_console.log"
            stdout = common.pdsh(self.cluster["user"],[node],get_line,'check_return')
            h = int(stdout[0].split()[1])

            if not node_log.has_key(node):
                node_log[node] = h
                get_log = "sed -n '1,"+ str(h) +"p' "+ self.cluster["tmp_dir"] +node+"-cetune_console.log"
            elif h > node_log[node]:
                get_log = "sed -n '"+ str(node_log[node]) +","+ str(h) +"p' "+ self.cluster["tmp_dir"] +node+"-cetune_console.log"

            if len(get_log):
                log = common.pdsh(self.cluster["user"],[node],get_log,'check_return')[0]
                list = log.split('\n')
                for l in list:
                    common.printout("LOG",l)
            node_log[node] = h + 1
        except Exception as e:
                common.printout("WARNING","print_remote_log failed")
                common.printout("WARNING",str(e))

    def process_data(self, use_tmp):
        case_type = re.findall('\d\-\S+', self.cluster["dest_dir"])[0].split('-')[2]
        if case_type == "vdbench":
            self.result["description"] = "Description:"+ str(self.getDescription()) +"  Parameters:"+ str(self.getParameters())
        user = self.cluster["user"]
        dest_dir = self.cluster["dest_dir"]
        session_name = self.cluster["dest_dir_root"].split('/')
        if session_name[-1] != '':
            self.result["session_name"] = session_name[-1]
        else:
            self.result["session_name"] = session_name[-2]

        #-------------------remote   start------------------------
        if self.cluster["distributed"] == "true":
            self.workpath = os.path.join(self.cluster["dest_dir"],"remote_tmp")
            remote_file = "../analyzer/analyzer_remote.py"
            remote_file1 = "%s/all.conf" % self.cluster["dest_conf_dir"]
            remote_file2 = "../conf/common.py"
            remote_file3 = "../conf/config.py"
            remote_file4 = "../conf/description.py"

            if not os.path.isdir(self.workpath):
                os.mkdir(self.workpath)

            all_node = []
            for node in self.cluster["osds"] + self.cluster["client"]:
                common.printout("LOG","note "+ node + " start analysis")
                common.scp(self.cluster["user"],node,remote_file,self.cluster["tmp_dir"])
                common.scp(self.cluster["user"],node,remote_file1,self.cluster["tmp_dir"])
                common.scp(self.cluster["user"],node,remote_file2,self.cluster["tmp_dir"])
                common.scp(self.cluster["user"],node,remote_file3,self.cluster["tmp_dir"])
                common.scp(self.cluster["user"],node,remote_file4,self.cluster["tmp_dir"])
                try:
                    common.pdsh(self.cluster["user"],[node],"echo \"\" > " + self.cluster["tmp_dir"] +node+"-cetune_console.log")
                except:
                    pass

                p = Process(target=self._process_remote,args=(node,use_tmp))
                p.daemon = True
                p.start()
                all_node.append((p,node))

            common.printout("LOG","waiting for all note finish analysis")
            log_line = {}
            while(1):
                for proc,node in all_node:
                    if proc.is_alive():
                        self.print_remote_log(log_line,node)
                    else:
                        common.rscp(self.cluster["user"],node,self.workpath,os.path.join(self.cluster["tmp_dir"],node,node+"-system.json"))
                        common.rscp(self.cluster["user"],node,self.workpath,os.path.join(self.cluster["tmp_dir"],node,node+"-workload.json"))
                        common.rscp(self.cluster["user"],node,self.cluster["dest_dir"].replace('raw','conf'),os.path.join(self.cluster["tmp_dir"],node,node+"_interrupt.csv"))
                        self.print_remote_log(log_line,node)
                        all_node.remove((proc,node))
                if not len(all_node):
                    break
                time.sleep(1)

            common.printout("LOG","all note finish analysis")
            common.printout("LOG","Merging node process.")
            for dir_name in  self.cluster["osds"] + self.cluster["client"]:
                system_file = os.path.join(self.workpath,dir_name+"-system.json")
                workload_file = os.path.join(self.workpath,dir_name+"-workload.json")

                if dir_name in self.cluster["osds"]:
                    self.result["ceph"][dir_name]={}
                    system = self._process_remote_data(system_file)
                    workload = self._process_remote_data(workload_file)
                    self.result["ceph"][dir_name]=system
                    self.result["ceph"].update(workload)
                elif dir_name in self.cluster["rgw"]:
                    self.result["rgw"][dir_name]={}
                    system = self._process_remote_data(system_file)
                    workload = self._process_remote_data(workload_file)
                    self.result["rgw"][dir_name]=system
                    self.result["rgw"].update(workload)
                elif dir_name in self.cluster["client"]:
                    self.result["client"][dir_name]={}
                    system = self._process_remote_data(system_file)
                    workload = self._process_remote_data(workload_file)
                    self.result["client"][dir_name]=system
                    self.result["workload"].update(workload)
                elif dir_name in self.cluster["vclient"]:
                    params = self.result["session_name"].split('-')
                    self.cluster["vclient_disk"] = ["/dev/%s" % params[-1]]
                    self.result["vclient"][dir_name]={}
                    system = self._process_remote_data(system_file)
                    workload = self._process_remote_data(workload_file)
                    self.result["vclient"][dir_name]=system
                    self.result["workload"].update(workload)
        #-------------------remote   end--------------------------
        else:
            for dir_name in os.listdir(dest_dir):
                if not os.path.isdir("%s/%s" % (dest_dir, dir_name)):
                    continue
                if dir_name in self.cluster["osds"]:
                    self.result["ceph"][dir_name]={}
                    system, workload = self._process_data(dir_name)
                    self.result["ceph"][dir_name]=system
                    self.result["ceph"].update(workload)
                if dir_name in self.cluster["rgw"]:
                    self.result["rgw"][dir_name]={}
                    system, workload = self._process_data(dir_name)
                    self.result["rgw"][dir_name]=system
                    self.result["rgw"].update(workload)
                if dir_name in self.cluster["client"]:
                    self.result["client"][dir_name]={}
                    system, workload = self._process_data(dir_name)
                    self.result["client"][dir_name]=system
                    self.result["workload"].update(workload)
                if dir_name in self.cluster["vclient"]:
                    params = self.result["session_name"].split('-')
                    self.cluster["vclient_disk"] = ["/dev/%s" % params[-1]]
                    self.result["vclient"][dir_name]={}
                    system, workload = self._process_data(dir_name)
                    self.result["vclient"][dir_name]=system
                    self.result["workload"].update(workload)


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
        common.printout("LOG","Write analyzed results into result.json")
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
        diskformat = common.parse_disk_format( self.cluster['diskformat'] )
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
        mon = ''
        mon = cf.get("list_mon").split(",")[0]
        file_path = os.path.join(dest_dir,"raw",mon,mon+"_process_log.txt")
        if mon != '':
            if os.path.exists(os.path.join(dest_dir,"raw",mon)):
                for file_path in os.listdir(os.path.join(dest_dir,"raw",mon)):
                    if file_path.endswith("_process_log.txt"):
                        with open("%s/%s" % (os.path.join(dest_dir,"raw",mon),file_path), "r") as f:
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
            common.printout("ERROR", "Unable to get result infomation")
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
        tmp_data["99.00th%_lat(ms)"] = 0
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
            max_lat = 0
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
                max_lat += float(node_data["99.00th%_lat"])
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
            if rbd_count > 0:
                tmp_data["99.00th%_lat(ms)"] = "%.3f" % (max_lat/rbd_count)
        except:
            pass
        read_SN_IOPS = 0
        read_SN_BW = 0
        read_SN_Latency = 0
        write_SN_IOPS = 0
        write_SN_BW = 0
        write_SN_Latency = 0
        diskformat = common.parse_disk_format( self.cluster['diskformat'] )
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

    def _process_data(self, node_name):
        result = {}
        fio_log_res = {}
        workload_result = {}
        dest_dir = self.cluster["dest_dir"]
        process_return_val_queue = Queue()
        self.workpool.set_return_data_set( fio_log_res, workload_result, result )
        for dir_name in os.listdir("%s/%s" % (dest_dir, node_name)):
            common.printout("LOG","Processing %s_%s" % (node_name, dir_name))
            if 'smartinfo.txt' in dir_name:
                self.workpool.schedule( self.process_smartinfo_data,  "%s/%s/%s" % (dest_dir, node_name, dir_name))
            if 'cosbench' in dir_name:
                self.workpool.schedule( self.process_cosbench_data,  "%s/%s/%s" %(dest_dir, node_name, dir_name), dir_name)
            if '_sar.txt' in dir_name:
                self.workpool.schedule( self.process_sar_data,  "%s/%s/%s" % (dest_dir, node_name, dir_name))
            if 'totals.html' in dir_name:
                self.workpool.schedule( self.process_vdbench_data,  "%s/%s/%s" % (dest_dir, node_name, dir_name), "%s_%s" % (node_name, dir_name))
            if '_fio.txt' in dir_name:
                self.workpool.schedule( self.process_fio_data,  "%s/%s/%s" % (dest_dir, node_name, dir_name), dir_name)
            if '_fio_iops.1.log' in dir_name or '_fio_bw.1.log' in dir_name or '_fio_lat.1.log' in dir_name:
                if "_fio_iops.1.log" in dir_name:
                    volume = dir_name.replace("_fio_iops.1.log", "")
                if "_fio_bw.1.log" in dir_name:
                    volume = dir_name.replace("_fio_bw.1.log", "")
                if "_fio_lat.1.log" in dir_name:
                    volume = dir_name.replace("_fio_lat.1.log", "")
                self.workpool.schedule( self.process_fiolog_data,  "%s/%s/%s" % (dest_dir, node_name, dir_name), volume )
            if '_iostat.txt' in dir_name:
                self.workpool.schedule( self.process_iostat_data,  node_name, "%s/%s/%s" % (dest_dir, node_name, dir_name))
            if '_interrupts_end.txt' in dir_name:
                if os.path.exists("%s/%s/%s" % (dest_dir, node_name, dir_name.replace('end','start'))):
                    interrupt_end = "%s/%s/%s" % (dest_dir, node_name, dir_name)
                    interrupt_start = "%s/%s/%s" % (dest_dir, node_name, dir_name.replace('end','start'))
                    self.interrupt_diff(dest_dir,node_name,interrupt_start,interrupt_end)
            if '_process_log.txt' in dir_name:
                self.workpool.schedule( self.process_log_data,  "%s/%s/%s" % (dest_dir, node_name, dir_name) )
            if '.asok.txt' in dir_name:
                self.workpool.schedule( self.process_perfcounter_data, dir_name, "%s/%s/%s" % (dest_dir, node_name, dir_name) )
#                res = self.process_perfcounter_data( "%s/%s/%s" % (dest_dir, node_name, dir_name) )
#                for key, value in res.items():
#                    if dir_name not in workload_result:
#                        workload_result[dir_name] = OrderedDict()
#                    workload_result[dir_name][key] = value

        self.workpool.wait_all()
        return [result, workload_result]

    def process_smartinfo_data(self, path):
        output = {}
        with open(path, 'r') as f:
            tmp = f.read()
        output.update(json.loads(tmp, object_pairs_hook=OrderedDict))
        self.workpool.enqueue_data( ["process_smartinfo_data", output] )
        return output

    def interrupt_diff(self,dest_dir,node_name,s_path,e_path):
        s_p = s_path
        e_p = e_path
        result_name = node_name+'_interrupt.csv'
        result_path_node = os.path.join(dest_dir,node_name,result_name)
        result_path_conf = os.path.join(dest_dir.replace('raw','conf'),result_name)
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
            common.printout("LOG","write interrput to node and conf.")
            if os.path.exists(result_path_node):
                os.remove(result_path_node)
            if os.path.exists(result_path_conf):
                os.remove(result_path_conf)
            output_node = file(result_path_node,'wb')
            output_conf = file(result_path_conf,'wb')
            interrupt_csv_node = csv.writer(output_node)
            interrupt_csv_conf = csv.writer(output_conf)
            if len(diff_list) != 0:
                diff_list[0][0] = ""
                interrupt_csv_node.writerow(diff_list[0])
                interrupt_csv_conf.writerow(diff_list[0])
                del diff_list[0]
                new_diff_list = self.delete_colon(diff_list)
                for i in new_diff_list:
                    interrupt_csv_node.writerows([i])
                    interrupt_csv_conf.writerows([i])
                output_node.close()
                output_conf.close()
            else:
                common.printout("WARNING","no interrupt.")
        else:
            common.printout("ERROR",'interrupt_start lines and interrupt_end lines are different ! can not calculate different value!')

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
        self.workpool.enqueue_data( ["process_log_data", result] )
        return result

    def process_cosbench_data(self, path, dirname):
        result = {}
        result["cosbench"] = OrderedDict()
        result["cosbench"]["cosbench"] = OrderedDict([("read_lat",0), ("read_bw",0), ("read_iops",0), ("write_lat",0), ("write_bw",0), ("write_iops",0), ("lat_unit",'msec'), ('runtime_unit','sec'), ('bw_unit','MB/s')])
        tmp = result
        keys = common.bash("head -n 1 %s/%s.csv" %(path, dirname))
        keys = keys.split(',')
        values = common.bash('tail -n 1 %s/%s.csv' %(path, dirname) )
        values = values.split(',')
        size = len(keys)
        for i in range(size):
            tmp[keys[i]] = {}
            tmp[keys[i]]["detail"] = {}
            tmp[keys[i]]["detail"]["value"] = values[i]
        tmp = result["cosbench"]["cosbench"]
        io_pattern = result["Op-Type"]["detail"]["value"]
        tmp["%s_lat" % io_pattern] = result["Avg-ResTime"]["detail"]["value"]
        tmp["%s_bw" % io_pattern] = common.size_to_Kbytes('%s%s' % (result["Bandwidth"]["detail"]["value"], 'B'), 'MB')
        tmp["%s_iops" % io_pattern] = result["Throughput"]["detail"]["value"]
        self.workpool.enqueue_data( ["process_cosbench_data", result ])
        return result

    def get_validate_runtime(self):
        self.validate_time = 0
        dest_dir = self.cluster["dest_dir"]
        stdout = common.bash( 'grep " runt=.*" -r %s' % (dest_dir) )
        fio_runtime_list = re.findall('runt=\s*(\d+\wsec)', stdout)
        for fio_runtime in fio_runtime_list:
            validate_time = common.time_to_sec(fio_runtime, 'sec')
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

    def process_fiolog_data(self, path, volume_name):
        result = {}
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
                        #print "%s %d" % (path, cur_sec)
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
                        #print "%s %d" % (path, cur_sec)
                    self.tmp_res.append( value )
                if len(self.tmp_res) != 0:
                    res.append(numpy.mean(self.tmp_res))
        self.workpool.enqueue_data( ["process_fiolog_data", volume_name, result] )
        #print "pid:%d done" % os.getpid()
        return result

    def process_sar_data(self, path):
        result = {}
        #1. cpu
        stdout = common.bash( "grep ' *CPU *%' -m 1 "+path+" | awk -F\"CPU\" '{print $2}'; cat "+path+" | grep ' *CPU *%' -A 1 | awk '{flag=0;if(NF<=3)next;for(i=1;i<=NF;i++){if(flag==1){printf $i\"\"FS}if($i==\"all\")flag=1};if(flag==1)print \"\"}'" )
        result["cpu"] = common.convert_table_to_2Dlist(stdout)

        #2. memory
        stdout = common.bash( "grep 'kbmemfree' -m 1 "+path+" | awk -Fkbmemfree '{printf \"kbmenfree  \";print $2}'; grep \"kbmemfree\" -A 1 "+path+" | awk 'BEGIN{find=0;}{for(i=1;i<=NF;i++){if($i==\"kbmemfree\"){find=i;next;}}if(find!=0){for(j=find;j<=NF;j++)printf $j\"\"FS;find=0;print \"\"}}'" )
        result["memory"] = common.convert_table_to_2Dlist(stdout)

        #3. nic
        stdout = common.bash( "grep 'IFACE' -m 1 "+path+" | awk -FIFACE '{print $2}'; cat "+path+" | awk 'BEGIN{find=0;}{for(i=1;i<=NF;i++){if($i==\"IFACE\"){j=i+1;if($j==\"rxpck/s\"){find=1;start_col=j;col=NF;for(k=1;k<=col;k++){res_arr[k]=0;}next};if($j==\"rxerr/s\"){find=0;for(k=start_col;k<=col;k++)printf res_arr[k]\"\"FS; print \"\";next}}if($i==\"lo\")next;if(find){res_arr[i]+=$i}}}'" )
        result["nic"] = common.convert_table_to_2Dlist(stdout)
        #4. tps
        self.workpool.enqueue_data( ["process_sar_data", result] )
        return result

    def process_iostat_data(self, node, path):
        result = {}
        output_list = []
        dict_diskformat = {}
        if node in self.cluster["osds"]:
            output_list = common.parse_disk_format( self.cluster['diskformat'] )
            for i in range(len(output_list)):
                disk_list=[]
                for osd_journal in common.get_list(self.all_conf_data.get_list(node)): 
                   tmp_dev_name = osd_journal[i].split('/')[2]
                   if 'nvme' in tmp_dev_name:
                       tmp_dev_name = common.parse_nvme( tmp_dev_name )
                   if tmp_dev_name not in disk_list:
                       disk_list.append( tmp_dev_name )
                dict_diskformat[output_list[i]]=disk_list
        elif node in self.cluster["vclient"]:
            vdisk_list = []
            for disk in self.cluster["vclient_disk"]:
                vdisk_list.append( disk.split('/')[2] )
            output_list = ["vdisk"]
        # get total second
        runtime = common.bash("grep 'Device' "+path+" | wc -l ").strip()
        for output in output_list:
            if output != "vdisk":
                disk_list = " ".join(dict_diskformat[output])
                disk_num = len(list(set(dict_diskformat[output])))
            else:
                disk_list = " ".join(vdisk_list)
                disk_num = len(vdisk_list)
            stdout = common.bash( "grep 'Device' -m 1 "+path+" | awk -F\"Device:\" '{print $2}'; cat "+path+" | awk -v dev=\""+disk_list+"\" -v line="+runtime+" 'BEGIN{split(dev,dev_arr,\" \");dev_count=0;for(k in dev_arr){count[k]=0;dev_count+=1};for(i=1;i<=line;i++)for(j=1;j<=NF;j++){res_arr[i,j]=0}}{for(k in dev_arr)if(dev_arr[k]==$1){cur_line=count[k];for(j=2;j<=NF;j++){res_arr[cur_line,j]+=$j;}count[k]+=1;col=NF}}END{for(i=1;i<=line;i++){for(j=2;j<=col;j++)printf (res_arr[i,j]/dev_count)\"\"FS; print \"\"}}'")
            result[output] = common.convert_table_to_2Dlist(stdout)
            result[output]["disk_num"] = disk_num
        self.workpool.enqueue_data( ["process_iostat_data", result] )
        return result

    def process_vdbench_data(self, path, dirname):
        result = {}
        vdbench_data = {}
        runtime = int(common.bash("grep -o 'elapsed=[0-9]\+' "+path+" | cut -d = -f 2"))
        stdout, stderr = common.bash("grep 'avg_2-' "+path, True)
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
        self.workpool.enqueue_data( ["process_vdbench_data", result] )
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
        stdout, stderr = common.bash("grep \" IOPS=.*BW=.*\| *io=.*bw=.*iops=.*runt=.*\|^ *lat.*min=.*max=.*avg=.*stdev=.*\" "+path, True)
        stdout1, stderr1 = common.bash("grep \" *1.00th.*],\| *30.00th.*],\| *70.00th.*],\| *99.00th.*],\| *99.99th.*]\" "+path, True)
        stdout2, stderr2 = common.bash("grep \" *clat percentiles\" "+path, True)
        lat_per_dict = {}
        if stdout1 != '':
            lat_per_dict = self.get_lat_persent_dict(stdout1)

        fio_data_rw = {}
        fio_data_rw["read"] = {}
        fio_data_rw["write"] = {}
        fio_data = {}
        for data in re.split(',|\n|:',stdout):
            try:
                key, value = data.split('=')
                if key.strip().lower() not in fio_data:
                    fio_data[key.strip().lower()] = []
                    fio_data[key.strip().lower()].append( value.strip() )
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
            for tmp_key in ["95.00th", "99.00th", "99.99th"]:
                if tmp_key in lat_per_dict.keys():
                    lat_persent_unit = re.findall(r"(?<=[\(])[^\)]+(?=[\)])", stdout2.strip('\n').strip(' ').replace(' ',''))
                    if len(lat_persent_unit) != 0:
                        output_fio_data[tmp_key+"%_lat"] = float(common.time_to_sec("%s%s" % (lat_per_dict[tmp_key], lat_persent_unit[0]),'msec'))
                    else:
                        output_fio_data[tmp_key+"%_lat"] = 'null'
                else:
                    output_fio_data[tmp_key+"%_lat"] = 'null'
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
                if "avg" in fio_data:
                    output_fio_data['%s_lat' % io_pattern] += float(common.time_to_sec("%s%s" % (fio_data['avg'][index], fio_data['lat_unit'][index]),'msec'))
                if "iops" in fio_data:
                    output_fio_data['%s_iops' % io_pattern] += int(fio_data['iops'][index])
                if "bw" in fio_data:
                    res = re.search('(\d+\.*\d*)\s*(\w+)/s',fio_data['bw'][index])
                    if res:
                        output_fio_data['%s_bw' % io_pattern] += float( common.size_to_Kbytes("%s%s" % (res.group(1), res.group(2)),'MB') )
                if "runt" in fio_data:
                    output_fio_data['%s_runtime' % io_pattern] += float( common.time_to_sec(fio_data['runt'][index], 'sec') )
            output_fio_data['%s_lat' % io_pattern] /= list_len
            output_fio_data['%s_runtime' % io_pattern] /= list_len
        result[dirname] = {}
        result[dirname]["fio"] = output_fio_data
        
        self.workpool.enqueue_data( ["process_fio_data", result] )
        return result

    def process_lttng_data(self, path):
        pass

    def process_blktrace_data(self, path):
        pass

    def process_perfcounter_data(self, dir_name, path):
    #def process_perfcounter_data(self, path):
        precise_level = int(self.cluster["perfcounter_time_precision_level"])
#        precise_level = 6
        common.printout("LOG","loading %s" % path)
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
        result = common.MergableDict()
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
        self.workpool.enqueue_data( ["process_perfcounter_data", dir_name, output] )
        return output

class WorkPool:
    def __init__(self, cn):
        #1. get system available
        self.cpu_total = multiprocessing.cpu_count()
        self.running_process = []
        self.lock = Lock()
        self.process_return_val_queue = Queue()
        self.common = cn
        self.queue_check = False
        self.inflight_process_count = 0

    def schedule(self, function_name, *argv):
        self.wait_at_least_one_free_process()
        if (self.cpu_total - len(self.running_process)) > 0:
            p = Process(target=function_name, args=tuple(argv))
            p.daemon = True
            self.running_process.append(p)
            self.inflight_process_count += 1
            p.start()
            self.common.printout("LOG","Process "+str(p.pid)+", function_name:"+str(function_name.__name__))

            check_thread = threading.Thread(target=self.update_result, args = ())
            check_thread.daemon = True
            check_thread.start()

    def wait_at_least_one_free_process(self):
        start = time.clock()
        while (self.cpu_total - len(self.running_process)) <= 0:
            for proc in self.running_process:
                if not proc.is_alive():
                    proc.join()
                    self.running_process.remove(proc)
                    return
            if time.clock() - start > 1:
                self.common.printout("LOG","Looking for available process, %d proc pending, pids are: %s" % (len(self.running_process), [x.pid for x in self.running_process]))
                start = time.clock()

    def wait_all(self):
        running_proc = self.running_process
        self.common.printout("LOG","Waiting %d Processes to be done" % len(running_proc))
  
        for proc in running_proc:
            proc.join()
            self.running_process.remove(proc)
            self.common.printout("LOG","PID %d Joined" % proc.pid)
        while self.inflight_process_count:
            time.sleep(1)

    def set_return_data_set(self, fio_log_res, workload_result, result):
        self.fio_log_res = fio_log_res
        self.workload_result = workload_result
        self.result = result

    def update_result(self):
        if self.queue_check:
            return
        self.queue_check = True
        while self.inflight_process_count:
            if self.process_return_val_queue.empty():
                time.sleep(1)
                continue
            res = self.process_return_val_queue.get()
            self.inflight_process_count -= 1
            self.common.printout("LOG", "Updating on %s" % res[0])
            if res[0] == "process_smartinfo_data":
                self.result.update(res[1])
            elif res[0] == "process_cosbench_data":
                self.workload_result.update(res[1])
            elif res[0] == "process_sar_data":
                self.result.update(res[1])
            elif res[0] == "process_vdbench_data":
                self.workload_result.update(res[1])
            elif res[0] == "process_fio_data":
                self.workload_result.update(res[1])
            elif res[0] == "process_fiolog_data":
                volume = res[1]
                if volume not in self.fio_log_res:
                    self.fio_log_res[volume] = {}
                    self.fio_log_res[volume]["fio_log"] = {}
                self.fio_log_res[volume]["fio_log"].update(res[2])
                self.workload_result.update(self.fio_log_res)
            elif res[0] == "process_iostat_data":
                self.result.update(res[1])
            elif res[0] == "process_log_data":
                self.result.update(res[1])
            elif res[0] == "process_perfcounter_data":
                dir_name = res[1]
                for key, value in res[2].items():
                    if dir_name not in self.workload_result:
                        self.workload_result[dir_name] = OrderedDict()
                    self.workload_result[dir_name][key] = value
        self.queue_check = False

    def enqueue_data(self, data):
        self.process_return_val_queue.put(data)

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
        '--copy_data_to_remote',
        default = False,
        action='store_true'
        )
    args = parser.parse_args(args)
    process = Analyzer(args.path)
    if args.operation == "process_data":
        use_tmp = not args.copy_data_to_remote
        process.process_data(use_tmp)
    else:
        func = getattr(process, args.operation)
        if func:
            func(args.path_detail)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
