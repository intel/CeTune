import argparse
import os, sys
from mod.bblock import *
from mod.bobject import *
from  mod.bcephfs import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cephperf Benchmark Script.')
    parser.add_argument(
        '--engine',
        help = 'Choose the engine: qemurbd, fiorbd, fiocephfs, cosbench',
        )
    parser.add_argument(
        '--runtype',
        help = 'Choose the running-type: single, all ',
        )
    args = parser.parse_args()
    testcase_list = []
    with open("../conf/cases.conf", "r") as f:
        for line in f.readlines():
            p = line.split()
            testcase_list.append({
                "instance_number":p[0], "volume_size":p[1], "iopattern":p[2],
                "block_size":p[3], "qd":p[4], "rampup":p[5], 
                "runtime":p[6], "vdisk":p[7], "output_dir":p[8]
            }) 
    if args.runtype == "single":
        print "Not Done"
    if args.engine == "qemurbd":
        for testcase in testcase_list:
            benchmark = qemurbd.QemuRbd(testcase)
            benchmark.go()
