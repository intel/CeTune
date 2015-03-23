#!/bin/bash

# sample run:
# ./run1.sh 128KB-write  read_100con_100obj_10MB_ /cosbench/current "0 10 20" 192.168.4.253 root /data1/rui_script_tests 99999999 ./conf/128KB-write/100_100/
#-------------------------------------------
# Configurable Options
#-------------------------------------------

# TODO: change all these configs as the parameter, which is passed in as the class attributes of the class: Cosbench
#COSBENCH="/cosbench/current"
print $@

#COSBENCH=$3
#RUN_ID=w0
#TIME_OUT=$8
#CONFIG_DIR="./conf/$1/100_100"
#CONFIG_DIR=$9
#CONFIG_PREFIX=$2
#CONFIG_SUFFIX=w.xml
#CONFIG_LIST=$4
#CONFIG_LIST="640 1280"
#CONFIG_LIST="0 5 10 20 40 80"
#CONFIG_LIST="0 5 10 20 40 80 160 320 640 1280"
#CONFIG_LIST="00 01 02 03 04 05 06 07 08 09"
#CONFIG_LIST="$CONFIG_LIST $CONFIG_LIST $CONFIG_LIST"

#REMOTE_SERV=$5
#REMOTE_USER=$6
#REMOTE_DIR=$7
#RW=$1

#print $RW
#print $CONFIG_PREFIX
#print $COSBENCH
#print $CONFIG_LIST
#print $REMOTE_SERV
#print $REMOTE_USER
#print $REMOTE_DIR
#print $TIME_OUT
#print $CONFIG_DIR
