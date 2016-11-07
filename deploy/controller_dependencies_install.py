import os

apt_pkg_list = ['python-pip','pdsh','unzip','zip','expect','sysstat','curl','openjdk-7-jre','haproxy','python-matplotlib','python-numpy','python-yaml','sqlite']

pip_pkg_list = ['ceph-deploy','pyyaml','argparse','markdown2']
#update apt-get
os.system('sudo apt-get update')

#install apt pkgs
apt_failed_install_list = []
pip_failed_install_list = []
for pkg in apt_pkg_list:
    os.system('sudo apt-get install -y '+pkg)
    #import pdb
    output = os.popen('echo $?')
    re_st = output.read().strip('\n')
    if str(re_st) != "0":
        apt_failed_install_list.append(pkg)

#install pip pkgs
for pkg in pip_pkg_list:
    os.system('sudo pip install '+pkg)
    output = os.popen('echo $?')
    re_st = output.read().strip('\n')
    if str(re_st) != "0":
        pip_failed_install_list.append(pkg)

if len(apt_failed_install_list) != 0:
    print 'APT Install Failed Pkgs:'
    print '============================'
    for i in apt_failed_install_list:
        print i
    print 'Solution:'
    print '----------------------------'
    print '    #sudo apt-get install -y package_name'

if len(pip_failed_install_list) != 0:
    print 'PIP Install Failed Pkgs:'
    print '============================'
    for i in apt_failed_install_list:
        print i
    print 'Solution:'
    print '----------------------------'
    print '    #sudo pip install package_name'

if len(apt_failed_install_list) == 0 and len(pip_failed_install_list) == 0:
    print "============================"
    print "Successfully Installed !"
