#!/bin/bash

cat /proc/interrupts > $1/interrupts_begin.dat
sleep 10
cat /proc/interrupts > $1/interrupts_10s.dat
sleep 10
cat /proc/interrupts > $1/interrupts_20s.dat
sleep 180
cat /proc/interrupts > $1/interrupts_200s.dat
