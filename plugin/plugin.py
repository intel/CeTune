#!/usr/bin/python
import yaml
import sys
import os
from subprocess import *
import re
import socket
import argparse

lib_path = os.path.abspath(os.path.join('ceph-tools/cbt/'))
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
        help = 'specify the cbt config path, default using ceph-perf/cbt/tmp.yaml  ',
        )
    args = parser.parse_args()
    if args.operation == "deploy":
        if args.engine == "cbt" or args.engine == "CBT":
            yaml_file = "ceph-tools/cbt/tmp.yaml"
            config = ConfigHub()
            config.load_all_conf()
            config.copy_all_to_yaml()
            config.write_yaml( yaml_file )
            
            cbt_api = CBTAPI( yaml_file )
            cbt_api.deploy_ceph_cluster()
    elif args.operation == "benchmark":
        if args.engine == "cosbench":
            if args.cbt_yaml:
                yaml_file = args.cbt_yaml
            else:
                yaml_file = "ceph-tools/cbt/tmp.yaml"
            print yaml_file

