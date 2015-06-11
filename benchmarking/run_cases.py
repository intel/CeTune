import argparse
import os, sys

lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
sys.path.append(lib_path)
print sys.path
from conf import common
from mod import *
from mod.bblock import *
from mod.bobject import *
from  mod.bcephfs import *

def main(args):
    parser = argparse.ArgumentParser(description='Cephperf Benchmark Script.')
    parser.add_argument(
        'engine',
        help = 'Choose the engine: qemurbd, fiorbd, fiocephfs, cosbench',
        )
    parser.add_argument(
        '--tuning',
        )
    args = parser.parse_args(args)
    testcase_list = []
    print args
    try:
        tuning_section = args.tuning
    except:
        tuning_section = ""
    with open("../conf/cases.conf", "r") as f:
        for line in f.readlines():
            p = line.split()
            testcase_list.append({
                "instance_number":p[0], "volume_size":p[1], "iopattern":p[2],
                "block_size":p[3], "qd":p[4], "rampup":p[5], 
                "runtime":p[6], "vdisk":p[7], "output_dir":p[8], "tuning_section": tuning_section
            }) 
    if args.engine == "qemurbd":
        for testcase in testcase_list:
            benchmark = qemurbd.QemuRbd(testcase)
            try:
                benchmark.go()
            except KeyboardInterrupt:
                common.printout("WARNING","Caught KeyboardInterrupt Interruption")
    if args.engine == "fiorbd":
        for testcase in testcase_list:
            benchmark = fiorbd.FioRbd(testcase)
            try:
                benchmark.go()
            except KeyboardInterrupt:
                common.printout("WARNING","Caught KeyboardInterrupt Interruption")
    if args.engine == "fiocephfs":
        for testcase in testcase_list:
            benchmark = fiocephfs.FioCephFS(testcase)
            try:
                benchmark.go()
            except KeyboardInterrupt:
                common.printout("WARNING","Caught KeyboardInterrupt Interruption")
    if args.engine == "cosbench":
        for testcase in testcase_list:
            benchmark = cosbench.Cosbench(None)
            try:
                benchmark.go()
            except KeyboardInterrupt:
                common.printout("WARNING","Caught KeyboardInterrupt Interruption")
if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
