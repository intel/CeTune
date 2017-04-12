import time
import datetime
import os
import sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
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
import argparse

cetune_log_file = "../conf/cetune_process.log"
cetune_error_file = "../conf/cetune_error.log"
cetune_console_file = "../conf/cetune_console.log"

cetune_python_log_file = "../log/cetune_python_log_file.log"
cetune_python_error_log_file = "../log/cetune_python_error_log_file.log"
cetune_console_log_file = "../log/cetune_console_log_file.log"
cetune_process_log_file = "../log/cetune_process_log_file.log"
cetune_error_log_file = "../log/cetune_error_log_file.log"
cetune_operate_log_file = "../log/cetune_operate_log_file.log"
no_die = False

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
        netmask = self.makeMask(bits) << (32 - bits)
        return [self.dottedQuadToNum(ip) & netmask, netmask]

    def addressToNetwork(self,ip,net):
       "Is an address in a network"
       return ip & net

    def getIpByHostInSubnet(self, hostname, subnet ):
        "Get IP by hostname and filter with subnet"
        stdout, stderr = pdsh('root', [hostname] ,"ifconfig", option = "check_return",loglevel="LVL6")
        if len(stderr):
            printout("ERROR", 'Error to get ips: %s' % stderr,log_level="LVL1")
            sys.exit()
        ipaddrlist = []
        res = re.findall("inet addr:\d+\.\d+\.\d+\.\d+",stdout)
        if len(res) == 0:
            res = re.findall("inet \d+\.\d+\.\d+\.\d+",stdout)
        for item in res:
            tmp = re.findall("\d+\.\d+\.\d+\.\d+",item)
            b = tmp[0]
            if b != "127.0.0.1":
                ipaddrlist.append(b)
        if len(ipaddrlist) == 0:
            printout("ERROR", "No IP found",log_level="LVL1")
            sys.exit()
        try:
            network, netmask = self.networkMask(subnet)
        except:
            return ipaddrlist[0]
        for ip in ipaddrlist:
            if self.addressToNetwork(self.dottedQuadToNum(ip),netmask) == network:
                return ip
        return ipaddrlist[0]

def get_list( string ):
    res = []
    if isinstance(string, str):
        string = string.split(",")
    for value in string:
        if re.search(":", value):
            res.append(value.split(':'))
        else:
            res.append([value,""])
    return res

def get_largest_list_len( data ):
    max_len = 0;
    if isinstance(data, dict):
        for key, value in data.items():
            if max_len < len(value):
                max_len = len(value)
    if isinstance(data, list):
        for value in data:
            if max_len < len(value):
                max_len = len(value)
    return max_len

def clean_console():
    bash("echo > %s" % cetune_console_file)

