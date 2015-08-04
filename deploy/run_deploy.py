import os,sys
lib_path = ( os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ))
sys.path.append(lib_path)
from conf import common
import time
import pprint
import re
import socket
import uuid
import argparse
import yaml
from ceph_deploy import cli
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
    args = parser.parse_args(args)
    if args.operation == "redeploy":
        mydeploy = deploy.Deploy()
        mydeploy.redeploy()
    if args.operation == "restart":
        mydeploy = deploy.Deploy()
        mydeploy.cleanup()
        mydeploy.startup()
    if args.operation == "distribute_conf":
        mydeploy = deploy.Deploy()
        mydeploy.distribute_conf()
    if args.operation == "gen_cephconf":
        if args.config:
            mydeploy = deploy.Deploy(args.config)
        else:
            mydeploy = deploy.Deploy()
        mydeploy.gen_cephconf()
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
