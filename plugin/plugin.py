#!/usr/bin/python
import yaml
import sys
import os
import subprocess
import re
import socket
import argparse
import cbt_api
import types

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

def bash(command, force=False):
    args = ['bash', '-c', command]
    #print('bash: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    return [stdout, stderr]

def check_dependency():
    pass

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
    args = parser.parse_args()
    if args.operation == "check":
        check_dependency()
    if args.operation == "deploy":
        if args.engine == "cbt" or args.engine == "CBT":
            yaml_file = "tmp.1.yaml"
            config = ConfigHub()
            config.load_all_conf()
            config.copy_all_to_yaml()
            config.write_yaml( yaml_file )
            
            _cbt_api = cbt_api.CBTAPI( yaml_file )
            _cbt_api.deploy_ceph_cluster()
    elif args.operation == "benchmark":
        if args.engine == "cbt":
            if args.cbt_yaml:
                yaml_file = args.cbt_yaml
            else:
                yaml_file = "tmp.1.yaml"
            _cbt_api = cbt_api.CBTAPI( yaml_file )
            _cbt_api.run_benchmark("cosbench")
