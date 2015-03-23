#!/bin/bash

cat /proc/softirqs > $1/softirqs_begin.dat
sleep 10
cat /proc/softirqs > $1/softirqs_10s.dat
sleep 10
cat /proc/softirqs > $1/softirqs_20s.dat
sleep 180
cat /proc/softirqs > $1/softirqs_200s.dat
