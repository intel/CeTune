#!/bin/python
#-*- coding: utf-8 -*-
# this prg tries to change the conf's hosts and its port

import os
import sys
import re

global hosts_old
global hosts_new
hosts_old = 'http://10.10.9.100:8080/auth/v1.0'
hosts_new = 'http://10.4.9.105/auth/v1.0'


def change_hosts(filename):
	change_str(filename,hosts_old,hosts_new)

def change_str(filename,string_old,string_new):
	data = open(filename).read()
	data = re.sub(string_old,string_new,data)
	open(filename,'wb').write(data)

def walk_dir(dir,topdown=True):
	for root,dirs,files in os.walk(dir,topdown):
		for name in files:
			filename = os.path.join(root,name)
			change_hosts(filename)
			print filename

def main():
	walk_dir(sys.argv[1])
	print 'done'
if __name__ == '__main__':
	main()
#change_str(sys.argv[1],hosts_old,hosts_new)
