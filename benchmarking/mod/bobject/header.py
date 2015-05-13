#/usr/bin/python
import subprocess

import re
import sys
import os
lib_path =  os.path.dirname((os.path.abspath(__file__)))

sys.path.append(lib_path)
from conf import common 

def remote_file_exist(host,path):
    proc = subprocess.Popen(
        ['ssh',host,'test  %s' % path])
    proc.wait()
    return proc.returncode == 0
'''
def remote_proc_running(host,proc):
    out = subprocess.Popen(
        ['ssh','-R',host,"ps aux | grep "+proc+"|wc -l"])
    if out
'''
def read_test_id(test_file):
    with open(lib_path +"/"+ test_file,'r') as f:
        out = f.readline()
    print "test_id is "+out
    return int(out)

def update_test_id(test_file,runid):
    #with open(lib_path + "/" + test_file,'r') as f:
        #out = int(f.readline())
        #f.close()
    with open(lib_path + "/" +test_file,'w') as f:
        f.write(runid)
        f.close()