def cetune_log_collecter(func):
    def wrapper(level, content, screen = True,log_level = "LVL3"):
        #if not os.path.exists("../log/"):
        #    bash("mkdir -p ../log")
        if log_level in ["LVL1"]:
            output = "[%s][%s]: %s" % (log_level,level,content)
            with open(cetune_error_log_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if log_level in ["LVL2"]:
            output = "[%s][%s]: %s" % (log_level,level,content)
            with open(cetune_python_error_log_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if log_level in ["LVL1","LVL3"]:
            output = "[%s][%s]: %s" % (log_level,level,content)
            with open(cetune_console_log_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if log_level in ["LVL2","LVL4"]:
            output = "[%s][%s]: %s" % (log_level,level,content)
            with open(cetune_python_log_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if log_level in ["LVL1","LVL2","LVL3"]:
            output = "[%s][%s]: %s" % (log_level,level,content)
            with open(cetune_process_log_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if log_level in ["LVL6"]:
            output = "[%s][%s]: %s" % (log_level,level,content)
            with open(cetune_operate_log_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        return func(level, content, screen)
    return wrapper

@cetune_log_collecter
def printout(level, content, screen = True):
    if level == "ERROR":
        output = "[ERROR]: %s" % content
        with open(cetune_error_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if screen:
            with open(cetune_console_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
            print bcolors.FAIL + output + bcolors.ENDC
    if level == "LOG":
        output = "[LOG]: %s" % content
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if screen:
            with open(cetune_console_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
            print bcolors.OKGREEN + output + bcolors.ENDC
    if level == "WARNING":
        output = "[WARNING]: %s" % content
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
        if screen:
            with open(cetune_console_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),output))
            print bcolors.WARNING + output + bcolors.ENDC
    if level == "CONSOLE":
        with open(cetune_log_file, "a+") as f:
            f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),content))
        if screen:
            with open(cetune_console_file, "a+") as f:
                f.write("[%s]%s\n" % (datetime.datetime.now().isoformat(),content))
            print content

def clean_process_log(file_path):
    start_line = 0
    with open(os.path.join(file_path,'cetune_process_log_file.log'),'rw') as f:
        data = f.readlines()
    for i in range(len(data)):
        if data[i].strip('\n').find("============start deploy============") > 0:
            start_line = int(i)+1
    if start_line != 0:
        old_name = os.path.join(file_path,'cetune_process_log_file.log')
        new_name = os.path.join(file_path,'cetune_process_log_file.log') + '.new'
        bash("tail -n +%d %s > %s" % (start_line,old_name,new_name))
        bash("mv %s %s"%(new_name,old_name))
    else:
        bash("rm  %s/*" % (file_path))
    printout("LOG", "Clean process log file.",log_level="LVL3")

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

def pdsh(user, nodes, command, option="error_check", except_returncode=0, nodie=False,loglevel="LVL3"):
    _nodes = []
    for node in nodes:
        _nodes.append("%s@%s" % (user, node))
    _nodes = ",".join(_nodes)
    args = ['pdsh', '-R', 'exec', '-w', _nodes, '-f', str(len(nodes)), 'ssh', '%h', '-oConnectTimeout=15', command]
#    args = ['pdsh', '-w', _nodes, command]
    printout("CONSOLE", args, screen=False,log_level=loglevel)

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
    if stdout:
        printout("CONSOLE", stdout, screen=False,log_level=loglevel)
    if stderr:
        printout("CONSOLE", stderr, screen=False,log_level=loglevel)

    if stderr:
        returncode_re = re.search('ssh exited with exit code (\d+)', stderr)
        if returncode_re:
            try:
                returncode += int(returncode_re.group(1))
            except:
                pass
    if returncode == except_returncode:
        returncode = 0

    if "check_return" in option:
        if returncode or "Connection timed out" in stderr:
            if stderr:
                stderr_tmp = stderr.split('\n')
                stderr_print = []
                for line in stderr_tmp:
                    if "ssh exited with exit code 255" not in line:
                        stderr_print.append(line)
                printout("ERROR",'\n'.join(stderr_print), screen=False,log_level="LVL1")
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
                printout("ERROR",'\n'.join(stderr_print),log_level="LVL1")
            if not nodie:
                sys.exit()

def bash(command, force=False, option="", nodie=False,loglevel = "LVL3"):
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
    if stdout:
        printout("CONSOLE", stdout, screen=False,log_level=loglevel)
    if stderr:
        printout("CONSOLE", stderr, screen=False,log_level=loglevel)

    if force:
        return [stdout, stderr]
    if returncode:
        if stderr:
            print('bash: %s' % args)
            printout("ERROR",stderr+"\n",log_level="LVL1")
        if not nodie:
            sys.exit()
    return stdout

def cp(localfile, remotefile):
    args = ['cp', '-r', localfile, remotefile]
    printout("CONSOLE", args, screen=False)
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    printout("CONSOLE", stdout, screen=False)
    if stderr:
        print('scp: %s' % args)
        printout("WARNING",stderr+"\n")

def scp(user, node, localfile, remotefile):
    args = ['scp', '-oConnectTimeout=15', '-r',localfile, '%s@%s:%s' % (user, node, remotefile)]
    printout("CONSOLE", args, screen=False)
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    printout("CONSOLE", stdout, screen=False)
    if stderr:
        print('scp: %s' % args)
        printout("WARNING",stderr+"\n")

def rscp(user, node, localfile, remotefile):
    args = ['scp', '-oConnectTimeout=15', '-r', '%s@%s:%s' % (user, node, remotefile), localfile]
    printout("CONSOLE", args, screen=False)
    #print('rscp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('rscp: %s' % args)
        printout("WARNING",stderr+"\n")

# scp from one remote machine to another remote machine
def rrscp(user, node1, node1_file, node2,node2_file):
    args = ['scp', '-oConnectTimeout=15', '-r', '%s@%s:%s'%(user,node1,node1_file)  , '%s@%s:%s' % (user, node2, node2_file)]
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('scp: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

def load_yaml_conf(yaml_path):
    with file(yaml_path) as f:
        config = f.read()
    data = yaml.load(config)
    return data

def write_yaml_file(yaml_path, data):
    with file(yaml_path, 'w') as f:
        f.write( yaml.dump(dict(data)) )

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
        if 'pdsh@' in node:
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
            printout("LOG","Tuning [%s] not in configuration" % (key))
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
        #print conf
        if dest_data == {}:
            dest_data = copy.deepcopy(conf)
            return dest_data
        if self.dedup and dest_data == conf:
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
    if not str(size).isdigit():
        res = re.search('(\d+\.*\d*)\s*(\D*)',size)
        space_num = float(res.group(1))
        space_unit = res.group(2)
        if space_unit == "":
            space_unit = 'B'
    else:
        space_num = float(size)
        space_unit = 'B'
    if space_unit == 'k':
        space_unit = 'K'
    if space_unit in ['Z','E','P','T','G','M','K']:
        space_unit += 'B'
    if space_unit in ['ZiB','EiB','PiB','TiB','GiB','MiB','KiB']:
        space_unit = space_unit.replace("i","")
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

def read_file_after_stamp(path, stamp = None):
    lines = []
    output = False
    with open(path,'r') as fd:
        for line in fd.readlines():
            if output or not stamp or stamp in line:
                output = True
                lines.append(line.rstrip('\n'))
    return lines

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

def check_ceph_running(user, node):
    stdout, stderr = pdsh(user, [node], "timeout 3 ceph -s 2>/dev/null 1>/dev/null; echo $?", option = "check_return")
    res = format_pdsh_return(stdout)
    ceph_is_up = False
    if node in res:
        if int(res[node]) == 0:
            ceph_is_up = True
    if not ceph_is_up:
        return False
    return True

def eval_args( obj, function_name, args ):
    argv = {}
    for key, value in args.items():
        argv[key] = value
    argv = _decode_dict(argv)
    if function_name != "":
        func = getattr(obj, function_name)
        if func:
            res = func( **argv )
    return res

def wait_ceph_to_health( user, controller ):
        #wait ceph health to be OK
        waitcount = 0
        try:
            while not check_health( user, controller ) and waitcount < 300:
                printout("WARNING","Applied tuning, waiting ceph to be healthy")
                time.sleep(3)
                waitcount += 3
        except:
            printout("WARNING","Caught KeyboardInterrupt, exit")
            sys.exit()
        if waitcount < 300:
            printout("LOG","Tuning has applied to ceph cluster, ceph is Healthy now")
        else:
            printout("ERROR","ceph is unHealthy after 300sec waiting, please fix the issue manually",log_level="LVL1")
            sys.exit()

def check_health( user, controller ):
    check_count = 0
    stdout, stderr = pdsh(user, [controller], 'ceph health', option="check_return")
    if "HEALTH_OK" in stdout:
        return True
    else:
        return False

def get_ceph_health(user, node):
    check_count = 0
    output = {}
    stdout, stderr = pdsh(user, [node], "timeout 3 ceph -s", option = "check_return",loglevel="LVL5")
    res = format_pdsh_return(stdout)
    if len(res):
        stdout = res[node]
        stdout = stdout.split('\n')
        output["ceph_status"] = stdout[1]
        if "client io" in stdout[-2]:
            output["ceph_throughput"] = stdout[-2]
        if "client io" in stdout[-1]:
            output["ceph_throughput"] = stdout[-1]
    else:
        output["ceph_status"] = "NOT ALIVE"
    return output

def try_ssh( node ):
    stdout = bash("timeout 5 ssh %s hostname > /dev/null; echo $?" % node)
    if stdout.strip() == "0":
        return True
    else:
        return False

def try_disk( node, disk ):
    stdout = bash("timeout 5 ssh %s 'df %s > /dev/null'; echo $?" % (node, disk))
    if stdout.strip() == "0":
        stdout = bash("ssh %s mount -l | grep boot | awk '{print $1}'" % node)
        if disk == stdout.strip():
            return False
        return True
    else:
        return False

def parse_nvme( dev_name ):
    if 'p' in dev_name:
        dev_name = dev_name.split('p')[0]
    return dev_name

def parse_device_name(dev_name):
    sata_pattern = re.compile(r'sd\D*')
    nvme_pattern = re.compile(r'nvme\dn\d*')
    res = sata_pattern.search(dev_name)
    if res:
        return res.group()
    res = nvme_pattern.search(dev_name)
    if res:
        return res.group()
    printout("ERROR", "device path error!\n",log_level="LVL1")
    return None

def parse_disk_format( disk_format_str ):
    if disk_format_str == "":
        disk_format_str = "osd:journal"
    disk_type_list = disk_format_str.split(":")
    return disk_type_list

