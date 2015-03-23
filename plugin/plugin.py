#!/usr/bin/python
import yaml
import sys
import os
from subprocess import *
import re
import socket
import argparse
import json
lib_path = os.path.abspath(os.path.join('cbt/'))
sys.path.append(lib_path)
import cbt
import settings
import common
import benchmarkfactory
from cluster.ceph import Ceph

def get_list( string ):
    res = []
    for value in string.split(","):
        if re.search(":", value):
            res.append(value.split(':'))
        else:
            res.append(value)
    return res

def get_len( string ):
    return len(string.split(","))

class CBTAPI:
    config_file = ""
    conf = ""
    archive = ""
 
    def __init__( self, yaml_file ):
        self.config_file = yaml_file
        self.conf = "ceph.conf"
        self.archive = "/opt/"
    
    def deploy_ceph_cluster( self ):
        settings.initialize( self )
        print settings.cluster
        cluster = Ceph(settings.cluster)
        cluster.initialize()

    def run_benchmark(self, benchmark):
        settings.initialize( self )
        print settings.cluster
        cluster = Ceph(settings.cluster)
        if benchmark not in settings.benchmarks:
            return False
        iteration = 0
        while (iteration < settings.cluster.get("iterations", 0)):
            benchmarks = benchmarkfactory.getAll(cluster, iteration)
            for _benchmark in benchmarks:
                if _benchmark.exists():
                    return False
                _benchmark.initialize()
            iteration += 1
        #_benchmark.run()
        #_benchmark.cleanup()

class ConfigHub:
    all_conf_data = {}
    yaml_data = {}
    
    def load_all_conf( self ):
        with open("../conf/all.conf", "r") as f:
            for line in f:
                if( not re.search('^#', line) ):
                    key, value = line.split("=")
                    if( value[-1] == '\n' ):
                        self.all_conf_data[key] = value[:-1]
                    else:
                        self.all_conf_data[key] = value
    
    def write_yaml( self, output ):
        with open(output,"w") as f:
            f.write( yaml.dump(self.yaml_data) )

    def copy_all_to_yaml( self ):
        self.yaml_data["cluster"] = {}
        self.yaml_data["cluster"]["head"] =  os.getenv('HOSTNAME')
        self.yaml_data["cluster"]["clients"] = get_list( self.all_conf_data["deploy_rbd_nodes"] )
        self.yaml_data["cluster"]["osds"] = get_list( self.all_conf_data["deploy_osd_servers"] )
        self.yaml_data["cluster"]["mons"] = {}
        for mon in get_list(self.all_conf_data["deploy_mon_servers"]):
            self.yaml_data["cluster"]["mons"][mon] = { mon: ''.join(socket.gethostbyname(mon)) }
        self.yaml_data["cluster"]["user"] = "root"        
        self.yaml_data["cluster"]["osds_per_node"] = get_len( self.all_conf_data[self.yaml_data["cluster"]["osds"][0]] )       
        for osd in self.yaml_data["cluster"]["osds"]:
            self.yaml_data["cluster"][osd] = []
            for osd_journal in get_list( self.all_conf_data[osd] ):
                self.yaml_data["cluster"][osd].append( osd_journal[0] )
        self.yaml_data["cluster"]["fs"] = "xfs"        
        self.yaml_data["cluster"]["mkfs_opts"] = "-f -i size=2048 -n size=64k"        
        self.yaml_data["cluster"]["mount_opts"] = "-o inode64,noatime,logbsize=256k"
        self.yaml_data["cluster"]["conf_file"] = "ceph.conf"
        self.yaml_data["cluster"]["tmp_dir"] = "/tmp/cbt"
        self.yaml_data["cluster"]["use_existing"] = True
        self.yaml_data["benchmarks"] = {}
        self.yaml_data["benchmarks"]["radosbench"] = {}
    
    def load_yaml_conf(self, cbt_yaml):
        config = self.yaml_data
        try:
            with file(cbt_yaml) as f:
                g = yaml.safe_load_all(f)
                for new in g:
                    config.update(new)
        except IOError, e:
            raise argparse.ArgumentTypeError(str(e))
        

class Cosbench:
    conf={}

    def __init__(self, cosbench_conf_file):
        with open(cosbench_conf_file) as conf_file:
            self.conf = json.load(conf_file)
        with open("./cosbench/NodeList",'w') as node_list:
            node_list.write(self.conf["gw"]+"\n")
            for osd in  self.conf["osd"].split():
                node_list.write(osd+"\n")
            for client in self.conf["ceph_client"].split():
                node_list.write(client+"\n")

    def run_test(self):
        if self.conf["scale"] == "small":
            prefix_xml = self.conf["rw"]+"_100con_100obj_"+self.conf["size"]+"_"
            xml_dir ="./conf/"+self.conf["size"]+"-"+self.conf["rw"]+"/100_100/"
        else:
            prefix_xml = self.conf["rw"]+"_10000con_10000obj_"+self.conf["size"]+"_"
            xml_dir = "./conf/"+self.conf["size"]+"-"+self.conf["rw"]+"-large/"
        old_path = os.getcwd()
        test_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(test_path+"/cosbench/")
        command = "./run1.sh "+self.conf["size"]+"-"+self.conf["rw"]+" "+prefix_xml
        command +=" "+self.conf["cosbench_setup_folder"]+" \""+self.conf["config_list"]+"\" "+self.conf["remote_data_server"] 
        command += " "+self.conf["remote_data_user"]+" "+self.conf["remote_data_dir"]+" " + self.conf["timeout"]+" "+xml_dir
        print command
        os.system(command)
        os.chdir(old_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cephperf third party plugin hub.')
    parser.add_argument(
        '--engine',
        help = 'Choose the PLUGIN: CBT, cosbench.',
        )
    parser.add_argument(
        'operation',
        help = 'Choose the operation: deploy, benchmark  ',
        )
    parser.add_argument(
        '--cbt_yaml',
        help = 'specify the cbt config path, default using cbt/tmp.yaml  ',
        )
    parser.add_argument(
        '--cosbench_config',
        help = 'Choose the path of the cosbench config json file. Default is ./cosbench/cosbench_conf.json'
        )
    args = parser.parse_args()

    if args.operation == "deploy":
        if args.engine == "cbt" or args.engine == "CBT":
            yaml_file = "cbt/tmp.yaml"
            config = ConfigHub()
            config.load_all_conf()
            config.copy_all_to_yaml()
            config.write_yaml( yaml_file )
            
            cbt_api = CBTAPI( yaml_file )
            cbt_api.deploy_ceph_cluster()
    elif args.operation == "benchmark":
<<<<<<< HEAD
        if args.engine == "cosbench":
            if args.cosbench_config:
                cosbench_instance = Cosbench(args.cosbench_config)
            else:
                cosbench_instance = Cosbench("./cosbench/cosbench_conf.json")
                cosbench_instance.run_test()
=======
        if args.engine == "cbt":
            if args.cbt_yaml:
                yaml_file = args.cbt_yaml
            else:
                yaml_file = "cbt/conf/cosbench/tmp.1.yaml"
            cbt_api = CBTAPI( yaml_file )
            cbt_api.run_benchmark("cosbench")
>>>>>>> 223f797b7b1abfcdb702b1dff4a6e94b1309b2ce
