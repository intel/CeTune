import time
import datetime
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
from collections import OrderedDict

cetune_log_file = "../conf/cetune_process.log"
cetune_error_file = "../conf/cetune_error.log"
no_die = False

class Config():
    def __init__(self, conf_path):
        self.conf_data = OrderedDict()
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

    def dump(self, key=""):
        pp = pprint.PrettyPrinter(indent=4)
        try:
            pp.pprint(self.conf_data[key])
        except:
            pp.pprint(self.conf_data)

    def dump_to_file(self, output, key=""):
        with open(output, 'w') as f:
            f.write( self.dump(key) )

    def get(self, key, dotry=False):
        if key in self.conf_data:
            return self.conf_data[key]
        else:
            print "%s not defined in all.conf" % key
            if not dotry:
                sys.exit()
            else:
                return ""

    def get_list(self,key):
        if key in self.conf_data:
            if re.search(',', self.conf_data[key]):
                return self.conf_data[key].split(",")
            else:
                return [self.conf_data[key]]
        else:
            print "%s not defined in all.conf" % key

    def get_all(self):
        return self.conf_data

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

def printout(level, content, screen = True):
    if level == "ERROR":
        output = "[ERROR]: %s" % content
        with open(cetune_error_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if screen:
            print bcolors.FAIL + output + bcolors.ENDC
    if level == "LOG":
        output = "[LOG]: %s" % content
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if screen:
            print bcolors.OKGREEN + output + bcolors.ENDC
    if level == "WARNING":
        output = "[WARNING]: %s" % content
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if screen:
            print bcolors.WARNING + output + bcolors.ENDC
    if level == "CONSOLE":
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),content))
        if screen:
            print content

def remote_dir_exist( user, node, path ):
    stdout, stderr = pdsh(user, [node] ,"test -d %s; echo $?" % path, option = "check_return")
    res = format_pdsh_return(stdout)
    for node, returncode in res.items():
        return int(returncode) == 0

def remote_file_exist( user, node ,path):
    stdout, stderr = pdsh(user, [node], "test -f %s; echo $?" % path, "check_return")
    res = format_pdsh_return(stdout)
    for node, returncode in res.items():
        return int(returncode) == 0

def pdsh(user, nodes, command, option="error_check", nodie=False):
    _nodes = []
    for node in nodes:
        _nodes.append("%s@%s" % (user, node))
    _nodes = ",".join(_nodes)
    args = ['pdsh', '-R', 'exec', '-w', _nodes, 'ssh', '%h', command]
    printout("CONSOLE", args, screen=False)

    _subp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if "force" in option:
        return _subp
    stdout = []
    for line in iter(_subp.stdout.readline,""):
        stdout.append(line)
        if "console" in option:
            print line,

    returncode = _subp.poll()
    #returncode = _subp.returncode
    _subp.stdout.close()
    stderr = _subp.stderr.read()
    stdout = "".join(stdout)
    printout("CONSOLE", stdout, screen=False)

    if "check_return" in option:
        if returncode or "Connection timed out" in stderr:
            if stderr:
                stderr_tmp = stderr.split('\n')
                stderr_print = []
                for line in stderr_tmp:
                    if "ssh exited with exit code 255" not in line:
                        stderr_print.append(line)
                printout("ERROR",'\n'.join(stderr_print), screen=False)
        return [stdout, stderr]
    else:
        if returncode or "Connection timed out" in stderr:
            if stderr:
                stderr_tmp = stderr.split('\n')
                stderr_print = []
                for line in stderr_tmp:
                    if "ssh exited with exit code 255" not in line:
                        stderr_print.append(line)
                print('pdsh: %s' % args)
                printout("ERROR",'\n'.join(stderr_print))
            if not nodie:
                sys.exit()

def bash(command, force=False, option="", nodie=False):
    args = ['bash', '-c', command]
    printout("CONSOLE", args, screen=False)

    _subp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = []
    for line in iter(_subp.stdout.readline,""):
        stdout.append(line)
        if "console" in option:
            print line,
    returncode = _subp.poll()
    _subp.stdout.close()
    stderr = _subp.stderr.read()
    stdout = "".join(stdout)
    printout("CONSOLE", stdout, screen=False)

    if force:
        return [stdout, stderr]
    if returncode:
        if stderr:
            print('bash: %s' % args)
            printout("ERROR",stderr+"\n")
        if not nodie:
            sys.exit()
    return stdout

def scp(user, node, localfile, remotefile):
    args = ['scp', '-r',localfile, '%s@%s:%s' % (user, node, remotefile)]
    printout("CONSOLE", args, screen=False)
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    printout("CONSOLE", stdout, screen=False)
    if stderr:
        print('scp: %s' % args)
        printout("ERROR",stderr+"\n")
        sys.exit()

def rscp(user, node, localfile, remotefile):
    args = ['scp', '-r', '%s@%s:%s' % (user, node, remotefile), localfile]
    #print('rscp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('rscp: %s' % args)
        printout("ERROR",stderr+"\n")
        sys.exit()

