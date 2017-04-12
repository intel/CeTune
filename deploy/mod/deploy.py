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
        common.printout("LOG", "============start deploy============",log_level="LVL3")
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
        self.cluster["mdss"] = {}
        self.cluster["ceph_conf"] = OrderedDict()
        self.cluster["ceph_conf"]["global"] = OrderedDict()
        self.cluster["ceph_conf"]["mon"] = OrderedDict()
        self.cluster["ceph_conf"]["osd"] = OrderedDict()
        self.cluster["ceph_conf"]["global"]["fsid"] = str(uuid.uuid1())
        self.cluster["ceph_conf"]["global"]["pid_path"] = "/var/run/ceph"
        self.cluster["ceph_conf"]["global"]["auth_service_required"] = "none"
        self.cluster["ceph_conf"]["global"]["auth_cluster_required"] = "none"
        self.cluster["ceph_conf"]["global"]["auth_client_required"] = "none"
        self.cluster["ceph_conf"]["mon"]["mon_data"] = "/var/lib/ceph/mon.$id"
        self.cluster["ceph_conf"]["osd"]["osd_data"] = "/var/lib/ceph/mnt/osd-device-$id-data"
        self.cluster["collector"] = self.all_conf_data.get_list("collector")
        self.cluster["ceph_disk"] = {}
	self.cluster["disk_format"] = self.all_conf_data.get("disk_format")

        for key, value in self.all_conf_data.get_group("ceph_hard_config").items():
            section_name = "global"
            if "|" in key:
                section_name, key = key.split("|")
            if section_name not in self.cluster["ceph_conf"]:
                self.cluster["ceph_conf"][section_name] = OrderedDict()
            self.cluster["ceph_conf"][section_name][key] = value

        for k, v in self.all_conf_data.get_group("ceph_disk_config").items():
            self.cluster["ceph_disk"][k] = v

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
        self.bluestore_block_pathes = ("bluestore_block_db_path", "bluestore_block_wal_path")
        for bluestore_block_path in self.bluestore_block_pathes:
            if bluestore_block_path in self.cluster["ceph_conf"]["global"]:
                device_pathes = self.cluster["ceph_conf"]["global"][bluestore_block_path]
                pathes = device_pathes.split(",")
                for path in pathes:
                    (osd_host, device_path) = path.split(":")
                    if not self.cluster["osds"].has_key(osd_host):
                        self.cluster["osds"][osd_host] = {bluestore_block_path: device_path}
                    else:
                        self.cluster["osds"][osd_host].update({bluestore_block_path: device_path})
                self.cluster["ceph_conf"]["global"].pop(bluestore_block_path, None)
        if not cluster_subnet:
            cluster_subnet = subnet
        if not public_subnet:
            public_subnet = subnet

        for osd in self.all_conf_data.get_list("list_server"):
	    if not self.cluster["osds"].has_key(osd):
                self.cluster["osds"][osd] = {"public":ip_handler.getIpByHostInSubnet(osd, public_subnet), "cluster":ip_handler.getIpByHostInSubnet(osd, cluster_subnet)}
	    else:
	        self.cluster["osds"][osd].update({"public":ip_handler.getIpByHostInSubnet(osd, public_subnet), "cluster":ip_handler.getIpByHostInSubnet(osd, cluster_subnet)})
        for mon in self.all_conf_data.get_list("list_mon"):
            self.cluster["mons"][mon] = ip_handler.getIpByHostInSubnet(mon, monitor_subnet)
        for mds in self.all_conf_data.get_list("list_mds"):
            self.cluster["mdss"][mds] = ip_handler.getIpByHostInSubnet(mds)

        for osd in self.cluster["osds"]:
            self.cluster[osd] = self.all_conf_data.get_list(osd)

        self.cluster["fs"] = "xfs"
        self.cluster["mkfs_opts"] = "-f -i size=2048 -n size=64k"
        self.cluster["mount_opts"] = "-o inode64,noatime,logbsize=256k"

        self.cluster["ceph_conf"]["client"] = {}
        self.cluster["ceph_conf"]["client"]["rbd_cache"] = "false"
        self.cluster["ceph_conf"]["osd"]["osd_mkfs_type"] = "xfs"
        osd_mount_options_fs_type = "osd_mount_options" + "_" + self.cluster["ceph_conf"]["osd"]["osd_mkfs_type"]
        self.cluster["ceph_conf"]["osd"][osd_mount_options_fs_type] = "rw,noatime,inode64,logbsize=256k"

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
                if section_name == 'mds':
                    if 'mds' not in self.cluster["ceph_conf"]:
                        self.cluster["ceph_conf"]['mds'] = OrderedDict()
                    for key, value in section.items():
                        self.cluster["ceph_conf"]['mds'][key] = value
                if section_name == 'client':
		    if 'client' not in self.cluster["ceph_conf"]:
			self.cluster["ceph_conf"]['client'] = OrderedDict()
		    for key, value in section.items():
			self.cluster["ceph_conf"]['client'][key] = value

        self.map_diff = None

    def _get_ceph_disk_config(self, parameter):
        default_value = ""
        if parameter == "prepend_to_path":
            default_value = "/usr/bin"
        elif parameter == "statedir":
            default_value = "/var/lib/ceph"
        elif parameter == "sysconfdir":
            default_value = "/etc/ceph"
        value = self.cluster["ceph_disk"].get(parameter, default_value)
        return value

    def install_binary(self, version=""):
        installed, non_installed = self.check_ceph_installed()
        uninstall_nodes = []
        need_to_install_nodes = []
        correctly_installed_nodes = {}
        installed_list = []
        version_map = {'cuttlefish': '0.61',
                       'dumpling': '0.67',
                       'emperor': '0.72',
                       'firefly': '0.80',
                       'giant': '0.87',
                       'hammer': '0.94',
                       'infernalis': '9.2',
		       'jewel': '10.2'}
        for node, version_code in installed.items():
            if version == "":
                for release_name, short_version in version_map.items():
                    if short_version in version_code:
                        version_release_name = release_name
                        break
                installed_list = common.unique_extend( installed_list, [version_release_name])
                continue
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
            common.printout("ERROR", "More than two versions of ceph installed, %s" % installed_list,log_level="LVL1")
            sys.exit()
        if len(uninstall_nodes):
            self.uninstall_binary(uninstall_nodes)
        need_to_install_nodes.extend(non_installed)
        common.printout("LOG", "Ceph already installed on below nodes")
        for node, value in correctly_installed_nodes.items():
            common.printout("LOG", "%s, installed version: %s" % (node, value))
        if len(need_to_install_nodes):
            common.printout("LOG", "Will start to install ceph on %s" % str(need_to_install_nodes))

        if "testing" == version:
            install_opts = "--testing"
        elif "," in version:
            repo, gpg = version.split(",")
            repo_url = ":".join(repo.split(":")[1:])
            gpg_url = ":".join(gpg.split(":")[1:])
            install_opts = "--repo-url %s --gpg-url %s" % (str(repo_url), str(gpg_url))
        elif ":" in version:
            pkg_type = version.split(":")[0]
            version = ":".join(version.split(":")[1:])
            install_opts = "--%s %s" % (str(pkg_type), str(version))
        else:
            install_opts = "--release %s" % str(version)

        common.printout("LOG", "Install opts is '%s'" % str(install_opts))
        # pkg_type = "release"
        # if ":" in version:
        #     try:
        #         pkg_type, version = version.split(":")
        #     except:
        #         common.printout("ERROR", "Please check version, received $s" % version)

        user = self.cluster["user"]
        node_os_dict = common.return_os_id(user, need_to_install_nodes)
        for node in need_to_install_nodes:
            if node in node_os_dict and "Ubuntu" in node_os_dict[node]:
                common.pdsh(user, [node], "apt-get -f -y autoremove", option="console")
            common.bash("ceph-deploy install %s %s 2>&1" % (install_opts, node), option="console")

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
                common.pdsh(user, [node], "apt-get purge -f -y python-cephfs", option="console")
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

    def gen_cephconf(self, option="refresh", ceph_disk=False):
        if self.cluster["clean_build"] == "true":
            clean_build = True
        else:
            clean_build = False

        map_diff = self.cal_cephmap_diff(ceph_disk=ceph_disk)
        common.printout("WARNING","Found different configuration from conf/ceph_current_conf with your desired config : %s" % map_diff)
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

        backend_storage = self.cluster["ceph_conf"]["global"]["osd_objectstore"]

	disk_format_list = common.parse_disk_format(self.cluster["disk_format"])

        if backend_storage == "filestore":
            assert(2 == len(disk_format_list))
            osd_pos = disk_format_list.index("osd")
            journal_pos = disk_format_list.index("journal")
        elif backend_storage == "bluestore":
            assert(3 <= len(disk_format_list))
            assert(4 >= len(disk_format_list))
            osd_pos = disk_format_list.index("osd")
            block_pos = disk_format_list.index("data")
            if (3 == len(disk_format_list)):
                db_wal_pos = disk_format_list.index("db_wal")
            else:
                db_pos = disk_format_list.index("db")
                wal_pos = disk_format_list.index("wal")
	for osd in sorted(osds):
            for device_bundle in common.get_list(osd_dict[osd]):
                disk_format_list_len = len(disk_format_list)
		assert(disk_format_list_len <= len(device_bundle))
                cephconf.append("[osd.%d]\n" % osd_id)
                osd_id += 1
                cephconf.append("    host = %s\n" % osd)
                cephconf.append("    public addr = %s\n" % osds[osd]["public"])
                cephconf.append("    cluster addr = %s\n" % osds[osd]["cluster"])
                if ceph_disk:
                    cephconf.append("    devs = %s\n" % (device_bundle[osd_pos]))
                else:
                    cephconf.append("    devs = %s\n" % device_bundle[osd_pos])
                if disk_format_list_len == 1 or device_bundle[1] == "":
                    continue
                if ceph_disk:
                    if backend_storage == "filestore":
                        cephconf.append("    osd journal = %s\n" % (device_bundle[journal_pos]))
                    else:
                        cephconf.append("    bluestore_block_path = %s\n" % (device_bundle[block_pos]))
                else:
                    if backend_storage == "filestore":
                        cephconf.append("    osd journal = %s\n" % device_bundle[journal_pos])
                    else:
                        cephconf.append("    bluestore_block_path = %s\n" % device_bundle[block_pos])
                if disk_format_list_len == 2 or backend_storage == "filestore":
                    continue

                # bluestore specific
                if disk_format_list_len == 3:
                    cephconf.append("    bluestore_block_db_path = %s\n" % (device_bundle[db_wal_pos]))
                    continue
                if disk_format_list_len == 4:
                    cephconf.append("    bluestore_block_db_path = %s\n" % (device_bundle[db_pos]))
                    cephconf.append("    bluestore_block_wal_path = %s\n" % device_bundle[wal_pos])

                for bluestore_block_path in self.bluestore_block_pathes:
                    if osds[osd].has_key(bluestore_block_path):
                        cephconf.append("    %s = %s\n" % (bluestore_block_path, osds[osd][bluestore_block_path]))
	

        output = "".join(cephconf)
        with open("../conf/ceph.conf", 'w') as f:
            f.write(output)

    def read_cephconf(self, request_type="json"):
        cephconf_dict = OrderedDict()
        cephconf_dict["mon"] = []
        cephconf_dict["osd"] = {}
        cephconf_dict["mds"] = []
        cephconf_dict["radosgw"] = []
        tmp_dict = {}

        cephconf = ""
        try:
            if not os.path.exists("../conf/ceph_current_status"):
                with open("/etc/ceph/ceph.conf", 'r') as f:
                    cephconf = f.readlines()
            else:
                with open("../conf/ceph_current_status", 'r') as f:
                    cephconf = f.readlines()
        except:
            common.printout("WARNING", "Current Cluster ceph.conf file not exists under CeTune/conf/")
            return cephconf_dict

        ceph_daemon_lines = []

        section_name = None
        host = None
        for line in cephconf:
            line = line.strip()
            re_res = re.search('\[(.*)\]', line)
            if re_res:
                section_name = re_res.group(1)
                if 'mds.' in line or 'mon.' in line or 'osd.' in line or 'radosgw.' in line:
                    ceph_daemon_lines.append( line+"\n" )
            if not section_name or not ( 'mds.' in section_name or 'mon.' in section_name or 'osd.' in section_name or 'radosgw.' in section_name ):
                continue

            try:
                key, value = line.split('=')
            except:
                key = line
                value = ""

            if not ( 'mds.' in line or 'mon.' in line or 'osd.' in line or 'radosgw.' in line ):
                ceph_daemon_lines.append( line+"\n" )

            if section_name not in tmp_dict:
                tmp_dict[section_name] = {}
                tmp_dict[section_name]["device"] = ["",""]
                tmp_dict[section_name]["host"] = ""

            if "mds." in section_name:
                if key.strip() == "host":
                    cephconf_dict["mds"].append( value.strip() )

            if "mon." in section_name:
                if key.strip() == "host":
                    cephconf_dict["mon"].append( value.strip() )

            if "osd." in section_name:
                if key.strip() == "host":
                    host = value.strip()
                    tmp_dict[section_name]["host"] = host
                    if host not in cephconf_dict["osd"]:
                        cephconf_dict["osd"][host] = []

                if key.strip() == "osd journal":
                    tmp_dict[section_name]["device"][1] = value.strip()

                if key.strip() == "devs":
                    tmp_dict[section_name]["device"][0] = value.strip()

                if tmp_dict[section_name]["host"] != "" and tmp_dict[section_name]["device"][0] != "" and tmp_dict[section_name]["device"][1] != "":
                    device = tmp_dict[section_name]["device"]
                    cephconf_dict["osd"][host].append(':'.join(device))

            if "radosgw." in section_name:
                if key.strip() == "host":
                    host = value.strip()
                    if host not in cephconf_dict["radosgw"]:
                        cephconf_dict["radosgw"].append(host)

        if request_type == "json":
            return cephconf_dict
        if request_type == "plain":
            return ceph_daemon_lines

    def cal_cephmap_diff(self, ceph_disk=False):
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
                    if ceph_disk:
                        data, journal = device.split(":")
                        device = data + "1" + ":" + journal + "1"
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

        for node in self.cluster["mdss"]:
            if node not in old_conf["mds"]:
                cephconf_dict["mds"][node] = self.cluster["mdss"][node]

        return cephconf_dict

    def redeploy(self, gen_cephconf, ceph_disk=False):
        common.printout("LOG","ceph.conf file generated")
        if self.cluster["clean_build"] == "true":
            clean_build = True
        else:
            clean_build = False

        if ceph_disk:
            statedir = self._get_ceph_disk_config("statedir")
            self.cluster["ceph_conf"]["osd"]["osd_data"] = statedir + "/osd/ceph-$id"

        if clean_build:
            self.cleanup(ceph_disk=ceph_disk)
            common.printout("LOG","Killed ceph-mon, ceph-osd and cleaned mon dir")

            if gen_cephconf:
                self.gen_cephconf(ceph_disk=ceph_disk)
                self.distribute_conf()

            common.printout("LOG","Started to build mon daemon")
            self.make_mon()
            common.printout("LOG","Succeeded in building mon daemon")
            common.printout("LOG","Started to build osd daemon")
            self.make_osds(ceph_disk=ceph_disk)
            common.printout("LOG","Succeeded in building osd daemon")
            common.bash("cp -f ../conf/ceph.conf ../conf/ceph_current_status")

        else:
            diff_map = self.cal_cephmap_diff(ceph_disk=ceph_disk)

            if gen_cephconf:
                self.gen_cephconf(ceph_disk=ceph_disk)
                self.distribute_conf()

            common.printout("LOG","Started to build mon daemon")
            self.make_mon(diff_map["mon"])
            common.printout("LOG","Succeeded in building mon daemon")
            common.printout("LOG","Started to build osd daemon")
            self.make_osds(diff_map["osd"], diff_map, ceph_disk=ceph_disk)
            common.printout("LOG","Succeeded in building osd daemon")
            common.bash("cp -f ../conf/ceph.conf ../conf/ceph_current_status")

    def restart(self, ceph_disk=False):
        self.cleanup(ceph_disk=ceph_disk)
        self.startup(ceph_disk=ceph_disk)

    def startup(self, ceph_disk=False):
        common.printout("LOG","Starting mon daemon")
        self.start_mon()
        common.printout("LOG","Starting osd daemon")
        if ceph_disk:
            self.start_osd_created_by_ceph_disk()
        else:
            self.start_osd()

    def cleanup(self, ceph_disk=False):
        user = self.cluster["user"]
        mons = self.cluster["mons"]
        osds = self.cluster["osds"]
        mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["mon"]["mon_data"])
        mon_filename = os.path.basename(self.cluster["ceph_conf"]["mon"]["mon_data"]).replace("$id","*")
        common.printout("LOG", "Shutting down mon daemon")
        common.pdsh(user, mons, "killall -9 ceph-mon", option="check_return")

        try_kill = True
        if ceph_disk:
            try_kill = False
            try:
                osd_list = self.get_daemon_info_from_ceph_conf("osd")
            except:
                common.printout("WARNING", "Unable to fetch old cluster configuration, try killall")
                try_kill = True
            if not try_kill:
                for osd in osd_list:
                    osd_name = osd["daemon_name"]
                    osd_host = osd["daemon_host"]
                    common.pdsh(user, [osd_host], 'stop ceph-osd id=%s' % osd_name,
                                option="console", except_returncode=1)
                    common.printout("LOG","Stop osd.%s daemon on %s" % (osd_name, osd_host))
        if try_kill:
            common.printout("LOG", "Shutting down osd daemon")
            common.pdsh(user, osds, "killall -9 ceph-osd", option="check_return")

    def distribute_hosts(self, node_ip_bond):
        user = self.cluster["user"]
        nodes = []
        common.unique_extend(nodes, sorted(self.cluster["clients"]) )
        common.unique_extend(nodes, sorted(self.cluster["mons"]) )
        common.unique_extend(nodes, sorted(self.cluster["osds"]) )

        common.add_to_hosts(node_ip_bond)
        for node in nodes:
            common.scp( user, node, '/etc/hosts', '/etc/hosts')

    def distribute_conf(self):
        user = self.cluster["user"]
        nodes = []
        common.unique_extend(nodes, sorted(self.cluster["clients"]) )
        common.unique_extend(nodes, sorted(self.cluster["mons"]) )
        common.unique_extend(nodes, sorted(self.cluster["osds"]) )
        common.pdsh(user, nodes, "mkdir -p /etc/ceph")

        for node in nodes:
            common.pdsh(user, [node], "rm -rf /etc/ceph/ceph.conf")
            common.scp(user, node, "../conf/ceph.conf", "/etc/ceph/")

    def make_osds(self, osds=None, diff_map=None, ceph_disk=False):
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
                journal_device = None
                if self.cluster["ceph_conf"]["global"]["osd_objectstore"] == "filestore":
                    journal_device = device_bundle[0][1]
                if not ceph_disk:
                    self.make_osd_fs( osd, osd_num, osd_device, journal_device, mount_list )
                    self.make_osd( osd, osd_num, osd_device, journal_device )
                else:
                    self.make_osd_ceph_disk_prepare(osd, osd_device, journal_device, mount_list)
                    self.make_osd_ceph_disk_activate(osd, osd_device)
                osd_num = osd_num+1

    def make_osd_ceph_disk_prepare(self, osd, osd_device, journal_device, mount_list):
        """

            ceph-disk prepare.
            The mount path is {statedir} + "/osd" + "/{cluster-name}-{osd-id}".
            The osd_device here should be a block deivce not a partition. The ceph-disk
            will check it.
        :param osd:
        :param osd_device:
        :param journal_device:
        :return:
        """

        common.printout("LOG", "Begin to use ceph-disk to prepare disk for osd")

        user = self.cluster["user"]

        try:
            mounted_dir = mount_list[osd][osd_device + "1"]
            common.printout("LOG", "mounted_dir: %s" % mounted_dir)
            if mounted_dir:
                common.printout("LOG", "Begin to umount the dir %s" % mounted_dir)
                common.pdsh( user, [osd], 'umount %s' % (osd_device + "1") )
                common.printout("LOG", "End to umount the dir %s" % mounted_dir)
                common.pdsh( user, [osd], 'rm -rf %s' % mounted_dir )
        except:
            pass
        #common.pdsh(user, [osd], 'ceph-disk zap %s' % osd_device)
        #common.pdsh(user, [osd], 'ceph-disk zap %s' % journal_device)
        #common.printout("LOG", "End clean up the dirty device and dir")

        prepend_to_path = self._get_ceph_disk_config("prepend_to_path")
        statedir = self._get_ceph_disk_config("statedir")
        sysconfdir = self._get_ceph_disk_config("sysconfdir")
        prepend_to_path_arg = " --prepend-to-path %s" % prepend_to_path
        statedir_arg = " --statedir %s" % statedir
        sysconfdir_arg = " --sysconfdir %s" % sysconfdir
        data_dev = osd_device
        journal_dev = journal_device
        fsid = self.cluster["ceph_conf"]["global"]["fsid"]
        backend_storage = self.cluster["ceph_conf"]["global"]["osd_objectstore"]
        if backend_storage == "filestore":
            cmd = "ceph-disk -v" + prepend_to_path_arg + statedir_arg + \
                sysconfdir_arg + " prepare " + data_dev + " " + journal_dev + \
                " --cluster ceph" + " --cluster-uuid " + fsid
        else:
            cmd = "ceph-disk -v" + prepend_to_path_arg + statedir_arg + \
                sysconfdir_arg + " prepare --bluestore " + data_dev + " " + \
                " --cluster ceph" + " --cluster-uuid " + fsid

        common.printout("LOG", "Command is " + cmd)
        common.pdsh(user, [osd], cmd)

    def make_osd_ceph_disk_activate(self, osd, osd_deivce):
        common.printout("LOG", "Begin to use ceph-disk to activate osd")
        user = self.cluster["user"]
        dev_path = osd_deivce
        cmd = "ceph-disk -v activate %s --mark-init upstart" % dev_path
        common.printout("LOG", "Command is " + cmd)
        common.pdsh(user, [osd], cmd)

    def make_osd_fs(self, osd, osd_num, osd_device, journal_device, mount_list):
        user = self.cluster["user"]
        mkfs_opts = self.cluster['mkfs_opts']
        mount_opts = self.cluster['mount_opts']
        osd_basedir = os.path.dirname(self.cluster["ceph_conf"]["osd"]["osd_data"])
        osd_filename = os.path.basename(self.cluster["ceph_conf"]["osd"]["osd_data"])

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
        mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["mon"]["mon_data"])
        osd_basedir = os.path.dirname(self.cluster["ceph_conf"]["osd"]["osd_data"])
        osd_filename = os.path.basename(self.cluster["ceph_conf"]["osd"]["osd_data"])

        common.printout("LOG","start to build osd daemon for %s on %s" % (osd_device, osd))
        # Build the OSD
        osduuid = str(uuid.uuid4())
        osd_filedir = osd_filename.replace("$id",str(osd_num))
        key_fn = '%s/%s/keyring' % (osd_basedir, osd_filedir)
        common.pdsh(user, [osd], 'ceph osd create %s' % (osduuid), option="console")
        common.pdsh(user, [osd], 'ceph osd crush add osd.%d 1.0 host=%s rack=localrack root=default' % (osd_num, osd), option="console", except_returncode=2)
        common.pdsh(user, [osd], 'sh -c "ulimit -n 16384 && ulimit -c unlimited && exec ceph-osd -i %d --mkfs --mkkey --osd-uuid %s"' % (osd_num, osduuid), option="console", except_returncode=1)
        #common.pdsh(user, [osd], 'ceph -i %s/keyring auth add osd.%d osd "allow *" mon "allow profile osd"' % (mon_basedir, osd_num), option="console", except_returncode=22)
        common.pdsh(user, [osd], 'ceph -i %s auth add osd.%d osd "allow *" mon "allow profile osd"' % (key_fn, osd_num), option="console", except_returncode=22)

        # Start the OSD
        # common.pdsh(user, [osd], 'mkdir -p %s/pid' % mon_basedir)
        pid_path = self.cluster["ceph_conf"]["global"]["pid_path"]
        pidfile="%s/ceph-osd.%d.pid" % (pid_path, osd_num)
        cmd = 'ceph-osd -i %d --pid-file=%s' % (osd_num, pidfile)
        cmd = 'ceph-run %s' % cmd
        common.pdsh(user, [osd], 'sh -c "ulimit -n 16384 && ulimit -c unlimited && exec %s"' % cmd, option="console", except_returncode=1)
        common.printout("LOG","Builded osd.%s daemon on %s" % (osd_num, osd))

    def make_mon(self, mons = None):
        user = self.cluster["user"]
        osds = sorted(self.cluster["osds"])
        if mons==None:
            mons = self.cluster["mons"]
        # Keyring
        if not len(mons.keys()):
            return 

        mon = mons.keys()[0]
	mon_basedir = os.path.dirname(self.cluster["ceph_conf"]["mon"]["mon_data"])
	common.pdsh(user, [mon], 'mkdir -p %s' % mon_basedir)
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
            mon_filename = os.path.basename(self.cluster["ceph_conf"]["mon"]["mon_data"]).replace("$id",mon)
            common.pdsh(user, [mon], 'rm -rf %s/%s' % (mon_basedir, mon_filename))
            common.pdsh(user, [mon], 'mkdir -p %s/%s' % (mon_basedir, mon_filename))
            common.pdsh(user, [mon], 'sh -c "ulimit -c unlimited && exec ceph-mon --mkfs -i %s --monmap=%s/monmap --keyring=%s/keyring"' % (mon, mon_basedir, mon_basedir), option="console", except_returncode=1)
            common.pdsh(user, [mon], 'cp %s/keyring %s/%s/keyring' % (mon_basedir, mon_basedir, mon_filename))

        # Start the mons
        for mon, addr in mons.items():
            # common.pdsh(user, [mon], 'mkdir -p %s/pid' % mon_basedir)
            pid_path = self.cluster["ceph_conf"]["global"]["pid_path"]
            pidfile="%s/%s.pid" % (pid_path, mon)
            cmd = 'sh -c "ulimit -c unlimited && exec ceph-mon -i %s --keyring=%s/keyring --pid-file=%s"' % (mon, mon_basedir, pidfile)
            cmd = 'ceph-run %s' % cmd
            common.pdsh(user, [mon], '%s' % cmd, option="console", except_returncode=1)
            common.printout("LOG","Builded mon.%s daemon on %s" % (mon, mon))

    def get_daemon_info_from_ceph_conf(self, daemon):

        """

        :param: daemon: The daemon must be one of osd, mon or mds
        :type: string
        :return: daemon_list: the list of daemon info
                    [
                        {
                            "daemon_name": "0",
                            "daemon_host": "ceph_node0",
                            "daemon_data": "/var/lib/ceph/osd/osd$id"
                        }
                    ]
        :rtype: tuple
        """

        if not daemon:
            common.printout("ERROR",
                            "please select your daemon[osd, mon or mds]",log_level="LVL1")
            sys.exit(1)

        if daemon not in ["osd", "mon", "mds"]:
            common.printout("ERROR",
                            "the daemon is not one of osd, mon or mds",log_level="LVL1")
            sys.exit(1)

        ceph_conf = ""
        try:
            if not os.path.exists("../conf/ceph_current_status"):
                with open("/etc/ceph/ceph.conf", 'r') as f:
                    ceph_conf = f.readlines()
            else:
                with open("../conf/ceph_current_status", 'r') as f:
                    ceph_conf = f.readlines()
        except:
            common.printout("ERROR",
                            "Current Cluster ceph_current_status file not exists under CeTune/conf/",log_level="LVL1")
            sys.exit(1)

        num = 0
        daemon_name = ""
        daemon_data = ""
        daemon_list = []
        for line in ceph_conf:
            line = line.strip()
            if "%s_data" % daemon in line or "%s data" % daemon in line:
                daemon_data = line.split("=")[1].strip()
                continue
            if "%s." % daemon in line:
                daemon_name = line[5:-1]
                num = num + 1
                continue
            if num == 1:
                if "host" not in line:
                    continue
                num = 0
                daemon_host = line.split("=")[1].strip()
                daemon_list.append({
                    "daemon_name": daemon_name,
                    "daemon_host": daemon_host,
                    "daemon_data": daemon_data
                })
        return daemon_list

    def start_mon(self):
        user = self.cluster["user"]
        mon_list = self.get_daemon_info_from_ceph_conf("mon")
        for mon in mon_list:
            mon_name = mon["daemon_name"]
            mon_host = mon["daemon_host"]
            mon_data = mon["daemon_data"]
            pid_path = self.cluster["ceph_conf"]["global"]["pid_path"]
            pidfile = "%s/mon.%s.pid" % (pid_path, mon_name)
            lttng_prefix = ""
            keyring_file = mon_data.replace("$id", mon_name) + "/keyring"
            cmd = 'sh -c "ulimit -c unlimited && exec ceph-mon -i %s ' \
                  '--keyring=%s --pid-file=%s"' % (mon_name, keyring_file, pidfile)
            cmd = 'ceph-run %s' % cmd
            common.pdsh(user, [mon_host], '%s %s' % (lttng_prefix, cmd),
                        option="console", except_returncode=1)
            common.printout("LOG","Started mon.%s daemon on %s" % (mon_host, mon_host))

    def start_osd_created_by_ceph_disk(self):
        user = self.cluster["user"]
        osd_list = self.get_daemon_info_from_ceph_conf("osd")
        for osd in osd_list:
            osd_name = osd["daemon_name"]
            osd_host = osd["daemon_host"]
            common.pdsh(user, [osd_host], 'start ceph-osd id=%s' % osd_name,
                        option="console", except_returncode=1)
            common.printout("LOG","Started osd.%s daemon on %s" % (osd_name, osd_host))

    def start_osd(self):
        user = self.cluster["user"]
        osd_list = self.get_daemon_info_from_ceph_conf("osd")
        print osd_list
        for osd in osd_list:
            osd_name = osd["daemon_name"]
            osd_host = osd["daemon_host"]
            pid_path = self.cluster["ceph_conf"]["global"]["pid_path"]
            pidfile = "%s/osd.%s.pid" % (pid_path, osd_name)
            if "lttng" in self.cluster["collector"]:
                lttng_prefix = "LD_PRELOAD=/usr/lib/x86_64-linux-gnu/liblttng-ust-fork.so"
            else:
                lttng_prefix = ""
            cmd = 'ceph-osd -i %s --pid-file=%s' % (osd_name, pidfile)
            cmd = 'ceph-run %s' % cmd
            common.pdsh(user, [osd_host],
                        '%s sh -c "ulimit -n 16384 && ulimit -c unlimited && '
                        'exec %s"' % (lttng_prefix, cmd), option="console",
                        except_returncode=1)
            common.printout("LOG","Started osd.%s daemon on %s" % (osd_name, osd_host))

    def osd_perf_reset(self):
        osd_list = self.get_daemon_info_from_ceph_conf("osd")
        user = self.cluster["user"]
        for osd in osd_list:
            osd_name = osd["daemon_name"]
            osd_host = osd["daemon_host"]
            cmd = "ceph daemon osd.{0} perf reset all".format(osd_name)
            common.pdsh(user, [osd_host],cmd)
            common.printout("LOG","ceph daemon osd.{0} perf clean on {1}. ".format (osd_name, osd_host))
