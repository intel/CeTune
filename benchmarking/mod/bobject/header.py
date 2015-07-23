#/usr/bin/python
from conf import common
import shutil

import re
import sys
import os
lib_path =  os.path.dirname((os.path.abspath(__file__)))
sys.path.append(lib_path)

def read_test_id(test_file):
    with open(lib_path +"/"+ test_file,'r') as f:
        out = f.readline()
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
    object_num = container_num
    config_file_name = "%s_%scon_%sobj_%s_%s%s" %(rw,container_num,object_num,size,workers,suffix)

    print "config_file_name is "+config_file_name
    with open(lib_path+"/.template_config.xml",'r') as infile:
        with open(lib_path+"/configs/"+config_file_name,'w+') as outfile:
            for line in infile:
                match = re.compile("\{\{config_middle\}\}")
                line = match.sub(config_middle,line)
                match = re.compile("\{\{size\}\}")
                line = match.sub(size,line)
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
                match = re.compile("\{\{rw\}\}")
                line = match.sub(rw,line)
                match = re.compile("\{\{workers\}\}")
                line = match.sub(workers,line)

                # for workers more than 0
                if workers != "0":
                    match = re.compile("\{\{main\}\}")
                    line = match.sub("main",line)
                    match = re.compile("\{\{description\}\}")
                    if rw == "read":
                        line = match.sub("READ-ONLY",line)
                    elif rw == "write":
                        line = match.sub("WRITE-ONLY",line)
                    #print "new line is "+line
                    match = re.compile("/auth/v1.0\"")
                    line = match.sub("/auth/v1.0;retry=9\"",line)
                    if size == "128KB":
                        match = re.compile("cprefix=[0-9]+(KB|MB)\-(read|write)\"")
                        new_string = "cprefix=%s-%s;sizes=c(%s)%s\"" %(size,rw,size[:-2],size[-2:])
                        line = match.sub(new_string,line)

                # for workers larger than 0, that is, initialize the containers
                else:
                    #print "Preparation confix generation..."
                    match = re.compile("\{\{description\}\}")
                    line = match.sub("INIT-PREPARE",line) 
                    match = re.compile("<operation type.*B-(read|write)\"/>")
                    line = match.sub("",line)
                    match = re.compile("</work>")
                    line = match.sub("",line)
                   
                    # TODO: only care about small scale currenlty
                    if rw == "read":
                        match = re.compile("\{\{main\}\}\">")
                        if size == "10MB":
                            prepare_workers = "320"
                        elif size == "128KB":
                            prepare_workers = "10"
                        read_config_line = "init\">\n<work type=\"init\" workers=\"5\" config=\"containers=r(1,100);cprefix=%s-%s\"/>\n</workstage>\n<workstage name=\"prepare\">\n<work type=\"prepare\" workers=\"%s\" config=\"containers=r(1,100);objects=r(1,100);cprefix=%s-%s;sizes=c(%s)%s\"/>" %(size,rw,prepare_workers,size,rw,size[:-2],size[-2:])
                        line = match.sub(read_config_line,line)
                        match = re.compile("<work name=.*rampdown=\"[0-9]+\">")
                        line = match.sub("",line)
                    else:
                        match = re.compile("\{\{main\}\}\">")
                        line = match.sub("init\">",line)
                        match = re.compile("/auth/v1.0\" />")
                        line = match.sub("/auth/v1.0;retry=9\" />",line)
                        match = re.compile("<work name=.*rampdown=\"[0-9]+\">")
                        new_string = "<work type=\"init\" workers=\"10\" config=\"containers=r(1,100);cprefix=%s-%s\"/>" %(size,rw)
                        line = match.sub(new_string,line)
                   

                outfile.write(line)
    
