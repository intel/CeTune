import os,sys
lib_path = os.path.abspath(os.path.join('../conf/'))
sys.path.append(lib_path)
from conf import *
import time
import pprint
import re
import socket
import uuid
import argparse
import json
from threading import Thread
from collections import OrderedDict

pp = pprint.PrettyPrinter(indent=4)
class Deploy(object):
    def __init__(self, tunings=""):
        self.all_conf_data = config.Config("../conf/all.conf")
        self.cluster = {}
        self.cluster["clean_build"] = self.all_conf_data.get("clean_build")
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["clients"] = self.all_conf_data.get_list("list_client")
        self.cluster["rgws"] = self.all_conf_data.get_list("rgw_server")
        self.cluster["monitor_network"] = self.all_conf_data.get("monitor_network", True)
        self.cluster["osds"] = {}
        self.cluster["mons"] = {}
        self.cluster["ceph_conf"] = {}
        self.cluster["ceph_conf"]["global"] = OrderedDict()
        self.cluster["ceph_conf"]["global"]["auth_service_required"] = "none"
        self.cluster["ceph_conf"]["global"]["auth_cluster_required"] = "none"
        self.cluster["ceph_conf"]["global"]["auth_client_required"] = "none"
        self.cluster["ceph_conf"]["global"]["mon_data"] = "/var/lib/ceph/mon.$id"
        self.cluster["ceph_conf"]["global"]["osd_data"] = "/var/lib/ceph/mnt/osd-device-$id-data"

        for key, value in self.all_conf_data.get_group("ceph_hard_config").items():
            self.cluster["ceph_conf"]["global"][key] = value

        ip_handler = common.IPHandler()
        subnet = ""
        monitor_subnet = ""
        cluster_subnet = None
        public_subnet = None
        if 'cluster_network' in self.cluster["ceph_conf"]["global"]:
            cluster_subnet = self.cluster["ceph_conf"]["global"]['cluster_network']
            subnet = cluster_subnet
        if 'public_network' in self.cluster["ceph_conf"]["global"]:
            public_subnet = self.cluster["ceph_conf"]["global"]['public_network']
            subnet = public_subnet
        if self.cluster['monitor_network'] != "":
            monitor_subnet = self.cluster["monitor_network"]

        if not cluster_subnet:
            cluster_subnet = subnet
        if not public_subnet:
            public_subnet = subnet

        for osd in self.all_conf_data.get_list("list_server"):
            self.cluster["osds"][osd] = {"public":ip_handler.getIpByHostInSubnet(osd, public_subnet), "cluster":ip_handler.getIpByHostInSubnet(osd, cluster_subnet)}
        for mon in self.all_conf_data.get_list("list_mon"):
            self.cluster["mons"][mon] = ip_handler.getIpByHostInSubnet(mon, monitor_subnet)

        for osd in self.cluster["osds"]:
            self.cluster[osd] = self.all_conf_data.get_list(osd)

        self.cluster["fs"] = "xfs"
        self.cluster["mkfs_opts"] = "-f -i size=2048 -n size=64k"
        self.cluster["mount_opts"] = "-o inode64,noatime,logbsize=256k"

        self.cluster["ceph_conf"]["client"] = {}
        self.cluster["ceph_conf"]["client"]["rbd_cache"] = "false"
        self.cluster["ceph_conf"]["global"]["osd_mount_options"] = "rw,noatime,inode64,logbsize=256k"
        self.cluster["ceph_conf"]["global"]["osd_mkfs_type"] = "xfs"

        tuning_dict = {}
        if tunings != "":
            tuning_dict = json.loads(tunings,object_pairs_hook=OrderedDict )
        if isinstance( tuning_dict, dict ):
            for section_name, section in tuning_dict.items():
                if section_name == 'global':
                    if 'global' not in self.cluster["ceph_conf"]:
                        self.cluster["ceph_conf"]['global'] = OrderedDict()
                    for key, value in section.items():
                        self.cluster["ceph_conf"]['global'][key] = value
                if section_name == 'mon':
                    if 'mon' not in self.cluster["ceph_conf"]:
                        self.cluster["ceph_conf"]['mon'] = OrderedDict()
                    for key, value in section.items():
                        self.cluster["ceph_conf"]['mon'][key] = value
                if section_name == 'osd':
                    if 'osd' not in self.cluster["ceph_conf"]:
                        self.cluster["ceph_conf"]['osd'] = OrderedDict()
                    for key, value in section.items():
                        self.cluster["ceph_conf"]['osd'][key] = value

        self.map_diff = None

    def install_binary(self, version=""):
        installed, non_installed = self.check_ceph_installed()
        uninstall_nodes=[]
        need_to_install_nodes=[]
        correctly_installed_nodes={}
        installed_list = []
        version_map = {'cuttlefish':'0.61','dumpling':'0.67','emperor':'0.72','firefly':'0.80','giant':'0.87','hammer':'0.94'}
        for node, version_code in installed.items():
            if version == "":
                for release_name, short_version in version_map.items():
                    if short_version in version_code:
                        version_release_name = release_name
                        break
                installed_list = common.unique_extend( installed_list, [version_release_name])
                continue;
            if version_map[version] not in version_code:
                uninstall_nodes.append(node)
                need_to_install_nodes.append(node)
            else:
                correctly_installed_nodes[node]=version_code
        if len(installed_list) == 1:
            for version_name, code in version_map.items():
                if code in installed_list[0]:
                    version = version_name
        elif len(installed_list) >= 2:
            common.printout("ERROR", "More than two versions of ceph installed, %s" % installed_list)
            sys.exit()
        if len(uninstall_nodes):
            self.uninstall_binary(uninstall_nodes)
        need_to_install_nodes.extend(non_installed)
        common.printout("LOG", "Ceph already installed on below nodes")
        for node, value in correctly_installed_nodes.items():
            common.printout("LOG", "%s, installed version: %s" % (node, value))
        if len(need_to_install_nodes):
            common.printout("LOG", "Will start to install ceph on %s" % str(need_to_install_nodes))

        pkg_type = "release"
        if ":" in version:
            try:
                pkg_type, version = version.split(":")
            except:
                common.printout("ERROR", "Please check version, received $s" % version)

        user = self.cluster["user"]
        node_os_dict = common.return_os_id(user, need_to_install_nodes)
        for node in need_to_install_nodes:
            if node in node_os_dict and "Ubuntu" in node_os_dict[node]:
                common.pdsh(user, [node], "apt-get -f -y autoremove", option="console")
            common.bash("ceph-deploy install --%s %s %s 2>&1" % (pkg_type, version, node), option="console")

    def uninstall_binary(self, nodes=[]):
        if not len(nodes):
            installed, non_installed = self.check_ceph_installed()
            nodes = installed.keys()
        user = self.cluster["user"]
        node_os_dict = common.return_os_id(user, nodes)
        common.printout("LOG", "Uninstalled ceph on below nodes: %s" % str(nodes))
        for node in nodes:
            if node in node_os_dict and "Ubuntu" in node_os_dict[node]:
                common.pdsh(user, [node], "apt-get -f -y autoremove", option="console")
            common.bash("ceph-deploy purge %s" % (node), option="console")
            if node in node_os_dict and "Ubuntu" in node_os_dict[node]:
                common.pdsh(user, [node], "apt-get purge -f -y librbd1", option="console")
                common.pdsh(user, [node], "apt-get purge -f -y librados2", option="console")
                common.pdsh(user, [node], "apt-get -f -y autoremove", option="console")

    def check_ceph_installed(self):
        user = self.cluster["user"]
        mons = sorted(self.cluster["mons"].keys())
        osds = sorted(self.cluster["osds"].keys())
        clients = sorted(self.cluster["clients"])
        rgws = sorted(self.cluster["rgws"])
        nodes = []
        nodes = common.unique_extend(nodes, mons)
        nodes = common.unique_extend(nodes, osds)
        nodes = common.unique_extend(nodes, clients)
        nodes = common.unique_extend(nodes, rgws)
        need_to_install_nodes = []
        stdout, stderr = common.pdsh(user, nodes, "ceph -v", option = "check_return")
        if stderr:
            err = common.format_pdsh_return(stderr)
            if err != {}:
                need_to_install_nodes = err.keys()
            else:
                need_to_install_nodes = []
        res = common.format_pdsh_return(stdout)
        return [res, need_to_install_nodes]

    def gen_cephconf(self, option="refresh"):
        if self.cluster["clean_build"] == "true":
            clean_build = True
        else:
            clean_build = False

        map_diff = self.cal_cephmap_diff()
        self.map_diff = map_diff
        cephconf = []
        for section in self.cluster["ceph_conf"]:
            cephconf.append("[%s]\n" % section)
            for key, value in self.cluster["ceph_conf"][section].items():
                cephconf.append("    %s = %s\n" % (key, value))

        original_daemon_config = self.read_cephconf(request_type="plain")

        if not clean_build:
            osds = map_diff["osd"]
            mons = map_diff["mon"]
            osd_id = map_diff["osd_num"]
            osd_dict = map_diff
            cephconf.extend( original_daemon_config )
        else:
            osds = self.cluster["osds"]
            mons = self.cluster["mons"]
            osd_dict = self.cluster
            osd_id = 0

        for mon in mons:
            cephconf.append("[mon.%s]\n" % mon)
            cephconf.append("    host = %s\n" % mon)
            cephconf.append("    mon addr = %s\n" % self.cluster["mons"][mon])

        for osd in sorted(osds):
            for device_bundle in common.get_list(osd_dict[osd]):
                osd_device = device_bundle[0]
                journal_device = device_bundle[1]
                cephconf.append("[osd.%d]\n" % osd_id)
                osd_id += 1
                cephconf.append("    host = %s\n" % osd)
                cephconf.append("    public addr = %s\n" % osds[osd]["public"])
                cephconf.append("    cluster addr = %s\n" % osds[osd]["cluster"])
                cephconf.append("    osd journal = %s\n" % journal_device)
                cephconf.append("    devs = %s\n" % osd_device)

        output = "".join(cephconf)
        with open("../conf/ceph.conf", 'w') as f:
            f.write(output)

    def read_cephconf(self, request_type="json"):
        cephconf_dict = OrderedDict()
        cephconf_dict["mon"] = []
        cephconf_dict["osd"] = {}
        cephconf_dict["mds"] = {}
        cephconf_dict["radosgw"] = []

        try:
            with open("../conf/ceph_current_status", 'r') as f:
                cephconf = f.readlines()
        except:
            common.printout("ERROR", "Current Cluster ceph.conf file not exists under CeTune/conf/")
            return cephconf_dict

        ceph_daemon_lines = []

        section_name = None
        host = None
        for line in cephconf:
            re_res = re.search('\[(.*)\]', line)
            if re_res:
                section_name = re_res.group(1)
                if 'mon.' in line or 'osd.' in line or 'radosgw.' in line:
                    ceph_daemon_lines.append( line )
            if not section_name:
                continue

            try:
                key, value = line.split('=')
            except:
                continue

            if "mon." in section_name:
                ceph_daemon_lines.append( line )
                if key.strip() == "host":
                    cephconf_dict["mon"].append( value.strip() )

            if "osd." in section_name:
                ceph_daemon_lines.append( line )
                if key.strip() == "host":
                    host = value.strip()
                    if host not in cephconf_dict["osd"]:
                        cephconf_dict["osd"][host] = []
                    device = ["",""]

                if key.strip() == "osd journal" and host:
                    device[1] = value.strip()
                    if device[0] != "" and device[1] != "":
                        cephconf_dict["osd"][host].append(':'.join(device))

                if key.strip() == "devs" and host:
                    device[0] = value.strip()
                    if device[0] != "" and device[1] != "":
                        cephconf_dict["osd"][host].append(':'.join(device))

            if "radosgw." in section_name:
                ceph_daemon_lines.append( line )
                if key.strip() == "host":
                    host = value.strip()
                    if host not in cephconf_dict["radosgw"]:
                        cephconf_dict["radosgw"].append(host)

        if request_type == "json":
            return cephconf_dict
        if request_type == "plain":
            return ceph_daemon_lines

    def cal_cephmap_diff(self):
        old_conf = self.read_cephconf()

        cephconf_dict = OrderedDict()
        cephconf_dict["mon"] = {}
        cephconf_dict["osd"] = {}
        cephconf_dict["mds"] = {}
        cephconf_dict["osd_num"] = 0

        for osd in self.cluster["osds"]:
            if osd not in old_conf["osd"].keys():
                cephconf_dict["osd"][osd] = self.cluster["osds"][osd]
                cephconf_dict[osd] = self.cluster[osd]
            else:
                for device in self.cluster[osd]:
                    if device not in old_conf["osd"][osd]:
                        if osd not in cephconf_dict["osd"]:
                            cephconf_dict["osd"][osd] = self.cluster["osds"][osd]
                        if osd not in cephconf_dict:
                            cephconf_dict[osd] = []
                        cephconf_dict[osd].append(device)
                    else:
                        cephconf_dict["osd_num"] += 1

        for node in self.cluster["mons"]:
            if node not in old_conf["mon"]:
                cephconf_dict["mon"][node] = self.cluster["mons"][node]

        return cephconf_dict

    def redeploy(self, gen_cephconf):
        common.printout("LOG","ceph.conf file generated")
        if self.cluster["clean_build"] == "true":
            clean_build = True
        else:
            clean_build = False

        if clean_build:
            self.cleanup()
            common.printout("LOG","Killed ceph-mon, ceph-osd and cleaned mon dir")

            if gen_cephconf:
                self.gen_cephconf()
                self.distribute_conf()

            common.printout("LOG","Started to build mon daemon")
            self.make_mon()
            common.printout("LOG","Succeeded in building mon daemon")
            common.printout("LOG","Started to build osd daemon")
            self.make_osds()
            common.printout("LOG","Succeeded in building osd daemon")
            common.bash("cp -f ../conf/ceph.conf ../conf/ceph_current_status")

        else:
            diff_map = self.cal_cephmap_diff()

            if gen_cephconf:
                self.gen_cephconf()
                self.distribute_conf()

            common.printout("LOG","Started to build mon daemon")
            self.make_mon(diff_map["mon"])
            common.printout("LOG","Succeeded in building mon daemon")
            common.printout("LOG","Started to build osd daemon")
            self.make_osds(diff_map["osd"], diff_map)
            common.printout("LOG","Succeeded in building osd daemon")
            common.bash("cp -f ../conf/ceph.conf ../conf/ceph_current_status")

    def restart(self):
        self.cleanup()
        self.startup()

    def startup(self):
        common.printout("LOG","Starting mon daemon")
        self.start_mon()
        common.printout("LOG","Starting osd daemon")
        self.start_osd()

    def cleanup(self):
        user = self.cluster["user"]
        mons = self.cluster["mons"]
        osds = self.cluster["osds"]
        mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["mon_data"])
        mon_filename = os.path.basename(self.cluster["ceph_conf"]["global"]["mon_data"]).replace("$id","*")
        common.printout("LOG","Shutting down mon daemon")
        common.pdsh( user, mons, " killall -9 ceph-mon", option="check_return")
        common.printout("LOG","Shutting down osd daemon")
        common.pdsh( user, osds, " killall -9 ceph-osd", option="check_return")

    def distribute_hosts(self, node_ip_bond):
        user = self.cluster["user"]
        nodes = []
        nodes.extend(self.cluster["clients"])
        nodes.extend(sorted(self.cluster["osds"]))

        common.add_to_hosts(node_ip_bond)
        for node in nodes:
            common.scp( user, node, '/etc/hosts', '/etc/hosts')

    def distribute_conf(self):
        user = self.cluster["user"]
        clients = self.cluster["clients"]
        osds = sorted(self.cluster["osds"])
        common.pdsh(user, osds, "mkdir -p /etc/ceph")
        common.pdsh(user, clients, "mkdir -p /etc/ceph")

        for client in clients:
            common.scp(user, client, "../conf/ceph.conf", "/etc/ceph/")
        for osd in osds:
            common.scp(user, osd, "../conf/ceph.conf", "/etc/ceph/")

    def make_osds(self, osds=None, diff_map=None):
        print diff_map
        user = self.cluster["user"]
        if osds==None:
            osds = sorted(self.cluster["osds"])
            diff_map = self.cluster
            osd_num = 0
        else:
            osd_num = diff_map["osd_num"]

        stdout, stderr = common.pdsh( user, osds, 'mount -l', option="check_return" )
        mount_list = {}
        for node, mount_list_tmp in common.format_pdsh_return(stdout).items():
            mount_list[node] = {}
            for line in mount_list_tmp.split('\n'):
                tmp = line.split()
                mount_list[node][tmp[0]] = tmp[2]

        for osd in osds:
            for device_bundle_tmp in diff_map[osd]:
                device_bundle = common.get_list(device_bundle_tmp)
                osd_device = device_bundle[0][0]
                journal_device = device_bundle[0][1]
                self.make_osd_fs( osd, osd_num, osd_device, journal_device, mount_list )
                self.make_osd( osd, osd_num, osd_device, journal_device )
                osd_num = osd_num+1

    def make_osd_fs(self, osd, osd_num, osd_device, journal_device, mount_list):
        user = self.cluster["user"]
        mkfs_opts = self.cluster['mkfs_opts']
        mount_opts = self.cluster['mount_opts']
        osd_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["osd_data"])
        osd_filename = os.path.basename(self.cluster["ceph_conf"]["global"]["osd_data"])

        common.printout("LOG","mkfs.xfs for %s on %s" % (osd_device, osd))
        try:
            mounted_dir = mount_list[osd][osd_device]
            common.pdsh( user, [osd], 'umount %s' % osd_device )
            common.pdsh( user, [osd], 'rm -rf %s' % mounted_dir )
        except:
            pass
        common.pdsh( user, [osd], 'mkfs.xfs %s %s' % (mkfs_opts, osd_device), option="console")
        osd_filedir = osd_filename.replace("$id", str(osd_num))
        common.pdsh( user, [osd], 'mkdir -p %s/%s' % (osd_basedir, osd_filedir))
        common.pdsh( user, [osd], 'mount %s -t xfs %s %s/%s' % (mount_opts, osd_device, osd_basedir, osd_filedir))

    def make_osd(self, osd, osd_num, osd_device, journal_device):
        user = self.cluster["user"]
        mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["mon_data"])
        osd_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["osd_data"])
        osd_filename = os.path.basename(self.cluster["ceph_conf"]["global"]["osd_data"])

        common.printout("LOG","start to build osd daemon for %s on %s" % (osd_device, osd))
        # Build the OSD
        osduuid = str(uuid.uuid4())
        osd_filedir = osd_filename.replace("$id",str(osd_num))
        key_fn = '%s/%s/keyring' % (osd_basedir, osd_filedir)
        common.pdsh(user, [osd], 'ceph osd create %s' % (osduuid), option="console")
        common.pdsh(user, [osd], 'ceph osd crush add osd.%d 1.0 host=%s rack=localrack root=default' % (osd_num, osd), option="console", except_returncode=2)
        common.pdsh(user, [osd], 'sh -c "ulimit -n 16384 && ulimit -c unlimited && exec ceph-osd -i %d --mkfs --mkkey --osd-uuid %s"' % (osd_num, osduuid), option="console", except_returncode=1)
        common.pdsh(user, [osd], 'ceph -i %s/keyring auth add osd.%d osd "allow *" mon "allow profile osd"' % (mon_basedir, osd_num), option="console", except_returncode=22)

        # Start the OSD
        common.pdsh(user, [osd], 'mkdir -p %s/pid' % mon_basedir)
        pidfile="%s/pid/ceph-osd.%d.pid" % (mon_basedir, osd_num)
        cmd = 'ceph-osd -i %d --pid-file=%s' % (osd_num, pidfile)
        cmd = 'ceph-run %s' % cmd
        common.pdsh(user, [osd], 'sh -c "ulimit -n 16384 && ulimit -c unlimited && exec %s"' % cmd, option="console", except_returncode=1)
        common.printout("LOG","Builded osd.%s daemon on %s" % (osd_num, osd))

    def make_mon(self, mons = None):
        user = self.cluster["user"]
        osds = sorted(self.cluster["osds"])
        if mons==None:
            mons = self.cluster["mons"]
        mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["mon_data"])

        # Keyring
        if not len(mons.keys()):
            return 

        mon = mons.keys()[0]
        common.pdsh(user, [mon], 'ceph-authtool --create-keyring --gen-key --name=mon. %s/keyring --cap mon \'allow *\'' % mon_basedir)
        common.pdsh(user, [mon], 'ceph-authtool --gen-key --name=client.admin --set-uid=0 --cap mon \'allow *\' --cap osd \'allow *\' --cap mds allow %s/keyring' % mon_basedir)
        common.rscp(user, mon, '%s/keyring.tmp' % mon_basedir, '%s/keyring' % mon_basedir )
        for node in osds:
            common.scp(user, node, '%s/keyring.tmp' % mon_basedir, '%s/keyring' % mon_basedir)
        # monmap
        cmd = 'monmaptool --create --clobber'
        for mon, addr in mons.items():
            cmd = cmd + ' --add %s %s' % (mon, addr)
        cmd = cmd + ' --print %s/monmap' % mon_basedir
        common.pdsh(user, [mon], cmd)
        common.rscp(user, mon, '%s/monmap.tmp' % mon_basedir, '%s/monmap' % mon_basedir)
        for node in mons:
            common.scp(user, node, '%s/monmap.tmp' % mon_basedir, '%s/monmap' % mon_basedir)

        # ceph-mons
        for mon, addr in mons.items():
            mon_filename = os.path.basename(self.cluster["ceph_conf"]["global"]["mon_data"]).replace("$id",mon)
            common.pdsh(user, [mon], 'rm -rf %s/%s' % (mon_basedir, mon_filename))
            common.pdsh(user, [mon], 'mkdir -p %s/%s' % (mon_basedir, mon_filename))
            common.pdsh(user, [mon], 'sh -c "ulimit -c unlimited && exec ceph-mon --mkfs -i %s --monmap=%s/monmap --keyring=%s/keyring"' % (mon, mon_basedir, mon_basedir), option="console", except_returncode=1)
            common.pdsh(user, [mon], 'cp %s/keyring %s/%s/keyring' % (mon_basedir, mon_basedir, mon_filename))

        # Start the mons
        for mon, addr in mons.items():
            common.pdsh(user, [mon], 'mkdir -p %s/pid' % mon_basedir)
            pidfile="%s/pid/%s.pid" % (mon_basedir, mon)
            cmd = 'sh -c "ulimit -c unlimited && exec ceph-mon -i %s --keyring=%s/keyring --pid-file=%s"' % (mon, mon_basedir, pidfile)
            cmd = 'ceph-run %s' % cmd
            common.pdsh(user, [mon], '%s' % cmd, option="console", except_returncode=1)
            common.printout("LOG","Builded mon.%s daemon on %s" % (mon, mon))

    def start_mon(self):
        mons = self.cluster["mons"]
        user = self.cluster["user"]
        mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["mon_data"])
        # Start the mons
        for mon, addr in mons.items():
            common.pdsh(user, [mon], 'mkdir -p %s/pid' % mon_basedir)
            pidfile="%s/pid/%s.pid" % (mon_basedir, mon)
            #lttng_prefix = "LD_PRELOAD=/usr/lib/x86_64-linux-gnu/liblttng-ust-fork.so"
            lttng_prefix = ""
            cmd = 'sh -c "ulimit -c unlimited && exec ceph-mon -i %s --keyring=%s/keyring --pid-file=%s"' % (mon, mon_basedir, pidfile)
            cmd = 'ceph-run %s' % cmd
            common.pdsh(user, [mon], '%s %s' % (lttng_prefix, cmd), option="console", except_returncode=1)
            common.printout("LOG","Started mon.%s daemon on %s" % (mon, mon))

    def start_osd(self):
        user = self.cluster["user"]
        osds = sorted(self.cluster["osds"])
        mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["mon_data"])
        osd_basedir = os.path.dirname(self.cluster["ceph_conf"]["global"]["osd_data"])
        osd_filename = os.path.basename(self.cluster["ceph_conf"]["global"]["osd_data"])
        osd_num = 0
        for osd in osds:
            for device_bundle_tmp in self.cluster[osd]:
                # Start the OSD
                common.pdsh(user, [osd], 'mkdir -p %s/pid' % mon_basedir)
                pidfile="%s/pid/ceph-osd.%d.pid" % (mon_basedir, osd_num)
                #lttng_prefix = "LD_PRELOAD=/usr/lib/x86_64-linux-gnu/liblttng-ust-fork.so"
                lttng_prefix = ""
                cmd = 'ceph-osd -i %d --pid-file=%s' % (osd_num, pidfile)
                cmd = 'ceph-run %s' % cmd
                common.pdsh(user, [osd], '%s sh -c "ulimit -n 16384 && ulimit -c unlimited && exec %s"' % (lttng_prefix, cmd), option="console",except_returncode=1)
                common.printout("LOG","Started osd.%s daemon on %s" % (osd_num, osd))
                osd_num = osd_num+1
