import os,sys
lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
sys.path.append(lib_path)
from conf import *
import time
import pprint
import re
import socket
import uuid
import argparse
import yaml
from threading import Thread
from mod import *

def main(args):
    parser = argparse.ArgumentParser(description='Deploy tool')
    parser.add_argument(
        'operation',
        help = 'only support redeploy now',
        )
    parser.add_argument(
        '--config',
        )
    parser.add_argument(
        '--version',
        )
    parser.add_argument(
        '--with_rgw',
        default = False,
        action='store_true'
        )
    parser.add_argument(
        '--gen_cephconf',
        default = False,
        action='store_true'
        )
    parser.add_argument(
        '--ceph_disk',
        default=False,
        action='store_true'
    )

    args = parser.parse_args(args)
    if args.operation == "caldiff":
        mydeploy = deploy.Deploy()
        mydeploy.cal_cephmap_diff(ceph_disk=args.ceph_disk)

    if args.operation == "redeploy":
        mydeploy = deploy.Deploy()
        if args.with_rgw:
            mydeploy = deploy_rgw.Deploy_RGW()
#            mydeploy.deploy()
        mydeploy.redeploy(args.gen_cephconf,
                          ceph_disk=args.ceph_disk)

    if args.operation == "restart":
        mydeploy = deploy.Deploy()
        mydeploy.restart(ceph_disk=args.ceph_disk)
        if args.with_rgw:
            mydeploy = deploy_rgw.Deploy_RGW()
            mydeploy.restart_rgw()
    if args.operation == "startup":
        mydeploy = deploy.Deploy()
        mydeploy.startup(ceph_disk=args.ceph_disk)
    if args.operation == "shutdown":
        mydeploy = deploy.Deploy()
        mydeploy.cleanup(ceph_disk=args.ceph_disk)
    if args.operation == "distribute_conf":
        if args.with_rgw:
            mydeploy = deploy_rgw.Deploy_RGW()
        else:
            mydeploy = deploy.Deploy()
        mydeploy.distribute_conf()
    if args.operation == "gen_cephconf":
        tuning = ""
        if args.config:
            tuning = args.config
        if args.with_rgw:
            mydeploy = deploy_rgw.Deploy_RGW(tuning)
        else:
            mydeploy = deploy.Deploy(tuning)
        mydeploy.gen_cephconf(ceph_disk=args.ceph_disk)
    if args.operation == "install_binary":
        mydeploy = deploy.Deploy()
        mydeploy.install_binary(args.version)
    if args.operation == "uninstall_binary":
        mydeploy = deploy.Deploy()
        mydeploy.uninstall_binary()
    if args.operation == "deploy_rgw":
        mydeploy = deploy_rgw.Deploy_RGW()
        mydeploy.deploy()
    if args.operation == "restart_rgw":
        mydeploy = deploy_rgw.Deploy_RGW()
        mydeploy.restart_rgw()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
