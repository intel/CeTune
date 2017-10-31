import os
import sys
import mock
import pytest
from benchmarking.mod.bblock import fiorbd
from analyzer import analyzer
from conf import common

def test_benchmark():
    #from benchmarking.mod.bblock import fiorbd
    #from conf import common
    #from analyzer import analyzer

    benchmark = fiorbd.FioRbd()
    common.wait_ceph_to_health = mock.Mock(return_value='OK')
    benchmark.load_parameter = mock.Mock(return_value='OK')
    benchmark.parse_benchmark_cases = mock.Mock(return_value={})
    benchmark.generate_benchmark_cases = mock.Mock(return_value=True)
    benchmark.prepare_result_dir = mock.Mock(return_value='OK')
    benchmark.cal_run_job_distribution = mock.Mock(return_value='OK')
    benchmark.prerun_check = mock.Mock(return_value='OK')
    benchmark.prepare_run = mock.Mock(return_value='OK')
    benchmark.run = mock.Mock(return_value='OK')
    benchmark.after_run = mock.Mock(return_value='OK')
    benchmark.archive = mock.Mock(return_value='OK')
    benchmark.setStatus = mock.Mock(return_value='OK')
    analyzer.main = mock.Mock(return_value='OK')

    testcase = [100, "30g", "randwrite", "4k", 16, 300, 300, "fiorbd", "rbd", "optane+directIO+w/-patch", "restart"]
    user = benchmark.all_conf_data.get("user")
    controller = benchmark.all_conf_data.get("head")
    benchmark.cluster["dest_dir"] = ''
    benchmark.go(testcase,'')

    common.wait_ceph_to_health.assert_any_call(user, controller)
    benchmark.load_parameter.assert_any_call()
    benchmark.parse_benchmark_cases.assert_any_call(testcase)
    benchmark.generate_benchmark_cases.assert_any_call(benchmark.benchmark)
    benchmark.prepare_result_dir.assert_any_call()
    benchmark.cal_run_job_distribution.assert_any_call()
    benchmark.prerun_check.assert_any_call()
    benchmark.prepare_run.assert_any_call()
    benchmark.run.assert_any_call() 
    benchmark.after_run.assert_any_call()
    benchmark.archive.assert_any_call()
    benchmark.setStatus.assert_any_call("Completed")
    analyzer.main.assert_any_call(['--path', benchmark.cluster["dest_dir"], 'process_data'])

    mockFoo = mock.Mock(spec = fiorbd.FioRbd, return_value = 'test')
    mockFoo.go(testcase, '')
    print mockFoo.method_calls
