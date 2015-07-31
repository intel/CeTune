#/usr/bin/python
import os,sys,re,copy
lib_path = os.path.abspath(os.path.join('../conf/'))
sys.path.append(lib_path)
import argparse
import socket
from deploy import *
import common
lib_path = os.path.dirname(os.path.abspath(__file__))

class Deploy_RGW(Deploy) :
    def __init__(self, tunings=""):
        super(self.__class__, self).__init__()
        self.cluster["rgw"] = self.all_conf_data.get_list('rgw_server')
        self.cluster['rgw_num'] = int(self.all_conf_data.get('rgw_num_per_server'))
        self.cluster['rgw_start_index'] = self.all_conf_data.get('rgw_start_index')
        self.cluster['rgw_index'] = [x+int(self.cluster['rgw_start_index']) for x in range(int(self.cluster['rgw_num']))]
        cluster_network = self.all_conf_data.get('ceph_conf')["cluster_network"]
        self.cluster['rgw_ip_bond'] = {}
        ip_handler = common.IPHandler()
        for node in self.cluster['rgw']:
            self.cluster["rgw_ip_bond"][node] = ip_handler.getIpByHostInSubnet(node, cluster_network)

    def deploy(self):
        self.rgw_dependency_install()
        self.rgw_install()
        self.rgw_deploy()

        self.distribute_conf()
        self.create_pools()
        self.init_auth()
        self.configure_haproxy()

        self.gen_cephconf()
        self.distribute_conf()

        self.restart_rgw()

    def restart_rgw(self):
        common.pdsh(self.cluster['user'], self.cluster['rgw'], "killall radosgw", "check_return")
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'/etc/init.d/radosgw restart; /etc/init.d/haproxy restart')

    def check_if_rgw_installed(self):
        stdout,stderr = common.pdsh(self.cluster['user'],self.cluster['rgw'],'curl localhost','check_return')
        if re.search('<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',stdout) == None:
            common.printout("ERROR","radosgw is NOT installed correctly!")
            return False
        else:
            common.printout("LOG","radosgw is installed correctly")
            return True

    def distribute_conf(self):
        super(self.__class__, self).distribute_conf()
        common.pdsh(self.cluster["user"], self.cluster["rgw"], "mkdir -p /etc/ceph")
        for node in self.cluster["rgw"]:
            common.scp(self.cluster["user"], node, "../conf/ceph.conf", "/etc/ceph")

    def gen_cephconf(self):
        super(self.__class__, self).gen_cephconf()
        rgw_conf = self.gen_conf()
        with open("../conf/ceph.conf", 'a+') as f:
            f.write("".join(rgw_conf))

    def rgw_dependency_install(self):
        user = self.cluster["user"]
        rgw_nodes = self.cluster["rgw"]
        common.printout("LOG","Install radosgw dependencies: haproxy ")
        os_type_list = common.return_os_id( user, rgw_nodes )
        for node, os_type in os_type_list.items():
            if "Ubuntu" in os_type:
                install_method = "apt-get -y install"
            elif "CentOS" in os_type:
                install_method = "yum -y install"
            common.pdsh( user, [node], "%s haproxy" % ( install_method ),"console")

    def rgw_install(self):
        user = self.cluster["user"]
        rgw_nodes = self.cluster["rgw"]
        common.printout("LOG","Install radosgw: radosgw, radosgw-agent")
        os_type_list = common.return_os_id( user, rgw_nodes )
        for node, os_type in os_type_list.items():
            if "Ubuntu" in os_type:
                install_method = "apt-get -y install"
                rados_pkg = "radosgw"
            elif "CentOS" in os_type:
                install_method = "yum -y install"
                rados_pkg = "ceph-radosgw"
            common.pdsh( user, [node], "%s radosgw radosgw-agent --force-yes" % install_method,"console")

    def rgw_deploy(self):
        user = self.cluster["user"]
        rgw_nodes = self.cluster["rgw"]
        common.printout("LOG","deploy radosgw instances")
        common.pdsh( user, rgw_nodes, 'sudo ceph-authtool --create-keyring /etc/ceph/ceph.client.radosgw.keyring', 'check_return')
        common.pdsh( user, rgw_nodes, 'sudo chmod +r /etc/ceph/ceph.client.radosgw.keyring', 'check_return')

        rgw_ins_per_nodes = self.cluster["rgw_num"] / len( rgw_nodes )
        rgw_node_index = 0
        rgw_index = 1
        rgw_ins = {}
        while (int(self.cluster["rgw_num"]) - rgw_index + 1) > 0:
            host_name_id = self.cluster['rgw'][rgw_node_index]+"-"+str(rgw_index)
            # ceph auth for all radosgw instances
            common.pdsh( user, [rgw_nodes[0]], 'ceph auth del client.radosgw.%s' %( host_name_id ), 'check_return')
            common.pdsh( user, [rgw_nodes[0]], 'sudo ceph-authtool /etc/ceph/ceph.client.radosgw.keyring -n client.radosgw.%s --gen-key' %(host_name_id), 'check_return')
            common.pdsh( user, [rgw_nodes[0]], "sudo ceph-authtool -n client.radosgw.%s --cap osd 'allow rwx' --cap mon 'allow rwx' /etc/ceph/ceph.client.radosgw.keyring" %(host_name_id), 'check_return')
            common.pdsh( user, [rgw_nodes[0]], 'sudo ceph -k /etc/ceph/ceph.client.admin.keyring auth add client.radosgw.%s -i /etc/ceph/ceph.client.radosgw.keyring' %(host_name_id), 'check_return')

            rgw_ins[host_name_id] = self.cluster["rgw_ip_bond"][self.cluster['rgw'][rgw_node_index]]
            if rgw_index % rgw_ins_per_nodes == 0:
                rgw_node_index += 1
            rgw_index += 1

        self.distribute_hosts(rgw_ins)

        if len(self.cluster['rgw']) == 1:
            return
        for node in self.cluster['rgw']:
            common.rscp(self.cluster['user'],rgw_nodes[0], "/etc/ceph/ceph.client.radosgw.keyring", "/etc/ceph/ceph.client.radosgw.keyring")
            common.scp(self.cluster['user'], node, "/etc/ceph/ceph.client.radosgw.keyring", "/etc/ceph/ceph.client.radosgw.keyring")

    def distribute_hosts(self, node_ip_bond):
        user = self.cluster["user"]
        nodes = []
        nodes.extend(self.cluster["rgw"])

        common.add_to_hosts(node_ip_bond)
        for node in nodes:
            common.scp( user, node, '/etc/hosts', '/etc/hosts')

    def create_pools(self):
        # generate new pools
        common.printout('LOG','Creating rgw required pools')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.buckets 8192 8192', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.buckets.index 1024 1024', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .log 512 512')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.gc 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.control 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .users 512 512 ', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.root 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .users.swift 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .users.uid 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'sleep 5', 'check_return')

    def init_auth(self):
        rgw_node = [self.cluster['rgw'][0]]
        common.pdsh(self.cluster['user'],rgw_node,'radosgw-admin user create --uid="cosbench" --display-name="cosbench"', 'check_return')
        common.pdsh(self.cluster['user'],rgw_node,'radosgw-admin subuser create --uid=cosbench --subuser=cosbench:operator --access=full', 'check_return')
        common.pdsh(self.cluster['user'],rgw_node,'radosgw-admin key create --uid=cosbench --subuser=cosbench:operator --key-type=swift', 'check_return')
        common.pdsh(self.cluster['user'],rgw_node,'radosgw-admin user modify --uid=cosbench --max-buckets=100000', 'check_return')
        common.pdsh(self.cluster['user'],rgw_node,'radosgw-admin subuser modify --uid=cosbench --subuser=cosbench:operator --secret=intel2012 --key-type=swift', 'check_return')

    def gen_conf(self):
        common.printout('LOG', 'Generating rgw ceph.conf parameters' )
        rgw_nodes = self.cluster["rgw"]
        rgw_ins_per_nodes = self.cluster["rgw_num"] / len( rgw_nodes )
        rgw_node_index = 0
        rgw_index = 1

        conf = []
        while (int(self.cluster["rgw_num"]) - rgw_index + 1) > 0:
            host_id = self.cluster["rgw"][rgw_node_index]+"-"+str(rgw_index)
            civetweb_port = 7480 + rgw_index
            conf.append("[client.radosgw.%s]\n" %(host_id))
            conf.append("host = %s\n" %(self.cluster['rgw'][rgw_node_index]))
            conf.append("keyring = /etc/ceph/ceph.client.radosgw.keyring\n")
            conf.append("rgw cache enabled = true\n")
            conf.append("rgw cache lru size = 100000\n")
            conf.append("rgw socket path = /var/run/ceph/ceph.client.radosgw.%s.sock\n" %(host_id))
            conf.append("rgw thread pool size = 256\n")
            conf.append("rgw enable ops log = false\n")
            conf.append("log file = /var/log/radosgw/client.radosgw.%s.log\n" %(host_id))
            conf.append("rgw frontends =civetweb port=%s\n" %(str(civetweb_port)))
            conf.append("rgw override bucket index max shards = 8\n\n")
            if rgw_index % rgw_ins_per_nodes == 0:
                rgw_node_index += 1
            rgw_index += 1
        return conf

    def configure_haproxy(self):
        common.printout('LOG','Updating haproxy configuration')
        rgw_nodes = self.cluster["rgw"]
        rgw_ins_per_nodes = self.cluster["rgw_num"] / len( rgw_nodes )
        rgw_node_index = 0
        rgw_index = 1
        haproxy_per_rgw = {}
        haproxy_per_rgw[self.cluster['rgw'][rgw_node_index]] = []
        while (int(self.cluster["rgw_num"]) - rgw_index + 1) > 0:
            haproxy_per_rgw[self.cluster['rgw'][rgw_node_index]].append("server web%d 127.0.0.1:%d check" % (rgw_index, 7480+rgw_index))
            if rgw_index % rgw_ins_per_nodes == 0:
                rgw_node_index += 1
                try:
                    haproxy_per_rgw[self.cluster['rgw'][rgw_node_index]] = []
                except:
                    break
            rgw_index += 1

        haproxy_cfg = {}
        for rgw, value in haproxy_per_rgw.items():
            common.pdsh(self.cluster['user'], [rgw], "awk 'BEGIN{skip=0}{if($1==\"frontend\")skip=1;if(skip==0)print}' /etc/haproxy/haproxy.cfg > /etc/haproxy_haproxy.cfg" )
            haproxy_cfg[rgw] = []
            server_lists = haproxy_cfg[rgw]
            server_lists.append("frontend localnodes")
            server_lists.append("    bind *:80")
            server_lists.append("    mode http")
            server_lists.append("    default_backend nodes")
            server_lists.append("")
            server_lists.append("backend nodes")
            server_lists.append("    mode http")
            server_lists.append("    balance roundrobin")
            server_lists.append("    option forwardfor")
            server_lists.append("    option httpchk HEAD / HTTP/1.1\r\nHost:localhost")
            server_lists.extend(value)
            server_lists.append("")
            server_lists.append("listen stats *:1936")
            server_lists.append("    stats enable")
            server_lists.append("    stats uri /")
            server_lists.append("    stats hide-version")
            server_lists.append("    stats auth someuser:password")
            common.pdsh(self.cluster['user'], [rgw], "echo %s >> /etc/haproxy/haproxy.cfg" % "\n".join(server_lists) )
        common.pdsh(self.cluster['user'], [rgw], "/etc/init.d/haproxy restart" )

def main(args):
    parser = argparse.ArgumentParser(description='Deploy tool')
    parser.add_argument(
        '--option',
        )
    args = parser.parse_args(args)
    if args.option == "gen_conf":
        mydeploy = Deploy_RGW()
        mydeploy.gen_conf()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
