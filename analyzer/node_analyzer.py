# -*- coding: utf-8 -*
import os,sys
import argparse
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import *
from visualizer import *
from analyzer import *
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

class Node_analyzer(Analyzer):
    def node_process_data(self):
        self.tmp_dir = sys.argv[2]
        self.node_name = sys.argv[7]
        self.cluster["dest_dir"] = sys.argv[5]
        self.result["session_name"] = sys.argv[5]
        case_type = re.findall('\d\-\S+', self.cluster["dest_dir"])[0].split('-')[2]
        if case_type == "vdbench":
            self.result["description"] = "NULL"
        user = self.cluster["user"]
        if self.node_name in self.cluster["osds"]:
            self.result["ceph"][self.node_name]={}
            system, workload = self._node_process_data(self.tmp_dir)
            self.result["ceph"][self.node_name]=system
            self.result["ceph"].update(workload)
        if self.node_name in self.cluster["rgw"]:
            self.result["rgw"][self.node_name]={}
            system, workload = self._node_process_data(self.tmp_dir)
            self.result["rgw"][self.node_name]=system
            self.result["rgw"].update(workload)
        if self.node_name in self.cluster["client"]:
            self.result["client"][self.node_name]={}
            system, workload = self._node_process_data(self.tmp_dir)
            self.result["client"][self.node_name]=system
            self.result["workload"].update(workload)
        if self.node_name in self.cluster["vclient"]:
            params = self.result["session_name"].split('-')
            self.cluster["vclient_disk"] = ["/dev/%s" % params[-1]]
            self.result["vclient"][self.node_name]={}
            system, workload = self._node_process_data(self.tmp_dir)
            self.result["vclient"][self.node_name]=system
            self.result["workload"].update(workload)

        result = self.format_result_for_visualizer( self.result )
        common.printout("LOG","Write analyzed results into result.json")
        with open('%s/%s_result.json' %(self.tmp_dir,self.node_name), 'w') as f:
            json.dump(result, f, indent=4)

    def node_ceph_version(self,dest_dir):
        node_list = []
        node_list.extend(self.cluster["osds"])
        node_list.append(self.cluster["head"])
        version_list = {}
        node_list = set(node_list)
        for node in node_list:
            if os.path.exists(os.path.join(dest_dir,node+'_ceph_version.txt')):
                data = open(os.path.join(dest_dir,node+'_ceph_version.txt'),'r')
                if data:
                    version_list[node] = data.read().strip('\n')
                else:
                    version_list[node] = 'None'
            else:
                version_list[node] = 'None'
        return version_list

    def _node_process_data(self, tmp_dir):
        result = {}
        fio_log_res = {}
        workload_result = {}
        for dir_name in os.listdir("%s" % (tmp_dir)):
            if os.path.isfile("%s%s"%(tmp_dir,dir_name)):
                common.printout("LOG","Processing %s_%s" % (tmp_dir, dir_name))
                if 'smartinfo.txt' in dir_name:
                    res = self.process_smartinfo_data( "%s/%s" % (tmp_dir, dir_name))
                    result.update(res)
                if 'cosbench' in dir_name:
                    workload_result.update(self.process_cosbench_data("%s/%s" %(tmp_dir, dir_name), dir_name))
                if '_sar.txt' in dir_name:
                    result.update(self.process_sar_data("%s/%s" % (tmp_dir, dir_name)))
                if 'totals.html' in dir_name:
                    workload_result.update(self.process_vdbench_data("%s/%s" % (tmp_dir, dir_name), "%s_%s" % (tmp_dir, dir_name)))
                if '_fio.txt' in dir_name:
                    workload_result.update(self.process_fio_data("%s/%s" % (tmp_dir, dir_name), dir_name))
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
                    fio_log_res[volume]["fio_log"] = self.process_fiolog_data("%s/%s" % (tmp_dir, dir_name), fio_log_res[volume]["fio_log"] )
                    workload_result.update(fio_log_res)
                if '_iostat.txt' in dir_name:
                    res = self.node_process_iostat_data( tmp_dir, "%s/%s" % (tmp_dir, dir_name),self.node_name)
                    result.update(res)
                if '_interrupts_end.txt' in dir_name:
                    if os.path.exists("%s/%s" % ( tmp_dir, dir_name.replace('end','start'))):
                        interrupt_start = "%s/%s" % ( tmp_dir, dir_name)
                        interrupt_end   = "%s/%s" % ( tmp_dir, dir_name.replace('end','start'))
                        self.interrupt_diff(tmp_dir,self.node_name,interrupt_start,interrupt_end)
                if '_process_log.txt' in dir_name:
                    res = self.process_log_data( "%s/%s" % (tmp_dir, dir_name) )
                    result.update(res)
                if '.asok.txt' in dir_name:
                    try:
                        res = self.process_perfcounter_data("%s/%s" % (tmp_dir, dir_name))
                        for key, value in res.items():
                            if dir_name not in workload_result:
                                workload_result[dir_name] = OrderedDict()
                            workload_result[dir_name][key] = value
                    except:
                        pass
        return [result, workload_result]


    def interrupt_diff(self,tmp_dir,node_name,s_path,e_path):
        s_p = s_path
        e_p = e_path
        result_name = node_name+'_interrupt.txt'
        result_path = os.path.join(tmp_dir,result_name)
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
                        diff_value = int(e_l[i][j]) - int(s_l[i][j])
                        lines.append(int(e_l[i][j]) - int(s_l[i][j]))
                    else:
                        lines.append(e_l[i][j])
                diff_list.append(lines)
            if os.path.exists(result_path):
                os.remove(result_path)
            output = open(result_path,'w+')
            for line in diff_list:
                line_str = ''
                for col in range(len(line)):
                    if col != len(line)-1:
                        line_str += str(line[col])+'    '
                    else:
                        line_str += str(line[col])
                output.writelines(line_str)
            output.close()
        else:
            print 'ERROR: interrupt_start lines and interrupt_end lines are diffrent ! can not calculate diffrent value!'

    def node_process_iostat_data(self, node, path,node_name):
        result = {}
        output_list = []
        dict_diskformat = {}
        if node_name in self.cluster["osds"]:
            output_list = common.parse_disk_format( self.cluster['diskformat'] )
            for i in range(len(output_list)):
                disk_list=[]
                for osd_journal in common.get_list(self.all_conf_data.get_list(node_name)): 
                   tmp_dev_name = osd_journal[i].split('/')[2]
                   if 'nvme' in tmp_dev_name:
                       tmp_dev_name = common.parse_nvme( tmp_dev_name )
                   if tmp_dev_name not in disk_list:
                       disk_list.append( tmp_dev_name )
                dict_diskformat[output_list[i]]=disk_list
        elif node_name in self.cluster["vclient"]:
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
        return result

def main(args):
    parser = argparse.ArgumentParser(description='Analyzer tool')
    parser.add_argument(
        'operation',
        )
    parser.add_argument(
        '--case_name',
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
        '--node_name',
        )
    args = parser.parse_args(args)
    process = Node_analyzer(args.path)
    if args.operation == "node_process_data":
        process.node_process_data()
    else:
        func = getattr(process, args.operation)
        if func:
            func(args.path_detail)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
