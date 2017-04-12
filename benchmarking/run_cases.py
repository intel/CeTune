import argparse
import os, sys

lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
this_file_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(lib_path)

from conf import *
from mod import *
from mod.bblock import *
from mod.bobject import *
from mod.bcephfs import *
from mod.generic import *
from deploy import *
from tuner import *

def main(args):
    parser = argparse.ArgumentParser(description='Cephperf Benchmark Script.')
    parser.add_argument(
        '--tuning',
        )
    parser.add_argument(
        '--option',
        )
    args = parser.parse_args(args)
    testcase_list = []
    try:
        tuning_section = args.tuning
    except:
        tuning_section = ""
    try:
        option = args.option
    except:
        option = "benchmark"

    if option == "gen_case":
        testcase_list = []
        benchmark = qemurbd.QemuRbd()
        benchmark_engine_config = benchmark.generate_benchmark_cases()
        fio_list = benchmark_engine_config

        benchmark = fiorbd.FioRbd()
        benchmark_engine_config = benchmark.generate_benchmark_cases()
        fio_list.extend( benchmark_engine_config )

        #benchmark = fiocephfs.FioCephFS()
        #testcases, benchmark_engine_config = benchmark.generate_benchmark_cases()
        #testcase_list.extend(testcases)
        #fio_list.extend( benchmark_engine_config )

        benchmark = cosbench.Cosbench()
        benchmark.generate_benchmark_cases()

        #benchmark = generic.Generic()
        #testcases, benchmark_engine_config = benchmark.generate_benchmark_cases()
        #testcase_list.extend(testcases)
        #fio_list.extend( benchmark_engine_config )

        if len(fio_list) > 0:
            with open("../conf/fio.conf", "w") as f:
                f.write( '\n'.join(fio_list) + "\n" )

    else:
        with open("../conf/cases.conf", "r") as f:
            case_lines = f.readlines()
            for line in case_lines:
                p = line.split()
                if len(p) > 0 and p!="\n":
                    if not p[0].startswith('#'):
                        testcase_list.append({"engine":p[0],"parameter":p[1:]})
        for testcase in testcase_list:
            if testcase["engine"] == "qemurbd":
                benchmark = qemurbd.QemuRbd()
            if testcase["engine"] == "fiorbd":
                benchmark = fiorbd.FioRbd()
            if testcase["engine"] == "fiocephfs":
                benchmark = fiocephfs.FioCephFS()
            if testcase["engine"] == "cosbench":
                benchmark = cosbench.Cosbench()
            if testcase["engine"] == "generic":
                benchmark = generic.Generic()
            if testcase["engine"] == "hook":
                benchmark = hook.Hook()
            if testcase["engine"] == "vdbench":
                benchmark = vdbench.VdBench()
            if not benchmark:
                common.printout("ERROR","Unknown benchmark engine",log_level="LVL1")
            try:
                additional_option = ''
                for i in testcase["parameter"]:
                    if i in ["restart","redeploy","resetPerf"]:
                        additional_option = i
                if additional_option != '':
                    if additional_option == "restart":
                        run_deploy.main(['restart'])
                    if additional_option == "redeploy":
                        run_deploy.main(['redeploy'])
                        tuner.main(['--section', tuning_section,'apply_tuning'])
                    if additional_option == "resetPerf":
                        run_deploy.main(['osd_perf_reset'])

                benchmark.go(testcase["parameter"], tuning_section)
            except KeyboardInterrupt:
                common.printout("WARNING","Caught KeyboardInterrupt Interruption",log_level="LVL1")

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
