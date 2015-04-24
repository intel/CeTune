import time
import os
import errno
import sys
import re
import subprocess
import pprint
import json
import copy
import yaml
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
import socket
import struct

class Config():
    def __init__(self, conf_path):
        self.conf_data = {}
        cur_conf_section = self.conf_data
        with open(conf_path, "r") as f:
            for line in f:
                if re.search('^#', line):
                    continue
                section = re.search('^\[(\w+)\]', line)
                if section:
                    self.conf_data[section.group(1)] = {}
                    cur_conf_section = self.conf_data[section.group(1)]
                else:
                    try:
                        key, value = line.split("=")
                        key = key.strip()
                        value = value.strip()
                    except:
                        pass
                    if( value[-1] == '\n' ):
                        cur_conf_section[key] = value[:-1]
                    else:
                        cur_conf_section[key] = value
                    if re.search(',', cur_conf_section[key]):
                        cur_conf_section[key] = cur_conf_section[key].split(",")

    def dump(self):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.conf_data)

    def get(self, key):
        if key in self.conf_data:
            return self.conf_data[key]
        else:
            print "%s not defined in all.conf" % key
            sys.exit()

    def get_list(self,key):
	if key in self.conf_data:
	    if type(self.conf_data[key]) == str:
		return [self.conf_data[key]]
	    else:
		return self.conf_data[key]
	else:
	    print "%s not defined in all.conf" % key

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class IPHandler:
    def makeMask(self,n):
        "return a mask of n bits as a long integer"
        return (2L<<n-1) - 1
    
    def dottedQuadToNum(self,ip):
        res = re.search(r'(\d+).(\d+).(\d+).(\d+)',ip)
        ip_hex = "%02x" % int(res.group(1))
        ip_hex += "%02x" % int(res.group(2))
        ip_hex += "%02x" % int(res.group(3))
        ip_hex += "%02x" % int(res.group(4))
        return int(ip_hex,16)
    
    def networkMask(self,subnet):
        "Convert a network address to a long integer" 
        res = re.search(r'(\d+.\d+.\d+.\d+)/(\d+)',subnet)
        ip = res.group(1)
        bits = int(res.group(2))
        return self.dottedQuadToNum(ip) & self.makeMask(bits)
    
    def addressInNetwork(self,ip,net):
       "Is an address in a network"
       return ip & net == net

    def getIpByHostInSubnet(self, hostname, subnet ):
        "Get IP by hostname and filter with subnet"
        (hostname, aliaslist, ipaddrlist) = socket.gethostbyname_ex(hostname)
        network = self.networkMask(subnet)
        for ip in ipaddrlist:
            if self.addressInNetwork(self.dottedQuadToNum(ip),network):
                return ip


def get_list( string ):
    res = []
    if isinstance(string, str):
        string = string.split(",")
    for value in string:
        if re.search(":", value):
            res.append(value.split(':'))
        else:
            res.append(value)
    return res

def pdsh(user, nodes, command, option="error_check"):
    _nodes = []
    for node in nodes:
        _nodes.append("%s@%s" % (user, node))
    _nodes = ",".join(_nodes)
    args = ['pdsh', '-R', 'ssh', '-w', _nodes, command]
    #print('pdsh: %s' % args)
    if option == "force":
        _subp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return _subp
    if option == "non_blocking_return":
        _subp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        flags = fcntl(_subp.stdout, F_GETFL)
        fcntl(_subp.stdout, F_SETFL, flags | O_NONBLOCK)
        time.sleep(1)
        while True:
            try:
                print read(_subp.stdout.fileno())
            except:
                break
        return _subp
    if option == "check_return":
        stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
        return [stdout, stderr]
    if option == "error_check":
        _subp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        stdout, stderr = _subp.communicate()
        if stderr:
            print('pdsh: %s' % args)
            print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
            sys.exit()

def bash(command, force=False):
    args = ['bash', '-c', command]
    #print('bash: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if force:
        return [stdout, stderr]
    if stderr:
        print('bash: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

def scp(user, node, localfile, remotefile):
    args = ['scp', '-r',localfile, '%s@%s:%s' % (user, node, remotefile)]
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('scp: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

def rscp(user, node, localfile, remotefile):
    args = ['scp', '%s@%s:%s' % (user, node, remotefile), localfile]
    #print('rscp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('rscp: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

def load_yaml_conf(yaml_path):
    config = {}
    try:
        with file(yaml_path) as f:
            g = yaml.safe_load_all(f)
            for new in g:
                config.update(new)
    except IOError, e:
        raise argparse.ArgumentTypeError(str(e))
    return config

def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv

def format_pdsh_return(pdsh_res):
    formatted_output = {}
    for line in pdsh_res.split('\n'):
        #print line
        try:
            node, output = line.split(':', 1)
        except:
            continue
        if node not in formatted_output:
            formatted_output[node] = []
        formatted_output[node].append(output)
    output = {}
    for node in formatted_output:
        output[node] = "\n".join(formatted_output[node])
        try:
            output[node] = json.loads(output[node], object_hook=_decode_dict)
        except:
            pass
    return output

def check_if_adict_contains_bdict(adict, bdict):
    for key in bdict:
        if key in adict:
            if isinstance(adict[key], dict) and isinstance(bdict[key], dict):
                if not check_if_adict_contains_bdict(adict[key], bdict[key]):
                    return False
            else:
                if not str(adict[key]) == str(bdict[key]):
                    print bcolors.OKGREEN + "[LOG]Tuning [%s] differs with current configuration, will apply" % (key+":"+str(bdict[key])) + bcolors.ENDC
                    return False 
        else:
            print key
            return False
    return True      

class MergableDict:
    def __init__(self):
        self.mergable_dict = {}

    def update(self, conf):
        self.mergable_dict = self.update_leaf( self.mergable_dict, conf)

    def update_leaf(self, dest_data, conf):
        #print dest_data
        #print conf
        if dest_data == {}:
            dest_data = copy.deepcopy(conf)
            return dest_data
        if dest_data == conf:
            return dest_data
        if isinstance(conf, str):
            if not isinstance(dest_data, list):
                new_dest_data = [dest_data]
            else:
                new_dest_data = dest_data
            if conf not in new_dest_data:
                new_dest_data.append(conf)
            return new_dest_data
        if isinstance(conf, dict):
            for root in conf:
                if root in dest_data:
                    dest_data[root] = self.update_leaf(dest_data[root], conf[root])
                else:
                    dest_data[root] = conf[root]
            return dest_data

    def dump(self):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.mergable_dict)
       
    def get(self):
        return self.mergable_dict

def size_to_Kbytes(size):
    res = re.search('(\d+)\s*(\w+)',size)
    space_num = float(res.group(1))
    space_unit = res.group(2)
    if space_unit == 'KB':
        return space_num
    last_unit = "-1"
    for unit in ['ZB','EB','PB','TB','GB','MB','KB']:
        if space_unit != last_unit:
            last_unit = unit
            continue
        space_num *= 1024.0
        space_unit = unit
        last_unit = unit
    return space_num
        
