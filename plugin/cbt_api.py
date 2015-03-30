#!/usr/bin/python
import os
import sys
lib_path = os.path.abspath(os.path.join('cbt/'))
sys.path.append(lib_path)
import cbt
import settings
import common
import benchmarkfactory
from cluster.ceph import Ceph

class CBTAPI:
    config_file = ""
    conf = ""
    archive = ""
 
    def __init__( self, yaml_file ):
        self.config_file = yaml_file
        self.conf = "ceph.conf"
        self.archive = "/opt/"
    
    def deploy_ceph_cluster( self ):
        settings.initialize( self )
        print settings.cluster
        cluster = Ceph(settings.cluster)
        cluster.initialize()

    def run_benchmark(self, benchmark):
        settings.initialize( self )
        print settings.cluster
        cluster = Ceph(settings.cluster)
        if benchmark not in settings.benchmarks:
            return False
        iteration = 0
        while (iteration < settings.cluster.get("iterations", 0)):
            benchmarks = benchmarkfactory.getAll(cluster, iteration)
            for _benchmark in benchmarks:
                if _benchmark.exists():
                    return False
                _benchmark.initialize()
                #_benchmark._run()
            iteration += 1
        #_benchmark.cleanup()

