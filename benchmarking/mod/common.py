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
                    key, value = line.split("=")
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

def pdsh(user, nodes, command, force=False):
    _nodes = []
    for node in nodes:
        _nodes.append("%s@%s" % (user, node))
    _nodes = ",".join(_nodes)
    args = ['pdsh', '-R', 'ssh', '-w', _nodes, command]
    #print('pdsh: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if force:
        return [stdout, stderr]
    if stderr:
        print('pdsh: %s' % args)
        print "[ERROR]:"+stderr+"\n"
        sys.exit()

def scp(user, node, localfile, remotefile):
    args = ['scp', localfile, '%s@%s:%s' % (user, node, remotefile)]
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('pdsh: %s' % args)
        print "[ERROR]:"+stderr+"\n"
        sys.exit()

def rscp(user, node, localfile, remotefile):
    args = ['scp', '%s@%s:%s' % (user, node, remotefile), localfile]
    #print('scp: %s' % args)
    stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
    if stderr:
        print('pdsh: %s' % args)
        print "[ERROR]:"+stderr+"\n"
        sys.exit()

