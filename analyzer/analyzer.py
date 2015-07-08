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

        self.result = {}
        self.result["ceph"] = OrderedDict()
        self.result["client"] = OrderedDict()
        self.result["vclient"] = OrderedDict()
        self.result["cosbench"] = OrderedDict()
        self.result["fio"] = OrderedDict()
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
            if dir_name == 'cosbench':
                self.result["cosbench"][dir_name]={}
                system, fio = self._process_data(dir_name)
                self.result["cosbench"][dir_name]=system

            if dir_name in self.cluster["osds"]:
                self.result["ceph"][dir_name]={}
                system, fio = self._process_data(dir_name)
                self.result["ceph"][dir_name]=system
            if dir_name in self.cluster["client"]: 
                self.result["client"][dir_name]={}
                system, fio = self._process_data(dir_name)
                self.result["client"][dir_name]=system
                self.result["fio"].update(fio)
            if dir_name in self.cluster["vclient"]: 
                self.result["vclient"][dir_name]={}
                system, fio = self._process_data(dir_name)
                self.result["vclient"][dir_name]=system
                self.result["fio"].update(fio)
       
        print self.result
        view = visualizer.Visualizer(self.result)
        output = view.generate_summary_page()
        with open("%s/%s.html" % (dest_dir, self.result["session_name"]), 'w') as f:
            f.write(output)
        common.bash("cp -r %s %s" % ("../visualizer/include/", dest_dir))
        common.bash("scp -r %s %s" % (dest_dir, self.cluster["dest_dir_remote_bak"]))
        
        remote_bak, remote_dir = self.cluster["dest_dir_remote_bak"].split(':')
        output = view.generate_history_view(remote_bak, remote_dir, user, self.result["session_name"])
        common.printout("LOG","History view generated, copy to remote")
        with open("%s/cetune_history.html" % dest_dir, 'w') as f:
            f.write(output)
        common.bash("scp -r %s/cetune_history.html %s" % (dest_dir, self.cluster["dest_dir_remote_bak"]))
        common.bash("scp -r ../visualizer/include %s" % (self.cluster["dest_dir_remote_bak"]))
    
    def _process_data(self, node_name):
        result = {}
        fio_result = {}
        dest_dir = self.cluster["dest_dir"]
        for dir_name in os.listdir("%s/%s" % (dest_dir, node_name)):
            common.printout("LOG","Processing %s_%s" % (node_name, dir_name))
            if '_cosbench.csv' in dir_name:
                result.update(self.process_cosbench_data("%s/%s/%s" %(dest_dir, node_name, dir_name)))
            if '_sar.txt' in dir_name:
                result.update(self.process_sar_data("%s/%s/%s" % (dest_dir, node_name, dir_name)))
            if '_fio.txt' in dir_name:
                fio_result.update(self.process_fio_data("%s/%s/%s" % (dest_dir, node_name, dir_name), dir_name))
            if '_iostat.txt' in dir_name:
                res = self.process_iostat_data( node_name, "%s/%s/%s" % (dest_dir, node_name, dir_name))
                result.update(res)
            if '.asok.txt' in dir_name:
                try:
                    res = self.process_perfcounter_data("%s/%s/%s" % (dest_dir, node_name, dir_name), dir_name)
                    for key, value in res.items():
                        if not key in result:
                            result[key] = OrderedDict()
                        result[key].update(value)
                except:
                    pass
            
        return [result, fio_result]

    def process_cosbench_data(self,path):
        result = {}
        keys = common.bash("head -n 1 %s" %(path))
        print 'keys are '+keys
        keys = keys.split(',')
        values = common.bash('tail -n 1 %s' %(path) )
        print 'values are '+values
        values = values.split(',')
        size = len(keys)
        for i in range(size):
            result[keys[i]] = values[i]
        return result

    def get_validate_runtime(self):
        self.validate_time = 0
        dest_dir = self.cluster["dest_dir"]
        stdout = common.bash( 'grep " runt=.*" -r %s' % (dest_dir) )
        fio_runtime = re.search('runt=\s*(\d+\wsec)', stdout)
        if fio_runtime:
            validate_time = common.time_to_sec(fio_runtime.group(1), 'sec')
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
        stdout = common.bash("grep \" *io=.*bw=.*iops=.*runt=.*\|^ *lat.*min=.*max=.*avg=.*stdev=.*\" "+path)
        fio_data = {}
        for data in re.split(',|\n|:',stdout):
            try:
                key, value = data.split("=")
                fio_data[key.strip()] = value.strip()
            except:
                if 'lat' in data:
                    res = re.search('lat\s*\((\w+)\)',data)
                    fio_data['lat_unit'] = res.group(1)
        output_fio_data = OrderedDict()
        try:
            output_fio_data['lat'] = common.time_to_sec("%s%s" % (fio_data['avg'], fio_data['lat_unit']),'msec')
            output_fio_data['iops'] = fio_data['iops']
            res = re.search('(\d+\.*\d*)\s*(\w+)/s',fio_data['bw'])
            if res:
                output_fio_data['bw'] = common.size_to_Kbytes("%s%s" % (res.group(1), res.group(2)),'MB')
            output_fio_data['runtime'] = common.time_to_sec(fio_data['runt'], 'sec')
            output_fio_data['lat_unit'] = 'msec'
            output_fio_data['runtime_unit'] = 'sec'
            output_fio_data['bw_unit'] = 'MB/s'
        except:
            pass
        result[dirname] = {}
        result[dirname]["fio"] = output_fio_data
        return result

    def process_lttng_data(self, path):
        pass        

    def process_perf_data(self, path):
        pass        

    def process_blktrace_data(self, path):
        pass        

    def process_perfcounter_data(self, path, dirname):
        common.printout("LOG","loading %s" % path)
        perfcounter = []
        try:
            with open(path,"r") as fd:
                data = fd.readlines()
            if re.search('^,\n', data[0]):
                if ',' in data[-1]:
                    tmp_data = "[\n"+"\n".join(data[1:-1])+"]"
                else:
                    tmp_data = "[\n"+"\n".join(data[1:])+"]"
            elif ',' in data[-1]:
                tmp_data = "[\n"+"\n".join(data[:-1])+"]"
            else:
                tmp_data = "[\n"+"\n".join(data)+"]"
            perfcounter = yaml.load(tmp_data)
        except IOError as e:
            raise
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
            output["perfcounter_"+key][dirname] = {}
            current = output["perfcounter_"+key][dirname]
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
    args = parser.parse_args(args)
    process = Analyzer(args.path)
    func = getattr(process, args.operation)
    if func:
        func()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
