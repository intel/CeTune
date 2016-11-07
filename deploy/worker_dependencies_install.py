import os

pkg_list = ['python-pip','unzip','sysstat','curl','openjdk-7-jre','haproxy']

#update apt-get
os.system('sudo apt-get update')

#install pkg
failed_install_list = []
for pkg in pkg_list:
    os.system('sudo apt-get install -y '+pkg)
    #import pdb
    output = os.popen('echo $?')
    re_st = output.read().strip('\n')
    if str(re_st) != "0":
        failed_install_list.append(pkg)
if len(failed_install_list) != 0:
    print 'Install Failed Pkgs:'
    print '============================'
    for i in failed_install_list:
        print i
else:
    print "============================"
    print "Successfully Installed !"