# scp from one remote machine to another remote machine
def rrscp(user, node1, node1_file, node2,node2_file):
    args = ['scp', '-r', '%s@%s:%s'%(user,node1,node1_file)  , '%s@%s:%s' % (user, node2, node2_file)]
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('scp: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

def load_yaml_conf(yaml_path):
    config = {}
    with file(yaml_path) as f:
        g = yaml.safe_load_all(f)
        for new in g:
            config.update(new)
    return config

def write_yaml_file(yaml_path, data):
    with file(yaml_path, 'w') as f:
        f.write( yaml.dump(data, indent=4, default_flow_style=False) )

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
    rv = OrderedDict()
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

def convert_table_to_2Dlist(table_str):
    res_dict = OrderedDict()
    first_line = False
    for line in table_str.split('\n'):
        if not first_line:
            title_dict = line.split()
            first_line = True
        else:
            index = 0
            for data in line.split():
                try:
                    data_float = float(data)
                except:
                    continue
                if not index < len(title_dict):
                    continue
                if title_dict[index] not in res_dict:
                    res_dict[title_dict[index]] = []
                res_dict[title_dict[index]].append(data_float)
                index += 1
    return res_dict

def check_if_adict_contains_bdict(adict, bdict):
    for key in bdict:
        if key in adict:
            if isinstance(adict[key], dict) and isinstance(bdict[key], dict):
                if not check_if_adict_contains_bdict(adict[key], bdict[key]):
                    return False
            else:
                if not str(adict[key]) == str(bdict[key]):
                    printout("LOG","Tuning [%s] differs with current configuration, will apply" % (key+":"+str(bdict[key])))
                    return False
        else:
            print key
            return False
    return True

class MergableDict:
    def __init__(self):
        self.mergable_dict = {}

    def update(self, conf, dedup = True, diff = False):
        self.dedup = dedup
        self.diff = diff
        self.mergable_dict = self.update_leaf( self.mergable_dict, conf)

    def update_leaf(self, dest_data, conf):
        #print dest_data
        #print conf
        if dest_data == {}:
            dest_data = copy.deepcopy(conf)
            return dest_data
        if dest_data == conf:
            return dest_data
        if isinstance(conf, str) or isinstance(conf, int) or isinstance(conf, float):
            if not isinstance(dest_data, list):
                new_dest_data = [dest_data]
            else:
                new_dest_data = dest_data
            if not self.dedup:
                if self.diff:
                    conf_tmp = conf
                    conf = round(conf - new_dest_data[0],3)
                    new_dest_data[0] = conf_tmp
                new_dest_data.append(conf)
            else:
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

def size_to_Kbytes(size, dest_unit='KB'):
    res = re.search('(\d+\.*\d*)\s*(\w+)',size)
    space_num = float(res.group(1))
    space_unit = res.group(2)
    if space_unit in ['Z','E','P','T','G','M','K']:
        space_unit += 'B'
    if space_unit == 'bytes':
        space_unit = 'B'
    unit_list = ['ZB','EB','PB','TB','GB','MB','KB','B']
    dest_unit_index = unit_list.index(dest_unit)
    space_unit_index = unit_list.index(space_unit)
    if dest_unit_index > space_unit_index:
        for i in range(space_unit_index, dest_unit_index):
            space_num *= 1024.0
    else:
        for i in range(dest_unit_index, space_unit_index):
            space_num /= 1024.0
    return float('%.3f' % space_num)

def time_to_sec(fio_runtime, dest_unit='sec'):
    res = re.search('(\d+.*\d*)(\wsec)', fio_runtime)
    if not res:
        printout("WARNING","fio result file seems broken, can't obtain real runing time")
        return 0
    runtime = float(res.group(1))
    unit = res.group(2)
    unit_list = ['sec','msec','usec']
    dest_unit_index = unit_list.index(dest_unit)
    cur_unit_index = unit_list.index(unit)
    if dest_unit_index > cur_unit_index:
        for i in range(cur_unit_index, dest_unit_index):
            runtime *= 1000.0
    else:
        for i in range(dest_unit_index, cur_unit_index):
            runtime /= 1000.0
    return '%.3f' % runtime

def unique_extend( list_data, new_list ):
    for data in new_list:
        if data not in list_data:
            list_data.append( data )
    return list_data

class shellEmulator():
    def __init__(self):
        self.kill_tailf = False

    def tail_f(self, fd):
        fd.seek(-1)
        interval = 1.0
        while not self.kill_tailf:
            where = fd.tell()
            line = fd.readline()
            if not line:
              time.sleep(interval)
              fd.seek(where)
            else:
              yield line

def return_os_id(user, nodes):
    stdout, stderr = pdsh(user, nodes, "lsb_release -i | awk -F: '{print $2}'", option="check_return")
    res = format_pdsh_return(stdout)
    return res

def add_to_hosts( nodes ):
    for node, ip in nodes.items():
        res = bash("grep '%s' /etc/hosts" % str(ip)).strip()
        if node in res:
            continue
        if res != "":
            bash("sed -i 's/%s/%s %s/g' /etc/hosts" % (res, res, node))
        else:
            bash("echo %s %s >> /etc/hosts" % (str(ip), node))
