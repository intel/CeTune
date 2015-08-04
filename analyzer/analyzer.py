import os,sys
import argparse
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import common
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
        self.all_conf_data = common.Config("%s/all.conf" % dest_dir)
        self.cluster = {}
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["client"] = self.all_conf_data.get_list("list_client")
        self.cluster["osds"] = self.all_conf_data.get_list("list_ceph")
        self.cluster["mons"] = self.all_conf_data.get_list("list_mon")
        self.cluster["vclient"] = self.all_conf_data.get_list("list_vclient")
        self.cluster["vclient_disk"] = self.all_conf_data.get_list("run_file")
        self.cluster["dest_dir"] = dest_dir
        self.cluster["dest_dir_remote_bak"] = self.all_conf_data.get("dest_dir_remote_bak")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["osd_daemon_num"] = 0
        self.result = OrderedDict()
        self.result["workload"] = OrderedDict()
        self.result["ceph"] = OrderedDict()
        self.result["client"] = OrderedDict()
        self.result["vclient"] = OrderedDict()
        self.get_validate_runtime()
        self.result["runtime"] = int(float(self.validate_time))

    def process_data(self):
        user = self.cluster["user"]
        dest_dir = self.cluster["dest_dir"]
        session_name = dest_dir.split('/')
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
            if dir_name in self.cluster["client"]:
                self.result["client"][dir_name]={}
                system, workload = self._process_data(dir_name)
                self.result["client"][dir_name]=system
                self.result["workload"].update(workload)
            if dir_name in self.cluster["vclient"]:
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
        common.printout("LOG","Write analyzed results into result.json")
        with open('%s/result.json' % dest_dir, 'w') as f:
            json.dump(result, f, indent=4)
        view = visualizer.Visualizer(result, dest_dir)
        output = view.generate_summary_page()
        common.bash("scp -r %s %s" % (dest_dir, self.cluster["dest_dir_remote_bak"]))

        remote_bak, remote_dir = self.cluster["dest_dir_remote_bak"].split(':')
        output = view.generate_history_view(remote_bak, remote_dir, user, self.result["session_name"])

        common.printout("LOG","History view generated, copy to remote")
        with open("%s/cetune_history.html" % dest_dir, 'w') as f:
            f.write(output)
        common.bash("scp -r %s/cetune_history.html %s" % (dest_dir, self.cluster["dest_dir_remote_bak"]))
        common.bash("scp -r ../visualizer/include %s" % (self.cluster["dest_dir_remote_bak"]))

    def format_result_for_visualizer(self, data):
        output_sort = OrderedDict()
        output_sort["summary"] = OrderedDict()
        res = re.search('^(\d+)-(\w+)-(\w+)-(\w+)-(\w+)-(\w+)-(\w+)-(\d+)-(\d+)-(\w+)$',data["session_name"])
        if not res:
            return output_sort
        rampup = int(res.group(8))
        runtime = int(res.group(9))
        phase_name_map = {"cpu": "sar", "memory": "sar", "nic": "sar", "osd": "iostat", "journal": "iostat", "vdisk": "iostat" }

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
                        start = int(data[node_type][node]["phase"][phase_name_map[field_type]]["benchmark_start"])
                        end = int(data[node_type][node]["phase"][phase_name_map[field_type]]["benchmark_stop"])
                        benchmark_active_time = end - start
                        if benchmark_active_time > (rampup + runtime):
                            runtime_end = start + rampup + runtime
                        else:
                            runtime_end = end
                        runtime_start = start + rampup
                        output[field_type][node] = OrderedDict()
                        for colume_name, colume_data in data[node_type][node][field_type].items():
                            if isinstance(colume_data, list):
                                colume_data = colume_data[runtime_start:runtime_end]
                            output[field_type][node][colume_name] = colume_data
                    else:
                        output[field_type][node] = data[node_type][node][field_type]
            for key in sorted(output.keys()):
                output_sort[node_type][key] = copy.deepcopy( output[key] )

        return output_sort

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
        tmp_data["op_size"] = res.group(5)
        tmp_data["op_type"] = res.group(4)
        tmp_data["QD"] = res.group(6)
        tmp_data["engine"] = res.group(3)
        tmp_data["serverNum"] = 0
        tmp_data["clientNum"] = 0
        tmp_data["worker"] = res.group(2)
        tmp_data["runtime"] = "%d sec" % (data["runtime"])
        tmp_data["workload_iops"] = 0
        tmp_data["workload_bw"] = 0
        tmp_data["workload_latency"] = 0
        tmp_data["osd_iops"] = 0
        tmp_data["osd_bw"] = 0
        tmp_data["osd_latency"] = 0
        rbd_count = 0
        osd_node_count = 0
        try:
            for engine_candidate in data["workload"].keys():
                if engine_candidate in benchmark_tool:
                    engine = engine_candidate
            for node, node_data in data["workload"][engine].items():
                rbd_count += 1
                tmp_data["workload_iops"] += ( float(node_data["read_iops"]) + float(node_data["write_iops"]) )
                tmp_data["workload_bw"] += ( float(node_data["read_bw"]) + float(node_data["write_bw"]) )
                tmp_data["workload_latency"] += ( float(node_data["read_lat"]) + float(node_data["write_lat"]) )
            tmp_data["workload_iops"] = "%.3f" % (tmp_data["workload_iops"])
            tmp_data["workload_bw"] = "%.3f MB/s" % (tmp_data["workload_bw"])
            if rbd_count > 0:
                tmp_data["workload_latency"] = "%.3f msec" % (tmp_data["workload_latency"]/rbd_count)
        except:
            pass
        if tmp_data["op_type"] in ["randread", "seqread", "read"]:
            for node, node_data in data["ceph"]["osd"].items():
                osd_node_count += 1
                tmp_data["osd_iops"] += numpy.mean(node_data["r/s"])*int(node_data["disk_num"])
                tmp_data["osd_bw"] += numpy.mean(node_data["rMB/s"])*int(node_data["disk_num"])
                tmp_data["osd_latency"] += numpy.mean(node_data["r_await"])
        if tmp_data["op_type"] in ["randwrite", "seqwrite", "write"]:
            for node, node_data in data["ceph"]["osd"].items():
                osd_node_count += 1
                tmp_data["osd_iops"] += numpy.mean(node_data["w/s"])*int(node_data["disk_num"])
                tmp_data["osd_bw"] += numpy.mean(node_data["wMB/s"])*int(node_data["disk_num"])
                tmp_data["osd_latency"] += numpy.mean(node_data["w_await"])
        tmp_data["osd_iops"] = "%.3f" % (tmp_data["osd_iops"])
        tmp_data["osd_bw"] = "%.3f MB/s" % (tmp_data["osd_bw"])
        if osd_node_count > 0:
            tmp_data["osd_latency"] = "%.3f msec" % (tmp_data["osd_latency"]/osd_node_count)

        tmp_data["serverNum"] = osd_node_count
        tmp_data["clientNum"] = len(data["client"]["cpu"])
        return data

    def _process_data(self, node_name):
        result = {}
        workload_result = {}
        dest_dir = self.cluster["dest_dir"]
        for dir_name in os.listdir("%s/%s" % (dest_dir, node_name)):
            common.printout("LOG","Processing %s_%s" % (node_name, dir_name))
            if 'cosbench' in dir_name:
                workload_result.update(self.process_cosbench_data("%s/%s/%s" %(dest_dir, node_name, dir_name), dir_name))
            if '_sar.txt' in dir_name:
                result.update(self.process_sar_data("%s/%s/%s" % (dest_dir, node_name, dir_name)))
            if '_fio.txt' in dir_name:
                workload_result.update(self.process_fio_data("%s/%s/%s" % (dest_dir, node_name, dir_name), dir_name))
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

    def process_sar_data(self, path):
        result = {}
        #1. cpu
        stdout = common.bash( "grep ' *CPU *%' -m 1 "+path+" | awk -F\"CPU\" '{print $2}'; cat "+path+" | grep ' *CPU *%' -A 1 | awk '{if($3==\"all\"){for(i=4;i<=NF;i++)printf $i\"\"FS; print \"\"}}'" )
        result["cpu"] = common.convert_table_to_2Dlist(stdout)

        #2. memory
        stdout = common.bash( "grep 'kbmemfree' -m 1 "+path+" | awk -F\"AM|PM\" '{print $2}'; cat "+path+" | awk 'BEGIN{find=0;}{if($3==\"kbmemfree\"){find=1}else if(find==1){for(i=3;i<=NF;i++)printf $i\"\"FS;print \"\";find=0}}'" )
        result["memory"] = common.convert_table_to_2Dlist(stdout)

        #3. nic
        stdout = common.bash( "grep 'IFACE' -m 1 "+path+" | awk -F\"IFACE\" '{print $2}'; cat "+path+" | awk 'BEGIN{find=0;}{if($3==\"IFACE\" && $4==\"rxpck/s\"){find=1;count=0;col=NF;for(i=1;i<=col;i++){res_arr[i]=0}};if($4==\"rxerr/s\"){find=0;for(i=4;i<=col;i++)printf res_arr[i]\"\"FS; print \"\"}if(find && $3!=\"lo\"){for(i=1;i<=col;i++)res_arr[i]+=$i }}'" )
        result["nic"] = common.convert_table_to_2Dlist(stdout)
        #4. tps
        return result

    def process_iostat_data(self, node, path):
        result = {}
        output_list = []
        if node in self.cluster["osds"]:
            osd_list = []
            journal_list = []
            for osd_journal in common.get_list( self.all_conf_data.get_list(node) ):
               osd_list.append( osd_journal[0].split('/')[2] )
               journal_list.append( osd_journal[1].split('/')[2] )
            output_list = ["osd", "journal"]
        elif node in self.cluster["vclient"]:
            vdisk_list = []
            for disk in self.cluster["vclient_disk"]:
                vdisk_list.append( disk.split('/')[2] )
            output_list = ["vdisk"]
        # get total second
        runtime = common.bash("grep 'Device' "+path+" | wc -l ").strip()
        for output in output_list:
            if output == "osd":
                disk_list = " ".join(osd_list)
                disk_num = len(osd_list)
            if output == "journal":
                disk_list = " ".join(journal_list)
                disk_num = len(journal_list)
            if output == "vdisk":
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
        for key in ["osd", "filestore", "objecter"]:
            output["perfcounter_"+key] = {}
            current = output["perfcounter_"+key]
            if not key in result:
                continue
            for param, data in result[key].items():
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
                            current[param].append( round((data['sum'][i]-last_sum)/(data['avgcount'][i]-last_avgcount),3) )
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
    if args.operation == "process_iostat_data":
        process.process_iostat_data(args.node, args.path_detail)
    else:
        func = getattr(process, args.operation)
        if func:
            func()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
