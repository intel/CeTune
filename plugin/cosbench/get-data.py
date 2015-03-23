#!/usr/bin/python

import subprocess
import sys
import re
import os
# argv[1]: read/write flag
# argv[2]: 128KB or 10MB
# argv[3]: the range of folders for test results, should be in order

# input example: ./get-data.py read 128KB 893-899

os.chdir("/data1/rui/")
all_tests = os.popen("ls").read()

folder_list = sys.argv[3].split('-')
start_folder = int(folder_list[0])
end_folder = int(folder_list[1])

find_peak_file = open(sys.argv[2]+"-"+sys.argv[1]+"-find-peak.csv",'w+')
find_peak_file.write("N/A,Throughput,Avg Res Time, 95% Res Time\n")

for folder in range(start_folder,end_folder+1):
    pattern = re.compile("w"+ str(folder) + "[\-|\_|a-z|0-9|\.|A-Z]*")
    match = pattern.search(all_tests)
    if match == None:
        print "None test index match: w" + str(folder)
        continue
    curr_folder = match.group(0)
    #print "curr_folder: "+curr_folder
    rw_flag = re.search('(read|write)',curr_folder).group(0)
    workers = re.search('[0-9]+',curr_folder[-5:-1]).group(0)
    print "workers is "+workers
    size = re.search('(128KB|10MB)',curr_folder).group(0)
    #print "rw_flag = "+rw_flag
    #print "size = "+size
    if rw_flag != sys.argv[1] or size != sys.argv[2]:
        print "test w"+str(folder)+" doesn't meet requirement"
        continue
    f = open("/data1/rui/"+curr_folder+"/"+curr_folder+".csv",'r')
    f.readline()
    data_line = f.readline().split(',')
    throughput = data_line[13]
    avg_res = data_line[5]
    res_95 = data_line[10]
    find_peak_file.write(workers+","+throughput+","+avg_res+","+res_95+"\n")
    f.close()
# fetch the throughput, and append it into a csv file



