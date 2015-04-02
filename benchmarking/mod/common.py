import time
import os
import errno
import sys
import re
import subprocess

class Config():
    all_conf_data = {}
    def __init__(self):
        with open("../conf/all.conf", "r") as f:
            for line in f:
                if( not re.search('^#', line) ):
                    try:
                        key, value = line.split("=")
                    except:
                        pass
                    if( value[-1] == '\n' ):
                        self.all_conf_data[key] = value[:-1]
                    else:
                        self.all_conf_data[key] = value
                    if re.search(',', self.all_conf_data[key]):
                        self.all_conf_data[key] = self.all_conf_data[key].split(",")
    def get(self, key):
        if key in self.all_conf_data:
            return self.all_conf_data[key]
        else:
            print "%s not defined in all.conf" % key
            sys.exit()
    def get_list(self,key):
	if key in self.all_conf_data:
	    if type(self.all_conf_data[key]) == str:
		return [self.all_conf_data[key]]
	    else:
		return self.all_conf_data[key]
	else:
	    print "%s not defined in all.conf" % key

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def pdsh(user, nodes, command, option="error_check"):
    _nodes = []
    for node in nodes:
        _nodes.append("%s@%s" % (user, node))
    _nodes = ",".join(_nodes)
    args = ['pdsh', '-R', 'ssh', '-w', _nodes, command]
    #print('pdsh: %s' % args)
    if option == "force":
        _subp = subprocess.Popen(args)
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
    print('bash: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if force:
        return [stdout, stderr]
    if stderr:
        print('bash: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

def scp(user, node, localfile, remotefile):
    args = ['scp', localfile, '%s@%s:%s' % (user, node, remotefile)]
#   print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('pdsh: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

def rscp(user, node, localfile, remotefile):
    args = ['scp', '%s@%s:%s' % (user, node, remotefile), localfile]
#    print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('pdsh: %s' % args)
        print bcolors.FAIL + "[ERROR]:"+stderr+"\n" + bcolors.ENDC
        sys.exit()

