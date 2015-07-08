#/usr/bin/python
import os,sys,re,copy

common_path = os.path.abspath(os.path.join('../conf/'))
sys.path.append(common_path)
import common
lib_path = os.path.dirname(os.path.abspath(__file__))

class Deploy_RGW:
    def __init__(self, tunings=""):
        self.all_conf_data = common.Config(common_path + "/all.conf")
        self.cluster = {}
        self.cluster["user"] = self.all_conf_data.get("user")
        self.cluster["head"] = self.all_conf_data.get("head")
        self.cluster["clients"] = self.all_conf_data.get_list("list_client")
        self.cluster["osd"] = self.all_conf_data.get_list("deploy_osd_servers")
        self.cluster["mon"] = self.all_conf_data.get_list("deploy_mon_servers")
        self.cluster["rgw"] = [self.all_conf_data.get('rgw_server')]
        self.cluster['rgw_num'] = self.all_conf_data.get('rgw_num_per_server')
        self.cluster['rgw_start_index'] = self.all_conf_data.get('rgw_start_index')
        self.cluster['rgw_index'] = [x+int(self.cluster['rgw_start_index']) for x in range(int(self.cluster['rgw_num']))]

    def check_if_rgw_installed(self):
        stdout,stderr = common.pdsh(self.cluster['user'],self.cluster['rgw'],'curl localhost','check_return')
        if re.search('<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',stdout) == None:
            common.printout("ERROR","radosgw is NOT installed correctly!")
        else:
            common.printout("LOG","radosgw is installed correctly")
            
    def rgw_dependency_install(self):
        common.printout("LOG","Install apache2 and fastcgi...")
        #common.pdsh(self.cluster["user"],self.cluster["rgw"],"wget -q -O- https://raw.github.com/ceph/ceph/master/keys/autobuild.asc --no-check-certificate | sudo apt-key add -","check_return")
        #common.pdsh(self.cluster["user"],self.cluster["rgw"],"echo deb http://gitbuilder.ceph.com/apache2-deb-$(lsb_release -sc)-x86_64-basic/ref/master $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/ceph-apache.list","check_return")
        #common.pdsh(self.cluster["user"],self.cluster["rgw"],"echo deb http://gitbuilder.ceph.com/libapache-mod-fastcgi-deb-$(lsb_release -sc)-x86_64-basic/ref/master $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/ceph-fastcgi.list","check_return")
        #common.pdsh(self.cluster["user"],self.cluster['rgw'],'sudo apt-get update','console')
        common.pdsh(self.cluster["user"],self.cluster["rgw"],"sudo apt-get -y install apache2 libapache2-mod-fastcgi","console")
        common.printout('LOG','Installing radosgw and radosgw-agent...')
        common.pdsh(self.cluster["user"],self.cluster["rgw"],"sudo apt-get -y install radosgw radosgw-agent --force-yes","console")
        #common.pdsh(self.cluster["user"],self.cluster["rgw"],"sudo apt-get -y install apache2","check_return")
        common.printout("LOG","Updating apache2 conf")
        line, error = common.pdsh(self.cluster["user"],self.cluster["rgw"],"grep 'ServerName[ ]*' /etc/apache2/apache2.conf | wc -l","check_return")
        lines = line.split()[1]
        if lines is not '0':
            common.pdsh(self.cluster['user'],self.cluster['rgw'],"sudo sed -i.install_rgw_backup 's/ServerName[ ]*.*/ServerName %s/g' /etc/apache2/apache2.conf" %(self.cluster['rgw'][0]),'check_return')
        else:
            common.pdsh(self.cluster['user'],self.cluster['rgw'],'sudo echo "ServerName %s" >> /etc/apache2/apache2.conf' %(self.cluster['rgw'][0]),'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],"sudo a2enmod rewrite; sudo a2enmod fastcgi; sudo a2enmod proxy; sudo a2enmod proxy_http; sudo a2enmod proxy_balancer",'check_return')

        common.pdsh(self.cluster['user'],self.cluster['rgw'],'sudo ceph-authtool --create-keyring /etc/ceph/ceph.client.radosgw.keyring', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'sudo chmod +r /etc/ceph/ceph.client.radosgw.keyring', 'check_return')

        # TODO: automatically add ceph-gw[index] to /etc/environment
        '''
        for i in self.cluster['rgw_index']:
            etc_environment = '/etc/environment'
            lines,stder = common.pdsh(self.cluster['user'],self.cluster['rgw'],'sudo grep %s %s | wc -l' %(self.cluster['rgw'],etc_environment),'check_return')
            if lines != '0':
                common.pdsh(self.cluster['user'],self.cluster['rgw'],"sudo sed -i.install_rgw_backup 's/%s$/ ceph-gw%s/' %s" %(str(i),),'check_return')
            else:
                common.printout('ERROR','/etc/environment file doesn\'t contain the host name for rgw itself')
                sys.exit()
        '''

        for i in self.cluster['rgw_index']:
            host_name_id = self.cluster['rgw'][0]+"-"+str(i)
            common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph auth del client.radosgw.%s' %(host_name_id), 'check_return')
            common.pdsh(self.cluster['user'],self.cluster['rgw'],'sudo ceph-authtool /etc/ceph/ceph.client.radosgw.keyring -n client.radosgw.%s --gen-key' %(host_name_id), 'check_return')
            common.pdsh(self.cluster['user'],self.cluster['rgw'],"sudo ceph-authtool -n client.radosgw.%s --cap osd 'allow rwx' --cap mon 'allow rwx' /etc/ceph/ceph.client.radosgw.keyring" %(host_name_id), 'check_return')
            common.pdsh(self.cluster['user'],self.cluster['rgw'],'sudo ceph -k /etc/ceph/ceph.client.admin.keyring auth add client.radosgw.%s -i /etc/ceph/ceph.client.radosgw.keyring' %(host_name_id), 'check_return')


    def create_pools(self):
        # remove existing pools
        #common.printout("LOG",'Removing existing pools...')
        #common.pdsh(self.cluster['user'],self.cluster['rgw'],'for node in `rados lspools`; do ceph osd pool delete $node $node --yes-i-really-really-mean-it; done; sleep 10','check_return')
        
        # generate new pools
        common.printout('LOG','Generating new pools...')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.buckets 2048 2048', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.buckets.index 1024 1024', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .log 512 512')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool set .rgw.buckets.index crush_ruleset 1', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.gc 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.control 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .users 512 512 ', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .rgw.root 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .users.swift 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'ceph osd pool create .users.uid 512 512', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'sleep 5', 'check_return')

    def init_auth(self):

        common.pdsh(self.cluster['user'],self.cluster['rgw'],'radosgw-admin user create --uid="cosbench" --display-name="cosbench"', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'radosgw-admin subuser create --uid=cosbench --subuser=cosbench:operator --access=full', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'radosgw-admin key create --uid=cosbench --subuser=cosbench:operator --key-type=swift', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'radosgw-admin user modify --uid=cosbench --max-buckets=100000', 'check_return')
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'radosgw-admin subuser modify --uid=cosbench --subuser=cosbench:operator --secret=intel2012 --key-type=swift', 'check_return')

    def gen_conf(self):
        common.printout('LOG', 'updating ceph.conf for radosgw' )
        remote_ceph_conf = "/etc/ceph/ceph.conf"
        ceph_conf_file = lib_path+"/ceph.conf.tmp"
        common.rscp(self.cluster['user'],self.cluster['rgw'][0],ceph_conf_file,remote_ceph_conf)
        common.printout("LOG","The index of rgw instances are {%s..%s}" %(self.cluster['rgw_index'][0],self.cluster['rgw_index'][-1]))
        for i in self.cluster['rgw_index']:
            host_id = self.cluster["rgw"][0]+"-"+str(i)
            
            civetweb_port = 7480 + i
            lines,stder = common.bash('grep "client.radosgw.%s" %s | wc -l' %(host_id,ceph_conf_file), force=True)
            print lines
            if lines != '0':
                common.printout("LOG", "ceph conf already has gateway "+str(i))
                continue
            with open(ceph_conf_file,'a') as f:
                f.write("[client.radosgw.%s]\n" %(host_id))
                f.write("host = %s\n" %(self.cluster['rgw'][0]))
                f.write("keyring = /etc/ceph/ceph.client.radosgw.keyring\n")
                f.write("rgw cache enabled = true\n")
                f.write("rgw cache lru size = 100000\n")
                #f.write("rgw socket path = /var/run/ceph/ceph.client.radosgw.%s.fastcgi.sock\n" %(host_id))
                f.write("rgw thread pool size = 256\n")
                f.write("rgw enable ops log = false\n")
                # enable log
                f.write("log file = /var/log/radosgw/client.radosgw.%s.log\n" %(host_id))
                #using civetweb as front end server
                f.write("rgw frontends =civetweb port=%s\n" %(str(civetweb_port)))
                # bucket index limit
                f.write("rgw override bucket index max shards = 8\n\n")
                #f.write("log file = /dev/null\n\n")
                #f.flush()
            print 'finish rgw ceph.conf for host_id: '+ host_id
        common.bash("cat "+ceph_conf_file, force=True,option="console")
        push_conf_or_not = raw_input("This is the new conf file. Is it corrent? [y/n] ")

        if push_conf_or_not != 'y':
            sys.exit()
        common.printout('LOG','Push ceph conf to all the ceph nodes...')
        ceph_nodes = copy.deepcopy(self.cluster['rgw'])
        ceph_nodes.extend(self.cluster['mon'])
        ceph_nodes.extend(self.cluster['osd'])
        for node in ceph_nodes:
            common.scp(self.cluster['user'],node,ceph_conf_file,remote_ceph_conf)
        

    def add_gw_script(self):
        common.printout('LOG','Adding gateway scripts')
        for i in self.cluster['rgw_index']:
            host_id = self.cluster['rgw'][0]+'-'+str(i)
            common.pdsh(self.cluster['user'],self.cluster['rgw'],"mkdir -p /var/www/radosgw-%s;cd /var/www/radosgw-%s; rm -f s3gw.fcgi;sudo echo '#!/bin/sh' > s3gw.fcgi; sudo echo 'exec /usr/bin/radosgw -c /etc/ceph/ceph.conf -n client.radosgw.%s' >>s3gw.fcgi;sudo chmod +x s3gw.fcgi; chown www-data:www-data /var/www/radosgw-%s; mkdir -p /var/www/proxy"%(host_id,host_id,host_id,host_id), 'check_return')


    def gw_config(self):
        common.printout('LOG','Configuring gateway')
        for i in self.cluster['rgw_index']:
            host_id = self.cluster['rgw'][0]+'-'+str(i)
            common.pdsh(self.cluster['user'],self.cluster['rgw'],"sudo  mkdir -p /var/lib/ceph/radosgw/ceph-radosgw.%s; rm -rf /var/lib/ceph/radosgw/ceph-radosgw.%s/*; sudo mkdir -p /var/log/apache2; sudo mkdir /var/log/radosgw/client.radosgw.%s.log" %(host_id,host_id,host_id) )
        site_root = "/etc/apache2/sites-available/"
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'rm -rf %s/radosgw-*; a2enmod lbmethod_byrequests' %(site_root), 'check_return')
        for i in self.cluster['rgw_index']:
            host_id = self.cluster['rgw'][0]+'-'+str(i)
            cfg="%s/radosgw-%s.conf" %(site_root,host_id)
            with open(cfg,'w') as f:
                f.write("FastCgiExternalServer /var/www/radosw-%s/s3gw.fcgi -socket /var/run/ceph/ceph.client.radosgw.%s.fastcgi.sock\n" %(host_id,host_id)) 
                f.write("<VirtualHost *:80>\n")
                f.write("ServerName %s\n" %(self.cluster['rgw'][0]))
                f.write("DocumentRoot /var/www/radosgw-%s\n" %(host_id))
                f.write("RewriteEngine On\n")
                f.write("RewriteRule ^/([a-zA-Z0-9-_.]*)([/]?.*) /s3gw.fcgi?page=$1&params=$2&%{QUERY_STRING} [E=HTTP_AUTHORIZATION:%{HTTP:Authorization},L]\n")
                f.write("<Directory /var/www/radosgw-%s>\n" %(host_id))
                f.write("Options +ExecCGI\n")
                f.write("AllowOverride All\n")
                f.write("SetHandler fastcgi-script\n")
                f.write( "Order allow,deny\n" )
                f.write( "Allow from all\n" )
                f.write( "AuthBasicAuthoritative Off\n" )
                f.write( "</Directory>\n" )
                f.write( "AllowEncodedSlashes On\n" )
                f.write( "ErrorLog /var/log/apache2/error.log\n" )
                f.write( "ServerSignature Off\n" )
                f.write( "</VirtualHost>\n" )
            common.scp(self.cluster['user'],self.cluster['rgw'][0],cfg,cfg)
            common.pdsh(self.cluster["user"],self.cluster["rgw"],"sudo a2ensite radosgw-%s" %(host_id))
        common.pdsh(self.cluster["user"],self.cluster["rgw"],"sudo a2dissite 000-default; a2enmode rewrite; a2enmod fastcgi;sudo chown www-data:www-data /var/log/apache2")

        common.pdsh(self.cluster["user"],self.cluster["rgw"],"rm -rf %s/proxy" %(site_root))
        cfg = site_root+"/proxy.conf"
        common.pdsh(self.cluster["user"],self.cluster["rgw"],'node=`hostname -s`; echo "<VirtualHost *:80>\nServerName ${node}\nDocumentRoot /var/www/proxy/\nProxyPass / balancer://ceph/\nProxyPassReverse / balancer://ceph/\n<Proxy balancer://ceph>\n" > %s' %(cfg) )
        # TODO: add ceph-gw[start_index] to ceph-gw[end_index] in /etc/hosts
        for i in self.cluster['rgw_index']:
            common.pdsh(self.cluster["user"],self.cluster["rgw"],'echo "BalancerMember http://ceph-gw%s:%s\n">>%s' %(i,str(7480+i),cfg))

        common.pdsh(self.cluster["user"],self.cluster["rgw"],'echo "Order allow,deny\nAllow from all\n</Proxy>\n<Directory /var/www/proxy>\nOrder allow,deny\nAllow from all\n</Directory>\nAllowEncodedSlashes On\nErrorLog /var/log/apache2/error.log\nServerSignature Off\n</VirtualHost>">>%s'%(cfg) )

        common.pdsh(self.cluster["user"],self.cluster["rgw"],"sudo a2ensite proxy; sudo chown www-data:www-data /var/log/apcache2/; sudo chown www-data:www-data /var/run/ceph")

        
    def deploy(self):
        self.rgw_dependency_install()
        self.create_pools()
        self.init_auth()
        self.gen_conf()
        self.add_gw_script()
        self.gw_config()
        common.pdsh(self.cluster['user'],self.cluster['rgw'],'host_name=`hostname -s`; for inst in {%s..%s}; do /usr/bin/radosgw -n client.radosgw.${host_name}-$inst; done'%(self.cluster['rgw_index'][0],self.cluster['rgw_index'][-1]),'check_return' )
