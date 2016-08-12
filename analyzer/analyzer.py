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

    def process_data(self):
        user = self.cluster["user"]
        dest_dir = self.cluster["dest_dir"]
        session_name = self.cluster["dest_dir_root"].split('/')
        if session_name[-1] != '':
            self.result["session_name"] = session_name[-1]
        else:
            self.result["session_name"] = session_name[-2]

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
        head = ''
        head = cf.get("head")
        file_path = dest_dir+"raw/"+head+"/"+head+"_process_log.txt"
        print file_path
        if head != '':
            if os.path.exists(dest_dir+"raw/"+head+"/"):
                with open(file_path, "r") as f:
                    lines = f.readlines()
                if len(lines) != 0 and lines != None:
                    str_time = ''
                    str_time = lines[0].replace('CST ','')
                    str_time = str_time.replace('\n','')
                    str_time = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(str_time))
                    return str_time
            else:
                return ''

    def summary_result(self, data):
        # generate summary
        benchmark_tool = ["fio", "cosbench"]
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
        for dir_name in os.listdir("%s/%s" % (dest_dir, node_name)):
            common.printout("LOG","Processing %s_%s" % (node_name, dir_name))
            if 'smartinfo.txt' in dir_name:
                res = self.process_smartinfo_data( "%s/%s/%s" % (dest_dir, node_name, dir_name))
                result.update(res)
            if 'cosbench' in dir_name:
                workload_result.update(self.process_cosbench_data("%s/%s/%s" %(dest_dir, node_name, dir_name), dir_name))
            if '_sar.txt' in dir_name:
                result.update(self.process_sar_data("%s/%s/%s" % (dest_dir, node_name, dir_name)))
            if '_fio.txt' in dir_name:
                workload_result.update(self.process_fio_data("%s/%s/%s" % (dest_dir, node_name, dir_name), dir_name))
            if '_fio_iops.1.log' in dir_name or '_fio_bw.1.log' in dir_name or '_fio_lat.1.log' in dir_name:
                if "_fio_iops.1.log" in dir_name:
                    volume = dir_name.replace("_fio_iops.1.log", "")
                if "_fio_bw.1.log" in dir_name:
                    volume = dir_name.replace("_fio_bw.1.log", "")
                if "_fio_lat.1.log" in dir_name:
                    volume = dir_name.replace("_fio_lat.1.log", "")
                if volume not in fio_log_res:
                    fio_log_res[volume] = {}
                    fio_log_res[volume]["fio_log"] = {}
                fio_log_res[volume]["fio_log"] = self.process_fiolog_data("%s/%s/%s" % (dest_dir, node_name, dir_name), fio_log_res[volume]["fio_log"] )
                workload_result.update(fio_log_res)
            if '_iostat.txt' in dir_name:
                res = self.process_iostat_data( node_name, "%s/%s/%s" % (dest_dir, node_name, dir_name))
                result.update(res)
            if '_process_log.txt' in dir_name:
                res = self.process_log_data( "%s/%s/%s" % (dest_dir, node_name, dir_name) )
                result.update(res)
            if '.asok.txt' in dir_name:
                try:
                    res = self.process_perfcounter_data("%s/%s/%s" % (dest_dir, node_name, dir_name))
                    for key, value in res.items():
                        if dir_name not in workload_result:
                            workload_result[dir_name] = OrderedDict()
                        workload_result[dir_name][key] = value
                except:
                    pass
        return [result, workload_result]

    def process_smartinfo_data(self, path):
        output = {}
        with open(path, 'r') as f:
            tmp = f.read()
        output.update(json.loads(tmp, object_pairs_hook=OrderedDict))
        return output

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
            for line in f.readlines():
                data = line.split(",")
                timestamp_sec = int(data[0])/time_shift
                value = int(data[1])
                while ( timestamp_sec > (cur_sec + 1) ):
                    res.append( 0 )
                    cur_sec += 1
                if (cur_sec + 1) == timestamp_sec:
                    res.append( value )
                    cur_sec += 1
                elif cur_sec == timestamp_sec:
                    res[-1] = (res[-1] + value)/2
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
                disk_num = len(dict_diskformat[output])
            else:
                disk_list = " ".join(vdisk_list)
                disk_num = len(vdisk_list)
            stdout = common.bash( "grep 'Device' -m 1 "+path+" | awk -F\"Device:\" '{print $2}'; cat "+path+" | awk -v dev=\""+disk_list+"\" -v line="+runtime+" 'BEGIN{split(dev,dev_arr,\" \");dev_count=0;for(k in dev_arr){count[k]=0;dev_count+=1};for(i=1;i<=line;i++)for(j=1;j<=NF;j++){res_arr[i,j]=0}}{for(k in dev_arr)if(dev_arr[k]==$1){cur_line=count[k];for(j=2;j<=NF;j++){res_arr[cur_line,j]+=$j;}count[k]+=1;col=NF}}END{for(i=1;i<=line;i++){for(j=2;j<=col;j++)printf (res_arr[i,j]/dev_count)\"\"FS; print \"\"}}'")
            result[output] = common.convert_table_to_2Dlist(stdout)
            result[output]["disk_num"] = disk_num
        return result

    def process_fio_data(self, path, dirname):
        result = {}
        stdout, stderr = common.bash("grep \" *io=.*bw=.*iops=.*runt=.*\|^ *lat.*min=.*max=.*avg=.*stdev=.*\" "+path, True)
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
                output_fio_data['%s_lat' % io_pattern] += float(common.time_to_sec("%s%s" % (fio_data['avg'][index], fio_data['lat_unit'][index]),'msec'))
                output_fio_data['%s_iops' % io_pattern] += int(fio_data['iops'][index])
                res = re.search('(\d+\.*\d*)\s*(\w+)/s',fio_data['bw'][index])
                if res:
                    output_fio_data['%s_bw' % io_pattern] += float( common.size_to_Kbytes("%s%s" % (res.group(1), res.group(2)),'MB') )
                output_fio_data['%s_runtime' % io_pattern] += float( common.time_to_sec(fio_data['runt'][index], 'sec') )
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
    args = parser.parse_args(args)
    process = Analyzer(args.path)
    if args.operation == "process_data":
        process.process_data()
    else:
        func = getattr(process, args.operation)
        if func:
            func(args.path_detail)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
