#!/bin/bash

#-------------------------------------------
# Configurable Options
#-------------------------------------------

SSHCMD="ssh -f -o StrictHostKeyChecking=no"
SCPCMD="scp"
INSTALLDIR=/var/lib/multiperf
OUTPUTDIR=/tmp/multiperf
INTERVAL=5
RAMPUP=90
RUNTIME=300

# a spike is the value is greater or lesser 50x of average
SPIKETHRESHOLD=50

RUNID=-1
if [ -f ".run_number" ]; then
        read RUNID < .run_number
fi
if [ $RUNID -eq -1 ]; then
        RUNID=0
fi
RESULTRT=/var/cache/multiperf
RESULTDIR=$RESULTRT/run$RUNID
#RESULTDIR=$RESULTRT/killosdprocess

export SSHCMD SCPCMD INSTALLDIR OUTPUTDIR INTERVAL RAMPUP RUNTIME RUNID RESULTRT RESULTDIR SPIKETHRESHOLD
