#/usr/bin/python
import subprocess
import shutil

import re
import sys
import os
lib_path =  os.path.dirname((os.path.abspath(__file__)))
sys.path.append(lib_path)

def remote_file_exist(host,path):
    proc = subprocess.Popen(
        ['ssh',host,'test  %s' % path])
    proc.wait()
    return proc.returncode == 0

def read_test_id(test_file):
    with open(lib_path +"/"+ test_file,'r') as f:
        out = f.readline()
    print "test_id is "+out
    return int(out)

def update_test_id(test_file,runid):
    with open(lib_path + "/" +test_file,'w') as f:
        f.write(runid)
        f.close()


def replace_conf_xml(rw,size,workers,config_middle,cluster_ip):
    suffix = "w.xml"

    unit = size[-2:]
    size_num = size[:-2]
    container_num = re.search('[0-9]+',config_middle).group(0)
    #object_num = re.search('[0-9]+',config_middle).group(1)
    # TODO: object_num may be different for large scale read
    object_num = container_num
    config_file_name = "%s_%scon_%sobj_%s_%s%s" %(rw,container_num,object_num,size,workers,suffix)
    with open(lib_path+"/.template.xml",'r') as infile:
        with open(lib_path+"/configs/"+config_file_name,'w+') as outfile:
            for line in infile:
                match = re.compile("\{\{rw\}\}")
                line = match.sub(rw,line)
                #print line
                match = re.compile("\{\{config_middle\}\}")
                line = match.sub(config_middle,line)
                #print line
                match = re.compile("\{\{size\}\}")
                line = match.sub(size,line)
                match = re.compile("\{\{workers\}\}")
                #print workers
                if workers == "0":
                    workers = "10"
                line = match.sub(workers,line)
                match = re.compile("\{\{description\}\}")
                if rw == "read":
                    line = match.sub("READ-ONLY",line)
                elif rw == "write":
                    line = match.sub("WRITE-ONLY",line)
                match = re.compile("\{\{cluster_ip\}\}")
                line = match.sub(cluster_ip,line)
                match = re.compile("\{\{container_num\}\}")
                line = match.sub(container_num,line)
                match = re.compile("\{\{object_num\}\}")
                line = match.sub(object_num,line)
                match = re.compile("\{\{size_num\}\}")
                line = match.sub(size_num,line)
                match = re.compile("\{\{unit\}\}")
                line = match.sub(unit,line)
               
                outfile.write(line)
    
